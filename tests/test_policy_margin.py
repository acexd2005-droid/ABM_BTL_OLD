"""Test Giai đoạn 7c: biến cường độ chỉ đạo và hồi quy biên cho vay."""

import numpy as np
import pandas as pd
import pytest

from src.calibration import estimate_policy_margin as pm


@pytest.fixture(scope="module")
def events():
    return pm.load_events()


@pytest.fixture(scope="module")
def estimates(events):
    return pm.estimate_all(events)


def test_events_loaded_and_quarters_consistent(events):
    assert len(events) == 24
    assert (events.quy == "2026Q4").sum() == 2                    # ngoài panel (kết thúc 2026Q3)
    assert (events.q_date == events.quy).all()


def test_shift_rule_moves_only_two_events(events):
    moved = events[events.dich_quy]
    assert sorted(moved.ngay) == ["2023-06-19", "2026-03-30"]     # sau ngày 15 của tháng cuối quý
    assert list(moved.sort_values("ngay").quy_shift) == ["2023Q3", "2026Q2"]
    # ngày chỉ có tháng (2023-02, 2023-07) không dời; ngày 2023-03-15 (đúng ngày 15) không dời
    assert not events[events.ngay.isin(["2023-02", "2023-07", "2023-03-15"])].dich_quy.any()


def test_intensity_values_by_quarter(events):
    # Tính tay từ file CSV (xem quy tắc 0/1/2 trong docstring)
    shifted = [1, 0, 2, 1, 1, 2, 0, 1, 1, 0, 1, 0, 0, 1, 0]
    unshifted = [1, 0, 2, 1, 1, 2, 0, 1, 1, 0, 1, 0, 1, 1, 0]
    assert list(pm.quarterly_intensity(events, True).I) == shifted
    assert list(pm.quarterly_intensity(events, False).I) == unshifted
    assert list(pm.quarterly_intensity(events, True).DH) == [1, 2, 1] + [0] * 12   # 2023Q1; 2023Q2 (2 QĐ); 2023Q3 (QĐ 19/6 dời)
    assert list(pm.quarterly_intensity(events, False).DH)[:3] == [1, 3, 0]


def test_cong_bo_and_dieu_hanh_not_counted_in_intensity(events):
    excluded = events[events.loai.isin(pm.EXCLUDED)]
    assert (excluded.intensity_doc == 0).all()
    q = pm.quarterly_intensity(events, False)
    # 2024Q1 có cong_bo_LS_cho_vay nhưng I vẫn do yeu_cau_giam_LS_cho_vay quyết định = 1
    assert q.loc[q.quy == "2024Q1", "I"].iloc[0] == 1
    assert q.loc[q.quy == "2023Q2", "I"].iloc[0] == 0               # chỉ có thay_doi_LS_dieu_hanh


def test_lending_target_rule(events):
    two = events[events.intensity_doc == 2]
    assert set(two.ngay) == {"2023-08-14", "2024-05-29", "2026-10-18"}
    # mục tiêu chỉ cho lãi suất huy động (2026-10-21) không tính là mục tiêu cho vay
    assert events.loc[events.ngay == "2026-10-21", "intensity_doc"].iloc[0] == 1


def test_inconsistent_quarter_raises(tmp_path):
    bad = pd.DataFrame({"ngay": ["2023-05-10"], "quy": ["2023Q1"], "loai": ["yeu_cau_giam_LS_cho_vay"],
                        "muc_tieu_dinh_luong": [None]})
    f = tmp_path / "bad.csv"
    bad.to_csv(f, index=False)
    with pytest.raises(ValueError):
        pm.load_events(f)


def test_panel_definitions(events):
    df, s = pm.build_panel(events, True)
    assert len(s) == 112
    r = s[(s.bank_id == "ACB") & (s.t == 5)].iloc[0]
    d = df[df.bank_id == "ACB"].sort_values("t").set_index("t")
    assert r.margin == pytest.approx(d.loc[5, "loan_rate_pct"] - (d.loc[4, "deposit_rate_pct"] + 0.15))
    assert r.I == 1 and r.I_lag == 1                                         # 2024Q1 và 2023Q4 đều có văn bản (I = 1)


def test_on_lag_alignment(events):
    df, s = pm.build_panel(events, True)
    r = s[(s.bank_id == "ACB") & (s.t == 5)].iloc[0]           # t = 5 -> 2024Q1; ON_{t-1} = ON(2023Q4) = 0.680
    assert r.ON1 == pytest.approx(0.680)


