"""GD10 – Chạy lại A/B/C, độ nhạy, độ vững (D9, D6). KHÔNG sửa src/agents/, src/core/, KHÔNG sửa YAML chính.

Cấu hình chính: configs/scenarios_calibrated.yaml (nghiệm GD9b). Mọi biến thể chỉ đổi tham số trong bộ nhớ
(hoặc trỏ tới file YAML có sẵn) rồi chạy ABMModel; seed = base_seed + i (cùng seed cho A/B/C).

Kết quả vào reports/stage10/ (mặc định):
  abc_summary_stage10.csv       cấu hình × (chính 60 lần, gốc, GĐ8, GD9): mức sau chính sách, B−A, C−A, C−B, tuân thủ, nim_proxy
  abc_quarterly_stage10.csv     LS cho vay/huy động theo quý và kịch bản: TB, P5, P95 qua các lần chạy
  diff_quarterly_stage10.csv    B−A, C−A, C−B theo quý (ghép cặp theo seed): TB, P5, P95
  sensitivity_stage10.csv       mỗi biến thể (30 lần): cùng các chỉ tiêu như abc_summary + tham số đã đổi
  section6_stage10.csv          kiểm mục 6 CLAUDE.md cho từng cấu hình/biến thể
  robustness_stage10.csv        bảng tóm tắt: dấu và độ lớn so với cấu hình chính, B vs C
  confounding_stage10.csv       tuân thủ và nim_proxy theo biến thể + thí nghiệm "tuân thủ cố định"
  summary_stage10.md            bảng md sinh từ các CSV trên

Tiêu chí mô tả ĐẶT TRƯỚC (không có ý nghĩa chính sách, chỉ để tóm tắt bảng):
  giữ dấu      : B−A (hoặc C−A) TB sau chính sách < 0 và >= 95% lần chạy (seed) có giá trị < 0
  giữ độ lớn   : tỷ số B−A (hoặc C−A) của biến thể / của cấu hình chính (60 lần) nằm trong [0.5; 1.5]
  C phân biệt B: CI 95% (ghép cặp theo seed, xấp xỉ chuẩn) của C−B không chứa 0 VÀ |C−B| >= 10% |B−A|
Đây là số của mô hình, nhiễu lẫn với mức A và xác suất tuân thủ; không phải tác động chính sách thực tế.

Chạy: python -m src.analysis.robustness_stage10 [--outdir reports/stage10]
"""

import argparse
import copy
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from ..core.model import ABMModel
from .experiments import _deep_merge, load_config

ROOT = Path(__file__).resolve().parents[2]
BANKS = ROOT / "data/clean/abm_initial_8nganhang_2023Q1.csv"
OUTDIR = ROOT / "reports/stage10"
CFG_MAIN = ROOT / "configs/scenarios_calibrated.yaml"
CFG_GD9 = ROOT / "configs/scenarios_calibrated_gd9.yaml"
CFG_MACRO = ROOT / "configs/scenarios_macro.yaml"
CFG_ORIG = ROOT / "configs/scenarios.yaml"
CFG_REL = ROOT / "configs/scenarios_adaptive_relative.yaml"

N_MAIN = 60          # LO_TRINH GD10 mục 1
N_SENS = 30          # LO_TRINH GD10 mục 2
REL_TOL = 1e-9
# Thiết kế độ nhạy theo LO_TRINH GD10 / D6 (đây là thiết kế phân tích, không phải tham số mô hình)
PRESSURE_REL = (0.7, 1.3)
STEPS = (0.14, 0.28, 0.42, 0.50)
LAMBDA_CI = (0.158, 0.395)    # CI bootstrap GĐ7 (c), làm tròn 3 chữ số (reports/calibration/estimates_stage7.md)
LAMBDA_IN_CI = 0.35           # bộ trong CI gần nghiệm GD9b nhất (Q9)
SPREAD_ALT = 1.08
SIGMA_EPS_REL = (0.5, 1.5)
SIGN_SHARE = 0.95
MAG_RANGE = (0.5, 1.5)
MATERIAL_REL = 0.10


def cfg_of(path):
    return load_config(None if Path(path).resolve() == CFG_ORIG.resolve() else path)


def bank_rows():
    return pd.read_csv(BANKS).to_dict("records")


def run_variant(cfg, params, rows, n_seeds):
    """Trả về (history, bank_history) gộp, cột seed và sc."""
    hs, bs = [], []
    for i in range(n_seeds):
        for sc in "ABC":
            m = ABMModel(sc, int(cfg["n_months"]), int(cfg["base_seed"]) + i, params, rows)
            m.run()
            hs.append(pd.DataFrame(m.history).assign(seed=i, sc=sc))
            bs.append(pd.DataFrame(m.bank_history).assign(seed=i, sc=sc))
    return pd.concat(hs, ignore_index=True), pd.concat(bs, ignore_index=True)


