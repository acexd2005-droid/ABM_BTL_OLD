"""Giai đoạn 7b: ước lượng phương trình lãi suất huy động (KHÔNG sửa mô hình, KHÔNG sửa configs).

Quy tắc trong mô hình (src/agents/bank.py, Bank.step, bước 1-2):
    Δr^D_t = base_deposit_rate_step + deposit_competition · clip(LDR − 0.82, ±0.5)       (0.018, 0.07)
LDR = loans/deposits đo ĐẦU quý t (= cuối quý t-1: ngân hàng chạy trước khối người gửi/người vay), nên
trong panel dùng LDR_{t-1}. Kịch bản C nhân thêm deposit_cap_factor sau chính sách (ngoài mẫu).

Dữ liệu: r^D_term = deposit_rate_pct/(1 - casa) (cơ sở `term`, đã được duyệt ở Bước A), LDR từ panel.

  PT5     Δr^D_t = a + δ LDR_{t-1}                         a = base_step - δ·0.82; δ ↔ deposit_competition
  PT5z    Δr^D_t = a + δ clip(LDR_{t-1} - 0.82, ±0.5)      dạng đúng của mô hình; a = base_step
  PT5-ON  Δr^D_t = α + δ LDR_{t-1} + φ (ON_{t-k} - r^D_{t-1}),  k = 1, 2, 3   (FE ngân hàng)
          φ = tốc độ điều chỉnh về phía lãi suất qua đêm bình quân đơn giản của quý
          Cân bằng ngụ ý: r* - ON = (α + δ LDR)/φ = Δr̄/φ + mean(r_{t-1} - ON_{t-k})   (vì Δr̄ = ᾱ + δ·LDR̄ + φ·W̄)
Biến thể: (a) OLS gộp, (b) FE ngân hàng, (c) FE ngân hàng + quý, (d) FE ngân hàng + số hạng ON.
Với PT5-ON ở (c): ON bị FE quý hấp thụ nên φ = -hệ số của r^D_{t-1} (tốc độ điều chỉnh về mức chung theo quý).
Mẫu: N = 112 (t >= 2), 104 (t >= 3), 96 (t >= 4); ON trễ k cần t >= k + 1. Mẫu chung nhỏ nhất N = 96.

Mô phỏng offline (không đưa vào mô hình): chạy phương trình huy động ước lượng được với ON thực và LDR thực,
rồi chi phí vốn c = r^D_term (1 - casa) + 0.15 và lãi suất cho vay theo PT1 hiện tại; so với chuỗi thực. TRONG MẪU.

Chạy: python -m src.calibration.estimate_deposit_equation
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .estimate_equations import (
    CONFIG, MACRO, T_CRIT, BOOT_SEED, FUNDING_CONST, TARGET_MARGIN, _codes, _read_param, _demean, _fe_level, _group_means, _row,
    estimate_all, fe_intercepts, fit, load_data, run_variant, sample, wild_cluster_bootstrap, yaml_values,
)

ROOT = Path(__file__).resolve().parents[2]
OUTDIR = ROOT / "reports/calibration"
PIVOT = _read_param("deposit_ldr_target", 0.82)   # YAML deposit_ldr_target: ldr - 0.82 trong bank.py
CLIP = _read_param("demand_pressure_cap", 0.5)     # YAML demand_pressure_cap: ±0.5 trong bank.py
T0 = 4               # quý bắt đầu mô phỏng offline (2023Q4); cần ON trễ tới 3 quý
def _read_margin_const():
    """target_margin (YAML, 3.2) + loan_spread_add (YAML, 1.35) = 4.55 hiện hành."""
    with open(CONFIG, encoding="utf-8") as f:
        return TARGET_MARGIN + float(yaml.safe_load(f)["parameters"]["loan_spread_add"])


MARGIN_CONST = _read_margin_const()
# FUNDING_CONST nhập từ estimate_equations (YAML funding_cost_add)


# ======================================================================
# 1. Dữ liệu
# ======================================================================

def prepare():
    df = load_data()
    m = pd.read_csv(MACRO)
    m["per"] = pd.PeriodIndex(m["quy"], freq="Q")
    on = dict(zip(m["per"].astype(int), m["bq_gian_don"]))
    base = int(df["per"].astype(int).min())
    g = df.groupby("bank_id")
    df["ldr"] = df["loans"] / df["deposits"]
    df["ldr_lag"] = g["ldr"].shift()
    df["rD_lag"] = g["rD"].shift()
    df["drD"] = df["rD"] - df["rD_lag"]
    df["z_lag"] = (df["ldr_lag"] - PIVOT).clip(-CLIP, CLIP)
    for k in (1, 2, 3):
        df[f"ONk{k}"] = (df["t"] - 1 + base - k).map(on)
        df[f"W{k}"] = df[f"ONk{k}"] - df["rD_lag"]
    return df, on


def yaml7b():
    with open(CONFIG, encoding="utf-8") as f:
        p = yaml.safe_load(f)["parameters"]
    base, delta = p["base_deposit_rate_step"], p["deposit_competition"]
    return {"delta": delta, "base_step_implied": base, "a_const": base - delta * PIVOT,
            "a_z": base}


TMIN = {1: 2, 2: 3, 3: 4}
SAMPLES = (("N112", 2), ("N104", 3), ("N96", 4))


# ======================================================================
# 2. Ước lượng PT5, PT5z, PT5-ON
# ======================================================================

def _mk(df, eq, variant, k, sname):
    meta = {"c_def": "-", "equation": eq, "variant": variant, "sample": sname,
            "lag_on": float(k) if k else np.nan}
    return meta


def _est(eq, df, variant, k, sname, yv):
    """Một mô hình → danh sách hàng. eq ∈ PT5, PT5z, PT5-ON."""
    y = df["drD"].to_numpy()
    n = len(df)
    meta = _mk(df, eq, variant, k, sname)
    base_col = "z_lag" if eq == "PT5z" else "ldr_lag"
    if eq in ("PT5", "PT5z"):
        X = df[[base_col]].to_numpy()
        names = ["delta"]
        spec = {"a": "pooled", "b": "fe_bank", "c": "fe_twoway"}[variant]
    elif variant == "d":
        X = df[["ldr_lag", f"W{k}"]].to_numpy()
        names = ["delta", "phi"]
        spec = "fe_bank"
    elif variant == "c":      # ON bị FE quý hấp thụ: φ = -hệ số của r_{t-1}
        X = df[["ldr_lag", "rD_lag"]].to_numpy()
        names = ["delta", "phi_neg"]
        spec = "fe_twoway"
    else:
        raise ValueError((eq, variant))
    res = fit(y, X, df["bank_id"], df["t"], spec)
    b, se, seo, cov = res["b"], res["se_cl"], res["se_ols"], res["cov_cl"]
    off = 1 if spec == "pooled" else 0
    r2, r2c, G = res["r2"], res["r2_common"], res["G"]
    rows = []

    def add(param, coef, scl, sols=np.nan, note=""):
        rows.append(_row(meta, param, coef, scl, sols, r2, r2c, n, G, yv, note))

    for j, nm in enumerate(names):
        if nm == "phi_neg":
            add("phi", -b[j + off], se[j + off], seo[j + off], "φ = -hệ số của r^D_{t-1} (ON bị FE quý hấp thụ)")
        else:
            add(nm, b[j + off], se[j + off], seo[j + off])
    jd = off  # chỉ số của delta

    # hằng số và đại lượng suy ra
    if spec == "pooled":
        a0, sa0 = b[0], se[0]
        if eq == "PT5":
            add("a_const", a0, sa0, seo[0], "hằng số gộp; mô hình ngụ ý base_step - δ·0.82")
            g = np.array([1.0, PIVOT])
            v = g @ cov[np.ix_([0, jd], [0, jd])] @ g
            add("base_step_implied", a0 + PIVOT * b[jd], np.sqrt(v), note="a + 0.82δ, delta cụm")
        else:   # PT5z
            add("base_step_implied", a0, sa0, seo[0], "hằng số = base_step (biến đã chặn)")
    elif spec == "fe_bank":
        al = fe_intercepts(y, X, b, df["bank_id"])
        am, sam = _fe_level(al)
        tag = "trung bình hằng số FE; cột SE = độ phân tán giữa NH sd/√8, KHÔNG phải SE chuẩn"
        if eq == "PT5":
            add("a_const", am, sam, note=tag)
            v = sam ** 2 + PIVOT ** 2 * se[jd] ** 2
            add("base_step_implied", am + PIVOT * b[jd], np.sqrt(v), note="ā + 0.82δ; SE xấp xỉ, bỏ hiệp phương sai")
        elif eq == "PT5z":
            add("base_step_implied", am, sam, note=tag)
        else:   # PT5-ON, biến thể d
            phi, sphi = b[1], se[1]
            dbar = float(np.mean(y))
            spread_now = float(np.mean(-df[f"W{k}"]))          # trung bình (r_{t-1} - ON_{t-k})
            add("alpha_mean", am, sam, note=tag + " (tại W = 0, tức r = ON)")
            add("speed_per_quarter", phi, sphi, seo[1], "= φ: phần chênh lệch với ON được thu hẹp mỗi quý")
            if 0 < phi < 1:
                add("half_life_quarters", np.log(0.5) / np.log(1 - phi), np.nan, note="ln0.5/ln(1-φ)")
            add("spread_actual_mean", spread_now, np.nan, note="trung bình mẫu của r^D_{t-1} - ON_{t-k}")
            add("spread_equilibrium", dbar / phi + spread_now, np.nan,
                note="Δr̄/φ + chênh lệch TB. Vì Δr̄ ≈ 0 nên gần như bằng chính spread thực trung bình (mang tính định nghĩa); KHÔNG có SE")
    return rows, res


def estimate_all_7b(df, yv):
    out = []
    for sname, tmin in SAMPLES:
        s = sample(df, tmin)
        for v in ("a", "b", "c"):
            out += _est("PT5", s, v, None, sname, yv)[0]
            out += _est("PT5z", s, v, None, sname, yv)[0]
        out += _est("PT5-ON", s, "c", None, sname, yv)[0]
        for k in (1, 2, 3):
            if TMIN[k] <= tmin:           # ON trễ k khả dụng trên mẫu này
                out += _est("PT5-ON", s, "d", k, sname, yv)[0]
    return pd.DataFrame(out)


# ======================================================================
# 3. Hấp thụ FE quý và tỷ lệ thay thế bởi ON
# ======================================================================

def absorption_7b(df):
    rows = []
    for k in (1, 2, 3):
        for sname, tmin in SAMPLES:
            if tmin < TMIN[k]:
                continue
            s = sample(df, tmin)
            y = s["drD"].to_numpy()
            X = s[["ldr_lag"]].to_numpy()
            Xon = s[["ldr_lag", f"W{k}"]].to_numpy()
            xb = fit(y, X, s["bank_id"], s["t"], "fe_bank")
            xc = fit(y, X, s["bank_id"], s["t"], "fe_twoway")
            xd = fit(y, Xon, s["bank_id"], s["t"], "fe_bank")
            xq = fit(y, np.zeros((len(s), 0)), s["bank_id"], s["t"], "fe_twoway")
            tss = xb["tss_bank"]
            sb, sc, sd, sq = (1 - r["ssr"] / tss for r in (xb, xc, xd, xq))
            N_, G_, T_ = len(s), xb["G"], xb["T"]
            adj = lambda share, k_all: 1 - (1 - share) * (N_ - G_) / (N_ - k_all)
            sb_a, sc_a, sd_a = adj(sb, 1 + G_), adj(sc, 1 + G_ + T_ - 1), adj(sd, 2 + G_)
            bc, tc = _codes(s["bank_id"]), _codes(s["t"])
            m = _group_means(_demean(y, bc, G_), tc, T_)[:, 0]
            wt = _group_means(s[f"W{k}"].to_numpy(), tc, T_)[:, 0]
            Zc = np.column_stack([np.ones(len(m)), wt])
            bcm = np.linalg.solve(Zc.T @ Zc, Zc.T @ m)
            r2m = 1 - ((m - Zc @ bcm) ** 2).sum() / ((m - m.mean()) ** 2).sum()
            rows.append({
                "lag_on": k, "sample": sname, "n": N_,
                "share_LDR_bank_FE": sb, "share_quarter_FE_only": sq,
                "share_LDR_bank_quarter_FE": sc, "share_LDR_ON_bank_FE": sd,
                "ratio_ON_vs_quarterFE": (sd - sb) / (sc - sb) if sc - sb > 1e-12 else np.nan,
                "ratio_adj_df": (sd_a - sb_a) / (sc_a - sb_a) if sc_a - sb_a > 1e-12 else np.nan,
                "R2_common_on_ON": r2m,
                "approx_share_explained_by_ON_via_common": r2m * sq,
            })
    return pd.DataFrame(rows)


def best_lag(df):
    """Độ trễ tốt nhất = k có phần phương sai within giải thích lớn nhất (SSR nhỏ nhất) trên mẫu chung N = 96."""
    s = sample(df, 4)
    y = s["drD"].to_numpy()
    out = {}
    for k in (1, 2, 3):
        r = fit(y, s[["ldr_lag", f"W{k}"]].to_numpy(), s["bank_id"], s["t"], "fe_bank")
        out[k] = r["r2_common"]
    return max(out, key=out.get), out


def bootstrap_phi(df, k):
    """Wild-cluster bootstrap Webb cho φ của độ trễ tốt nhất, trên mẫu chung N=96 và mẫu tự nhiên."""
    rows = []
    for sname, tmin in (("N96", 4), (f"tu_nhien_N{len(sample(df, TMIN[k]))}", TMIN[k])):
        s = sample(df, tmin)
        r = wild_cluster_bootstrap(s["drD"].to_numpy(), s[["ldr_lag", f"W{k}"]].to_numpy(),
                                   s["bank_id"], s["t"], "fe_bank", 1)
        r.update({"equation": "PT5-ON", "variant": "d", "lag_on": k, "parameter": "phi", "sample": sname,
                  "ci_cr1_lo": r["coef"] - T_CRIT * r["se_cr1"], "ci_cr1_hi": r["coef"] + T_CRIT * r["se_cr1"],
                  "n": len(s)})
        rows.append(r)
    cols = ["equation", "variant", "lag_on", "parameter", "sample", "coef", "se_cr1", "t_cr1", "ci_cr1_lo",
            "ci_cr1_hi", "p_boot", "ci_boot_lo", "ci_boot_hi", "B", "seed", "n"]
    return pd.DataFrame(rows)[cols]


# ======================================================================
# 4. Mô phỏng offline: phương trình huy động ước lượng được + PT1 hiện hành
# ======================================================================

def _alpha_params(df_s, variant_cols, bank_ids):
    """Ước lượng FE ngân hàng: trả (α_i theo ngân hàng, hệ số)."""
    y = df_s["drD"].to_numpy()
    X = df_s[variant_cols].to_numpy()
    res = fit(y, X, df_s["bank_id"], df_s["t"], "fe_bank")
    al = fe_intercepts(y, X, res["b"], df_s["bank_id"])
    order = pd.factorize(df_s["bank_id"])[1]
    return dict(zip(order, al)), res["b"]


def simulate_offline(df, on, lam, deposit_rule, k=None, alpha=None, coefs=None, yv=None):
    """Chạy offline từ t = T0 (khởi tạo bằng dữ liệu thực quý T0), tới t = max(t).

    deposit_rule ∈ actual | model_rule | pt5 | pt5on. LDR thực (trễ 1 quý) và ON thực được dùng làm ngoại sinh.
    Lãi suất cho vay: r^L_t = r^L_{t-1} + λ (c_{t-1} + MARGIN_CONST - r^L_{t-1}), c = r^D_term(1-casa)+0.15,
    casa giữ cố định ở giá trị quý T0 (như mô hình giữ casa khởi tạo).
    """
    banks = sorted(df["bank_id"].unique())
    tmax = int(df["t"].max())
    d0 = df[df["t"] == T0].set_index("bank_id")
    rD = d0.loc[banks, "rD"].to_numpy().copy()
    rL = d0.loc[banks, "rL"].to_numpy().copy()
    casa = d0.loc[banks, "casa_ratio"].to_numpy()
    path = []
    for t in range(T0 + 1, tmax + 1):
        cur = df[df["t"] == t].set_index("bank_id").loc[banks]
        ldr_lag = df[df["t"] == t - 1].set_index("bank_id").loc[banks, "ldr"].to_numpy()
        c_prev = rD * (1 - casa) + FUNDING_CONST
        if deposit_rule == "actual":
            c_prev = df[df["t"] == t - 1].set_index("bank_id").loc[banks, "c_main"].to_numpy()
            rD_new = cur["rD"].to_numpy()
        elif deposit_rule == "model_rule":
            rD_new = rD + yv["base_step_implied"] + yv["delta"] * np.clip(ldr_lag - PIVOT, -CLIP, CLIP)
        elif deposit_rule == "pt5":
            a = np.array([alpha[b] for b in banks])
            rD_new = rD + a + coefs[0] * ldr_lag
        elif deposit_rule == "pt5on":
            a = np.array([alpha[b] for b in banks])
            on_t = on_by_t(df, on, t - k)
            rD_new = rD + a + coefs[0] * ldr_lag + coefs[1] * (on_t - rD)
        else:
            raise ValueError(deposit_rule)
        rD = np.clip(rD_new, 0.0, 14.0)
        rL = np.clip(rL + lam * (c_prev + MARGIN_CONST - rL), 0.0, 20.0)
        w = cur["loans"].to_numpy()
        path.append({"t": t, "loan_rate": float((rL * w).sum() / w.sum()),
                     "deposit_rate_total_basis": float((rD * (1 - casa) * cur["deposits"].to_numpy()).sum()
                                                       / cur["deposits"].sum())})
    return pd.DataFrame(path)


def on_by_t(df, on, tq):
    """ON thực của quý có chỉ số t = tq (t = 1 ứng với quý đầu tiên của panel)."""
    base = int(df["per"].astype(int).min())
    return float(on[base + tq - 1])


def actual_paths(df):
    g = df.groupby("t")
    loan = (df["loans"] * df["rL"]).groupby(df["t"]).sum() / g["loans"].sum()
    dep = (df["deposit_rate_pct"] * df["deposits"]).groupby(df["t"]).sum() / g["deposits"].sum()
    return pd.DataFrame({"t": loan.index, "actual_loan_rate": loan.values, "actual_deposit_rate": dep.values})


def v_metrics(path, col, label, window):
    """Chỉ số hình chữ V trên cửa sổ so sánh (t >= T0 để thấy cả khởi đầu)."""
    p = path[path["t"] >= T0].reset_index(drop=True)
    i = int(p[col].idxmin())
    return {"chuoi": label, "tho_thap_nhat": p.loc[i, col], "quy_thap_nhat_t": int(p.loc[i, "t"]),
            "giam_tu_dau_den_day": p.loc[0, col] - p.loc[i, col],
            "hoi_phuc_tu_day_den_cuoi": p.iloc[-1][col] - p.loc[i, col]}


def margin_path(df):
    """Biên thực r^L_t - c_{t-1} (c = deposit_rate_pct + 0.15), gia quyền theo dư nợ, theo quý; mô hình giả định 4.55 không đổi."""
    d = df[df["t"] >= 2].copy()
    d["margin"] = d["rL"] - d["c_main_lag"]
    w = d["loans"]
    out = (d["margin"] * w).groupby(d["t"]).sum() / w.groupby(d["t"]).sum()
    q = d.groupby("t")["period"].first()
    return pd.DataFrame({"t": out.index, "quy": q.values, "bien_thuc_rL_tru_c_lag": out.values,
                         "bien_gia_dinh_mo_hinh": MARGIN_CONST})


def drift_table(df, yv):
    s = sample(df, 2)
    ldr_bar = float(s["ldr_lag"].mean())
    model_drift = yv["base_step_implied"] + yv["delta"] * float(np.clip(s["ldr_lag"] - PIVOT, -CLIP, CLIP).mean())
    return pd.DataFrame([{"mau": "N112", "dr_D_tb_thuc": float(s["drD"].mean()), "dr_D_sd_thuc": float(s["drD"].std()),
                          "LDR_lag_tb": ldr_bar, "LDR_lag_min": float(s["ldr_lag"].min()), "LDR_lag_max": float(s["ldr_lag"].max()),
                          "dr_D_ngu_y_quy_tac_hien_hanh_tai_LDR_thuc": model_drift}])


def run_simulation(df, on, est_lambda):
    yv = yaml7b()
    act = actual_paths(df)
    k, _ = best_lag(df)
    # Tham số huy động ước lượng (FE ngân hàng), mẫu tự nhiên của từng mô hình
    s_pt5 = sample(df, 2)
    al5, b5 = _alpha_params(s_pt5, ["ldr_lag"], None)
    s_on = sample(df, TMIN[k])
    alon, bon = _alpha_params(s_on, ["ldr_lag", f"W{k}"], None)
    runs = []
    for lam_name, lam in (("lambda_GD7_c", est_lambda), ("lambda_YAML_0.48", 0.48)):
        for rule, label in (("actual", "huy động thực (chỉ PT1)"),
                            ("model_rule", "quy tắc huy động hiện hành"),
                            ("pt5", "PT5 ước lượng (FE ngân hàng, không ON)"),
                            ("pt5on", f"PT5-ON ước lượng (k = {k})")):
            kw = {}
            if rule == "pt5":
                kw = dict(alpha=al5, coefs=b5)
            if rule == "pt5on":
                kw = dict(alpha=alon, coefs=bon, k=k)
            p = simulate_offline(df, on, lam, rule, yv=yv, **kw)
            p = p.merge(act, on="t")
            p["lambda_set"], p["huy_dong"] = lam_name, label
            runs.append(p)
    sim = pd.concat(runs, ignore_index=True)
    rows = []
    a_window = act[act["t"] >= T0]
    rows.append({"lambda_set": "-", "chuoi": "THỰC (cho vay)", "RMSE": 0.0, "RMSE_khu_muc": 0.0, "MAE": 0.0, "sai_so_tb": 0.0, "tuong_quan": 1.0,
                 **{k_: v for k_, v in v_metrics(act, "actual_loan_rate", "", T0).items() if k_ != "chuoi"}})
    for (lam_name, lab), g in sim.groupby(["lambda_set", "huy_dong"], sort=False):
        e = g["loan_rate"] - g["actual_loan_rate"]
        vm = v_metrics(g, "loan_rate", lab, T0)
        rows.append({"lambda_set": lam_name, "chuoi": lab, "RMSE": float(np.sqrt((e ** 2).mean())),
                     "RMSE_khu_muc": float(e.std(ddof=0)),
                     "MAE": float(e.abs().mean()), "sai_so_tb": float(e.mean()),
                     "tuong_quan": float(np.corrcoef(g["loan_rate"], g["actual_loan_rate"])[0, 1]),
                     **{k_: v for k_, v in vm.items() if k_ != "chuoi"}})
    return sim, pd.DataFrame(rows), k


# ======================================================================
# 5. Xuất bảng
# ======================================================================

HEAD = ["delta", "a_const", "base_step_implied", "phi", "speed_per_quarter", "half_life_quarters",
        "spread_actual_mean", "spread_equilibrium", "alpha_mean"]


def md_table(df, cols, digits=4):
    head = "| " + " | ".join(cols) + " |\n|" + "|".join(["---"] * len(cols)) + "|\n"
    body = ""
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                cells.append("" if v != v else f"{v:.{digits}f}")
            else:
                cells.append(str(v))
        body += "| " + " | ".join(cells) + " |\n"
    return head + body


def headline(est, eq, sname):
    d = est[(est.equation == eq) & (est["sample"] == sname) & est.parameter.isin(HEAD)].copy()
    d["bien_the"] = d.variant + d.lag_on.map(lambda k: "" if k != k else f"(k={int(k)})")
    return d[["parameter", "bien_the", "coef", "se_cluster", "t_cluster", "ci95_lo", "ci95_hi", "se_ols", "r2", "n", "yaml_value"]]


INTERPRETATION = """
## Diễn giải (viết tay sau khi xem kết quả; các con số lấy từ bảng ở trên, mẫu N = 112 nếu không nói khác)

