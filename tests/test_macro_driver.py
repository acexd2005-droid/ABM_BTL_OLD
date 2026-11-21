"""Giai đoạn 8: biến vĩ mô ngoại sinh (ON) trong phương trình huy động."""

import numpy as np
import pandas as pd
import pytest

from src.analysis.experiments import load_config
from src.core.model import ABMModel
from tests.test_golden import ROOT, GOLDEN, SEEDS, run_model

BANKS = ROOT / "data/clean/abm_initial_8nganhang_2023Q1.csv"
ON_CSV = ROOT / "data/raw/sbv_lnh_qua_dem_theo_quy.csv"


def rows():
    return pd.read_csv(BANKS).to_dict("records")


def build(scenario="A", n_months=None, seed=202611, **extra):
    cfg = load_config()
    params = dict(cfg["parameters"])
    params.update(extra)
    return ABMModel(scenario, n_months or cfg["n_months"], seed, params, rows())


def write_on(tmp_path, values, start="2023Q1", name="on.csv"):
    q = pd.period_range(start, periods=len(values), freq="Q")
    f = tmp_path / name
    pd.DataFrame({"quy": [str(x) for x in q], "bq_gian_don": values}).to_csv(f, index=False)
    return str(f)


def test_defaults_in_code_and_yaml():
    m = ABMModel(seed=1)
    p = load_config()["parameters"]
    assert m.macro_driver == p["macro_driver"] == "none"
    assert m.macro_dep_speed == pytest.approx(p["macro_dep_speed"])
    assert m.macro_dep_spread == pytest.approx(p["macro_dep_spread"])
    assert m.macro_lending_on_coef == p["macro_lending_on_coef"] == 0.0
    assert m.macro_lending_on_ref == pytest.approx(p["macro_lending_on_ref"])
    assert m.macro_on_path == p["macro_on_path"]


def test_yaml_values_trace_to_stage7b_and_data():
    p = load_config()["parameters"]
    e = pd.read_csv(ROOT / "reports/calibration/estimates_stage7b.csv", keep_default_na=False, na_values=[""])
    d1 = e[(e.equation == "PT5-ON") & (e.variant == "d") & (e.lag_on == 1) & (e["sample"] == "N112")]
    phi = d1[d1.parameter == "phi"].coef.iloc[0]
    spread = d1[d1.parameter == "spread_equilibrium"].coef.iloc[0]
    assert p["macro_dep_speed"] == pytest.approx(phi, abs=5e-4)
    assert p["macro_dep_spread"] == pytest.approx(spread, abs=5e-5)
    on = pd.read_csv(ON_CSV).set_index("quy").bq_gian_don
    assert p["macro_lending_on_ref"] == pytest.approx(on.loc["2023Q1":"2026Q2"].mean(), abs=5e-5)


# (a) golden với none (mặc định và tường minh)
@pytest.mark.parametrize("scenario", "ABC")
def test_a_none_matches_golden(scenario):
    cfg = load_config()
    cfg["parameters"]["macro_driver"] = "none"
    for seed in SEEDS:
        hist, bank = run_model(scenario, seed, cfg)
        for name, frame in (("history", hist), ("bank_history", bank)):
            expected = pd.read_csv(GOLDEN / f"{name}_{scenario}_{seed}.csv", float_precision="round_trip")
            pd.testing.assert_frame_equal(frame[list(expected.columns)], expected,
                                          check_exact=False, atol=1e-9, rtol=0)


# (b) exogenous với speed = 0 và coef = 0 trùng none
@pytest.mark.parametrize("scenario", "ABC")
def test_b_exogenous_with_zero_effects_equals_none(scenario):
    cfg = load_config()
    base_h, base_b = run_model(scenario, 202611, cfg)
    cfg["parameters"].update(macro_driver="exogenous", macro_dep_speed=0.0, macro_lending_on_coef=0.0)
    h, b = run_model(scenario, 202611, cfg)
    pd.testing.assert_frame_equal(h, base_h, check_exact=False, atol=1e-9, rtol=0)
    pd.testing.assert_frame_equal(b, base_b, check_exact=False, atol=1e-9, rtol=0)


