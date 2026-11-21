"""GD9b: hiệu chỉnh lại GD9 theo D9 (Q6 lưới ràng buộc, Q7 bù tăng trưởng).

Kiểm tra: lưới đúng như đăng ký, bù Q7 đúng quy tắc và khớp giá trị dự kiến, YAML sinh ra khớp nghiệm,
bản GD9 được giữ, argmin/quy tắc hòa, mục 6, các khóa không hiệu chỉnh giữ nguyên.
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

import src.calibration.calibrate_stage9 as c9
import src.calibration.calibrate_stage9b as c9b
from src.analysis.experiments import load_config

ROOT = Path(__file__).resolve().parents[1]
S9 = ROOT / "reports/calibration/stage9"
S9B = ROOT / "reports/calibration/stage9b"
DATA = ROOT / "data/clean/abm_initial_8nganhang_2023Q1.csv"


def rows():
    return pd.read_csv(DATA).to_dict("records")


def params_of(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)["parameters"]


def test_grid_as_registered():
    reg = (S9B / "DANG_KY_TRUOC_GD9b.md").read_text(encoding="utf-8")
    assert "6 × 8 × 4 × 4 × 2 = **1536**" in reg
    g = c9b.GRID_B
    assert g["pass_through"] == (0.15, 0.20, 0.25, 0.30, 0.35, 0.40)
    assert g["total_margin"] == (3.4, 3.6, 3.8, 4.0, 4.2, 4.4, 4.6, 4.8)
    assert g["base_deposit_rate_step"] == c9.GRID["base_deposit_rate_step"]
    assert g["deposit_competition"] == c9.GRID["deposit_competition"]
    assert g["ldr_choice"] == c9.GRID["ldr_choice"] == ("0.82", "ldr_mean")
    pts = c9.grid_points(g)
    assert len(pts) == 1536
    assert pts[0]["ldr_choice"] == "0.82" and pts[1]["ldr_choice"] == "ldr_mean"   # thứ tự quy tắc hòa
    q = c9.apply_point({"loan_spread_add": 1.35}, pts[0], 1.09)
    assert q["target_margin"] == pytest.approx(3.4 - 1.35)


def test_gd9_config_kept_with_header():
    txt = (ROOT / "configs/scenarios_calibrated_gd9.yaml").read_text(encoding="utf-8")
    assert txt.splitlines()[0].startswith("# BẢN GD9 GIỮ ĐỂ ĐỐI CHIẾU")
    p = params_of(ROOT / "configs/scenarios_calibrated_gd9.yaml")
    best = pd.read_csv(S9 / "best_by_variant_stage9.csv").set_index("bien_the").loc[c9.MAIN_VARIANT]
    assert p["pass_through"] == pytest.approx(best.pass_through) == pytest.approx(0.45)
    assert p["target_margin"] == pytest.approx(best.total_margin - 1.35)
    assert p["depositor_base_growth"] == c9b.GD9_BASE["depositor_base_growth"]
    assert p["borrower_base_growth"] == c9b.GD9_BASE["borrower_base_growth"]


def test_bu_rule_and_expected_values():
    panel = c9.load_panel()
    cfg, _ = c9.base_params()
    bu = c9b.growth_offset(panel, rows(), cfg)
    c9b.check_expected_bu(bu)                          # trong 1e-9 của giá trị đăng ký
    assert bu["delta_D"] == pytest.approx(0.0100059, abs=1e-7)
    assert bu["delta_L"] == pytest.approx(-0.0154334, abs=1e-7)
    # thước đo dữ liệu đúng như đăng ký
    assert bu["g_D_du_lieu"] == pytest.approx(0.0397609337, abs=1e-10)
    assert bu["g_L_du_lieu"] == pytest.approx(0.04475110499, abs=1e-10)
    # cộng một bước
    assert bu["depositor_base_growth_moi"] == pytest.approx(bu["depositor_base_growth_GD9"] + bu["delta_D"], abs=1e-15)
    out = c9b.apply_offset({"depositor_base_growth": 0.04, "borrower_base_growth": 0.05}, bu)
    assert out["depositor_base_growth"] == pytest.approx(0.04 + bu["delta_D"])
    assert out["borrower_base_growth"] == pytest.approx(0.05 + bu["delta_L"])
    bad = dict(bu, depositor_base_growth_moi=bu["depositor_base_growth_moi"] + 1e-6)
    with pytest.raises(SystemExit):
        c9b.check_expected_bu(bad)


def test_calibrated_yaml_matches_gd9b_best():
    p = params_of(ROOT / "configs/scenarios_calibrated.yaml")
    best = pd.read_csv(S9B / "best_by_variant_stage9b.csv").set_index("bien_the").loc[c9.MAIN_VARIANT]
    gr = pd.read_csv(S9B / "growth_rules_stage9b.csv").set_index("bien_the").loc[c9.MAIN_VARIANT]
    assert p["pass_through"] == pytest.approx(best.pass_through)
    assert p["target_margin"] == pytest.approx(best.total_margin - 1.35)
    assert p["base_deposit_rate_step"] == pytest.approx(best.base_deposit_rate_step)
    assert p["deposit_competition"] == pytest.approx(best.deposit_competition)
    assert p["deposit_ldr_target"] == pytest.approx(best.deposit_ldr_target)
    for k in c9.GROWTH_KEYS:
        assert p[k] == pytest.approx(gr[k]), k
    # bù Q7 = GD9 base + Δ
    bu = pd.read_csv(S9B / "bu_tang_truong_stage9b.csv").iloc[0]
    assert p["depositor_base_growth"] == pytest.approx(c9b.GD9_BASE["depositor_base_growth"] + bu.delta_D, abs=1e-12)
    assert p["borrower_base_growth"] == pytest.approx(c9b.GD9_BASE["borrower_base_growth"] + bu.delta_L, abs=1e-12)
    # ngưỡng chặn giữ như GD9
    p9 = params_of(ROOT / "configs/scenarios_calibrated_gd9.yaml")
    for k in ("depositor_min_growth", "depositor_max_growth", "borrower_growth_min", "borrower_growth_max"):
        assert p[k] == p9[k], k
    # khóa không hiệu chỉnh
    base = params_of(ROOT / "configs/scenarios.yaml")
    for k in ("depositor_sensitivity", "borrower_elasticity", "policy_pressure", "policy_step"):
        assert p[k] == base[k], k
    assert p["loan_spread_add"] == 1.35 and p["macro_dep_spread"] == 1.2723
    for k in c9.EXPLICIT_KEYS:                       # đủ khóa tường minh
        assert k in p, k
    # mỗi dòng giá trị đều có comment nguồn
    lines = (ROOT / "configs/scenarios_calibrated.yaml").read_text(encoding="utf-8").splitlines()
    assert all("#" in ln for ln in lines if re.match(r"^  \w+:", ln))
    assert "Δ_D" in " ".join(lines) and "Δ_L" in " ".join(lines)


def test_best_is_argmin_with_tie_rule():
    g = pd.read_csv(S9B / "grid_stage9b.csv")
    gm = g[g.bien_the == c9.MAIN_VARIANT]
    assert len(gm) == 1536
    best = pd.read_csv(S9B / "best_by_variant_stage9b.csv").set_index("bien_the").loc[c9.MAIN_VARIANT]
    assert best.J == pytest.approx(gm.J.min(), abs=1e-12)
    ties = gm[gm.J - gm.J.min() < 1e-12]
    assert int(ties.grid_index.min()) == int(gm.sort_values(["J", "grid_index"]).iloc[0].grid_index)


def test_grid_rows_reproducible_by_resimulation():
    g = pd.read_csv(S9B / "grid_stage9b.csv")
    gm = g[g.bien_the == c9.MAIN_VARIANT].reset_index(drop=True)
    cfg, base = c9.base_params()
    panel = c9.load_panel()
    bu = c9b.growth_offset(panel, rows(), cfg)
    gp, _ = c9.growth_rules(panel, True, False)
    params = c9b.apply_offset({**base, **gp}, bu)
    act = c9.actual_series(S9B).sort_values("month")
    act = act[act.month <= c9.N_SIM]
    al, ad = act.actual_loan_rate.to_numpy(), act.actual_deposit_rate.to_numpy()
    ldr = c9.ldr_mean(panel)
    for i in (0, 777, 1535):
        r = gm.iloc[i]
        q = c9.params_of(params, r, ldr)
        loan, dep, _ = c9.simulate(q, rows(), cfg=cfg, n=9)
        assert c9.objective(loan, dep, al, ad)[0] == pytest.approx(r.J, rel=1e-8)


def test_calibrated_config_section6_and_a_deterministic():
    cfg = load_config(ROOT / "configs/scenarios_calibrated.yaml")
    res = c9.section6(cfg, rows())
    assert res["pass"], res
    assert res["max_B_minus_A_after"] <= 0 and res["max_C_minus_A_after"] <= 0 and res["max_abs_diff_before"] == 0.0
    p = dict(cfg["parameters"])
    l1, d1, _ = c9.simulate(p, rows(), seed=1, cfg=cfg)
    l2, d2, _ = c9.simulate(p, rows(), seed=999, cfg=cfg)
    assert np.array_equal(l1, l2) and np.array_equal(d1, d2)


def test_stage9_outputs_still_describe_gd9_config():
    """Đầu ra GD9 giữ nguyên: nghiệm GD9 trong stage9 trùng configs/scenarios_calibrated_gd9.yaml (không phải bản GD9b)."""
    p9 = params_of(ROOT / "configs/scenarios_calibrated_gd9.yaml")
    best9 = pd.read_csv(S9 / "best_by_variant_stage9.csv").set_index("bien_the").loc[c9.MAIN_VARIANT]
    assert p9["pass_through"] == pytest.approx(best9.pass_through)
    assert c9.CALIBRATED_CFG.name == "scenarios_calibrated_gd9.yaml"      # chạy lại GD9 không ghi đè nghiệm GD9b