**Quy tắc huy động hiện hành không mô tả được dữ liệu.**
- Hệ số theo LDR: δ ước lượng là 1.10 (a, gộp), 5.29 (b, FE ngân hàng), 1.19 (c, FE ngân hàng + quý), 2.01 (d, k = 1) so với `deposit_competition = 0.07`, tức gấp khoảng 15 đến 75 lần. Khoảng tin cậy CR1 của (c) là [0.46; 1.91] (N = 112), [-0.17; 1.20] (N = 104) và [-0.18; 1.76] (N = 96): chỉ một phần chứa 0.07. Các khoảng này bị đánh giá quá hẹp (cú sốc chung theo quý, 8 cụm).
- Trôi bình quân: dữ liệu có Δr^D_term trung bình 0.0006 điểm %/quý (độ lệch chuẩn 0.565) trong khi quy tắc hiện hành ngụ ý khoảng +0.038 điểm %/quý tại LDR thực (trung bình 1.12). `base_step_implied` ở LDR = 0.82 là ngoại suy ngoài miền dữ liệu, không nên đọc như ước lượng của 0.018.
- Dạng đúng của mô hình (PT5z, biến đã chặn) cho cùng kết luận.

**Phần lớn biến động của Δr^D là cú sốc chung theo quý, và lãi suất qua đêm giải thích phần lớn cú sốc đó.**
- FE quý một mình giải thích 81% (N = 112), 82% (N = 104), 85% (N = 96) phương sai within-ngân-hàng của Δr^D.
- ON trễ 1 quý: tỷ lệ thay thế FE quý là 0.70 (chưa hiệu chỉnh) và 0.74 (hiệu chỉnh) ở N = 112; R² của thành phần chung theo quý là 0.77, nhưng chỉ trên 13-14 điểm theo quý. Phần phương sai within của Δr^D mà ON giải thích qua thành phần chung khoảng 0.62. ON trễ 2: 0.63-0.65; ON trễ 3: gần 0 (0.04). Độ trễ tốt nhất theo tiêu chí đặt trước: k = 1.
- Với PT5-ON (d, k = 1): tốc độ điều chỉnh φ = 0.177 mỗi quý (N = 112; nửa vòng khoảng 3.6 quý). Bootstrap WCR-t Webb (B = 9999): CI 95% [0.147; 0.228] trên N = 96 và [0.156; 0.196] trên N = 112; `p_boot = 0.0000` nghĩa là không lần lặp nào cực đoan hơn (p < 1/9999). Ở (c) (ON bị FE quý hấp thụ), φ = 0.40 [0.28; 0.53] (CR1): hai con số không cùng mô hình, và φ ở các biến thể FE có xu hướng bị lệch lên do thiên lệch Nickell.
- Mức cân bằng ngụ ý của r^D so với ON (khoảng 1.1 đến 1.3 điểm %) gần như bằng spread thực trung bình trong mẫu; vì Δr̄ ≈ 0 nên đây gần như là định nghĩa, không phải ước lượng độc lập (không có SE).