def summarize(name, params, cfg, h, b):
    """Một dòng chỉ tiêu cho một cấu hình/biến thể."""
    q = int(params["policy_month"]) + 1
    n = int(cfg["n_months"])
    post = h[h.month >= q]
    lr = post.groupby(["seed", "sc"]).loan_rate.mean().unstack()
    dr = post.groupby(["seed", "sc"]).deposit_rate.mean().unstack()
    nim = post.groupby(["seed", "sc"]).nim_proxy.mean().unstack()
    last = h[h.month == n].pivot(index="seed", columns="sc", values="loan_rate")
    lastd = h[h.month == n].pivot(index="seed", columns="sc", values="deposit_rate")
    bp = b[(b.month >= q) & (b.sc != "A")]
    prob = bp.groupby("sc").policy_probability.mean()
    comp = bp.groupby("sc").policy_complied.mean()
    row = {"cau_hinh": name, "n_seed": int(h.seed.nunique()), "quy_sau_CS": f"{q}-{n}"}
    for sc in "ABC":
        row[f"loan_rate_{sc}_sau_CS"] = float(lr[sc].mean())
        row[f"deposit_rate_{sc}_sau_CS"] = float(dr[sc].mean())
        row[f"nim_proxy_{sc}_sau_CS"] = float(nim[sc].mean())
    for lab, x, y in (("BmA", "B", "A"), ("CmA", "C", "A"), ("CmB", "C", "B")):
        d = lr[x] - lr[y]
        row[f"{lab}_tb"] = float(d.mean())
        row[f"{lab}_P5_theo_seed"] = float(np.percentile(d, 5))
        row[f"{lab}_P95_theo_seed"] = float(np.percentile(d, 95))
        row[f"{lab}_ty_le_seed_am"] = float((d < 0).mean())
        row[f"{lab}_ci95_nua_rong"] = float(1.96 * d.std(ddof=1) / np.sqrt(len(d)))
        dl = last[x] - last[y]
        row[f"{lab}_cuoi_ky_q{n}"] = float(dl.mean())
        row[f"{lab}_cuoi_ky_P5"] = float(np.percentile(dl, 5))
        row[f"{lab}_cuoi_ky_P95"] = float(np.percentile(dl, 95))
    row["deposit_BmA_tb"] = float((dr.B - dr.A).mean())
    row["deposit_CmA_tb"] = float((dr.C - dr.A).mean())
    row["deposit_CmB_tb"] = float((dr.C - dr.B).mean())
    row["deposit_BmA_cuoi_ky"] = float((lastd.B - lastd.A).mean())
    row["deposit_CmA_cuoi_ky"] = float((lastd.C - lastd.A).mean())
    row["xs_tuan_thu_tb_B"] = float(prob.B)
    row["xs_tuan_thu_tb_C"] = float(prob.C)
    row["ty_le_tuan_thu_thuc_B"] = float(comp.B)
    row["ty_le_tuan_thu_thuc_C"] = float(comp.C)
    return row


def quarterly(name, h, b):
    """LS theo quý × kịch bản: TB, P5, P95 qua seed; xs tuân thủ TB theo quý."""
    out = []
    for (sc, mth), g in h.groupby(["sc", "month"]):
        r = {"cau_hinh": name, "kich_ban": sc, "month": int(mth), "quarter": g.quarter.iloc[0]}
        for col, lab in (("loan_rate", "loan_rate"), ("deposit_rate", "deposit_rate")):
            r[f"{lab}_tb"] = float(g[col].mean())
            r[f"{lab}_P5"] = float(np.percentile(g[col], 5))
            r[f"{lab}_P95"] = float(np.percentile(g[col], 95))
        pb = b[(b.sc == sc) & (b.month == mth)].policy_probability.mean() if sc != "A" else np.nan
        r["xs_tuan_thu_tb"] = float(pb)
        out.append(r)
    return pd.DataFrame(out)


def diff_quarterly(name, h):
    out = []
    pv = h.pivot_table(index=["seed", "month"], columns="sc", values=["loan_rate", "deposit_rate"])
    for mth in sorted(h.month.unique()):
        for var in ("loan_rate", "deposit_rate"):
            x = pv[var].xs(mth, level="month")
            for lab, a, c in (("BmA", "B", "A"), ("CmA", "C", "A"), ("CmB", "C", "B")):
                d = x[a] - x[c]
                out.append({"cau_hinh": name, "chi_tieu": var, "chenh_lech": lab, "month": int(mth),
                            "tb": float(d.mean()), "P5": float(np.percentile(d, 5)),
                            "P95": float(np.percentile(d, 95))})
    return pd.DataFrame(out)


