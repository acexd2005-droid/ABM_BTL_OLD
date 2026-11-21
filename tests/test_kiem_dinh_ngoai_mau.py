"""GD11: khung kiểm định ngoài mẫu. Dữ liệu 2026Q4+ dùng trong test là GIẢ LẬP (sinh ở tmp_path, không ghi vào data/)."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import src.analysis.kiem_dinh_ngoai_mau as k

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data/clean/abm_panel_8nganhang_2023Q1_2026Q3.csv"
BANKS = pd.read_csv(ROOT / "data/clean/abm_initial_8nganhang_2023Q1.csv")


def make_synthetic_panel(tmp_path, quarters=("2026Q4", "2027Q1"), shift=-0.5):
    """GIẢ LẬP: sao chép dòng 2026Q3, đổi nhãn quý, lệch lãi suất `shift` mỗi quý. KHÔNG phải số liệu thực."""
    p = pd.read_csv(PANEL, encoding="utf-8-sig")
    last = p[p["period"] == "2026Q3"]
    add = []
    for i, q in enumerate(quarters, 1):
        d = last.copy()
        d["period"] = q
        d["loan_rate_pct"] = d["loan_rate_pct"] + shift * i
        d["deposit_rate_pct"] = d["deposit_rate_pct"] + shift * i / 2
        add.append(d)
    out = tmp_path / "GIA_LAP_panel.csv"
    pd.concat([p] + add).to_csv(out, index=False)
    return out


def test_no_new_quarters_writes_status_only(tmp_path):
    k.main(["--panel", str(PANEL), "--outdir", str(tmp_path / "o"), "--runs", "2"])
    files = sorted(f.name for f in (tmp_path / "o").iterdir())
    assert files == ["trang_thai_stage11.md"]


def test_validate_panel_rejects_bad_format():
    p = pd.read_csv(PANEL, encoding="utf-8-sig")
    ids = BANKS["bank_id"]
    k.validate_panel(p, ids, "2023Q1")
    with pytest.raises(ValueError, match="thiếu cột"):
        k.validate_panel(p.drop(columns=["casa_ratio"]), ids, "2023Q1")
    with pytest.raises(ValueError, match="Quý thiếu ngân hàng"):
        k.validate_panel(p.iloc[:-1], ids, "2023Q1")
    gap = p[p["period"] != "2025Q1"]
    with pytest.raises(ValueError, match="thiếu quý"):
        k.validate_panel(gap, ids, "2023Q1")
    dup = pd.concat([p, p.iloc[:1]])
    with pytest.raises(ValueError, match="trùng"):
        k.validate_panel(dup, ids, "2023Q1")


def test_actual_series_matches_hand_computation(tmp_path):
    path = make_synthetic_panel(tmp_path, ("2026Q4",))
    p = k.validate_panel(pd.read_csv(path), BANKS["bank_id"], "2023Q1")
    act = k.actual_oos(p, pd.Period("2026Q3", freq="Q")).set_index("quarter")
    g = p[p["period"] == "2026Q4"]
    assert act.loc["2026Q4", "actual_loan_rate"] == pytest.approx((g.loan_rate_pct * g.loans).sum() / g.loans.sum())
    assert act.loc["2026Q4", "actual_deposit_rate"] == pytest.approx((g.deposit_rate_pct * g.deposits).sum() / g.deposits.sum())
    assert list(act.index) == ["2026Q3", "2026Q4"]


def test_synthetic_run_end_to_end_and_marked(tmp_path):
    path = make_synthetic_panel(tmp_path)
    out = tmp_path / "res"
    args = ["--panel", str(path), "--outdir", str(out), "--runs", "3", "--gia-lap"]
    k.main(args)
    summ = pd.read_csv(out / "oos_summary_stage11.csv")
    assert set(summ["du_lieu"]) == {"GIA_LAP"} and list(summ["scenario"]) == ["A", "B", "C"]
    assert (summ["n_quarters"] == 2).all()
    assert "GIẢ LẬP" in (out / "summary_stage11.md").read_text(encoding="utf-8")
    fc = pd.read_csv(out / "oos_forecast_stage11.csv")
    assert len(fc) == 6
    assert np.allclose(fc["loan_error"], fc["loan_forecast"] - fc["loan_actual"])
    d = pd.read_csv(out / "oos_direction_stage11.csv")
    assert len(d) == 2 * 2 * 2   # quý x biến x (B, C)
    # rmse_combined = trung bình cộng hai RMSE; kịch bản gần nhất là argmin
    assert np.allclose(summ["rmse_combined"], 0.5 * summ["loan_rmse"] + 0.5 * summ["dep_rmse"])
    import json
    meta = json.loads((out / "meta_stage11.json").read_text(encoding="utf-8"))
    best = summ.loc[summ["rmse_combined"].idxmin(), "scenario"]
    assert meta["closest_scenario"] == best and meta["du_lieu"] == "GIA_LAP"
    # tái lập: chạy lại cho file giống hệt
    out2 = tmp_path / "res2"
    k.main(["--panel", str(path), "--outdir", str(out2), "--runs", "3", "--gia-lap"])
    for name in ("oos_forecast_stage11.csv", "oos_summary_stage11.csv", "oos_direction_stage11.csv"):
        assert (out / name).read_bytes() == (out2 / name).read_bytes()


def test_config_path_is_parameter(tmp_path):
    """Đổi cấu hình qua --config: kết quả phải đổi (không hard-code tham số)."""
    path = make_synthetic_panel(tmp_path)
    r1 = tmp_path / "r1"
    k.main(["--panel", str(path), "--outdir", str(r1), "--runs", "2", "--gia-lap"])
    alt = tmp_path / "alt.yaml"
    alt.write_text("parameters:\n  pass_through: 0.10\n", encoding="utf-8")
    r2 = tmp_path / "r2"
    k.main(["--panel", str(path), "--config", str(alt), "--outdir", str(r2), "--runs", "2", "--gia-lap"])
    a = pd.read_csv(r1 / "oos_forecast_stage11.csv")["loan_forecast"]
    b = pd.read_csv(r2 / "oos_forecast_stage11.csv")["loan_forecast"]
    assert not np.allclose(a, b)


def test_refuses_data_dir_and_default_outdir_for_synthetic():
    with pytest.raises(ValueError, match="data/"):
        k._check_outdir(ROOT / "data/clean/x", False)
    with pytest.raises(ValueError, match="gia-lap|giả lập|GIẢ"):
        k._check_outdir(k.DEFAULT_OUT, True)


def test_pre_policy_scenarios_equal_in_forecast_inputs():
    """Trước chính sách A/B/C trùng nhau (cùng seed): kiểm tra trên đầu ra run_scenarios."""
    cfg = k.load_config(k.DEFAULT_CONFIG)
    sim = k.run_scenarios(cfg, BANKS.to_dict("records"), 2)
    pre = sim[sim["month"] <= int(cfg["parameters"]["policy_month"])]
    piv = pre.pivot_table(index=["run_id", "month"], columns="scenario", values="loan_rate")
    assert np.allclose(piv["A"], piv["B"]) and np.allclose(piv["A"], piv["C"])


def test_provenance_refusals(tmp_path):
    path = make_synthetic_panel(tmp_path)   # tên GIA_LAP_panel.csv, nằm ngoài data/clean
    with pytest.raises(ValueError, match="gia_lap"):
        k.classify_panel(path, False)
    other = tmp_path / "panel_x.csv"
    other.write_bytes(path.read_bytes())
    with pytest.raises(ValueError, match="ngoài data/clean"):
        k.classify_panel(other, False)
    assert k.classify_panel(other, True) == "GIA_LAP"
    assert k.classify_panel(PANEL, False) == "THUC"
    with pytest.raises(ValueError):
        k.main(["--panel", str(path), "--outdir", str(tmp_path / "o")])


def test_meta_records_panel_provenance(tmp_path):
    import hashlib, json
    path = make_synthetic_panel(tmp_path)
    out = tmp_path / "res"
    k.main(["--panel", str(path), "--outdir", str(out), "--runs", "2", "--gia-lap"])
    meta = json.loads((out / "meta_stage11.json").read_text(encoding="utf-8"))
    assert meta["panel_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert meta["panel_rows"] == len(pd.read_csv(path)) and meta["panel_cu_rows_checked_unchanged"] == len(pd.read_csv(PANEL))
    assert "GIẢ LẬP" in (out / "summary_stage11.md").read_text(encoding="utf-8")


def test_old_numbers_must_be_unchanged(tmp_path):
    path = make_synthetic_panel(tmp_path)
    new = pd.read_csv(path)
    old = pd.read_csv(PANEL, encoding="utf-8-sig")
    assert k.check_old_unchanged(new, old) == len(old)
    chg = new.copy()
    chg.loc[0, "loans"] = chg.loc[0, "loans"] + 1
    with pytest.raises(ValueError, match="thay đổi"):
        k.check_old_unchanged(chg, old)
    with pytest.raises(ValueError, match="thiếu"):
        k.check_old_unchanged(new.iloc[1:], old)
    bad = tmp_path / "GIA_LAP_chg.csv"
    chg.to_csv(bad, index=False)
    with pytest.raises(ValueError, match="thay đổi"):
        k.main(["--panel", str(bad), "--outdir", str(tmp_path / "o"), "--runs", "2", "--gia-lap"])


def test_direction_has_noise_columns_and_on_status(tmp_path):
    path = make_synthetic_panel(tmp_path)
    out = tmp_path / "res"
    k.main(["--panel", str(path), "--outdir", str(out), "--runs", "3", "--gia-lap"])
    d = pd.read_csv(out / "oos_direction_stage11.csv")
    for c in ("abs_effect", "sd_effect_across_seeds", "signal_to_noise"):
        assert c in d.columns
    assert np.allclose(d["abs_effect"], d["forecast_effect_vs_A"].abs())
    assert "|B−C|" in (out / "summary_stage11.md").read_text(encoding="utf-8")
    on = pd.DataFrame({"quy": ["2026Q4", "2026Q3"], "phien_cuoi": ["2026-11-19", "2026-09-30"]})
    st = k.on_quarter_status(on)["trang_thai"]
    assert st[0].startswith("CHƯA KẾT THÚC") and st[1] == "đủ quý"
