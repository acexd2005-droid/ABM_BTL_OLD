"""Test ước lượng Giai đoạn 7 (OLS, within, SE cụm) với ví dụ tính tay."""

import numpy as np
import pandas as pd
import pytest

from src.calibration import estimate_equations as ee


def test_ols_hand_example_with_cluster_se():
    # y = [1,2,3,5], x = [1,2,3,4]: x̄=2.5, ȳ=2.75, Sxy=6.5, Sxx=5 => b=1.3, a=-0.5
    # u = [.2,-.1,-.4,.3]; s²=0.15 => var_ols(b)=0.03
    # cụm {0,1},{2,3}: điểm số theo cụm = Σ(x-x̄)u = -0.25 và +0.25
    # var_cl = 2/1 * 3/2 * (0.0625+0.0625)/25 = 0.015
    y = [1, 2, 3, 5]
    x = np.array([1, 2, 3, 4.0])[:, None]
    r = ee.fit(y, x, ["a", "a", "b", "b"], [0, 1, 0, 1], "pooled")
    assert r["b"] == pytest.approx([-0.5, 1.3])
    assert r["se_ols"][1] == pytest.approx(np.sqrt(0.03))
    assert r["se_cl"][1] == pytest.approx(np.sqrt(0.015))
    # R² = 1 - SSR/TSS = 1 - 0.30/(1.75²... ) tính tay: TSS = 3.0625+0.5625+0.0625+5.0625 = 8.75
    assert r["r2"] == pytest.approx(1 - 0.30 / 8.75)


def test_two_way_demean_hand_example():
    x = np.array([1.0, 2.0, 4.0, 8.0])           # bank 0: (1,2); bank 1: (4,8)
    bank = np.array([0, 0, 1, 1])
    time = np.array([0, 1, 0, 1])
    out = ee._demean(ee._demean(x, bank, 2), time, 2)
    # Tính tay: x̄_i = (1.5, 6), x̄_t = (2.5, 5), x̄ = 15/4 = 3.75; x̃ = x - x̄_i - x̄_t + x̄
    assert out == pytest.approx([0.75, -0.75, -0.75, 0.75])


def test_fe_bank_recovers_slope_and_r2_within():
    bank = np.repeat([0, 1, 2], 4)
    t = np.tile(np.arange(4), 3)
    x = np.array([1, 3, 2, 5, 4, 1, 6, 2, 3, 3, 1, 7.0])
    y = 2.0 * x + np.repeat([10.0, -5.0, 0.5], 4)
    r = ee.fit(y, x[:, None], bank, t, "fe_bank")
    assert r["b"][0] == pytest.approx(2.0)
    assert r["r2"] == pytest.approx(1.0)
    assert ee.fe_intercepts(y, x[:, None], r["b"], bank) == pytest.approx([10.0, -5.0, 0.5])


def test_two_way_fe_recovers_slope():
    rng = np.random.default_rng(0)
    G, T = 4, 5
    bank = np.repeat(np.arange(G), T)
    t = np.tile(np.arange(T), G)
    x = rng.normal(size=G * T)
    y = 3.0 * x + np.repeat(rng.normal(size=G), T) + np.tile(rng.normal(size=T), G)
    r = ee.fit(y, x[:, None], bank, t, "fe_twoway")
    assert r["b"][0] == pytest.approx(3.0)
    assert r["r2"] == pytest.approx(1.0)


def test_recovers_model_parameters_from_model_generated_data():
    # Sinh dữ liệu đúng theo PT1 của mô hình (λ=0.48, m+s=4.55), không nhiễu
    rng = np.random.default_rng(1)
    lam, ms = 0.48, 4.55
    rows = []
    for b in range(8):
        r = 9.0
        for t in range(1, 16):
            c = 4.0 + rng.normal(scale=0.5)
            if t > 1:
                r_new = r + lam * (c_prev + ms - r)
                rows.append((b, t, r_new - r, c_prev - r))
                r = r_new
            c_prev = c
    d = pd.DataFrame(rows, columns=["b", "t", "y", "x"])
    r = ee.fit(d.y, d[["x"]].to_numpy(), d.b, d.t, "pooled")
    assert r["b"][1] == pytest.approx(lam)
    assert r["b"][0] / r["b"][1] == pytest.approx(ms)


@pytest.fixture(scope="module")
def data():
    return ee.load_data()