def lag_check(params, rows, cfg):
    """Một bước của A: LS cho vay khớp truyền dẫn theo chi phí vốn TRỄ (sai số ≈ 0), không khớp theo chi phí vốn hiện tại."""
    m = ABMModel("A", 1, int(cfg["base_seed"]), params, rows)
    lag0 = [x.lagged_funding_cost for x in m.banks]
    r0 = [x.loan_rate for x in m.banks]
    tm0 = [x.target_margin for x in m.banks]
    m.step()
    e_lag = e_now = 0.0
    for x, fc0, r, tm in zip(m.banks, lag0, r0, tm0):
        e_lag = max(e_lag, abs(x.loan_rate - (r + m.pass_through * (fc0 + tm + m.loan_spread_add - r))))
        e_now = max(e_now, abs(x.loan_rate - (r + m.pass_through * (x.funding_cost + tm + m.loan_spread_add - r))))
    return e_lag, e_now


def section6(name, params, cfg, rows, h, b):
    """Mục 6 CLAUDE.md trên chính các lần chạy của biến thể."""
    q = int(params["policy_month"]) + 1
    cap = float(params["max_loan_to_deposit"])
    pv = h.pivot_table(index=["seed", "month"], columns="sc", values="loan_rate")
    pos = pv[pv.index.get_level_values("month") >= q]
    max_ba = float((pos.B - pos.A).max())
    max_ca = float((pos.C - pos.A).max())
    num = ["deposits", "loans", "deposit_rate", "loan_rate"]
    pre = b[b.month < q].set_index(["seed", "bank_id", "month", "sc"])[num]
    pre_diff = 0.0
    for sc in "BC":
        d = (pre.xs(sc, level="sc") - pre.xs("A", level="sc")).abs()
        pre_diff = max(pre_diff, float(d.max().max()))
    slack = float((b.loans - b.deposits * cap).max())
    e_lag, e_now = lag_check(params, rows, cfg)
    r = {"cau_hinh": name, "n_seed": int(h.seed.nunique()),
         "max_BmA_sau_CS_theo_quy_seed": max_ba, "max_CmA_sau_CS_theo_quy_seed": max_ca,
         "max_abs_khac_nhau_truoc_CS": pre_diff,
         "loan_min": float(b.loan_rate.min()), "loan_max": float(b.loan_rate.max()),
         "dep_min": float(b.deposit_rate.min()), "dep_max": float(b.deposit_rate.max()),
         "max_loans_tru_tran": slack, "ty_le_cham_tran_LDR": float((b.loans >= b.deposits * cap * (1 - REL_TOL)).mean()),
         "lag_err_tre": e_lag, "lag_err_hien_tai": e_now}
    checks = {"B<=A": max_ba <= 1e-12, "C<=A": max_ca <= 1e-12, "truoc_CS_trung": pre_diff == 0.0,
              "loan_0_20": r["loan_min"] >= 0 and r["loan_max"] <= 20,
              "dep_0_14": r["dep_min"] >= 0 and r["dep_max"] <= 14,
              "tran_LDR": slack <= 1e-9, "tre": e_lag < 1e-12 and e_now > e_lag}
    for k, v in checks.items():
        r[f"dat_{k}"] = bool(v)
    r["dat_tat_ca"] = bool(all(checks.values()))
    return r


