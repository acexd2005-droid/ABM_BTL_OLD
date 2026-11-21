"""Giai đoạn 7: ước lượng phương trình hành vi từ panel 8 ngân hàng x 15 quý.

KHÔNG sửa mô hình và KHÔNG sửa configs/. Chỉ ước lượng và so sánh với giá trị đang
giả định trong configs/scenarios.yaml. Chỉ dùng numpy + pandas (OLS, within-transform
và sai số chuẩn cụm tự cài). Chạy:

    python -m src.calibration.estimate_equations

Đơn vị: lãi suất %/năm; tăng trưởng và sai phân theo QUÝ.

Ánh xạ biến (đã xác nhận với người dùng):
  r^D_mô_hình = deposit_rate_pct / (1 - casa)  =>  c = r^D (1-casa) + 0.15 = deposit_rate_pct + 0.15
  (kết quả chính, c_def="main"); công thức cũ c = deposit_rate_pct (1-casa) + 0.15
  (trừ CASA hai lần) chỉ báo ở phụ lục (c_def="old").

Bốn phương trình (khớp code trong src/agents/):
  PT1  Δr^L_t = α + λ (c_{t-1} - r^L_{t-1})            λ = pass_through; α/λ = target_margin + loan_spread_add
  PT1b r^L_t = a + b r^L_{t-1} + γ c_{t-1}               dạng tự do; mô hình ngụ ý b + γ = 1
  PT2  r^L_t - c_{t-1} = μ                               μ = target_margin + loan_spread_add (trạng thái dừng)
  PT3  g^D_t = a_D + σ (r^D_{i,t} - mean_j r^D_{j,t-1})  σ = depositor_sensitivity; a_D = base_growth (0.004)
  PT4  g^L_t = a_L + β r^L_t                             ε = -β = borrower_elasticity;
                                                         base_growth = a_L + 9.5 β (giữ reference_rate = 9.5)
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data/clean/abm_panel_8nganhang_2023Q1_2026Q3.csv"
MACRO = ROOT / "data/raw/sbv_lnh_qua_dem_theo_quy.csv"
CONFIG = ROOT / "configs/scenarios.yaml"
OUTDIR = ROOT / "reports/calibration"

# t_{0.975} với 7 bậc tự do (8 cụm - 1). Không dùng scipy nên ghi cứng.
T_CRIT = 2.3646
FUNDING_CONST = 0.15      # bank.py: hằng số cộng vào chi phí vốn
def _read_reference_rate():
    with open(CONFIG, encoding="utf-8") as f:
        return float(yaml.safe_load(f)["parameters"]["borrower_reference_rate"])


REFERENCE_RATE = _read_reference_rate()   # YAML borrower_reference_rate (9.5)
TARGET_MARGIN = 3.2       # Bank(target_margin=3.2): mặc định trong code, KHÔNG nằm trong YAML
DEPOSITOR_BASE = 0.004    # DepositorBlock(base_growth=0.004): mặc định trong code, KHÔNG nằm trong YAML


# ======================================================================
# 1. Lõi ước lượng (numpy)
# ======================================================================

def _codes(labels):
    return pd.factorize(pd.Series(list(labels)))[0]


def _demean(a, codes, n_groups):
    """Trừ trung bình nhóm theo từng cột. a: (N,) hoặc (N,k)."""
    a = np.asarray(a, float)
    squeeze = a.ndim == 1
    if squeeze:
        a = a[:, None]
    sums = np.zeros((n_groups, a.shape[1]))
    np.add.at(sums, codes, a)
    counts = np.bincount(codes, minlength=n_groups)[:, None]
    out = a - (sums / counts)[codes]
    return out[:, 0] if squeeze else out


def _group_means(a, codes, n_groups):
    a = np.asarray(a, float)
    if a.ndim == 1:
        a = a[:, None]
    sums = np.zeros((n_groups, a.shape[1]))
    np.add.at(sums, codes, a)
    counts = np.bincount(codes, minlength=n_groups)[:, None]
    return sums / counts


def fit(y, X, bank, time, spec):
    """OLS với spec ∈ {pooled, fe_bank, fe_twoway}. X: (N,k), k có thể bằng 0.

    - pooled: thêm hằng số (cột đầu), R² thường.
    - fe_bank / fe_twoway: biến đổi within (panel cân bằng cho twoway); R² là within.
    Sai số chuẩn cụm CR1 theo ngân hàng:
        V = G/(G-1) * (N-1)/(N-K_adj) * A^-1 (Σ_g s_g s_g') A^-1,  s_g = Z_g' u_g
    K_adj = số cột hồi quy (+ T-1 biến giả quý nếu twoway; FE ngân hàng lồng trong cụm nên không tính).
    Sai số chuẩn thường: s² A^-1 với s² = SSR/(N - K_all), K_all tính đủ mọi FE.
    """
    y = np.asarray(y, float)
    N = len(y)
    X = np.asarray(X, float).reshape(N, -1)
    bc, tc = _codes(bank), _codes(time)
    G, T = bc.max() + 1, tc.max() + 1
    k = X.shape[1]
    tss_bank = (_demean(y, bc, G) ** 2).sum()   # nền chung cho mọi biến thể FE

    if spec == "pooled":
        Z = np.column_stack([np.ones(N), X])
        yy = y
        tss = ((y - y.mean()) ** 2).sum()
        k_all = k_adj = Z.shape[1]
    elif spec == "fe_bank":
        yy, Z = _demean(y, bc, G), _demean(X, bc, G)
        tss = (yy ** 2).sum()
        k_all, k_adj = k + G, k
    elif spec == "fe_twoway":
        if np.bincount(bc * T + tc, minlength=G * T).min() != 1 or N != G * T:
            raise ValueError("FE hai chiều cần panel cân bằng")
        yy = _demean(_demean(y, bc, G), tc, T)
        Z = _demean(_demean(X, bc, G), tc, T)
        tss = (yy ** 2).sum()
        k_all, k_adj = k + G + T - 1, k + T - 1
    else:
        raise ValueError(spec)

    if Z.shape[1] == 0:
        b, u = np.zeros(0), yy
        cov_ols = cov_cl = np.zeros((0, 0))
    else:
        Ainv = np.linalg.inv(Z.T @ Z)
        b = Ainv @ Z.T @ yy
        u = yy - Z @ b
        cov_ols = (u @ u) / (N - k_all) * Ainv
        meat = np.zeros((Z.shape[1], Z.shape[1]))
        for g in range(G):
            s = Z[bc == g].T @ u[bc == g]
            meat += np.outer(s, s)
        cov_cl = G / (G - 1) * (N - 1) / (N - k_adj) * Ainv @ meat @ Ainv

    ssr = u @ u
    return {
        "spec": spec, "b": b, "cov_cl": cov_cl, "cov_ols": cov_ols,
        "se_cl": np.sqrt(np.diag(cov_cl)), "se_ols": np.sqrt(np.diag(cov_ols)),
        "r2": 1 - ssr / tss if tss > 0 else np.nan,
        "r2_common": None if spec == "pooled" else 1 - ssr / tss_bank,
        "ssr": ssr, "tss_bank": tss_bank, "n": N, "G": G, "T": T,
    }


def fe_intercepts(y, X, b, bank):
    """α_i = ȳ_i - x̄_i' b (hằng số riêng từng ngân hàng sau within)."""
    bc = _codes(bank)
    G = bc.max() + 1
    ym = _group_means(y, bc, G)[:, 0]
    if X.shape[1] == 0:
        return ym
    return ym - _group_means(X, bc, G) @ b


# ======================================================================
# 2. Dữ liệu
# ======================================================================

def load_data(panel_path=PANEL, macro_path=MACRO):
    p = pd.read_csv(panel_path, encoding="utf-8-sig")
    p["per"] = pd.PeriodIndex(p["period"], freq="Q")
    p = p.sort_values(["bank_id", "per"]).reset_index(drop=True)
    p["t"] = p["per"].astype(int) - p["per"].astype(int).min() + 1

    m = pd.read_csv(macro_path)
    m["per"] = pd.PeriodIndex(m["quy"], freq="Q")
    on = dict(zip(m["per"].astype(int), m["bq_gian_don"]))

    p["rD"] = p["deposit_rate_pct"] / (1 - p["casa_ratio"])           # r^D mô hình
    p["c_main"] = p["rD"] * (1 - p["casa_ratio"]) + FUNDING_CONST      # = deposit_rate_pct + 0.15
    p["c_old"] = p["deposit_rate_pct"] * (1 - p["casa_ratio"]) + FUNDING_CONST
    p["rL"] = p["loan_rate_pct"]

    g = p.groupby("bank_id")
    p["rL_lag"] = g["rL"].shift()
    p["c_main_lag"] = g["c_main"].shift()
    p["c_old_lag"] = g["c_old"].shift()
    p["dRL"] = p["rL"] - p["rL_lag"]
    p["gD"] = g["deposits"].pct_change()
    p["gL"] = g["loans"].pct_change()

    # Mốc thị trường của khối người gửi tiền: bình quân đơn giản 8 NH của r^D đầu quý (= cuối quý t-1)
    rbar = p.groupby("t")["rD"].mean()
    p["rbar_lag"] = p["t"].map(lambda t: rbar.get(t - 1, np.nan))
    p["x_dep"] = p["rD"] - p["rbar_lag"]

    base = int(p["per"].astype(int).min())
    for k in (0, 1, 2):
        p[f"ON{k}"] = (p["t"] - 1 + base - k).map(on)
    return p


def sample(df, t_min):
    """Mẫu ước lượng: các quan sát có t >= t_min (t_min=2 -> N=112; 3 -> N=104)."""
    return df[df["t"] >= t_min].reset_index(drop=True)


# ======================================================================
# 3. Định nghĩa phương trình
# ======================================================================

def eq_vars(eq, df, c_def):
    """Trả về (y, DataFrame X) cho phương trình eq."""
    c_lag = df[f"c_{c_def}_lag"]
    if eq == "PT1":
        return df["dRL"].to_numpy(), pd.DataFrame({"lambda": c_lag - df["rL_lag"]})
    if eq == "PT1b":
        return df["rL"].to_numpy(), pd.DataFrame({"b": df["rL_lag"], "gamma": c_lag})
    if eq == "PT2":
        return (df["rL"] - c_lag).to_numpy(), pd.DataFrame(index=df.index)
    if eq == "PT3":
        return df["gD"].to_numpy(), pd.DataFrame({"sigma": df["x_dep"]})
    if eq == "PT4":
        return df["gL"].to_numpy(), pd.DataFrame({"beta": df["rL"]})
    raise ValueError(eq)


def yaml_values():
    with open(CONFIG, encoding="utf-8") as f:
        p = yaml.safe_load(f)["parameters"]
    ms = TARGET_MARGIN + p["loan_spread_add"]
    return {
        "lambda": p["pass_through"],
        "margin_const": ms, "mu_margin": ms,
        "a_const": p["pass_through"] * ms,
        "b+gamma-1": 0.0,
        "sigma": p["depositor_sensitivity"], "a_D": DEPOSITOR_BASE,
        "beta": -p["borrower_elasticity"], "epsilon": p["borrower_elasticity"],
        "a_L": p["borrower_base_growth"] + REFERENCE_RATE * p["borrower_elasticity"],
        "base_growth_L": p["borrower_base_growth"],
    }


# ======================================================================
# 4. Chạy một biến thể và gom hàng kết quả
# ======================================================================

def _row(meta, param, coef, se_cl, se_ols, r2, r2c, n, G, yv, note=""):
    t = coef / se_cl if se_cl and se_cl > 0 else np.nan
    return {
        **meta, "parameter": param, "coef": coef, "se_cluster": se_cl,
        "t_cluster": t,
        "ci95_lo": coef - T_CRIT * se_cl if se_cl == se_cl else np.nan,
        "ci95_hi": coef + T_CRIT * se_cl if se_cl == se_cl else np.nan,
        "se_ols": se_ols, "t_ols": coef / se_ols if se_ols and se_ols > 0 else np.nan,
        "r2": r2, "r2_common": r2c, "n": n, "n_clusters": G,
        "yaml_value": yv.get(param, np.nan), "note": note,
    }


def _fe_level(alpha_i):
    """Trung bình hằng số FE và độ phân tán giữa ngân hàng sd/√G (không phải SE chuẩn)."""
    G = len(alpha_i)
    return alpha_i.mean(), alpha_i.std(ddof=1) / np.sqrt(G)


def run_variant(eq, df, c_def, variant, k_on, sample_name, yv):
    """variant ∈ a, b, c, d (d dùng k_on). Trả về list hàng."""
    y, Xdf = eq_vars(eq, df, c_def)
    names = list(Xdf.columns)
    X = Xdf.to_numpy(float).reshape(len(df), -1)
    meta = {"c_def": c_def if eq in ("PT1", "PT1b", "PT2") else "-",
            "equation": eq, "variant": variant, "sample": sample_name,
            "lag_on": k_on if variant == "d" else np.nan}
    note = ""

    if variant == "d":
        on = df[f"ON{k_on}"].to_numpy(float)
        X = np.column_stack([X, on - on.mean()])      # tâm hoá: hằng số tính tại ON trung bình
        names = names + [f"ON_lag{k_on}"]
        spec = "fe_bank"
    else:
        spec = {"a": "pooled", "b": "fe_bank", "c": "fe_twoway"}[variant]
    if eq == "PT2" and variant == "b":
        spec, note = "pooled", "trùng (a) theo cấu trúc (không có biến giải thích)"

    res = fit(y, X, df["bank_id"], df["t"], spec)
    b, secl, seols = res["b"], res["se_cl"], res["se_ols"]
    off = 1 if spec == "pooled" else 0     # pooled: cột 0 là hằng số
    n, G, r2, r2c = res["n"], res["G"], res["r2"], res["r2_common"]
    rows = []

    def add(param, coef, scl, sols=np.nan, nt=""):
        rows.append(_row(meta, param, coef, scl, sols, r2, r2c, n, G, yv, nt))

    # --- hệ số trên biến giải thích
    for j, nm in enumerate(names):
        pn = nm
        if eq == "PT4" and nm == "beta":
            add("beta", b[j + off], secl[j + off], seols[j + off])
            add("epsilon", -b[j + off], secl[j + off], seols[j + off], "ε = -β")
        else:
            add(pn, b[j + off], secl[j + off], seols[j + off])

    if eq == "PT1b":   # kiểm định ràng buộc b + γ = 1 của mô hình
        jb, jg = names.index("b") + off, names.index("gamma") + off
        v = res["cov_cl"][jb, jb] + res["cov_cl"][jg, jg] + 2 * res["cov_cl"][jb, jg]
        add("b+gamma-1", b[jb] + b[jg] - 1, np.sqrt(v), nt="mô hình ngụ ý 0")

    # --- hằng số và đại lượng suy ra
    slope = None
    if eq in ("PT1", "PT3", "PT4"):
        slope = names.index({"PT1": "lambda", "PT3": "sigma", "PT4": "beta"}[eq]) + off
    if spec == "pooled":
        a0, sa0 = b[0], secl[0]
        if eq == "PT1":
            lam, sl = b[slope], secl[slope]
            g = np.array([1 / lam, -a0 / lam ** 2])
            idx = [0, slope]
            v = g @ res["cov_cl"][np.ix_(idx, idx)] @ g
            add("margin_const", a0 / lam, np.sqrt(v), nt="α/λ, delta cụm" + ("; λ gần 0 nên tỷ số kém tin cậy" if abs(lam / sl) < 2 else ""))
        elif eq == "PT1b":
            add("a_const", a0, sa0, seols[0])
        elif eq == "PT2":
            add("mu_margin", a0, sa0, seols[0])
        elif eq == "PT3":
            add("a_D", a0, sa0, seols[0])
        elif eq == "PT4":
            add("a_L", a0, sa0, seols[0])
            g = np.array([1.0, REFERENCE_RATE])
            idx = [0, slope]
            v = g @ res["cov_cl"][np.ix_(idx, idx)] @ g
            add("base_growth_L", a0 + REFERENCE_RATE * b[slope], np.sqrt(v), nt="a_L + 9.5β, delta cụm")
    elif spec == "fe_bank":
        al = fe_intercepts(y, X, b, df["bank_id"])
        am, sam = _fe_level(al)
        tag = "trung bình hằng số FE; cột SE = độ phân tán giữa NH sd/√8, KHÔNG phải SE chuẩn" + ("; hằng số tại ON trung bình" if variant == "d" else "")
        if eq == "PT1":
            lam, sl = b[slope], secl[slope]
            v = sam ** 2 / lam ** 2 + am ** 2 / lam ** 4 * sl ** 2
            add("margin_const", am / lam, np.sqrt(v), nt=tag + "; α_i/λ" + ("; λ gần 0 nên tỷ số kém tin cậy" if abs(lam / sl) < 2 else ""))
        elif eq == "PT1b":
            add("a_const", am, sam, nt=tag)
        elif eq == "PT2":
            add("mu_margin", am, sam, nt=tag)
        elif eq == "PT3":
            add("a_D", am, sam, nt=tag)
        elif eq == "PT4":
            add("a_L", am, sam, nt=tag)
            v = sam ** 2 + REFERENCE_RATE ** 2 * secl[slope] ** 2
            add("base_growth_L", am + REFERENCE_RATE * b[slope], np.sqrt(v), nt="ā + 9.5β; SE xấp xỉ, bỏ hiệp phương sai")
    return rows, res


def estimate_all(df, yv):
    """Toàn bộ biến thể cho cả bốn phương trình, mẫu N=112 và N=104."""
    s112, s104 = sample(df, 2), sample(df, 3)
    out = []
    plan = []   # (eq, c_def)
    for eq in ("PT1", "PT1b", "PT2"):
        plan += [(eq, "main"), (eq, "old")]
    plan += [("PT3", "main"), ("PT4", "main")]
    for eq, cd in plan:
        for sname, s in (("N112", s112), ("N104", s104)):
            variants = [("a", np.nan), ("b", np.nan), ("c", np.nan)]
            if sname == "N112":
                variants += [("d", 0), ("d", 1)]
            else:
                variants += [("d", 2)]
            for v, k in variants:
                rows, _ = run_variant(eq, s, cd, v, k, sname, yv)
                out += rows
    return pd.DataFrame(out)


# ======================================================================
# 5. FE quý hấp thụ bao nhiêu, lãi suất qua đêm thay thế được bao nhiêu
# ======================================================================

def absorption(df):
    rows = []
    for eq in ("PT1", "PT2", "PT3", "PT4"):
        for k, tmin in ((0, 2), (1, 2), (2, 3)):
            s = sample(df, tmin)
            cd = "main"
            y, Xdf = eq_vars(eq, s, cd)
            X = Xdf.to_numpy(float).reshape(len(s), -1)
            on = s[f"ON{k}"].to_numpy(float)
            xb = fit(y, X, s["bank_id"], s["t"], "fe_bank")
            xc = fit(y, X, s["bank_id"], s["t"], "fe_twoway")
            xd = fit(y, np.column_stack([X, on - on.mean()]), s["bank_id"], s["t"], "fe_bank")
            xq = fit(y, np.zeros((len(s), 0)), s["bank_id"], s["t"], "fe_twoway")
            tss = xb["tss_bank"]
            sb, sc, sd, sq = (1 - r["ssr"] / tss for r in (xb, xc, xd, xq))
            # Phiên bản hiệu chỉnh bậc tự do (nền: N - G sau khi trừ trung bình NH)
            N_, G_, T_, k_ = len(s), xb["G"], xb["T"], X.shape[1]
            adj = lambda share, k_all: 1 - (1 - share) * (N_ - G_) / (N_ - k_all)
            sb_a, sc_a, sd_a = adj(sb, k_ + G_), adj(sc, k_ + G_ + T_ - 1), adj(sd, k_ + 1 + G_)
            # Thành phần chung: trung bình theo quý của y sau khi trừ trung bình ngân hàng
            bc, tc = _codes(s["bank_id"]), _codes(s["t"])
            ytil = _demean(y, bc, bc.max() + 1)
            m = _group_means(ytil, tc, tc.max() + 1)[:, 0]
            ont = _group_means(on, tc, tc.max() + 1)[:, 0]
            # OLS đơn giản trên T điểm (m_t theo ON_{t-k}); chỉ lấy R² và hệ số góc
            Zc = np.column_stack([np.ones(len(m)), ont])
            bc_ = np.linalg.solve(Zc.T @ Zc, Zc.T @ m)
            ssr_c = ((m - Zc @ bc_) ** 2).sum()
            r2_common = 1 - ssr_c / ((m - m.mean()) ** 2).sum()
            rows.append({
                "equation": eq, "lag_on": k, "n": len(s),
                "share_X_bank_FE": sb, "share_quarter_FE_only": sq,
                "share_X_bank_quarter_FE": sc, "share_X_bank_ON": sd,
                "ratio_ON_vs_quarterFE": (sd - sb) / (sc - sb) if sc - sb > 1e-12 else np.nan,
                "ratio_adj_df": (sd_a - sb_a) / (sc_a - sb_a) if sc_a - sb_a > 1e-12 else np.nan,
                "R2_common_on_ON": r2_common, "slope_common_on_ON": bc_[1],
                "approx_share_explained_by_ON_via_common": r2_common * sq,
            })
    return pd.DataFrame(rows)


# ======================================================================
# 6. Mùa vụ quý 4 và quan sát bất thường (để Minh kiểm tra)
# ======================================================================

def seasonality_and_outliers(df):
    s = sample(df, 2).copy()
    s["q"] = s["per"].dt.quarter
    mean_rows, out_rows = [], []
    for v, label in (("gD", "g^D"), ("gL", "g^L"), ("dRL", "Δr^L")):
        dm = s[v] - s.groupby("bank_id")[v].transform("mean")
        for q in (1, 2, 3, 4):
            mean_rows.append({
                "bien": label, "quy_trong_nam": q,
                "tb_tho": s.loc[s.q == q, v].mean(),
                "tb_tru_TB_NH": dm[s.q == q].mean(),
                "n": int((s.q == q).sum()),
            })
        med = s[v].median()
        mad = 1.4826 * (s[v] - med).abs().median()
        s[f"z_{v}"] = (s[v] - med) / mad
    for v, label in (("gD", "g^D"), ("gL", "g^L"), ("dRL", "Δr^L")):
        top = s.reindex(s[f"z_{v}"].abs().sort_values(ascending=False).index).head(6)
        for _, r in top.iterrows():
            out_rows.append({"bien": label, "bank_id": r["bank_id"], "period": r["period"],
                             "gia_tri": r[v], "z_robust": r[f"z_{v}"], "ly_do": "z robust lớn nhất"})
    # Các quan sát người dùng yêu cầu kiểm tra
    chk = s[((s.bank_id == "HDBank") & (s.period == "2023Q2")) |
            ((s.bank_id == "MB Bank") & (s.q == 4))]
    for _, r in chk.iterrows():
        for v, label in (("gD", "g^D"), ("gL", "g^L"), ("dRL", "Δr^L")):
            out_rows.append({"bien": label, "bank_id": r["bank_id"], "period": r["period"],
                             "gia_tri": r[v], "z_robust": r[f"z_{v}"],
                             "ly_do": "HDBank 2023Q2 / MB Bank quý 4 (yêu cầu kiểm tra)"})
    return pd.DataFrame(mean_rows), pd.DataFrame(out_rows)


# ======================================================================
# 7. Xuất bảng
# ======================================================================

HEADLINE = ["lambda", "margin_const", "mu_margin", "sigma", "a_D", "epsilon", "base_growth_L", "b+gamma-1"]


def _fmt(x, d=4):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return ""
    return f"{x:.{d}f}"


def md_table(df, cols, digits=4):
    head = "| " + " | ".join(cols) + " |\n|" + "|".join(["---"] * len(cols)) + "|\n"
    body = ""
    for _, r in df.iterrows():
        body += "| " + " | ".join(
            _fmt(r[c], digits) if isinstance(r[c], (float, np.floating)) else str(r[c]) for c in cols) + " |\n"
    return head + body


def headline_table(est, c_def, sample_name="N112"):
    d = est[(est.parameter.isin(HEADLINE)) & (est["sample"] == sample_name)
            & (est.c_def.isin([c_def, "-"]))].copy()
    d["bien_the"] = d.variant + d.lag_on.map(lambda k: "" if k != k else f"(lag{int(k)})")
    d["R2"] = d["r2"]
    cols = ["equation", "parameter", "bien_the", "coef", "se_cluster", "t_cluster",
            "ci95_lo", "ci95_hi", "se_ols", "R2", "n", "yaml_value"]
    return d[cols]


def stability_table(est):
    """So hệ số và CI giữa mẫu N=112 và N=104 (bỏ 2023Q2) cho biến thể a, b, c."""
    d = est[est.variant.isin(["a", "b", "c"]) & est.parameter.isin(HEADLINE)
            & est.c_def.isin(["main", "-"])]
    w = d.pivot_table(index=["equation", "parameter", "variant"], columns="sample",
                      values=["coef", "ci95_lo", "ci95_hi"], aggfunc="first")
    w.columns = [f"{a}_{b}" for a, b in w.columns]
    w = w.reset_index()
    cont0 = lambda lo, hi: (lo <= 0) & (hi >= 0)
    w["CI112_chua_0"] = cont0(w.ci95_lo_N112, w.ci95_hi_N112)
    w["CI104_chua_0"] = cont0(w.ci95_lo_N104, w.ci95_hi_N104)
    w["doi_dau"] = np.sign(w.coef_N112) != np.sign(w.coef_N104)
    return w[["equation", "parameter", "variant", "coef_N112", "coef_N104",
              "CI112_chua_0", "CI104_chua_0", "doi_dau"]]


def write_outputs(est, absr, seas, outl, outdir=OUTDIR):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    est.to_csv(outdir / "estimates_stage7.csv", index=False)
    absr.to_csv(outdir / "absorption_stage7.csv", index=False)
    outl.to_csv(outdir / "outliers_stage7.csv", index=False)

    md = ["# Giai đoạn 7: ước lượng phương trình hành vi từ panel (sinh tự động)\n",
          "> Chỉ để đối chiếu với giá trị giả định trong `configs/scenarios.yaml`; **không** sửa configs. "
          "Kết quả là ước lượng trong mẫu, không phải tác động chính sách thực tế.\n",
          "## Phương pháp và hạn chế\n",
          "- Panel 8 ngân hàng x 15 quý; sau lấy trễ 1 quý còn N = 112 (N = 104 khi cần lãi suất qua đêm trễ 2 quý).",
          "- Ánh xạ: `r^D = deposit_rate_pct/(1-casa)`, nên `c = deposit_rate_pct + 0.15` (kết quả chính). Phụ lục dùng công thức cũ (trừ CASA hai lần).",
          "- Biến thể: (a) OLS gộp; (b) FE ngân hàng; (c) FE ngân hàng + quý; (d) FE ngân hàng + lãi suất qua đêm `bq_gian_don` trễ 0/1/2 quý (tâm hoá, nên hằng số tính tại ON trung bình).",
          f"- SE cụm CR1 theo ngân hàng, **chỉ 8 cụm**: SE cụm thường bị đánh thấp, nên dùng t với 7 bậc tự do (giá trị tới hạn {T_CRIT}). Kèm SE thường để so sánh.",
          "- R²: gộp = R² thường; FE = R² within (nền riêng của từng biến thể).",
          "- **Hạn chế quan trọng nhất:** SE cụm theo ngân hàng KHÔNG xử lý được phụ thuộc chéo giữa các ngân hàng trong cùng một quý. "
          "Quý FE một mình giải thích khoảng 71% phương sai within của Δr^L (xem mục hấp thụ), tức cú sốc chung rất lớn, nên t-stat và khoảng tin cậy của (a), (b), (d) bị đánh giá QUÁ CAO "
          "(với (d) thông tin hiệu dụng của lãi suất qua đêm chỉ cỡ 14 điểm theo quý). Chỉ (c) kiểm soát được cú sốc cộng chung, nhưng vẫn chỉ 8 cụm và vẫn có thể thấp SE. "
          "Không nên dùng chữ \"có ý nghĩa\" cho (a), (b), (d). Wild-cluster bootstrap hoặc Driscoll-Kraay chưa được làm (chờ nhóm quyết định).",
          "- Nickell (PT1, T = 14): FE ngân hàng làm lệch XUỐNG hệ số của biến trễ r^L_{t-1} (= 1-λ), nên λ của (b), (c), (d) có xu hướng bị lệch LÊN. "
          "Ngược lại λ của (a) bị kéo xuống vì hiệu ứng ngân hàng bị bỏ sót (biên khác nhau giữa các NH tương quan với mức r^L_{t-1}). "
          "Khoảng λ = 0.11 đến 0.53 là khoảng giữa hai cực thiên lệch, KHÔNG phải khoảng tin cậy.",
          "- Biến thể (d) thêm lãi suất qua đêm, vốn không có trong mô hình; kiểm định b+γ=1 bị bác ở (d0) và (d1), nên (d) không còn là PT1 của mô hình. Hằng số của (d) tính tại ON trung bình.",
          "- Hằng số/đại lượng suy ra trong biến thể FE (`margin_const`, `a_D`, `base_growth_L`, `mu_margin`) là trung bình hằng số FE theo ngân hàng; cột `se_cluster` của các hàng đó là **độ phân tán giữa NH sd/√8, không phải SE chuẩn** (bỏ qua sai số ước lượng hằng số từng NH và hiệp phương sai với độ dốc). Biến thể (c) không nhận diện được mức.",
          "- PT3/PT4 là cân bằng cung-cầu đồng thời, OLS không cho nhân quả. Hệ số PT4 gộp có dấu ngược (β > 0): xu hướng chung 2023-2026 (lãi suất giảm, tăng trưởng cao), không phải độ co giãn. "
          "Dấu dương của ε trong (b), (d1) KHÔNG bền: ở mẫu N = 104 các biến thể (b), (c), (d2) đều có khoảng tin cậy chứa 0 (xem bảng ổn định).",
          "- Cả `deposit_rate_pct` và `loan_rate_pct` là lợi suất sổ sách, trễ so với lãi suất cận biên.",
          "- Mô hình chặn g^D trong ±0.04 và g^L trong [-0.04, 0.035], nhưng 42% quan sát g^D và 59% g^L nằm ngoài; OLS ước lượng phần tuyến tính toàn mẫu. "
          "Hằng số ước lượng a_D ≈ 0.045 và base_growth_L ≈ 0.05 cao gấp 8-11 lần giá trị mô hình (0.004, 0.006): đây là **khoảng cách mô hình - dữ liệu** (tăng trưởng nền của dữ liệu lớn hơn cả trần chặn), không phải kết quả ước lượng độ nhạy lãi suất.",
          "- `target_margin` (3.2) và `loan_spread_add` (1.35) chỉ nhận diện được **tổng**. Việc μ ≈ 4.59 gần 4.55 chỉ là khớp trong mẫu: chưa xác nhận nguồn gốc con số 1.35 (nếu từng chọn theo dữ liệu 2023Q1 thì không phải kiểm định độc lập), và r^L - c_{t-1} chưa ở trạng thái dừng (c giảm mạnh giai đoạn 2023-2024, r^L điều chỉnh chậm).\n"]

    md.append("## Bảng chính (mẫu N = 112; c = deposit_rate_pct + 0.15)\n")
    md.append(md_table(headline_table(est, "main"),
                       ["equation", "parameter", "bien_the", "coef", "se_cluster", "t_cluster",
                        "ci95_lo", "ci95_hi", "se_ols", "R2", "n", "yaml_value"]))
    md.append("\n## Độ trễ 2 quý (mẫu N = 104, cùng mẫu cho a, b, c, d2)\n")
    md.append(md_table(headline_table(est, "main", "N104"),
                       ["equation", "parameter", "bien_the", "coef", "se_cluster", "t_cluster",
                        "ci95_lo", "ci95_hi", "se_ols", "R2", "n", "yaml_value"]))
    md.append("\n## FE quý hấp thụ bao nhiêu, lãi suất qua đêm thay thế được bao nhiêu\n")
    md.append("Các `share_*` là tỷ lệ phương sai within-ngân-hàng của biến phụ thuộc được giải thích (nền chung = tổng bình phương sau khi trừ trung bình ngân hàng). "
              "`ratio_ON_vs_quarterFE` = (share_X_bank_ON - share_X_bank_FE) / (share_X_bank_quarter_FE - share_X_bank_FE), chưa hiệu chỉnh bậc tự do (13 biến giả quý luôn cộng thêm R² giả nhiều hơn 1 biến ON, nên tỷ lệ này có thể thấp hơn thực tế); `ratio_adj_df` là bản hiệu chỉnh. "
              "`R2_common_on_ON` = R² khi hồi quy thành phần chung theo quý (trung bình các NH của biến sau khi trừ trung bình NH) lên lãi suất qua đêm trễ k, **chỉ trên 14 hoặc 13 điểm** và bị chi phối bởi cú sốc 2023 (ON giảm 4.8 -> 3.6 -> 0.2). "
              "`approx_share_explained_by_ON_via_common` = R2_common_on_ON x share_quarter_FE_only: phần phương sai within của biến phụ thuộc mà ON giải thích qua thành phần chung (ví dụ Δr^L, trễ 1: khoảng 0.5, không phải 0.71). "
              "Lưu ý: ở PT1 trễ 1, `share_quarter_FE_only` (0.708105) và `R2_common_on_ON` (0.708102) trùng đến 5 chữ số **do ngẫu nhiên**; chúng là hai đại lượng khác nhau.\n")
    md.append(md_table(absr, list(absr.columns)))
    md.append("\n## Ổn định giữa N = 112 và N = 104 (bỏ 2023Q2), biến thể a, b, c\n")
    md.append("`CI..._chua_0` = True nghĩa là khoảng tin cậy 95% (cụm, t7) chứa 0. Cảnh báo: với (a), (b) khoảng tin cậy bị đánh giá quá hẹp do cú sốc chung theo quý.\n")
    md.append(md_table(stability_table(est), ["equation", "parameter", "variant", "coef_N112", "coef_N104",
                                              "CI112_chua_0", "CI104_chua_0", "doi_dau"]))
    md.append("\n## Mùa vụ theo quý trong năm (chỉ là gợi ý, chưa kiểm định; số quan sát theo quý không cân bằng nên lẫn xu hướng thời gian)\n")
    md.append(md_table(seas, list(seas.columns)))
    md.append("\n## Quan sát bất thường để Minh kiểm tra\n")
    md.append("`z_robust` = (x - trung vị)/(1.4826 MAD) trên toàn mẫu 112 quan sát.\n")
    md.append(md_table(outl, list(outl.columns)))
    md.append("\n## Phụ lục: công thức chi phí vốn cũ (trừ CASA hai lần)\n")
    md.append(md_table(headline_table(est, "old"),
                       ["equation", "parameter", "bien_the", "coef", "se_cluster", "t_cluster",
                        "ci95_lo", "ci95_hi", "se_ols", "R2", "n", "yaml_value"]))
    md.append("\nToàn bộ hàng (mọi hệ số, hằng số, SE thường, R² chung nền): `estimates_stage7.csv`; hấp thụ: `absorption_stage7.csv`; bất thường: `outliers_stage7.csv`.\n")
    (outdir / "estimates_stage7.md").write_text("\n".join(md), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outdir", default=str(OUTDIR))
    args = ap.parse_args()
    df = load_data()
    est = estimate_all(df, yaml_values())
    absr = absorption(df)
    seas, outl = seasonality_and_outliers(df)
    write_outputs(est, absr, seas, outl, args.outdir)
    print(f"Đã ghi kết quả vào {args.outdir}")


if __name__ == "__main__":
    main()