# (c) đúng độ trễ 1 quý: tốc độ 1, spread 0, drift 0 => deposit_rate_t = ON_{t-1}
def test_c_lag_is_one_quarter_and_holds_after_last_data(tmp_path):
    values = [1.0 + 0.5 * i for i in range(15)]          # 2023Q1..2026Q3, khác nhau từng quý
    path = write_on(tmp_path, values)
    m = build(macro_driver="exogenous", macro_on_path=path, macro_dep_speed=1.0, macro_dep_spread=0.0,
              base_deposit_rate_step=0.0, deposit_competition=0.0)
    for i in range(18):
        m.step()
        expected = values[min(i, 14)]                    # bước đầu (2023Q2) dùng ON(2023Q1); sau 2026Q3 giữ nguyên
        assert [b.deposit_rate for b in m.banks] == pytest.approx([expected] * 8)


def test_c_uses_real_data_series():
    m = build(macro_driver="exogenous")
    on = pd.read_csv(ON_CSV).set_index("quy").bq_gian_don
    assert m._macro_on[0] == pytest.approx(on["2023Q1"])
    assert m._macro_on[14] == pytest.approx(on["2026Q3"]) == pytest.approx(3.946)
    m.month = 3
    assert m.macro_on_previous() == pytest.approx(on["2023Q4"])
    m.month = 17
    assert m.macro_on_previous() == pytest.approx(3.946)


# (d) tắt chính sách (A), không học, ON hằng, drift = 0 => deposit_rate hội tụ về ON + spread
def test_d_converges_to_on_plus_spread(tmp_path):
    path = write_on(tmp_path, [4.0] * 15)
    m = build(n_months=200, macro_driver="exogenous", macro_on_path=path, base_deposit_rate_step=0.0,
              deposit_competition=0.0, adaptive_learning=False)
    m.run()
    target = 4.0 + m.macro_dep_spread
    assert [b.deposit_rate for b in m.banks] == pytest.approx([target] * 8, abs=1e-6)


# (e) kịch bản C không giảm số hạng neo ON (chỉ giảm desired_increase)
def test_e_scenario_c_does_not_cap_the_on_anchor(tmp_path):
    path = write_on(tmp_path, [3.0 + 0.1 * i for i in range(15)])
    kw = dict(macro_driver="exogenous", macro_on_path=path, base_deposit_rate_step=0.05, deposit_competition=0.0)
    a, c = build("A", **kw), build("C", **kw)
    pm = a.policy_month
    for _ in range(pm):
        a.step(); c.step()
    prev_a = np.array([b.deposit_rate for b in a.banks])
    prev_c = np.array([b.deposit_rate for b in c.banks])
    assert prev_a == pytest.approx(prev_c)                     # trước chính sách A = C
    on = a.macro_on_previous()
    a.step(); c.step()
    d_a = np.array([b.deposit_rate for b in a.banks]) - prev_a
    d_c = np.array([b.deposit_rate for b in c.banks]) - prev_c
    anchor = a.macro_dep_speed * (on + a.macro_dep_spread - prev_a)
    cap = a.deposit_cap_factor
    assert d_a == pytest.approx(0.05 + anchor)
    assert d_c == pytest.approx(0.05 * cap + anchor)           # chỉ desired_increase bị nhân cap
    assert (d_a - d_c) == pytest.approx(0.05 * (1 - cap))      # neo ON giống hệt nhau