def test_main_coefficient_matches_independent_lsdv(events, estimates):
    """Đối chiếu hệ số I_t của biên thực (dời quý, có DH) với hồi quy biến giả ngân hàng tự viết."""
    est, _ = estimates
    row = est[(est.equation == "margin") & (est.I_def == "dich_quy") & (est.kiem_soat_DH) & (est.dang == "lin")
              & (est.parameter == "I_t")].iloc[0]
    df, s = pm.build_panel(events, True)
    D = pd.get_dummies(s.bank_id).to_numpy(float)
    X = np.column_stack([s.I, s.I_lag, s.ON1, s.DH, D])
    b = np.linalg.lstsq(X, s.margin.to_numpy(), rcond=None)[0]
    assert row.coef == pytest.approx(b[0])
    assert row.n == 112 and row.n_clusters == 8


def test_pipeline_outputs(events, estimates):
    est, boot = estimates
    assert {"margin", "dRL", "pt1_resid_2step", "pt1_onestep"} == set(est.equation)
    assert {"dich_quy", "khong_dich"} == set(est.I_def)
    assert len(boot) == 8 and (boot.B == 9999).all()
    assert (boot.ci_boot_lo < boot.coef).all() and (boot.coef < boot.ci_boot_hi).all()
    assert "I2_minus_I1" in set(est.parameter) and "I_sum" in set(est.parameter)
    q = pm.quarterly_check(events, True)
    assert (q["T"] == 14).all()
    q_desc, by_i = pm.descriptive(events)
    assert list(by_i.so_quy) == [6, 6, 2]


def test_spec_sensitivity_sign_depends_on_on_control(events):
    sp = pm.spec_sensitivity(events)
    g = lambda spec, outcome="margin", d="dich_quy": sp[(sp.dac_ta == spec) & (sp.outcome == outcome) & (sp.I_def == d)].coef_I_t.iloc[0]
    # Đối chiếu số đã được reviewer tính lại độc lập
    assert g("I_t") == pytest.approx(0.028, abs=1e-3)
    assert g("I_t, I_t-1") == pytest.approx(0.043, abs=1e-3)
    assert g("I_t, I_t-1, ON, DH (cơ sở)") == pytest.approx(0.2169, abs=5e-4)
    assert g("I_t, I_t-1, ON") == pytest.approx(0.259, abs=1e-3)            # có ON, không DH
    # Δ lãi suất cho vay: ÂM khi không kiểm soát ON, đổi dấu khi có ON
    assert g("I_t", "dRL") == pytest.approx(-0.2203, abs=5e-4) and g("I_t, ON", "dRL") > 0
    assert g("I_t, I_t-1, DH (không ON)") < 0.1 < g("I_t, I_t-1, ON, DH (cơ sở)")


def test_residual_and_dummy_rows_match_independent_calc(events, estimates):
    """Phần dư PT1 (d1) hai bước và I2-I1 tính lại độc lập (LSDV)."""
    est, _ = estimates
    df, s = pm.build_panel(events, True)
    D = pd.get_dummies(s.bank_id).to_numpy(float)
    x = (s.c_main_lag - s.rL_lag).to_numpy()
    X1 = np.column_stack([x, s.ON1c, D])
    b1 = np.linalg.lstsq(X1, s.dRL.to_numpy(), rcond=None)[0]
    u = s.dRL.to_numpy() - X1 @ b1
    X2 = np.column_stack([s.I, s.I_lag, s.DH, D])
    b2 = np.linalg.lstsq(X2, u, rcond=None)[0]
    row = est[(est.equation == "pt1_resid_2step") & (est.I_def == "dich_quy") & est.kiem_soat_DH & (est.dang == "lin")
              & (est.parameter == "I_t")].iloc[0]
    assert row.coef == pytest.approx(b2[0])
    X3 = np.column_stack([s.I1, s.I2, s.ON1, s.DH, D])
    b3 = np.linalg.lstsq(X3, s.margin.to_numpy(), rcond=None)[0]
    d = est[(est.equation == "margin") & (est.I_def == "dich_quy") & est.kiem_soat_DH & (est.dang == "dum")
            & (est.parameter == "I2_minus_I1")].iloc[0]
    assert d.coef == pytest.approx(b3[1] - b3[0])
