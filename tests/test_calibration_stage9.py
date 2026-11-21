"""Giai đoạn 9: hiệu chỉnh bằng mô phỏng.

- Script ước lượng GĐ7/7b đọc hằng số từ YAML (không còn bản sao cứng).
- Khóa tùy chọn depositor_min_growth: null = hành vi cũ; đặt số => sàn bất đối xứng.
- Quy tắc Bước 1, hàm mục tiêu, mốc ngây thơ, cấu hình scenarios_calibrated.yaml và mục 6.
"""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

import src.calibration.calibrate_stage9 as c9
import src.calibration.estimate_deposit_equation as de
import src.calibration.estimate_equations as ee
from src.agents.depositors import DepositorBlock
from src.analysis.experiments import load_config
from src.core.model import ABMModel

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/clean/abm_initial_8nganhang_2023Q1.csv"
STAGE9 = ROOT / "reports/calibration/stage9"
GD9A_KEYS = ("target_margin", "funding_cost_add", "deposit_ldr_target", "demand_pressure_cap",
             "depositor_base_growth", "depositor_max_growth", "borrower_growth_min", "borrower_growth_max",
             "compliance_pressure_coef", "compliance_pressure_center", "compliance_margin_coef",
             "compliance_prob_min", "compliance_prob_max")


def rows():
    return pd.read_csv(DATA).to_dict("records")