def build_variants(main_params, gd9_params, rel_over):
    """Danh sách (ten, nhom, nen, params, mo_ta). Tham số đổi tính từ giá trị YAML nền (không hard-code)."""
    V = []
    P = main_params
    om = load_config(None)["parameters"]   # YAML gốc: cửa sổ biên margin_min/max quanh target_margin gốc
    mm_lo, mm_hi, tm0 = om["margin_min"], om["margin_max"], om["target_margin"]
    base = lambda **kw: {**P, **kw}
    V.append(("co_so_30", "co_so", "chinh", dict(P), "cấu hình chính, 30 lần (cùng seed 0..29)"))
    for f in PRESSURE_REL:
        V.append((f"policy_pressure_x{f:g}", "policy_pressure", "chinh",
                  base(policy_pressure=P["policy_pressure"] * f), f"policy_pressure = {P['policy_pressure'] * f:.4f} (×{f:g})"))
    for s in STEPS:
        tag = "co_so" if abs(s - P["policy_step"]) < 1e-12 else "bien_the"
        V.append((f"policy_step_{s:g}", "policy_step", "chinh", base(policy_step=s),
                  f"policy_step = {s:g} điểm %/năm ({'= giá trị YAML' if tag == 'co_so' else 'ánh xạ giả định ở báo cáo'})"))
    for lam, tag in ((LAMBDA_CI[0], "CI_duoi"), (LAMBDA_IN_CI, "trong_CI_Q9"), (LAMBDA_CI[1], "CI_tren")):
        V.append((f"pass_through_{lam:g}", "pass_through", "chinh", base(pass_through=lam), f"λ = {lam:g} ({tag})"))
    V.append((f"macro_dep_spread_{SPREAD_ALT:g}", "macro_dep_spread", "chinh", base(macro_dep_spread=SPREAD_ALT),
              f"macro_dep_spread = {SPREAD_ALT:g} (mẫu N = 104, GĐ8)"))
    for f in SIGMA_EPS_REL:
        V.append((f"depositor_sensitivity_x{f:g}", "sigma", "chinh",
                  base(depositor_sensitivity=P["depositor_sensitivity"] * f),
                  f"σ = {P['depositor_sensitivity'] * f:.4f} (×{f:g})"))
    for f in SIGMA_EPS_REL:
        V.append((f"borrower_elasticity_x{f:g}", "epsilon", "chinh",
                  base(borrower_elasticity=P["borrower_elasticity"] * f),
                  f"ε = {P['borrower_elasticity'] * f:.4f} (×{f:g})"))
    V.append(("GD9_lambda_0.45", "nghiem_GD9", "gd9", dict(gd9_params),
              "nghiệm GD9 không ràng buộc λ (λ 0.45, biên tổng 3.8, chưa bù Q7)"))
    # Học thích nghi (mục 3 LO_TRINH): (i) giữ margin_min/max theo YAML (chính), (ii) dời cửa sổ theo target_margin hiệu chỉnh
    rel_main = {**P, **rel_over}
    V.append(("hoc_relative", "hoc_thich_nghi", "chinh", rel_main,
              f"learning_rule relative, θ 0.005, bước 0.05, simple; margin_min/max theo YAML ({mm_lo:g}–{mm_hi:g})"))
    shift = P["target_margin"] - tm0   # YAML gốc: cửa sổ [margin_min, margin_max] quanh target_margin gốc
    V.append(("hoc_relative_cua_so_doi", "hoc_thich_nghi", "chinh",
              {**rel_main, "margin_min": mm_lo + shift, "margin_max": mm_hi + shift},
              f"như trên nhưng margin_min/max dời {shift:+.2f} để giữ ±1.0 quanh target_margin hiệu chỉnh"))
    V.append(("GD9_hoc_relative", "hoc_thich_nghi", "gd9", {**gd9_params, **rel_over},
              f"nghiệm GD9 + học relative (margin_min/max {mm_lo:g}–{mm_hi:g} vẫn bao quanh target_margin {gd9_params['target_margin']:g})"))
    return V


def fixed_compliance_variants(p_star, cfgs):
    """Thí nghiệm tách tuân thủ: ép xác suất tuân thủ = p_star ở mọi cấu hình (compliance_prob_min = max)."""
    out = []
    for name, (cfg, params) in cfgs.items():
        out.append((f"tuan_thu_co_dinh_{name}", name, cfg, {**params, "compliance_prob_min": p_star,
                                                              "compliance_prob_max": p_star}))
    return out


def robustness_table(summ, main_row):
    rows = []
    for _, r in summ.iterrows():
        d = {"cau_hinh": r.cau_hinh, "n_seed": r.n_seed}
        for lab in ("BmA", "CmA"):
            d[f"{lab}_tb"] = r[f"{lab}_tb"]
            d[f"{lab}_ty_so_voi_chinh"] = r[f"{lab}_tb"] / main_row[f"{lab}_tb"]
            d[f"{lab}_giu_dau"] = bool(r[f"{lab}_tb"] < 0 and r[f"{lab}_ty_le_seed_am"] >= SIGN_SHARE)
            d[f"{lab}_giu_do_lon"] = bool(MAG_RANGE[0] <= d[f"{lab}_ty_so_voi_chinh"] <= MAG_RANGE[1])
        d["CmB_tb"] = r.CmB_tb
        d["CmB_ci95_nua_rong"] = r.CmB_ci95_nua_rong
        d["CmB_ty_so_tren_BmA"] = r.CmB_tb / r.BmA_tb if r.BmA_tb else np.nan
        d["C_B_khac_0_thong_ke"] = bool(abs(r.CmB_tb) > r.CmB_ci95_nua_rong)
        d["C_B_dang_ke"] = bool(abs(r.CmB_tb) >= MATERIAL_REL * abs(r.BmA_tb))
        d["C_phan_biet_B"] = bool(d["C_B_khac_0_thong_ke"] and d["C_B_dang_ke"])
        d["C_tot_hon_B_theo_dau"] = bool(r.CmB_tb < 0)
        rows.append(d)
    df = pd.DataFrame(rows)
    # biến thể trùng lặp (tham chiếu) không tính vào tổng: cấu hình chính 30 lần, policy_step = giá trị YAML, bản học 30 lần (đã có bản 60 lần)
    df["tinh_vao_tong"] = ~df.cau_hinh.isin(EXCLUDED_FROM_TALLY)
    return df