def test_variable_mapping_and_samples(data):
    # c chính = deposit_rate_pct + 0.15 (đã xác nhận ánh xạ r^D = deposit_rate_pct/(1-casa))
    assert (data.c_main - (data.deposit_rate_pct + 0.15)).abs().max() < 1e-12
    assert (data.c_old - (data.deposit_rate_pct * (1 - data.casa_ratio) + 0.15)).abs().max() < 1e-12
    assert len(ee.sample(data, 2)) == 112 and len(ee.sample(data, 3)) == 104
    # lãi suất qua đêm: ON0 ở 2023Q1 = 4.817; ON1 ở 2023Q2 = ON0 của 2023Q1
    q1 = data[data.period == "2023Q1"].ON0.iloc[0]
    q2 = data[data.period == "2023Q2"]
    assert q1 == pytest.approx(4.817) and q2.ON1.iloc[0] == pytest.approx(4.817)
    assert q2.ON0.iloc[0] == pytest.approx(3.573)
    # mốc thị trường: bình quân đơn giản 8 NH của r^D tại t-1
    t2 = data[data.t == 2].iloc[0]
    assert t2.rbar_lag == pytest.approx(data[data.t == 1].rD.mean())


def test_pipeline_runs_and_ses_positive(data):
    est = ee.estimate_all(data, ee.yaml_values())
    assert set(est.equation) == {"PT1", "PT1b", "PT2", "PT3", "PT4"}
    assert np.isfinite(est.coef).all()
    assert (est.se_cluster.dropna() > 0).all()
    assert set(est["sample"]) == {"N112", "N104"}
    assert (est[est["sample"] == "N112"].n == 112).all()
    assert (est[est["sample"] == "N104"].n == 104).all()
    # SE cụm dùng đúng 8 cụm
    assert (est.n_clusters == 8).all()
    absr = ee.absorption(data)
    assert len(absr) == 12
    assert absr.share_quarter_FE_only.between(0, 1).all()


def _lsdv_cluster_se(y, X, bank, time, two_way):
    """Đối chiếu độc lập: LSDV (biến giả NH [+ biến giả quý]) + sandwich cụm thô, rồi nhân hệ số CR1
    G/(G-1) * (N-1)/(N-K_adj), K_adj = k + (T-1 nếu hai chiều); biến giả NH lồng trong cụm nên không đếm."""
    N, k = X.shape
    G, T = len(set(bank)), len(set(time))
    cols = [X] + [(bank == g).astype(float)[:, None] for g in range(G)]
    if two_way:
        cols += [(time == t_).astype(float)[:, None] for t_ in range(1, T)]
    Z = np.hstack(cols)
    Ainv = np.linalg.inv(Z.T @ Z)
    b = Ainv @ Z.T @ y
    u = y - Z @ b
    meat = sum(np.outer(Z[bank == g].T @ u[bank == g], Z[bank == g].T @ u[bank == g]) for g in range(G))
    k_adj = k + (T - 1 if two_way else 0)
    cov = G / (G - 1) * (N - 1) / (N - k_adj) * Ainv @ meat @ Ainv
    k_all = Z.shape[1]
    cov_ols = (u @ u) / (N - k_all) * Ainv
    return b[:k], np.sqrt(np.diag(cov)[:k]), np.sqrt(np.diag(cov_ols)[:k])


@pytest.mark.parametrize("spec,two_way", [("fe_bank", False), ("fe_twoway", True)])
def test_fe_cluster_and_ols_se_match_lsdv(spec, two_way):
    rng = np.random.default_rng(7)
    G, T = 6, 7
    bank = np.repeat(np.arange(G), T)
    time = np.tile(np.arange(T), G)
    X = rng.normal(size=(G * T, 2))
    shock = np.tile(rng.normal(size=T), G)
    y = X @ np.array([0.7, -1.2]) + np.repeat(rng.normal(size=G), T) + shock + rng.normal(size=G * T)
    r = ee.fit(y, X, bank, time, spec)
    b, se_cl, se_ols = _lsdv_cluster_se(y, X, bank, time, two_way)
    assert r["b"] == pytest.approx(b)
    assert r["se_cl"] == pytest.approx(se_cl)
    assert r["se_ols"] == pytest.approx(se_ols)


def test_stability_table_and_absorption_columns(data):
    est = ee.estimate_all(data, ee.yaml_values())
    st = ee.stability_table(est)
    assert {"CI112_chua_0", "CI104_chua_0", "doi_dau"} <= set(st.columns)
    absr = ee.absorption(data)
    assert {"ratio_adj_df", "approx_share_explained_by_ON_via_common"} <= set(absr.columns)
    # Δr^L trễ 1: phần qua thành phần chung nhỏ hơn R² của thành phần chung
    r = absr[(absr.equation == "PT1") & (absr.lag_on == 1)].iloc[0]
    assert r.approx_share_explained_by_ON_via_common < r.R2_common_on_ON


# ---------------- Wild-cluster bootstrap ----------------

def test_webb_weights_moments():
    assert len(ee.WEBB) == 6
    assert ee.WEBB.mean() == pytest.approx(0.0)
    assert (ee.WEBB ** 2).mean() == pytest.approx(1.0)    # (1.5+1+0.5)*2/6 = 1


