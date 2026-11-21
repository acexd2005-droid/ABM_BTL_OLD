"""Test Giai đoạn 7b: ước lượng phương trình huy động và mô phỏng offline."""

import numpy as np
import pandas as pd
import pytest

from src.calibration import estimate_deposit_equation as de


@pytest.fixture(scope="module")
def data():
    return de.prepare()


def test_samples_and_variable_definitions(data):
    df, on = data
    assert [len(de.sample(df, t)) for t in (2, 3, 4)] == [112, 104, 96]
    r = df[df.bank_id == "ACB"].sort_values("t").reset_index(drop=True)
    # drD = r^D_t - r^D_{t-1}; r^D = deposit_rate_pct / (1 - casa)
    assert r.loc[2, "drD"] == pytest.approx(r.loc[2, "rD"] - r.loc[1, "rD"])
    assert r.loc[1, "rD"] == pytest.approx(r.loc[1, "deposit_rate_pct"] / (1 - r.loc[1, "casa_ratio"]))
    # LDR đầu quý t = cuối quý t-1
    assert r.loc[2, "ldr_lag"] == pytest.approx(r.loc[1, "loans"] / r.loc[1, "deposits"])
    # W_k = ON_{t-k} - r^D_{t-1}; quý 2023Q1 (t = 1) có ON = 4.817
    assert r.loc[1, "ONk1"] == pytest.approx(4.817)
    assert r.loc[3, "ONk3"] == pytest.approx(4.817)
    assert r.loc[2, "W1"] == pytest.approx(r.loc[2, "ONk1"] - r.loc[2, "rD_lag"])
    # biến đã chặn: clip(LDR - 0.82, ±0.5)
    assert (df.z_lag.dropna().abs() <= 0.5 + 1e-12).all()


def _synthetic(phi=0.2, delta=1.5, seed=0, G=8, T=12):
    rng = np.random.default_rng(seed)
    rows = []
    alpha = rng.normal(size=G)
    on = rng.normal(loc=4.0, scale=1.0, size=T)
    for b in range(G):
        r = 5.0
        for t in range(1, T):
            ldr = 1.0 + 0.2 * rng.normal()
            w = on[t - 1] - r
            d = alpha[b] + delta * ldr + phi * w
            rows.append({"bank_id": f"B{b}", "t": t + 1, "drD": d, "ldr_lag": ldr, "W1": w, "rD_lag": r, "z_lag": ldr})
            r += d
    return pd.DataFrame(rows), alpha


def test_recovers_parameters_and_equilibrium_identity():
    df, alpha = _synthetic()
    rows, res = de._est("PT5-ON", df, "d", 1, "syn", {})
    get = lambda n: [r["coef"] for r in rows if r["parameter"] == n][0]
    assert get("phi") == pytest.approx(0.2)
    assert get("delta") == pytest.approx(1.5)
    assert get("alpha_mean") == pytest.approx(alpha.mean())
    # r* - ON = (ᾱ + δ·LDR̄)/φ = Δr̄/φ + trung bình(r_{t-1} - ON): đồng nhất thức
    lhs = get("spread_equilibrium")
    rhs = (alpha.mean() + 1.5 * df.ldr_lag.mean()) / 0.2
    assert lhs == pytest.approx(rhs, rel=1e-9)
    assert [r for r in rows if r["parameter"] == "spread_equilibrium"][0]["se_cluster"] != \
        [r for r in rows if r["parameter"] == "spread_equilibrium"][0]["se_cluster"]   # NaN: không có SE


def test_offline_simulation_with_unit_lambda_matches_hand_calc(data):
    df, on = data
    yv = de.yaml7b()
    p = de.simulate_offline(df, on, 1.0, "actual", yv=yv)
    # λ = 1: r^L_t = c_{t-1} + 4.55 (thực), gia quyền theo dư nợ thực của quý t
    t = 6
    d_prev = df[df.t == t - 1].sort_values("bank_id")
    cur = df[df.t == t].sort_values("bank_id")
    expect = ((d_prev.c_main.to_numpy() + de.MARGIN_CONST) * cur.loans.to_numpy()).sum() / cur.loans.sum()
    assert p.loc[p.t == t, "loan_rate"].iloc[0] == pytest.approx(expect)
    assert list(p.t) == list(range(de.T0 + 1, 16))


def test_model_rule_with_zero_step_keeps_deposit_rate_constant(data):
    df, on = data
    yv = {"delta": 0.0, "base_step_implied": 0.0}
    p = de.simulate_offline(df, on, 0.3, "model_rule", yv=yv)
    # rD từng ngân hàng giữ nguyên bằng giá trị quý T0 => chuỗi tổng hợp = Σ rD0 (1-casa0) · tiền gửi_t / Σ tiền gửi_t
    d0 = df[df.t == de.T0].set_index("bank_id")
    for t in (5, 9, 15):
        cur = df[df.t == t].set_index("bank_id").loc[d0.index]
        expect = (d0.rD * (1 - d0.casa_ratio) * cur.deposits).sum() / cur.deposits.sum()
        assert p.loc[p.t == t, "deposit_rate_total_basis"].iloc[0] == pytest.approx(expect)


