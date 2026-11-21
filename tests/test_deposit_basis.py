"""Tùy chọn deposit_rate_basis (total | term): quy đổi lãi suất huy động khi nạp dữ liệu."""

import pandas as pd
import pytest

from src.analysis.experiments import load_config
from src.core.model import ABMModel
from tests.test_golden import ROOT, GOLDEN, run_model

DATA = ROOT / "data/clean/abm_initial_8nganhang_2023Q1.csv"
TERM = ROOT / "configs/scenarios_term.yaml"


def rows():
    return pd.read_csv(DATA).to_dict("records")


def build(basis=None, scenario="A", initial=True, **extra):
    cfg = load_config()
    params = dict(cfg["parameters"])
    if basis is not None:
        params["deposit_rate_basis"] = basis
    params.update(extra)
    return ABMModel(scenario, cfg["n_months"], 202611, params, rows() if initial else None)


def test_default_is_total_in_code_and_yaml():
    assert ABMModel(seed=1).deposit_rate_basis == "total"
    assert load_config()["parameters"]["deposit_rate_basis"] == "total"
    assert load_config(TERM)["parameters"]["deposit_rate_basis"] == "term"


def test_invalid_basis_rejected():
    with pytest.raises(ValueError):
        build("khac")


@pytest.mark.parametrize("scenario", "ABC")
def test_total_matches_golden_explicitly(scenario):
    cfg = load_config()
    cfg["parameters"]["deposit_rate_basis"] = "total"
    for seed in (202611, 202612, 202613):
        hist, bank = run_model(scenario, seed, cfg)
        for name, frame in (("history", hist), ("bank_history", bank)):
            expected = pd.read_csv(
                GOLDEN / f"{name}_{scenario}_{seed}.csv", float_precision="round_trip"
            )
            pd.testing.assert_frame_equal(
                frame[list(expected.columns)], expected,
                check_exact=False, atol=1e-9, rtol=0,
            )


def test_total_keeps_data_deposit_rate_and_double_casa():
    model = build("total")
    for bank, row in zip(model.banks, rows()):
        assert bank.deposit_rate == pytest.approx(row["deposit_rate"], abs=1e-12)
        assert bank.funding_cost == pytest.approx(
            row["deposit_rate"] * (1 - row["casa_ratio"]) + 0.15, abs=1e-12
        )


def test_term_funding_cost_equals_data_rate_plus_015():
    model = build("term")
    for bank, row in zip(model.banks, rows()):
        assert bank.deposit_rate == pytest.approx(
            row["deposit_rate"] / (1 - row["casa_ratio"]), abs=1e-12
        )
        assert bank.funding_cost == pytest.approx(row["deposit_rate"] + 0.15, abs=1e-12)
        assert bank.lagged_funding_cost == pytest.approx(row["deposit_rate"] + 0.15, abs=1e-12)


def test_term_does_not_touch_demo_banks():
    a, b = build("total", initial=False), build("term", initial=False)
    assert [x.deposit_rate for x in a.banks] == [x.deposit_rate for x in b.banks]


def test_term_threshold_selected_and_derivable_from_data():
    assert build("total").learning_nim_threshold == pytest.approx(5.5875)
    assert build("term").learning_nim_threshold == pytest.approx(4.6331)
    d = pd.read_csv(DATA)
    w = d.loans
    n_total = ((d.loan_rate - (d.deposit_rate * (1 - d.casa_ratio) + 0.15)) * w).sum() / w.sum()
    n_term = ((d.loan_rate - (d.deposit_rate + 0.15)) * w).sum() / w.sum()
    assert n_total == pytest.approx(5.5875, abs=5e-5)
    assert n_term == pytest.approx(4.6331, abs=5e-5)


@pytest.mark.parametrize("scenario", "ABC")
def test_term_run_respects_constraints(scenario):
    cfg = load_config(TERM)
    hist, bank = run_model(scenario, 202611, cfg)
    assert bank.loan_rate.between(0, 20).all() and bank.deposit_rate.between(0, 14).all()
    assert (bank.loans <= bank.deposits * cfg["parameters"]["max_loan_to_deposit"] + 1e-9).all()


def test_term_same_before_policy_and_b_not_above_a():
    cfg = load_config(TERM)
    pm = cfg["parameters"]["policy_month"]
    f = {s: run_model(s, 202611, cfg)[0] for s in "ABC"}
    for s in "BC":
        pre = lambda x: x[x.month <= pm][["loan_rate", "deposit_rate", "total_loans"]]
        pd.testing.assert_frame_equal(pre(f["A"]), pre(f[s]))
        post = f[s][f[s].month > pm].loan_rate.to_numpy()
        assert (post <= f["A"][f["A"].month > pm].loan_rate.to_numpy() + 1e-12).all()


def test_compare_script_smoke(tmp_path):
    from src.analysis import compare_deposit_basis as cmp
    actual = cmp.actual_series(tmp_path)
    assert list(actual.month) == list(range(1, 15))
    hist, bank, init = cmp.run_all(2)
    assert set(hist.basis) == {"total", "term"} and hist.run_id.max() == 1
    # quy đổi nhất quán: ở term, deposit_rate*(1-casa) khởi tạo = dữ liệu (sai số 1e-9)
    t0 = init.set_index("basis")
    assert t0.loc["term", "mean_funding_cost"] > t0.loc["total", "mean_funding_cost"]
    fit = cmp.fit_table(hist, actual)
    assert len(fit) == 4 and (fit["RMSE_tb_cac_lan"] > 0).all()
    chk = cmp.checks(hist, bank, load_config())
    assert (chk.chenh_lech_toi_da_A_B_C_truoc_chinh_sach == 0).all()
    assert (chk.so_vi_pham_B_cao_hon_A_sau_chinh_sach == 0).all()


def test_total_basis_deposit_rate_conversion_is_consistent():
    from src.analysis import compare_deposit_basis as cmp
    hist, bank, _ = cmp.run_all(1)
    tot, term = hist[hist.basis == "total"], hist[hist.basis == "term"]
    # total: deposit_rate mô hình đã cùng cơ sở dữ liệu => không nhân thêm (1-casa)
    assert (tot.deposit_rate_total_basis - tot.deposit_rate).abs().max() < 1e-9
    # term: quy đổi làm thấp đi
    assert (term.deposit_rate_total_basis < term.deposit_rate).all()
    # quý đầu: lãi suất huy động quy đổi của term gần bằng total (cùng dữ liệu khởi tạo, chỉ khác đường đi)
    first = lambda f: f[f.month == 1].deposit_rate_total_basis.iloc[0]
    assert abs(first(term) - first(tot)) < 0.5