def _toy_panel(effect, seed=3, G=8, T=9):
    rng = np.random.default_rng(seed)
    bank = np.repeat(np.arange(G), T)
    time = np.tile(np.arange(T), G)
    x = rng.normal(size=G * T)
    y = effect * x + np.repeat(rng.normal(size=G), T) + rng.normal(size=G * T)
    return y, x[:, None], bank, time


def _slow_wcr_p(y, X, bank, time, W, beta0, two_way):
    """Cài đặt chậm, độc lập: LSDV (biến giả NH [+ quý]) cho từng lần lặp, SE cụm CR1 tự tính."""
    N = len(y)
    G, T = len(set(bank)), len(set(time))
    dums = [(bank == g).astype(float)[:, None] for g in range(G)]
    if two_way:
        dums += [(time == t_).astype(float)[:, None] for t_ in range(1, T)]
    Z = np.hstack([X] + dums)
    k_adj = 1 + (T - 1 if two_way else 0)
    factor = G / (G - 1) * (N - 1) / (N - k_adj)
    Ainv = np.linalg.inv(Z.T @ Z)

    def t_stat(yv, b0):
        b = Ainv @ Z.T @ yv
        u = yv - Z @ b
        meat = sum(np.outer(Z[bank == g].T @ u[bank == g], Z[bank == g].T @ u[bank == g]) for g in range(G))
        v = factor * (Ainv @ meat @ Ainv)[0, 0]
        return (b[0] - b0) / np.sqrt(v)

    t_obs = t_stat(y, beta0)
    # mô hình bị ràng buộc: y - beta0*x hồi quy trên các biến giả
    D = np.hstack(dums)
    y0 = y - beta0 * X[:, 0]
    fit0 = D @ np.linalg.lstsq(D, y0, rcond=None)[0]
    ur = y0 - fit0
    ts = []
    for r in range(W.shape[0]):
        ystar = fit0 + beta0 * X[:, 0] + ur * W[r, bank]
        ts.append(t_stat(ystar, beta0))
    return float(np.mean(np.abs(ts) >= abs(t_obs) - 1e-12)), t_obs


@pytest.mark.parametrize("spec,two_way", [("fe_bank", False), ("fe_twoway", True)])
def test_wild_bootstrap_matches_slow_lsdv_implementation(spec, two_way):
    y, X, bank, time = _toy_panel(0.4)
    W = np.random.default_rng(11).choice(ee.WEBB, size=(300, 8))
    out = ee.wild_cluster_bootstrap(y, X, bank, time, spec, 0, weights=W, grid_n=5, grid_half_width=1.0)
    p_slow, t_slow = _slow_wcr_p(y, X, bank, time, W, 0.0, two_way)
    assert out["t_cr1"] == pytest.approx(t_slow)
    assert out["p_boot"] == pytest.approx(p_slow)


def test_wild_bootstrap_properties():
    # hiệu ứng mạnh: p nhỏ, khoảng tin cậy chứa giá trị thật và không chứa 0
    y, X, bank, time = _toy_panel(2.0, seed=5, T=12)
    out = ee.wild_cluster_bootstrap(y, X, bank, time, "fe_bank", 0, B=999)
    assert out["p_boot"] < 0.05
    assert out["ci_boot_lo"] < 2.0 < out["ci_boot_hi"] and out["ci_boot_lo"] > 0
    # tái lập: cùng seed -> cùng kết quả
    again = ee.wild_cluster_bootstrap(y, X, bank, time, "fe_bank", 0, B=999)
    assert again == out
    # không có hiệu ứng: p lớn, khoảng tin cậy chứa 0
    y0, X0, b0, t0 = _toy_panel(0.0, seed=9, T=12)
    out0 = ee.wild_cluster_bootstrap(y0, X0, b0, t0, "fe_bank", 0, B=999)
    assert out0["p_boot"] > 0.05 and out0["ci_boot_lo"] < 0 < out0["ci_boot_hi"]


def test_bootstrap_pt1_on_real_data(data):
    b = ee.bootstrap_pt1(data)
    assert list(b.parameter) == ["lambda", "lambda", "ON_lag1"]
    assert (b.B == 9999).all() and (b.seed == ee.BOOT_SEED).all()
    est = ee.estimate_all(data, ee.yaml_values())
    lam_c = est[(est.equation == "PT1") & (est.parameter == "lambda") & (est.variant == "c")
                & (est["sample"] == "N112")].iloc[0]
    assert b.coef.iloc[0] == pytest.approx(lam_c.coef)
    assert b.se_cr1.iloc[0] == pytest.approx(lam_c.se_cluster)
    assert ((b.p_boot > 0) & (b.p_boot <= 1)).all()
    assert (b.ci_boot_lo < b.coef).all() and (b.coef < b.ci_boot_hi).all()