# (f) thiếu dữ liệu => lỗi
def test_f_missing_data_raises(tmp_path):
    kw = dict(macro_driver="exogenous")
    with pytest.raises(ValueError):                              # thiếu quý khởi tạo
        build(macro_on_path=write_on(tmp_path, [1.0] * 10, start="2023Q2", name="a.csv"), **kw)
    gap = pd.DataFrame({"quy": ["2023Q1", "2023Q2", "2023Q4", "2024Q1"], "bq_gian_don": [1, 2, 3, 4]})
    gap.to_csv(tmp_path / "gap.csv", index=False)
    with pytest.raises(ValueError):                              # thiếu quý 2023Q3 giữa chuỗi
        build(macro_on_path=str(tmp_path / "gap.csv"), **kw)
    with pytest.raises(ValueError):                              # không có file
        build(macro_on_path=str(tmp_path / "khong_co.csv"), **kw)
    nan = write_on(tmp_path, [1.0, float("nan"), 2.0], name="nan.csv")
    with pytest.raises(ValueError):
        build(macro_on_path=nan, **kw)
    # driver none không đọc file
    build(macro_driver="none", macro_on_path=str(tmp_path / "khong_co.csv"))


def test_invalid_options_raise():
    with pytest.raises(ValueError):
        build(macro_driver="khac")
    with pytest.raises(ValueError):
        build(macro_driver="exogenous", macro_dep_speed=1.5)
    with pytest.raises(ValueError):
        build(macro_driver="none", macro_lending_on_coef=0.45)


def test_lending_on_term_shifts_first_step_by_hand_amount():
    base = build(macro_driver="exogenous", macro_dep_speed=0.0)
    ext = build(macro_driver="exogenous", macro_dep_speed=0.0, macro_lending_on_coef=0.45)
    base.step(); ext.step()
    on0 = 4.817                                                  # ON 2023Q1
    shift = base.pass_through * 0.45 * (on0 - ext.macro_lending_on_ref)
    for b0, b1 in zip(base.banks, ext.banks):
        assert b1.loan_rate - b0.loan_rate == pytest.approx(shift)


def test_compare_script_smoke(tmp_path):
    from src.analysis import compare_macro_driver as cm
    cfg, hist, bank = cm.run_all(2)
    assert set(hist.variant) == set(cm.VARIANTS) and hist.run_id.max() == 1
    actual = cm.actual_series(tmp_path)
    fit = cm.fit_table(hist, actual)
    assert len(fit) == 2 * len(cm.VARIANTS) and (fit.RMSE_tho >= fit.RMSE_khu_muc - 1e-12).all()
    # none: không có chữ V (đáy ở đầu chuỗi hoặc rất nông); exogenous: giảm đáng kể
    none = fit[(fit.bien_the == "none") & (fit.chuoi == "cho_vay")].iloc[0]
    exo = fit[(fit.bien_the == "exogenous") & (fit.chuoi == "cho_vay")].iloc[0]
    assert none.ty_le_giam < 0.1 < exo.ty_le_giam
    chk = cm.checks_table(hist, bank, cfg)
    assert (chk.chenh_toi_da_A_B_C_truoc_chinh_sach == 0).all()
    assert (chk.vi_pham_B_cao_hon_A == 0).all() and (chk.vi_pham_C_cao_hon_A == 0).all()
    drift = cm.drift_table(bank, cfg)
    assert drift.can_bang_ngu_y_ON_tb.iloc[0] == pytest.approx(
        drift.ON_tb_2023Q1_2026Q2.iloc[0] + drift.spread.iloc[0] + drift.drift_chia_phi.iloc[0])


def test_anchor_respects_deposit_rate_bounds(tmp_path):
    """Neo mạnh (tốc độ 1) tới mục tiêu ngoài [0, 14]: lãi suất huy động bị chặn đúng ở 14 và 0."""
    high = build(macro_driver="exogenous", macro_on_path=write_on(tmp_path, [4.0] * 15, name="h.csv"),
                 macro_dep_speed=1.0, macro_dep_spread=20.0, base_deposit_rate_step=0.0, deposit_competition=0.0)
    high.step()
    assert [b.deposit_rate for b in high.banks] == pytest.approx([14.0] * 8)
    low = build(macro_driver="exogenous", macro_on_path=write_on(tmp_path, [4.0] * 15, name="l.csv"),
                macro_dep_speed=1.0, macro_dep_spread=-20.0, base_deposit_rate_step=0.0, deposit_competition=0.0)
    low.step()
    assert [b.deposit_rate for b in low.banks] == pytest.approx([0.0] * 8)