def yaml_params():
    with open(ROOT / "configs/scenarios.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)["parameters"]


# ---------------------------------------------------------------- script ước lượng đọc YAML

def test_estimation_scripts_read_constants_from_yaml():
    p = yaml_params()
    assert ee.FUNDING_CONST == p["funding_cost_add"]
    assert ee.TARGET_MARGIN == p["target_margin"]
    assert ee.DEPOSITOR_BASE == p["depositor_base_growth"]
    assert ee.REFERENCE_RATE == p["borrower_reference_rate"]
    assert de.PIVOT == p["deposit_ldr_target"]
    assert de.CLIP == p["demand_pressure_cap"]
    assert de.FUNDING_CONST == p["funding_cost_add"]
    assert de.MARGIN_CONST == pytest.approx(p["target_margin"] + p["loan_spread_add"])


def test_estimation_scripts_have_no_hardcoded_copies():
    for name in ("estimate_equations.py", "estimate_deposit_equation.py"):
        src = (ROOT / "src/calibration" / name).read_text(encoding="utf-8")
        for bad in ("FUNDING_CONST = 0.15", "TARGET_MARGIN = 3.2", "DEPOSITOR_BASE = 0.004",
                    "PIVOT = 0.82", "CLIP = 0.5", "KHÔNG nằm trong YAML"):
            assert bad not in src, (name, bad)


# ---------------------------------------------------------------- depositor_min_growth

def test_min_growth_default_is_old_behaviour():
    assert yaml_params()["depositor_min_growth"] is None
    p = dict(load_config()["parameters"])
    stripped = {k: v for k, v in p.items() if k != "depositor_min_growth"}
    for sc in "ABC":
        a = ABMModel(sc, 18, 202611, p, rows())
        b = ABMModel(sc, 18, 202611, stripped, rows())
        a.run()
        b.run()
        pd.testing.assert_frame_equal(pd.DataFrame(a.bank_history), pd.DataFrame(b.bank_history), check_exact=True)


def test_min_growth_asymmetric_floor():
    m = ABMModel("A", 1, 1, {"depositor_min_growth": -0.01, "depositor_max_growth": 0.2}, None)
    d = m.depositor
    assert d.growth(0.0, 10.0) == -0.01            # raw rất âm -> sàn riêng
    assert d.growth(100.0, 0.0) == 0.2             # raw rất dương -> trần
    old = DepositorBlock(m, max_growth=0.2)
    assert old.growth(0.0, 10.0) == -0.2           # None -> -max_growth
    with pytest.raises(ValueError):
        ABMModel("A", 1, 1, {"depositor_min_growth": 0.05, "depositor_max_growth": 0.04}, None)


# ---------------------------------------------------------------- Bước 1

def test_growth_rules_match_independent_computation():
    panel = c9.load_panel()
    gp, st = c9.growth_rules(panel, asymmetric=True, exclude=False)
    p = pd.read_csv(ROOT / "data/clean/abm_panel_8nganhang_2023Q1_2026Q3.csv", encoding="utf-8-sig")
    tot = p.groupby("period")[["deposits", "loans"]].sum().sort_index()
    g = tot.pct_change().loc["2023Q2":"2025Q2"]
    assert len(g) == 9
    assert gp["depositor_base_growth"] == pytest.approx(g.deposits.mean(), abs=1e-14)
    assert gp["borrower_base_growth"] == pytest.approx(g.loans.mean(), abs=1e-14)
    p = p.sort_values(["bank_id", "period"])
    p["gd"] = p.groupby("bank_id").deposits.pct_change()
    w = p[(p.period >= "2023Q2") & (p.period <= "2025Q2")]
    assert len(w) == 72 and st["n_obs"] == 72
    assert gp["depositor_min_growth"] == pytest.approx(np.percentile(w.gd, 2.5))
    assert gp["depositor_max_growth"] == pytest.approx(np.percentile(w.gd, 97.5))
    sym, _ = c9.growth_rules(panel, asymmetric=False, exclude=False)
    assert sym["depositor_min_growth"] is None
    assert sym["depositor_max_growth"] == max(abs(gp["depositor_min_growth"]), abs(gp["depositor_max_growth"]))


def test_exclusion_drops_known_anomalies():
    panel = c9.load_panel()
    c9.check_anomalies_listed()
    assert int(panel.anomaly.sum()) == len(c9.KNOWN_ANOMALIES)
    _, full = c9.growth_rules(panel, True, False)
    _, excl = c9.growth_rules(panel, True, True)
    assert excl["n_obs"] == full["n_obs"] - 3


# ---------------------------------------------------------------- lưới, mục tiêu, ngây thơ

def test_grid_size_and_margin_mapping():
    pts = c9.grid_points()
    assert len(pts) == 8 * 6 * 4 * 4 * 2 == 1536
    q = c9.apply_point({"loan_spread_add": 1.35}, pts[0], 1.09)
    assert q["target_margin"] == pytest.approx(3.8 - 1.35)
    assert q["deposit_ldr_target"] == 0.82


def test_objective_zero_on_perfect_fit_and_window():
    a = np.arange(14, dtype=float)
    assert c9.objective(a, a + 1, a, a + 1)[0] == 0.0
    loan = a.copy()
    loan[9:] += 5.0                                 # sai số ngoài mẫu không vào J
    assert c9.objective(loan, a, a, a)[0] == 0.0
    loan[0] += 3.0                                  # sai số 3 ở 1/9 quý -> RMSE_L = 1
    j, rl, rd = c9.objective(loan, a, a, a)
    assert rl == pytest.approx(1.0) and rd == 0.0 and j == pytest.approx(0.5)


def test_scenario_a_deterministic_across_seeds():
    cfg = load_config(ROOT / "configs/scenarios_calibrated_gd9.yaml")
    p = dict(cfg["parameters"])
    l1, d1, _ = c9.simulate(p, rows(), seed=1, cfg=cfg)
    l2, d2, _ = c9.simulate(p, rows(), seed=999, cfg=cfg)
    assert np.array_equal(l1, l2) and np.array_equal(d1, d2)


def test_naive_on_formula():
    act = pd.DataFrame({"month": range(1, 15), "quarter": [str(pd.Period("2023Q1", freq="Q") + i) for i in range(1, 15)],
                        "actual_loan_rate": np.linspace(9, 10, 14), "actual_deposit_rate": np.linspace(4, 5, 14)})
    on = c9.on_series()
    nv = c9.naive_paths(act, on)
    hold_l, hold_d = nv["ngay_tho_giu_2025Q2"]
    assert np.all(hold_l == act.actual_loan_rate.iloc[8]) and np.all(hold_d == act.actual_deposit_rate.iloc[8])
    on_l, _ = nv["ngay_tho_ON"]
    # 2025Q3: ON_{t-1} = ON_2025Q2; tham chiếu ON_2025Q1
    assert on_l[0] == pytest.approx(act.actual_loan_rate.iloc[8] + 0.45 * (on["2025Q2"] - on["2025Q1"]))
    assert on_l[-1] == pytest.approx(act.actual_loan_rate.iloc[8] + 0.45 * (on["2026Q2"] - on["2025Q1"]))


# ---------------------------------------------------------------- cấu hình hiệu chỉnh

def test_calibrated_yaml_explicit_keys_and_matches_best():
    with open(ROOT / "configs/scenarios_calibrated_gd9.yaml", encoding="utf-8") as f:
        over = yaml.safe_load(f)["parameters"]
    for k in GD9A_KEYS + ("depositor_min_growth", "borrower_base_growth", "macro_driver", "deposit_rate_basis"):
        assert k in over, k
    assert over["macro_driver"] == "exogenous" and over["deposit_rate_basis"] == "term"
    assert over["macro_lending_on_coef"] == 0.0 and over["macro_dep_spread"] == 1.2723   # D1, D3
    assert over["loan_spread_add"] == 1.35                                               # D7/Q1
    base = yaml_params()
    for k in ("depositor_sensitivity", "borrower_elasticity", "policy_pressure", "policy_step"):
        assert over[k] == base[k], k                                                     # không hiệu chỉnh
    best = pd.read_csv(STAGE9 / "best_by_variant_stage9.csv").set_index("bien_the").loc[c9.MAIN_VARIANT]
    assert over["pass_through"] == pytest.approx(best.pass_through)
    assert over["target_margin"] == pytest.approx(best.total_margin - 1.35)
    assert over["base_deposit_rate_step"] == pytest.approx(best.base_deposit_rate_step)
    assert over["deposit_competition"] == pytest.approx(best.deposit_competition)
    assert over["deposit_ldr_target"] == pytest.approx(best.deposit_ldr_target)
    gr = pd.read_csv(STAGE9 / "growth_rules_stage9.csv").set_index("bien_the").loc[c9.MAIN_VARIANT]
    for k in c9.GROWTH_KEYS:
        assert over[k] == pytest.approx(gr[k]), k


def test_calibrated_config_section6():
    cfg = load_config(ROOT / "configs/scenarios_calibrated_gd9.yaml")
    res = c9.section6(cfg, rows())
    assert res["pass"], res
    assert res["max_B_minus_A_after"] <= 0 and res["max_C_minus_A_after"] <= 0
    assert res["max_abs_diff_before"] == 0.0


def test_calibrated_grid_best_is_argmin():
    g = pd.read_csv(STAGE9 / "grid_stage9.csv")
    gm = g[g.bien_the == c9.MAIN_VARIANT]
    assert len(gm) == 1536
    best = pd.read_csv(STAGE9 / "best_by_variant_stage9.csv").set_index("bien_the").loc[c9.MAIN_VARIANT]
    assert math.isclose(best.J, gm.J.min(), rel_tol=0, abs_tol=1e-12)


# ---------------------------------------------------------------- vòng sửa 2

def test_min_growth_positive_floor_warns_but_allowed():
    import warnings
    with pytest.warns(UserWarning, match="depositor_min_growth"):
        ABMModel("A", 1, 1, {"depositor_min_growth": 0.01, "depositor_max_growth": 0.04}, None)
    with warnings.catch_warnings():
        warnings.simplefilter("error")          # sàn <= 0 và null: không cảnh báo
        ABMModel("A", 1, 1, {"depositor_min_growth": -0.01, "depositor_max_growth": 0.04}, None)
        ABMModel("A", 1, 1, {"depositor_max_growth": 0.04}, None)


def test_confounding_files_consistent_with_section6():
    from pathlib import Path
    out = Path(__file__).resolve().parents[1] / "reports/calibration/stage9"
    c = pd.read_csv(out / "confounding_stage9.csv").set_index("cau_hinh")
    s6 = pd.read_csv(out / "section6_stage9.csv")
    cal = s6[s6.cau_hinh == "scenarios_calibrated.yaml"].iloc[0]
    row = c.loc["hieu_chinh_GD9"]
    assert row.max_BmA_theo_quy_va_seed == pytest.approx(cal.max_B_minus_A_after, abs=1e-6)
    assert row.loan_rate_A_sau_CS == pytest.approx(cal.mean_loan_after_A, abs=1e-6)
    assert row.BmA_tb > row.max_BmA_theo_quy_va_seed or row.BmA_tb < 0   # trung bình khác max theo quý/seed
    assert row.BmA_tb <= row.max_BmA_theo_quy_va_seed                      # TB không vượt max
    assert row.xs_tuan_thu_tb_B < c.loc["macro_GD8"].xs_tuan_thu_tb_B