**Mô phỏng offline (trong mẫu; LDR thực và ON thực là ngoại sinh, khởi tạo bằng dữ liệu thực 2023Q4, so sánh 11 quý 2024Q1-2026Q3).**
- Chuỗi thực của lãi suất cho vay gia quyền là chữ V: đáy 6.97% ở 2025Q1 (t = 9), giảm 1.76 điểm % từ 2023Q4 xuống đáy rồi hồi phục 1.81 điểm % tới 2026Q3.
- Quy tắc huy động hiện hành + PT1 cho đường gần như đi lên đơn điệu (giảm chỉ 0.02 điểm %): **không** tạo chữ V; RMSE 1.35 cho cả hai λ.
- PT5-ON + PT1 tạo chữ V đúng hướng, đáy lệch không quá 1 quý (t = 10 với λ = 0.274; t = 8 với λ = 0.48), nhưng **biên độ chỉ bằng khoảng 0.24 đến 0.44 lần biên độ thực**: giảm 0.57 và hồi phục 0.43 điểm % (λ = 0.274), giảm 0.73 và hồi phục 0.80 (λ = 0.48). RMSE 0.92 và 0.82 (so với 1.35 của quy tắc hiện hành); tương quan đường 0.72 và 0.89.
- PT5 không ON (FE ngân hàng): RMSE 1.06 (λ = 0.274) và 0.98 (λ = 0.48); biên độ giảm 0.44 và 0.51.
- **Ngay cả khi đưa lãi suất huy động thực vào PT1**, biên độ cũng chỉ giảm 0.75-0.88 và hồi phục 0.38-0.75 điểm % (RMSE 0.83 và 0.68). Quan sát mô tả (không phải nguyên nhân đã xác định): biên thực đã thực hiện `r^L − c_{t-1}` giảm từ 4.71 (2023Q2) xuống khoảng 3.68 (2025Q2) rồi tăng lên 4.51 (2026Q2), tức dao động khoảng 1 điểm %. 4.55 là biên MỤC TIÊU của PT1 (`target_margin` + `loan_spread_add`) mà `r^L` tiến tới với tốc độ λ, nên không so trực tiếp với biên thực; tuy vậy theo PT1 khi chi phí vốn giảm và `r^L` điều chỉnh trễ thì biên thực lẽ ra MỞ RỘNG, trong khi dữ liệu cho thấy biên thực HẸP lại, nghĩa là `r^L` giảm nhanh hơn chi phí vốn trễ. Phương trình huy động không bù được phần này; có kênh khác ngoài chi phí vốn trễ (chính sách, cạnh tranh, cơ cấu danh mục…) mà dữ liệu hiện có không phân biệt được. Kết quả mô phỏng này là kiểm tra trong mẫu (hệ số ước lượng trên cùng dữ liệu), không phải dự báo ngoài mẫu.
- RMSE/tương quan giữa các hàng chỉ dùng để so sánh tương đối; đường lai (huy động ước lượng + biên cố định) có thể tốt hơn đường dùng huy động thực ở một số chỉ số (ví dụ tương quan 0.89 so với 0.75 ở λ = 0.48), có thể do hai sai số bù nhau (chưa kiểm chứng); không nên diễn giải như bằng chứng cơ chế.
- **Sai số mức chi phối RMSE.** Sai số trung bình (mô hình − thực) là 0.57-1.26 điểm %, phần lớn của RMSE thô. Sau khi bỏ sai số trung bình (cột `RMSE_khu_muc`): PT5-ON 0.43 (λ = 0.274) và 0.33 (λ = 0.48); quy tắc huy động hiện hành 0.50 và 0.50; huy động thực 0.50 và 0.38; PT5 không ON 0.52 và 0.45. Về hình dạng, cải thiện của PT5-ON so với quy tắc hiện hành có thật nhưng khiêm tốn hơn con số RMSE thô; chênh lệch mức (mô hình cao hơn thực khoảng 0.57 đến 1.26 điểm %, tùy quy tắc huy động) chỉ một phần do phương trình huy động: ngay cả khi đưa lãi suất huy động thực vào PT1 mô hình vẫn lệch +0.57 đến +0.66 điểm %. Phần còn lại chưa được đo riêng (có thể liên quan biên mục tiêu 4.55 cao hơn biên thực trung bình khoảng 4.1); không kết luận nguyên nhân ở đây.