def test_v_metrics_on_known_path():
    path = pd.DataFrame({"t": [4, 5, 6, 7, 8], "x": [8.0, 7.0, 6.0, 7.0, 9.0]})
    m = de.v_metrics(path, "x", "v", de.T0)
    assert (m["tho_thap_nhat"], m["quy_thap_nhat_t"]) == (6.0, 6)
    assert m["giam_tu_dau_den_day"] == pytest.approx(2.0) and m["hoi_phuc_tu_day_den_cuoi"] == pytest.approx(3.0)


def test_pipeline_outputs(data, tmp_path):
    df, on = data
    yv = de.yaml7b()
    est = de.estimate_all_7b(df, yv)
    assert set(est["sample"]) == {"N112", "N104", "N96"}
    assert {"PT5", "PT5z", "PT5-ON"} == set(est.equation)
    assert est.groupby("sample").n.first().to_dict() == {"N96": 96, "N104": 104, "N112": 112}
    assert (est.n_clusters == 8).all()
    k, r2 = de.best_lag(df)
    assert k == max(r2, key=r2.get) and set(r2) == {1, 2, 3}
    absr = de.absorption_7b(df)
    assert len(absr) == 6 and absr.share_quarter_FE_only.between(0, 1).all()
    boot = de.bootstrap_phi(df, k)
    assert (boot.B == 9999).all() and (boot.ci_boot_lo < boot.coef).all() and (boot.coef < boot.ci_boot_hi).all()
    m = de.margin_path(df)
    assert len(m) == 14 and np.allclose(m.bien_gia_dinh_mo_hinh, 4.55)


def test_estimates_on_real_data_match_independent_values(data):
    """Đối chiếu số cụ thể (đã tái lập độc lập bằng LSDV tự viết ở bước phản biện)."""
    df, _ = data
    yv = de.yaml7b()
    est = de.estimate_all_7b(df, yv)
    g = lambda eq, v, k, param, sm="N112": est[(est.equation == eq) & (est.variant == v) & (est["sample"] == sm)
                                               & (est.lag_on.fillna(0) == (k or 0)) & (est.parameter == param)].coef.iloc[0]
    assert g("PT5", "b", None, "delta") == pytest.approx(5.2894, abs=5e-4)
    assert g("PT5-ON", "c", None, "delta") == pytest.approx(1.3016, abs=5e-4)
    assert g("PT5-ON", "c", None, "phi") == pytest.approx(0.4013, abs=5e-4)
    assert g("PT5-ON", "d", 1, "delta") == pytest.approx(2.0139, abs=5e-4)
    assert g("PT5-ON", "d", 1, "phi") == pytest.approx(0.1771, abs=5e-4)
    assert g("PT5-ON", "d", 1, "half_life_quarters") == pytest.approx(3.555, abs=5e-3)


def test_margin_const_read_from_yaml():
    assert de.MARGIN_CONST == pytest.approx(3.2 + 1.35)


def test_simulation_timing_with_full_adjustment_to_on(data):
    """φ = 1, δ = 0, α = 0, k = 1: r^D_t = ON_{t-1} cho mọi ngân hàng => bắt lỗi thời điểm ON."""
    df, on = data
    banks = sorted(df.bank_id.unique())
    p = de.simulate_offline(df, on, 0.3, "pt5on", k=1, alpha={b: 0.0 for b in banks}, coefs=np.array([0.0, 1.0]),
                            yv=de.yaml7b())
    d0 = df[df.t == de.T0].set_index("bank_id").loc[banks]
    for t in (5, 9, 15):
        cur = df[df.t == t].set_index("bank_id").loc[banks]
        on_prev = de.on_by_t(df, on, t - 1)
        expect = (on_prev * (1 - d0.casa_ratio) * cur.deposits).sum() / cur.deposits.sum()
        assert p.loc[p.t == t, "deposit_rate_total_basis"].iloc[0] == pytest.approx(expect)


def test_simulation_timing_of_ldr_in_model_rule(data):
    """δ = 1, base = 0: bước đầu r^D_5 = r^D_4 + clip(LDR_4 - 0.82, ±0.5) => bắt lỗi thời điểm LDR."""
    df, on = data
    banks = sorted(df.bank_id.unique())
    p = de.simulate_offline(df, on, 0.3, "model_rule", yv={"delta": 1.0, "base_step_implied": 0.0})
    d4 = df[df.t == 4].set_index("bank_id").loc[banks]
    d5 = df[df.t == 5].set_index("bank_id").loc[banks]
    rd5 = d4.rD + np.clip(d4.ldr - 0.82, -0.5, 0.5)
    expect = (rd5.clip(0, 14) * (1 - d4.casa_ratio) * d5.deposits).sum() / d5.deposits.sum()
    assert p.loc[p.t == 5, "deposit_rate_total_basis"].iloc[0] == pytest.approx(expect)