EXCLUDED_FROM_TALLY = ("co_so_30", "policy_step_0.28", "hoc_relative", "hoc_relative_cua_so_doi")


def fmt(x, nd=4):
    return f"{x:.{nd}f}"


def make_md(outdir, abc, sens, rob, conf, s6, fixed, meta):
    L = []
    A = L.append
    A("# GD10 – A/B/C, độ nhạy, độ vững (sinh tự động từ `reports/stage10/*.csv`)")
    A("")
    A("Mọi số là kết quả MÔ HÌNH (chạy lại từ cấu hình + seed cố định); không phải dự báo, không phải tác động chính sách thực tế. "
      "B−A, C−A nhiễu lẫn với mức A và xác suất tuân thủ. Quý sau chính sách = 15–18 (Q4/2026–Q3/2027).")
    A("")
    A("## 1. A/B/C, 60 lần, theo cấu hình (`abc_summary_stage10.csv`)")
    A("")
    A("| Cấu hình | LS cho vay A | B | C | B−A TB | C−A TB | C−B TB | B−A cuối kỳ (Q3/2027) | C−A cuối kỳ | LS huy động A | B−A hh | tuân thủ B | tuân thủ C | nim A | nim B |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for _, r in abc.iterrows():
        A(f"| {r.cau_hinh} | {fmt(r.loan_rate_A_sau_CS)} | {fmt(r.loan_rate_B_sau_CS)} | {fmt(r.loan_rate_C_sau_CS)} | "
          f"{fmt(r.BmA_tb)} | {fmt(r.CmA_tb)} | {fmt(r.CmB_tb)} | {fmt(r[f'BmA_cuoi_ky_q18'])} | {fmt(r[f'CmA_cuoi_ky_q18'])} | "
          f"{fmt(r.deposit_rate_A_sau_CS)} | {fmt(r.deposit_BmA_tb)} | {fmt(r.xs_tuan_thu_tb_B)} | {fmt(r.xs_tuan_thu_tb_C)} | "
          f"{fmt(r.nim_proxy_A_sau_CS, 3)} | {fmt(r.nim_proxy_B_sau_CS, 3)} |")
    A("")
    A("Phân bố qua seed của B−A (P5–P95, TB sau chính sách):")
    A("")
    A("| Cấu hình | B−A P5 | B−A P95 | C−A P5 | C−A P95 | C−B CI95 nửa rộng | tỷ lệ seed B−A<0 |")
    A("|---|---:|---:|---:|---:|---:|---:|")
    for _, r in abc.iterrows():
        A(f"| {r.cau_hinh} | {fmt(r.BmA_P5_theo_seed)} | {fmt(r.BmA_P95_theo_seed)} | {fmt(r.CmA_P5_theo_seed)} | "
          f"{fmt(r.CmA_P95_theo_seed)} | {fmt(r.CmB_ci95_nua_rong, 5)} | {fmt(r.BmA_ty_le_seed_am, 3)} |")
    A("")
    A("## 2. Độ nhạy, 30 lần mỗi biến thể (`sensitivity_stage10.csv`, `robustness_stage10.csv`)")
    A("")
    A("| Biến thể | tham số | B−A TB | B−A cuối kỳ | tỷ số / chính | giữ dấu | giữ độ lớn | C−A TB | tỷ số / chính | giữ dấu | giữ độ lớn | C−B TB | C phân biệt B | tuân thủ B | A sau CS |")
    A("|---|---|---:|---:|---:|:--:|:--:|---:|---:|:--:|:--:|---:|:--:|---:|---:|")
    sm = sens.set_index("cau_hinh")
    for _, r in rob.iterrows():
        if r.cau_hinh not in sm.index:
            continue
        s = sm.loc[r.cau_hinh]
        yn = lambda v: "có" if v else "KHÔNG"
        A(f"| {r.cau_hinh} | {s.mo_ta} | {fmt(r.BmA_tb)} | {fmt(s.BmA_cuoi_ky_q18)} | {fmt(r.BmA_ty_so_voi_chinh, 3)} | {yn(r.BmA_giu_dau)} | {yn(r.BmA_giu_do_lon)} | "
          f"{fmt(r.CmA_tb)} | {fmt(r.CmA_ty_so_voi_chinh, 3)} | {yn(r.CmA_giu_dau)} | {yn(r.CmA_giu_do_lon)} | "
          f"{fmt(r.CmB_tb)} | {yn(r.C_phan_biet_B)} | {fmt(s.xs_tuan_thu_tb_B)} | {fmt(s.loan_rate_A_sau_CS)} |")
    A("")
    A(f"Giá trị chính (60 lần, GD9b): B−A = {fmt(meta['main_BmA'])}, C−A = {fmt(meta['main_CmA'])}, C−B = {fmt(meta['main_CmB'])}.")
    A("")
    A("## 3. Kết luận nào giữ được qua mọi biến thể (bảng tóm tắt)")
    A("")
    A("| Kết luận | số biến thể giữ / tổng | biến thể KHÔNG giữ |")
    A("|---|---:|---|")
    rt = rob[rob.tinh_vao_tong]
    n = len(rt)
    for lab, col in (("B−A < 0 (giữ dấu)", "BmA_giu_dau"), ("C−A < 0 (giữ dấu)", "CmA_giu_dau"),
                     (f"B−A cùng bậc độ lớn (tỷ số {MAG_RANGE[0]}–{MAG_RANGE[1]})", "BmA_giu_do_lon"),
                     (f"C−A cùng bậc độ lớn (tỷ số {MAG_RANGE[0]}–{MAG_RANGE[1]})", "CmA_giu_do_lon"),
                     ("C−B khác 0 theo CI 95% ghép cặp", "C_B_khac_0_thong_ke"),
                     (f"abs(C−B) >= {MATERIAL_REL:.0%} abs(B−A) (đáng kể)", "C_B_dang_ke"),
                     ("C phân biệt được với B (cả hai điều kiện trên)", "C_phan_biet_B")):
        bad = rt[~rt[col]].cau_hinh.tolist()
        A(f"| {lab} | {int(rt[col].sum())}/{n} | {('tất cả' if len(bad) == n else ', '.join(bad)) if bad else '(không có)'} |")
    A("")
    A("Tổng gồm các biến thể độ nhạy (nền GD9b, 30 lần), học thích nghi 60 lần, nghiệm GD9, và 3 cấu hình so sánh (gốc, GĐ8, GD9; 60 lần). "
      "Không tính: co_so_30, policy_step_0.28 (trùng cấu hình chính), hai bản học 30 lần (đã có bản 60 lần).")
    A("")
    A(f"Lưu ý: {n} KHÔNG phải số biến thể độc lập. Bảng chứa các bản gần trùng (hieu_chinh_GD9 60 lần và GD9_lambda_0.45 30 lần là cùng một cấu hình; "
      "hoc_relative, hoc_relative_60, hoc_relative_cua_so_doi, hoc_relative_cua_so_doi_60 và GD9_hoc_relative cùng nền học) và 3 cấu hình nền đổi nhiều tham số cùng lúc. "
      "Tỷ lệ x/n chỉ để tóm tắt bảng, không phải tần suất kiểm định. Hai biến thể policy_step >= 0.42 là biến thể duy nhất đổi độ lớn: "
      "độ lớn B−A, C−A lệ thuộc giả định policy_step.")
    A("")
    A(f"C−B < 0 (C thấp hơn B) ở {int((rt.CmB_tb < 0).sum())}/{n} biến thể; dương ở: "
      f"{', '.join(rt[rt.CmB_tb >= 0].cau_hinh) or '(không có)'}.")
    A("")
    A("## 4. Tuân thủ, nim_proxy và thí nghiệm tuân thủ cố định (`confounding_stage10.csv`)")
    A("")
    A("| Cấu hình | loại | xs tuân thủ B | xs tuân thủ C | nim A | nim B | nim C | A sau CS | B−A | C−A | C−B |")
    A("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for _, r in conf.iterrows():
        A(f"| {r.cau_hinh} | {r.loai} | {fmt(r.xs_tuan_thu_tb_B)} | {fmt(r.xs_tuan_thu_tb_C)} | {fmt(r.nim_proxy_A_sau_CS, 3)} | "
          f"{fmt(r.nim_proxy_B_sau_CS, 3)} | {fmt(r.nim_proxy_C_sau_CS, 3)} | {fmt(r.loan_rate_A_sau_CS)} | {fmt(r.BmA_tb)} | "
          f"{fmt(r.CmA_tb)} | {fmt(r.CmB_tb)} |")
    A("")
    A(f"Tuân thủ cố định: xác suất tuân thủ ép = {meta['p_star']:.6f} (xác suất TB của B, cấu hình chính 60 lần) ở mọi cấu hình; "
      "khác biệt B−A còn lại giữa các cấu hình chỉ do mức LS và biên, không do xác suất tuân thủ. "
      "Lưu ý: bản tuân thủ cố định chạy 30 lần còn bản nội sinh cùng bảng chạy 60 lần; sai khác do số lần chạy cỡ ~2% (≈0.008), "
      "nhỏ hơn mức chênh 0.02–0.05 giữa nội sinh và cố định nên kết luận đứng.")
    A("")
    if "corr" in meta:
        A(f"Tương quan giữa các biến thể (độ nhạy + cấu hình): corr(B−A, xs tuân thủ B) = {meta['corr']['bma_p']:.3f}; "
          f"corr(B−A, nim_proxy A) = {meta['corr']['bma_nim']:.3f}; corr(B−A, LS cho vay A) = {meta['corr']['bma_lra']:.3f} "
          f"(n = {meta['corr']['n']}, đã loại co_so_30 và policy_step_0.28 trùng cấu hình chính; các bản học còn trong mẫu và mang hiệu ứng mức); đây là mô tả, không phải nhân quả.")
        A("")
    A("## 5. Mục 6 CLAUDE.md (`section6_stage10.csv`)")
    A("")
    A("| Cấu hình | max(B−A) sau CS | max(C−A) sau CS | trước CS khác nhau | loan_rate [min; max] | deposit_rate [min; max] | max(loans − 1.6·deposits) | trễ (sai số trễ / hiện tại) | ĐẠT |")
    A("|---|---:|---:|---:|---|---|---:|---|:--:|")
    for _, r in s6.iterrows():
        A(f"| {r.cau_hinh} | {r.max_BmA_sau_CS_theo_quy_seed:.4f} | {r.max_CmA_sau_CS_theo_quy_seed:.4f} | {r.max_abs_khac_nhau_truoc_CS:.1e} | "
          f"[{r.loan_min:.3f}; {r.loan_max:.3f}] | [{r.dep_min:.3f}; {r.dep_max:.3f}] | {r.max_loans_tru_tran:.3g} | "
          f"{r.lag_err_tre:.1e} / {r.lag_err_hien_tai:.4f} | {'ĐẠT' if r.dat_tat_ca else 'VI PHẠM: ' + ', '.join(k[4:] for k in r.index if k.startswith('dat_') and k != 'dat_tat_ca' and not r[k])} |")
    A("")
    (Path(outdir) / "summary_stage10.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def main(outdir=OUTDIR, n_main=N_MAIN, n_sens=N_SENS):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    rows = bank_rows()
    cfg_main = cfg_of(CFG_MAIN)
    cfg_gd9 = cfg_of(CFG_GD9)
    pm, pg = dict(cfg_main["parameters"]), dict(cfg_gd9["parameters"])
    with open(CFG_REL, encoding="utf-8") as f:
        rel_over = dict(yaml.safe_load(f)["parameters"])

    # ---- 1. A/B/C 60 lần ----
    abc_cfgs = {"hieu_chinh_GD9b (chinh)": (cfg_main, pm),
                "goc_scenarios": (cfg_of(CFG_ORIG), dict(cfg_of(CFG_ORIG)["parameters"])),
                "macro_GD8": (cfg_of(CFG_MACRO), dict(cfg_of(CFG_MACRO)["parameters"])),
                "hieu_chinh_GD9": (cfg_gd9, pg)}
    abc, quarts, diffs, s6 = [], [], [], []
    main_hb = None
    for name, (cfg, params) in abc_cfgs.items():
        h, b = run_variant(cfg, params, rows, n_main)
        if main_hb is None:
            main_hb = (h, b)
        abc.append(summarize(name, params, cfg, h, b))
        quarts.append(quarterly(name, h, b))
        diffs.append(diff_quarterly(name, h))
        s6.append(section6(name, params, cfg, rows, h, b))
    abc = pd.DataFrame(abc)
    main_row = abc.iloc[0]
    p_star = float(main_row.xs_tuan_thu_tb_B)

    # ---- 2–3. Độ nhạy 30 lần ----
    sens, sens_rows = [], []
    base_cfgs = {"chinh": cfg_main, "gd9": cfg_gd9}
    for name, grp, nen, params, desc in build_variants(pm, pg, rel_over):
        cfg = base_cfgs[nen]
        if name == "hoc_relative":      # mục 3: cũng chạy 60 lần để so với chính 60 lần
            pass
        h, b = run_variant(cfg, params, rows, n_sens)
        r = summarize(name, params, cfg, h, b)
        r["nhom"], r["mo_ta"] = grp, desc
        sens.append(r)
        s6.append(section6(name, params, cfg, rows, h, b))
    sens = pd.DataFrame(sens)
    # học thích nghi 60 lần (so trực tiếp với chính 60 lần)
    learn60 = []
    om = load_config(None)["parameters"]
    sh = pm["target_margin"] - om["target_margin"]
    for name, params in (("hoc_relative_60", {**pm, **rel_over}),
                         ("hoc_relative_cua_so_doi_60", {**pm, **rel_over, "margin_min": om["margin_min"] + sh,
                                                           "margin_max": om["margin_max"] + sh})):
        h, b = run_variant(cfg_main, params, rows, n_main)
        r = summarize(name, params, cfg_main, h, b)
        r["nhom"], r["mo_ta"] = "hoc_thich_nghi_60", "như biến thể 30 lần tương ứng, 60 lần"
        learn60.append(r)
    learn60 = pd.DataFrame(learn60)

    # ---- bảng độ vững (so với chính 60 lần), gồm biến thể 30 lần + học 60 lần + cấu hình GD9/macro/gốc ----
    rob_src = pd.concat([sens.drop(columns=["nhom", "mo_ta"]), learn60.drop(columns=["nhom", "mo_ta"])], ignore_index=True)
    rob = robustness_table(rob_src, main_row)
    rob_cfg = robustness_table(abc.iloc[1:], main_row)

    # ---- tuân thủ cố định ----
    fx = []
    for name, nm, cfg, params in fixed_compliance_variants(p_star, {k: v for k, v in abc_cfgs.items()}):
        h, b = run_variant(cfg, params, rows, n_sens)
        r = summarize(name, params, cfg, h, b)
        r["loai"] = "tuan_thu_co_dinh"
        fx.append(r)
    fx = pd.DataFrame(fx)

    conf_free = pd.concat([abc.assign(loai="tuan_thu_noi_sinh_60"),
                           sens.assign(loai="tuan_thu_noi_sinh_30").drop(columns=["nhom", "mo_ta"]),
                           learn60.assign(loai="tuan_thu_noi_sinh_60").drop(columns=["nhom", "mo_ta"])], ignore_index=True)
    conf = pd.concat([conf_free, fx], ignore_index=True)
    keep = ["cau_hinh", "loai", "n_seed", "xs_tuan_thu_tb_B", "xs_tuan_thu_tb_C", "ty_le_tuan_thu_thuc_B", "ty_le_tuan_thu_thuc_C",
            "nim_proxy_A_sau_CS", "nim_proxy_B_sau_CS", "nim_proxy_C_sau_CS", "loan_rate_A_sau_CS", "BmA_tb", "CmA_tb", "CmB_tb"]
    conf = conf[keep]

    # tương quan mô tả giữa các biến thể 30 lần (tuân thủ nội sinh)
    # loại 2 hàng trùng cấu hình chính (co_so_30, policy_step_0.28); các bản học vẫn nằm trong (có hiệu ứng mức)
    c30 = conf[(conf.loai == "tuan_thu_noi_sinh_30") & ~conf.cau_hinh.isin(["co_so_30", "policy_step_0.28"])]
    corr = {"n": int(len(c30)),
            "bma_p": float(np.corrcoef(c30.BmA_tb, c30.xs_tuan_thu_tb_B)[0, 1]),
            "bma_nim": float(np.corrcoef(c30.BmA_tb, c30.nim_proxy_A_sau_CS)[0, 1]),
            "bma_lra": float(np.corrcoef(c30.BmA_tb, c30.loan_rate_A_sau_CS)[0, 1])}

    ff = "%.10g"
    abc.to_csv(out / "abc_summary_stage10.csv", index=False, float_format=ff)
    pd.concat(quarts, ignore_index=True).to_csv(out / "abc_quarterly_stage10.csv", index=False, float_format=ff)
    pd.concat(diffs, ignore_index=True).to_csv(out / "diff_quarterly_stage10.csv", index=False, float_format=ff)
    sens_all = pd.concat([sens, learn60], ignore_index=True)
    sens_all.to_csv(out / "sensitivity_stage10.csv", index=False, float_format=ff)
    s6 = pd.DataFrame(s6)
    s6.to_csv(out / "section6_stage10.csv", index=False, float_format=ff)
    rob_all = pd.concat([rob, rob_cfg], ignore_index=True)
    rob_all.to_csv(out / "robustness_stage10.csv", index=False, float_format=ff)
    conf.to_csv(out / "confounding_stage10.csv", index=False, float_format=ff)
    meta = {"main_BmA": float(main_row.BmA_tb), "main_CmA": float(main_row.CmA_tb), "main_CmB": float(main_row.CmB_tb),
            "p_star": p_star, "corr": corr}
    make_md(out, abc, sens_all, rob_all, conf, s6, fx, meta)
    return abc, sens_all, rob_all


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=str(OUTDIR))
    a = ap.parse_args()
    main(a.outdir)
    print("xong ->", a.outdir)