**Hạn chế và việc chờ nhóm quyết định.** LDR là biến nội sinh (LDR cao khi huy động khan, huy động tăng giá khi LDR cao); δ ở (b) lớn có thể phản ánh tương quan chung hơn là độ nhạy cơ chế. δ dao động 1.1 đến 5.3 tùy cách kiểm soát cú sốc chung nên không số nào là \"tham số đúng\". Mô phỏng offline dùng LDR thực làm ngoại sinh; trong ABM đầy đủ LDR là nội sinh nên kết quả có thể khác. Hệ số ON (φ) ở (d) chủ yếu được xác định bởi chuỗi ON theo thời gian (13-14 điểm), không phải bởi khác biệt giữa ngân hàng. PT5 và PT5-ON có hằng số riêng từng ngân hàng ước lượng trên chính mẫu này (trong mẫu), còn quy tắc hiện hành thì không, nên so sánh không đều về số tham số. Hằng số FE (alpha_mean) đi cùng δ·LDR_trung bình nên không đọc riêng. `bank.py` và `scenarios.yaml` KHÔNG được sửa ở Giai đoạn 7b; mọi thay đổi (thêm số hạng ON vào quy tắc huy động, biên cho vay biến thiên theo thời gian) là quyết định cho Giai đoạn 8-9 của trưởng nhóm.
"""


def write_outputs(est, absr, boot, sim, simsum, kbest, kr2, outdir=OUTDIR, margin=None, drift=None):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    est.to_csv(outdir / "estimates_stage7b.csv", index=False)
    absr.to_csv(outdir / "absorption_stage7b.csv", index=False)
    boot.to_csv(outdir / "bootstrap_stage7b.csv", index=False)
    sim.to_csv(outdir / "simulation_paths_stage7b.csv", index=False)
    simsum.to_csv(outdir / "simulation_summary_stage7b.csv", index=False)
    if margin is not None:
        margin.to_csv(outdir / "margin_path_stage7b.csv", index=False)
    cols = ["parameter", "bien_the", "coef", "se_cluster", "t_cluster", "ci95_lo", "ci95_hi", "se_ols", "r2", "n", "yaml_value"]
    md = ["# Giai đoạn 7b: ước lượng phương trình lãi suất huy động (sinh tự động)\n",
          "> Không sửa mô hình, không sửa `configs/`. Ước lượng trong mẫu, chỉ để đối chiếu; không phải tác động chính sách thực tế.\n",
          "## Quy tắc hiện tại và dạng ước lượng\n",
          "`Bank.step` (src/agents/bank.py): `Δr^D_t = base_deposit_rate_step + deposit_competition · clip(LDR − 0.82, ±0.5)` với `base_deposit_rate_step = 0.018` (điểm %/quý), `deposit_competition = 0.07`. "
          "`LDR = loans/deposits` đo **đầu quý t** (= cuối quý t−1, vì ngân hàng chạy trước khối người gửi/người vay trong `step()`), nên trong panel dùng `LDR_{t-1}`. "
          "Cơ sở `term`: `r^D = deposit_rate_pct/(1−casa)`. Kịch bản C nhân thêm `deposit_cap_factor` sau chính sách (ngoài mẫu).\n",
          "- **PT5:** `Δr^D_t = a + δ·LDR_{t-1}`; mô hình ngụ ý `a = 0.018 − 0.07·0.82 = −0.0394`, `δ = 0.07`; `base_step_implied = a + 0.82δ` so với 0.018.",
          "- **PT5z:** như PT5 nhưng dùng đúng biến `clip(LDR_{t-1} − 0.82, ±0.5)` (11/112 quan sát LDR_{t-1} nằm ngoài miền tuyến tính [0.32; 1.32]); khi đó hằng số = `base_step` trực tiếp.",
          "- **PT5-ON:** `Δr^D_t = α_i + δ·LDR_{t-1} + φ·(ON_{t-k} − r^D_{t-1})`, k = 1, 2, 3, FE ngân hàng; φ = tốc độ điều chỉnh về phía lãi suất qua đêm bình quân đơn giản của quý; "
          "cân bằng ngụ ý `r* − ON = Δr̄/φ + trung bình(r^D_{t-1} − ON_{t-k})`. Ở biến thể (c) ON bị FE quý hấp thụ nên φ = −hệ số của `r^D_{t-1}`.",
          "- Biến thể: (a) OLS gộp; (b) FE ngân hàng; (c) FE ngân hàng + quý; (d) FE ngân hàng + số hạng ON. SE cụm CR1 theo ngân hàng, **8 cụm** (t với 7 bậc tự do, 2.3646).",
          "- Mẫu: N = 112 (k = 1), 104 (k = 2), 96 (k = 3); mẫu chung nhỏ nhất N = 96 để so sánh các độ trễ.",
          "- Hạn chế cũ vẫn áp dụng (Giai đoạn 7): SE cụm theo ngân hàng không xử lý cú sốc chung theo quý nên t/CI của (a), (b), (d) bị đánh giá quá hẹp; thiên lệch Nickell với T = 14 cho hệ số của biến trễ r^D_{t-1} (φ ở (d) bị lệch lên); cột `se_cluster` của hằng số FE là độ phân tán giữa ngân hàng, không phải SE chuẩn; lợi suất sổ sách.\n"]
    for sname in ("N112", "N104", "N96"):
        for eq, title in (("PT5", "PT5"), ("PT5z", "PT5z (biến đã chặn)"), ("PT5-ON", "PT5-ON")):
            h = headline(est, eq, sname)
            md += [f"### {title}, mẫu {sname}\n", md_table(h, cols)]
    if drift is not None:
        md.append("## Trôi bình quân: dữ liệu so với quy tắc hiện hành\n")
        md.append("`base_step_implied` ở LDR = 0.82 là ngoại suy ra ngoài miền dữ liệu (LDR_{t-1} quan sát được từ khoảng 0.85, trung bình khoảng 1.1), nên so sánh thực chất là trôi bình quân tại LDR thực:\n")
        md.append(md_table(drift, list(drift.columns)))
    md.append("## FE quý hấp thụ bao nhiêu, ON thay thế bao nhiêu\n")
    md.append("Cách đọc giống Giai đoạn 7: `share_*` là tỷ lệ phương sai within-ngân-hàng của Δr^D được giải thích; `ratio_ON_vs_quarterFE` = (share_LDR_ON − share_LDR) / (share_LDR_bank_quarter_FE − share_LDR); "
              "`ratio_adj_df` đã hiệu chỉnh bậc tự do; `R2_common_on_ON` là R² trên **13-14 điểm theo quý** (thành phần chung theo quý hồi quy lên trung bình các ngân hàng của ON_{t-k} − r^D_{t-1}), "
              "`approx_share_explained_by_ON_via_common` = R2_common × share_quarter_FE_only.\n")
    md.append(md_table(absr, list(absr.columns)))
    md.append(f"## Độ trễ tốt nhất và wild-cluster bootstrap cho φ\n")
    md.append(f"Tiêu chí chọn (đặt trước): độ trễ có phần phương sai within giải thích lớn nhất trên mẫu chung N = 96. Kết quả: " +
              ", ".join(f"k = {k}: {v:.4f}" for k, v in kr2.items()) + f" ⇒ **k = {kbest}**. "
              f"Bootstrap WCR-t, trọng số Webb 6 điểm, B = {int(boot.B.iloc[0])}, seed = {int(boot.seed.iloc[0])}; vẫn chỉ 8 cụm, "
              "ON là biến chung theo quý nên thông tin hiệu dụng của φ cỡ 13-14 điểm.\n")
    md.append(md_table(boot, ["lag_on", "sample", "coef", "se_cr1", "t_cr1", "ci_cr1_lo", "ci_cr1_hi", "p_boot", "ci_boot_lo", "ci_boot_hi"]))
    md.append("## Mô phỏng offline (không đưa vào mô hình; trong mẫu)\n")
    md.append(f"Bắt đầu từ t = {T0} (2023Q4), khởi tạo bằng dữ liệu thực của quý đó (r^D_term, r^L theo từng ngân hàng, casa cố định như mô hình), chạy tới 2026Q3 (t = 15, 11 quý so sánh). "
              "LDR thực (trễ 1 quý) và ON thực là biến ngoại sinh. Chi phí vốn `c = r^D_term(1−casa)+0.15`; lãi suất cho vay theo PT1 hiện hành `r^L_t = r^L_{t-1} + λ(c_{t-1} + 4.55 − r^L_{t-1})` "
              "với λ = GĐ7 biến thể (c) hoặc 0.48 (YAML); trọng số = dư nợ thực. Hàng đầu là chuỗi thực. Thang đo: lãi suất cho vay %/năm; RMSE trên 11 quý t = 5..15; "
              "chỉ số chữ V tính trên t ≥ 4. Hàng \"huy động thực\" dùng lãi suất huy động thực trong PT1, tức giới hạn trên của những gì chi phí vốn giải thích được. "
              "`RMSE_khu_muc` = độ lệch chuẩn của sai số (RMSE sau khi bỏ sai số trung bình) để so hình dạng chuỗi tách khỏi chênh lệch mức. "
              "Cột `deposit_rate_total_basis` trong simulation_paths_stage7b.csv dùng casa cố định ở quý T0 như mô hình nên không so trực tiếp với chuỗi huy động thực.\n")
    md.append(md_table(simsum, list(simsum.columns)))
    if margin is not None:
        md.append("\n### Biên thực r^L − c_{t-1} theo quý (gia quyền theo dư nợ) so với 4.55 giả định\n")
        md.append(md_table(margin, list(margin.columns), 3))
    md.append(INTERPRETATION)
    md.append("\nFile: estimates_stage7b.csv, absorption_stage7b.csv, bootstrap_stage7b.csv, simulation_paths_stage7b.csv, simulation_summary_stage7b.csv.\n")
    (outdir / "estimates_stage7b.md").write_text("\n".join(md), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outdir", default=str(OUTDIR))
    args = ap.parse_args()
    df, on = prepare()
    yv = yaml7b()
    est = estimate_all_7b(df, yv)
    absr = absorption_7b(df)
    kbest, kr2 = best_lag(df)
    boot = bootstrap_phi(df, kbest)
    # λ của Giai đoạn 7, biến thể (c), mẫu N = 112, c = deposit_rate_pct + 0.15
    lam_rows, _ = run_variant("PT1", sample(df, 2), "main", "c", np.nan, "N112", yaml_values())
    lam = [r["coef"] for r in lam_rows if r["parameter"] == "lambda"][0]
    sim, simsum, _ = run_simulation(df, on, lam)
    write_outputs(est, absr, boot, sim, simsum, kbest, kr2, args.outdir, margin_path(df), drift_table(df, yv))
    print(f"Đã ghi kết quả vào {args.outdir}; k tốt nhất = {kbest}; λ GĐ7(c) = {lam:.4f}")


if __name__ == "__main__":
    main()
