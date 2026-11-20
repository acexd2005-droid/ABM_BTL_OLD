"""Kiểm thử học thích nghi của ngân hàng (target_margin)."""

import pandas as pd
import pytest
import yaml
from pathlib import Path

from src.core.model import ABMModel
from tests.test_golden import ROOT, GOLDEN, load_config, run_model

ADAPTIVE = ROOT / "configs/scenarios_adaptive.yaml"


def adaptive_config():
    with open(ADAPTIVE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def make_model(**overrides):
    cfg = load_config()
    params = dict(cfg["parameters"])
    params["adaptive_learning"] = True
    params.update(overrides)
    rows = pd.read_csv(
        ROOT / "data/clean/abm_initial_8nganhang_2023Q1.csv"
    ).to_dict("records")
    return ABMModel("A", cfg["n_months"], 202611, params, rows)


def test_adaptive_yaml_only_differs_in_flag():
    off, on = load_config(), adaptive_config()
    assert off["parameters"]["adaptive_learning"] is False
    assert on["parameters"]["adaptive_learning"] is True
    on["parameters"]["adaptive_learning"] = False
    assert on == off


def test_off_by_default_in_code():
    assert ABMModel(seed=1).adaptive_learning is False


def test_off_matches_golden_and_margin_constant():
    for scenario in "ABC":
        history, bank_history = run_model(scenario, 202611)
        expected = pd.read_csv(
            GOLDEN / f"bank_history_{scenario}_202611.csv",
            float_precision="round_trip",
        )
        pd.testing.assert_frame_equal(
            bank_history[list(expected.columns)], expected,
            check_exact=False, atol=1e-9, rtol=0,
        )
        assert "target_margin" in bank_history.columns
        assert (bank_history.target_margin == 3.2).all()


def test_old_columns_unchanged_order():
    _, bank_history = run_model("A", 202611)
    expected = pd.read_csv(GOLDEN / "bank_history_A_202611.csv")
    assert list(bank_history.columns[:-1]) == list(expected.columns)
    assert bank_history.columns[-1] == "target_margin"


def test_margin_falls_when_loan_share_falls():
    model = make_model()
    bank = model.banks[0]
    # Dư nợ không đổi, các ngân hàng khác tăng => thị phần dư nợ giảm
    for other in model.banks[1:]:
        other.loans *= 1.2
    before = bank.target_margin
    bank.finish_month()
    assert bank.target_margin == pytest.approx(
        before - model.learning_down_step
    )


def test_margin_rises_when_growing_and_nim_high():
    model = make_model(learning_nim_threshold=0.0)
    bank = model.banks[0]
    # Chỉ ngân hàng này tăng mạnh => thị phần tăng, tăng trưởng >= g*
    bank.loans *= 1.10
    before = bank.target_margin
    bank.finish_month()
    assert bank.target_margin == pytest.approx(
        before + model.learning_up_step
    )


def test_no_rise_when_nim_below_threshold():
    model = make_model(learning_nim_threshold=1e9)
    bank = model.banks[0]
    bank.loans *= 1.10
    before = bank.target_margin
    bank.finish_month()
    assert bank.target_margin == before


def test_only_decrease_when_both_signals():
    model = make_model(learning_nim_threshold=0.0)
    bank = model.banks[0]
    # Tăng trưởng 1% >= g* nhưng các ngân hàng khác tăng nhanh hơn => thị phần giảm
    bank.loans *= 1.01
    for other in model.banks[1:]:
        other.loans *= 1.30
    before = bank.target_margin
    bank.finish_month()
    assert bank.target_margin == pytest.approx(
        before - model.learning_down_step
    )


def test_margin_clipped_to_bounds():
    # Sàn
    model = make_model(learning_down_step=10.0)
    bank = model.banks[0]
    for other in model.banks[1:]:
        other.loans *= 1.2
    bank.finish_month()
    assert bank.target_margin == model.margin_min
    # Trần
    model = make_model(learning_up_step=10.0, learning_nim_threshold=0.0)
    bank = model.banks[0]
    bank.loans *= 1.10
    bank.finish_month()
    assert bank.target_margin == model.margin_max


@pytest.mark.parametrize("scenario", "ABC")
def test_margin_within_bounds_full_run(scenario):
    cfg = adaptive_config()
    _, bank_history = run_model(scenario, 202611, cfg)
    p = cfg["parameters"]
    assert bank_history.target_margin.between(
        p["margin_min"], p["margin_max"]
    ).all()


def test_learning_has_no_effect_before_policy_only_via_state():
    # Học không dùng số ngẫu nhiên: A/B/C vẫn trùng nhau trước thời điểm chính sách
    cfg = adaptive_config()
    pm = cfg["parameters"]["policy_month"]
    frames = {s: run_model(s, 202611, cfg)[0] for s in "ABC"}
    pre = lambda f: f[f.month <= pm][["loan_rate", "deposit_rate", "total_loans"]]
    pd.testing.assert_frame_equal(pre(frames["A"]), pre(frames["B"]))
    pd.testing.assert_frame_equal(pre(frames["A"]), pre(frames["C"]))


def test_invalid_margin_bounds():
    with pytest.raises(ValueError):
        make_model(margin_min=5.0, margin_max=4.0)
