"""GD9b: hiệu chỉnh lại GD9 theo quyết định D9 (Q6 lưới ràng buộc, Q7 bù tăng trưởng, Q4b ngưỡng bất đối xứng).

Phương pháp chốt TRƯỚC khi chạy lưới: reports/calibration/stage9b/DANG_KY_TRUOC_GD9b.md (đã commit riêng).
Tái dùng nguyên hàm của calibrate_stage9 (không đổi phương pháp GD9, không đổi đầu ra stage9). Khác GD9:
  1. Q7: depositor_base_growth/borrower_base_growth += (tăng trưởng tổng dữ liệu − mô hình A) tính MỘT LẦN tại
     nghiệm GD9 (configs/scenarios_calibrated_gd9.yaml), rồi áp dụng nguyên cho mọi điểm lưới.
  2. Q6: λ ∈ {0.15..0.40}, biên tổng ∈ {3.4..4.8} (6 × 8 × 4 × 4 × 2 = 1536 bộ / biến thể).
Chỉ hiệu chỉnh tham số trong YAML; không chạm src/agents, src/core.

Đây là đối chiếu lịch sử; mô hình (và mốc ON) được cấp ON THỰC ngoài mẫu (lợi thế thông tin). Không phải dự báo,
A/B/C không phải tác động chính sách thực tế.

Chạy: python -m src.calibration.calibrate_stage9b [--outdir reports/calibration/stage9b] [--no-yaml]
Tất định (A không dùng số ngẫu nhiên; B/C dùng seed = base_seed + i); chạy lại cho file giống hệt.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..analysis.compare_deposit_basis import actual_series
from ..analysis.experiments import load_config
from ..core.model import ABMModel
from . import calibrate_stage9 as c9
from . import confounding_stage9 as cf9

ROOT = c9.ROOT
OUTDIR = ROOT / "reports/calibration/stage9b"
GD9_CFG = ROOT / "configs/scenarios_calibrated_gd9.yaml"      # bản GD9 giữ để đối chiếu (tham chiếu bù Q7)
NEW_CFG = ROOT / "configs/scenarios_calibrated.yaml"          # nghiệm GD9b (ghi đè)
CONFOUND_CONFIGS = {"macro_GD8": ROOT / "configs/scenarios_macro.yaml", "hieu_chinh_GD9": GD9_CFG,
                    "hieu_chinh_GD9b": NEW_CFG}
# Giá trị bù dự kiến trong DANG_KY_TRUOC_GD9b.md mục 2 (từ reports/calibration/stage9/diag_growth_stage9.csv)
EXPECTED_BU = {"depositor_base_growth": 0.0497668532, "borrower_base_growth": 0.02931768308}
EXPECTED_BU_TOL = 1e-9
GD9_BASE = {"depositor_base_growth": 0.03976093370475935, "borrower_base_growth": 0.044751104985969604}

GRID_B = {
    "pass_through": (0.15, 0.20, 0.25, 0.30, 0.35, 0.40),
    "total_margin": (3.4, 3.6, 3.8, 4.0, 4.2, 4.4, 4.6, 4.8),
    "base_deposit_rate_step": (0.0, 0.006, 0.012, 0.018),
    "deposit_competition": (0.07, 0.3, 0.7, 1.2),
    "ldr_choice": ("0.82", "ldr_mean"),
}
MAIN_VARIANT = c9.MAIN_VARIANT
VARIANTS_B = ("batdoixung_daydu", "doixung_daydu", "batdoixung_loaibatthuong")   # đăng ký mục 4
BOUNDS = {"pass_through": (0.15, 0.40), "total_margin": (3.4, 4.8), "base_deposit_rate_step": (0.0, 0.018),
          "deposit_competition": (0.07, 1.2)}


# ======================================================================
# Bù Q7 (một lần, tại nghiệm GD9)
# ======================================================================

def data_total_growth(panel):
    """Trung bình 9 quý (month 1–9) của sum_t/sum_{t−1} − 1 trên TỔNG tiền gửi/dư nợ 8 NH (thước đo dữ liệu)."""
    g = panel.groupby("per")[["deposits", "loans"]].sum().pct_change()
    per = pd.period_range(c9.WINDOW[0], c9.WINDOW[1], freq="Q")
    return float(g.loc[per, "deposits"].mean()), float(g.loc[per, "loans"].mean())


def model_total_growth(params, rows, cfg):
    """Trung bình month 1–9 của deposit_growth, credit_growth (history, kịch bản A)."""
    m = ABMModel("A", c9.N_SIM, int(cfg["base_seed"]), params, rows)
    m.run()
    h = pd.DataFrame(m.history)
    return float(h.deposit_growth.iloc[:9].mean()), float(h.credit_growth.iloc[:9].mean())


def growth_offset(panel, rows, cfg):
    """Δ_D, Δ_L tính tại nghiệm GD9 (cố định, không phụ thuộc J của GD9b)."""
    gd9 = load_config(GD9_CFG)
    p9 = dict(gd9["parameters"])
    dd_data, ll_data = data_total_growth(panel)
    dd_mod, ll_mod = model_total_growth(p9, rows, cfg)
    d_d, d_l = dd_data - dd_mod, ll_data - ll_mod
    out = {"g_D_du_lieu": dd_data, "g_L_du_lieu": ll_data, "g_D_mo_hinh_GD9": dd_mod, "g_L_mo_hinh_GD9": ll_mod,
           "delta_D": d_d, "delta_L": d_l,
           "depositor_base_growth_GD9": float(p9["depositor_base_growth"]),
           "borrower_base_growth_GD9": float(p9["borrower_base_growth"]),
           "depositor_base_growth_moi": float(p9["depositor_base_growth"]) + d_d,
           "borrower_base_growth_moi": float(p9["borrower_base_growth"]) + d_l}
    return out


def check_expected_bu(bu):
    """Đăng ký mục 2: nếu lệch giá trị dự kiến quá 1e-9 thì DỪNG (không tự đổi quy tắc)."""
    for k, exp in EXPECTED_BU.items():
        if abs(bu[k + "_moi"] - exp) > EXPECTED_BU_TOL:
            raise SystemExit(f"Giá trị bù {k} = {bu[k + '_moi']!r} lệch dự kiến {exp} quá {EXPECTED_BU_TOL}: DỪNG, báo điều phối viên")


def apply_offset(params, bu):
    """Cộng Δ vào base_growth của biến thể (bước Bước 1 của biến thể đó) – cùng Δ cho mọi biến thể."""
    q = dict(params)
    q["depositor_base_growth"] = q["depositor_base_growth"] + bu["delta_D"]
    q["borrower_base_growth"] = q["borrower_base_growth"] + bu["delta_L"]
    return q


# ======================================================================
# Ghi YAML
# ======================================================================

def write_calibrated_yaml(path, params, best, stats, ldr_value, lam_in_ci, bu):
    lam_note = f"GD9b lưới Q6 (argmin J, cửa sổ 2023Q2-2025Q2); CI GĐ7 (c) [0.158; 0.395]: {'trong' if lam_in_ci else 'NGOÀI'} CI"
    if best["pass_through"] in BOUNDS["pass_through"]:
        lam_note += f"; CHẠM BIÊN lưới ràng buộc {best['pass_through']} (giữ, D9)"
    src = {
        "pass_through": lam_note,
        "target_margin": f"GD9b lưới Q6: biên tổng {best['total_margin']} − loan_spread_add 1.35"
                         + ("; CHẠM cận dưới biên tổng 3.4 (giữ, D9)" if best["total_margin"] == 3.4 else ""),
        "base_deposit_rate_step": "GD9b lưới (argmin J)",
        "deposit_competition": "GD9b lưới (argmin J)",
        "deposit_ldr_target": ("GD9b lưới: LDR bình quân ngân hàng-quý 2023Q2-2025Q2 = " + f"{ldr_value:.6f}"
                               if best["ldr_choice"] == "ldr_mean" else "GD9b lưới: giữ 0.82"),
        "depositor_base_growth": (f"GD9b Q7: {bu['depositor_base_growth_GD9']:.10f} (TB tăng trưởng quý tổng tiền gửi 8 NH 2023Q2-2025Q2, GD9) "
                                  f"+ bù Δ_D = {bu['delta_D']:+.10f} (dữ liệu {bu['g_D_du_lieu']:.10f} − mô hình A tại nghiệm GD9 "
                                  f"{bu['g_D_mo_hinh_GD9']:.10f}); bù MỘT lần, không tối ưu J"),
        "depositor_min_growth": f"GD9 Bước 1 (giữ): P2.5 tăng trưởng tiền gửi ngân hàng-quý (N = {stats['n_obs']}); sàn bất đối xứng Q4b",
        "depositor_max_growth": f"GD9 Bước 1 (giữ): P97.5 tăng trưởng tiền gửi ngân hàng-quý (N = {stats['n_obs']})",
        "borrower_base_growth": (f"GD9b Q7: {bu['borrower_base_growth_GD9']:.10f} (TB tăng trưởng quý tổng dư nợ 8 NH 2023Q2-2025Q2, GD9) "
                                 f"+ bù Δ_L = {bu['delta_L']:+.10f} (dữ liệu {bu['g_L_du_lieu']:.10f} − mô hình A tại nghiệm GD9 "
                                 f"{bu['g_L_mo_hinh_GD9']:.10f}); bù MỘT lần, không tối ưu J"),
        "borrower_growth_min": f"GD9 Bước 1 (giữ): P2.5 tăng trưởng dư nợ ngân hàng-quý (N = {stats['n_obs']})",
        "borrower_growth_max": f"GD9 Bước 1 (giữ): P97.5 tăng trưởng dư nợ ngân hàng-quý (N = {stats['n_obs']})",
    }
    kept = "giữ giá trị scenarios.yaml/scenarios_macro.yaml (KHÔNG hiệu chỉnh)"
    assumption = {
        "depositor_sensitivity": "GIẢ ĐỊNH, không nhận diện được (GĐ7), không hiệu chỉnh",
        "borrower_elasticity": "GIẢ ĐỊNH, không nhận diện được (GĐ7), không hiệu chỉnh",
        "policy_pressure": "giả định kịch bản (D6), không hiệu chỉnh",
        "policy_step": "giả định kịch bản (D6), không hiệu chỉnh",
        "loan_spread_add": "giữ 1.35 (D7/Q1); biên tổng hiệu chỉnh qua target_margin",
    }
    lines = [
        "# FILE GHI ĐÈ lên scenarios.yaml (sinh tự động bởi `python -m src.calibration.calibrate_stage9b`, KHÔNG sửa tay).",
        "# Bộ tham số hiệu chỉnh Giai đoạn 9b (D9: Q6 lưới ràng buộc λ, Q7 bù tăng trưởng, Q4b ngưỡng bất đối xứng). Nền: scenarios.yaml + scenarios_macro.yaml (D2).",
        "# Phương pháp: reports/calibration/stage9b/DANG_KY_TRUOC_GD9b.md; kết quả: reports/calibration/stage9b/summary_stage9b.md.",
        "# Bản GD9 cũ giữ ở configs/scenarios_calibrated_gd9.yaml (đối chiếu).",
        "# Hàm mục tiêu: J = 0.5*RMSE thô LS cho vay + 0.5*RMSE thô LS huy động (cơ sở dữ liệu), kịch bản A, 2023Q2-2025Q2.",
        "# Mọi khóa hành vi (gồm 13 khóa GD9a) ghi TƯỜNG MINH ở đây, không dựa vào mặc định trong code.",
        "# Đây là đối chiếu trong mẫu; không phải dự báo và không phải tác động chính sách thực tế.",
        "# Chạy: python main.py --config configs/scenarios_calibrated.yaml",
        "parameters:",
    ]
    for k in c9.EXPLICIT_KEYS:
        note = src.get(k) or assumption.get(k) or kept
        lines.append(f"  {k}: {c9._fmt(params[k])}    # {note}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ======================================================================
# Nhiễu lẫn tuân thủ (tổng quát hóa confounding_stage9: 3 cấu hình)
# ======================================================================

def confounding(out):
    rows = pd.read_csv(c9.BANKS).to_dict("records")
    res, caps, starts = [], [], []
    for name, path in CONFOUND_CONFIGS.items():
        cfg = load_config(path)
        r, c = cf9.summarize(name, cfg, rows)
        res.append(r)
        caps.append(c)
        starts.append(cf9.start_2026q3(name, cfg))
    df = pd.DataFrame(res)
    df.to_csv(out / "confounding_stage9b.csv", index=False, float_format="%.10g")
    cap = pd.concat(caps, ignore_index=True)
    cap.to_csv(out / "ldr_cap_stage9b.csv", index=False, float_format="%.10g")
    st = pd.concat(starts, ignore_index=True)
    st.to_csv(out / "ldr_cap_2026q3_stage9b.csv", index=False, float_format="%.10g")

    names = list(CONFOUND_CONFIGS)
    d = df.set_index("cau_hinh")
    items = [("B−A (TB)", "BmA_tb"), ("C−A (TB)", "CmA_tb"), ("C−B (TB)", "CmB_tb"),
             ("độ lệch chuẩn B−A theo seed", "BmA_sd_theo_seed"),
             ("max(B−A) theo quý và seed", "max_BmA_theo_quy_va_seed"),
             ("max(C−A) theo quý và seed", "max_CmA_theo_quy_va_seed"),
             ("LS cho vay A", "loan_rate_A_sau_CS"), ("LS cho vay B", "loan_rate_B_sau_CS"),
             ("LS cho vay C", "loan_rate_C_sau_CS"),
             ("nim_proxy A", "nim_A_sau_CS"), ("nim_proxy B", "nim_B_sau_CS"), ("nim_proxy C", "nim_C_sau_CS"),
             ("xác suất tuân thủ TB, B", "xs_tuan_thu_tb_B"), ("xác suất tuân thủ TB, C", "xs_tuan_thu_tb_C"),
             ("tỷ lệ ngân hàng-quý chạm trần LDR, A (quý 15–18)", "ty_le_tran_LDR_A_sau_CS"),
             ("tỷ lệ chạm trần LDR, B (quý 15–18)", "ty_le_tran_LDR_B_sau_CS"),
             ("tỷ lệ chạm trần LDR, C (quý 15–18)", "ty_le_tran_LDR_C_sau_CS"),
             ("tỷ lệ chạm trần LDR, A, month 1–10", "tran_LDR_A_month_1_10"),
             ("tỷ lệ chạm trần LDR, A, month 11–15", "tran_LDR_A_month_11_15"),
             ("tỷ lệ chạm trần LDR, A, month 16–18", "tran_LDR_A_month_16_18")]
    lines = ["### Nhiễu lẫn tuân thủ và độ tin cậy của B−A / C−A (`confounding_stage9b.csv`, `ldr_cap_stage9b.csv`, `ldr_cap_2026q3_stage9b.csv`)", "",
             f"{cf9.N_SEEDS} seed (base_seed + 0..{cf9.N_SEEDS - 1}), trung bình theo seed rồi theo quý {d.iloc[0].quy_sau_CS}; "
             "phương pháp giữ nguyên `confounding_stage9.py`. `max(B−A)` là max theo quý và seed, KHÔNG phải mức trung bình. "
             "Số của mô hình, không phải tác động chính sách thực tế.", "",
             "| Chỉ tiêu (sau CS) | " + " | ".join(names) + " |", "|---|" + "---:|" * len(names)]
    for lab, k in items:
        lines.append(f"| {lab} | " + " | ".join(f"{d.loc[n, k]:.4f}" for n in names) + " |")
    capA = cap[cap.kich_ban == "A"].pivot_table(index="month", columns="cau_hinh", values="ty_le_cham_tran")[names]
    lines += ["", "Tỷ lệ ngân hàng-quý chạm trần LDR 1.60, kịch bản A, theo month (trung bình 10 seed):", "",
              "| month | " + " | ".join(names) + " |", "|---|" + "---:|" * len(names)]
    for mth, r in capA.iterrows():
        lines.append(f"| {int(mth)} | " + " | ".join(f"{r[n]:.4f}" for n in names) + " |")
    last = st.groupby("cau_hinh").ty_le_cham_tran.last()
    lines += ["", "Khởi đầu từ `abm_initial_8nganhang_2026Q3.csv`, kịch bản A, 18 quý: tỷ lệ ngân hàng chạm trần LDR ở quý cuối = "
              + "; ".join(f"{last[n]:.3f} ({n})" for n in names) + "."]
    text = "\n".join(lines) + "\n"
    (out / "confounding_stage9b.md").write_text(text, encoding="utf-8")
    return df, text


# ======================================================================
# Chính
# ======================================================================

def boundary_table(best):
    rows = []
    for k, (lo, hi) in BOUNDS.items():
        v = float(best[k])
        rows.append({"tham_so": k, "gia_tri": v, "can_duoi_luoi": lo, "can_tren_luoi": hi,
                     "cham_can_duoi": bool(v == lo), "cham_can_tren": bool(v == hi)})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outdir", default=str(OUTDIR))
    ap.add_argument("--no-yaml", action="store_true", help="không ghi configs/scenarios_calibrated.yaml")
    args = ap.parse_args()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    c9.check_anomalies_listed()
    cfg, base = c9.base_params()
    rows = pd.read_csv(c9.BANKS).to_dict("records")
    panel = c9.load_panel()
    act = actual_series(out).sort_values("month").reset_index(drop=True)
    act = act[act.month <= c9.N_SIM]
    act_loan, act_dep = act.actual_loan_rate.to_numpy(), act.actual_deposit_rate.to_numpy()
    ldr_value = c9.ldr_mean(panel)
    on = c9.on_series()
    gd9_params = dict(load_config(GD9_CFG)["parameters"])

    # Q7: bù một lần tại nghiệm GD9
    bu = growth_offset(panel, rows, cfg)
    pd.DataFrame([bu]).to_csv(out / "bu_tang_truong_stage9b.csv", index=False, float_format="%.12g")
    check_expected_bu(bu)

    # Bước 1 (giữ GD9) + bù Q7
    growth_rows, variant_params = [], {}
    for key in VARIANTS_B:
        asym, excl = c9.VARIANTS[key]
        gp, st = c9.growth_rules(panel, asym, excl)
        step1 = {**base, **gp}
        variant_params[key] = apply_offset(step1, bu)
        growth_rows.append({"bien_the": key, "bat_doi_xung": asym, "loai_bat_thuong": excl,
                            **{k: variant_params[key][k] for k in c9.GROWTH_KEYS},
                            "depositor_base_growth_buoc1": gp["depositor_base_growth"],
                            "borrower_base_growth_buoc1": gp["borrower_base_growth"], **st})
    growth = pd.DataFrame(growth_rows)
    growth["ldr_binh_quan_cua_so"] = ldr_value
    growth.to_csv(out / "growth_rules_stage9b.csv", index=False)

    # Lưới
    grids = []
    for key in VARIANTS_B:
        g = c9.run_grid(variant_params[key], rows, act_loan, act_dep, ldr_value, cfg, GRID_B)
        g.insert(0, "bien_the", key)
        grids.append(g)
    grid = pd.concat(grids, ignore_index=True)
    grid.to_csv(out / "grid_stage9b.csv", index=False, float_format="%.10g")
    gm = grid[grid.bien_the == MAIN_VARIANT]
    top10 = gm.sort_values(["J", "grid_index"], kind="mergesort").head(10)
    top10.to_csv(out / "top10_stage9b.csv", index=False, float_format="%.10g")
    prof = c9.profiles(gm)
    prof.to_csv(out / "profile_stage9b.csv", index=False, float_format="%.10g")
    corr = c9.top_corr(gm)
    corr.to_csv(out / "corr_top50_stage9b.csv", index=False, float_format="%.6g")
    bests = {key: c9.best_row(grid[grid.bien_the == key]) for key in VARIANTS_B}
    best_cols = list(c9.GRID) + ["target_margin", "deposit_ldr_target", "J", "RMSE_L_cal", "RMSE_D_cal"]
    best_tbl = pd.DataFrame([{"bien_the": k, **{c: r[c] for c in best_cols}} for k, r in bests.items()])
    best_tbl.to_csv(out / "best_by_variant_stage9b.csv", index=False, float_format="%.10g")
    best = bests[MAIN_VARIANT]
    best_params = c9.params_of(variant_params[MAIN_VARIANT], best, ldr_value)
    lam = float(best["pass_through"])
    lam_in_ci = c9.LAMBDA_CI_STAGE7[0] <= lam <= c9.LAMBDA_CI_STAGE7[1]
    bnd = boundary_table(best)
    bnd.to_csv(out / "boundary_stage9b.csv", index=False, float_format="%.10g")

    # Chẩn đoán (chỉ báo cáo): λ trong CI GĐ7; nghiệm không bù
    in_ci = gm[(gm.pass_through >= c9.LAMBDA_CI_STAGE7[0]) & (gm.pass_through <= c9.LAMBDA_CI_STAGE7[1])]
    best_ci = c9.best_row(in_ci)
    diag = pd.DataFrame([{"chan_doan": name, **{c: r[c] for c in best_cols}}
                         for name, r in (("luoi_chinh_tot_nhat", best), ("lambda_trong_CI_GD7_tot_nhat", best_ci))])
    diag.to_csv(out / "diagnostics_stage9b.csv", index=False, float_format="%.10g")

    # A tất định
    l1, d1, _ = c9.simulate(best_params, rows, cfg=cfg)
    l2, d2, _ = c9.simulate(best_params, rows, seed=int(cfg["base_seed"]) + c9.SECOND_SEED_OFFSET, cfg=cfg)
    a_deterministic = bool(np.array_equal(l1, l2) and np.array_equal(d1, d2))

    # Ngoài mẫu và so GD9
    paths = {"hieu_chinh_GD9b_" + MAIN_VARIANT: (l1, d1)}
    for key in VARIANTS_B:
        if key != MAIN_VARIANT:
            ln, dp, _ = c9.simulate(c9.params_of(variant_params[key], bests[key], ldr_value), rows, cfg=cfg)
            paths["hieu_chinh_GD9b_" + key] = (ln, dp)
    ln, dp, _ = c9.simulate(c9.params_of(variant_params[MAIN_VARIANT], best_ci, ldr_value), rows, cfg=cfg)
    paths["chan_doan_GD9b_lambda_trong_CI"] = (ln, dp)
    no_bu = {**best_params, "depositor_base_growth": best_params["depositor_base_growth"] - bu["delta_D"],
             "borrower_base_growth": best_params["borrower_base_growth"] - bu["delta_L"]}
    ln, dp, _ = c9.simulate(no_bu, rows, cfg=cfg)
    paths["chan_doan_GD9b_nghiem_khong_bu"] = (ln, dp)
    ln, dp, _ = c9.simulate(gd9_params, rows, cfg=cfg)
    paths["GD9_nghiem"] = (ln, dp)
    ln, dp, _ = c9.simulate(base, rows, cfg=cfg)
    paths["GD8_chua_hieu_chinh"] = (ln, dp)
    naive = c9.naive_paths(act, on)
    oos = c9.oos_table(paths, naive, act)
    oos.to_csv(out / "oos_stage9b.csv", index=False, float_format="%.10g")
    path_rows = []
    for name, (ln, dp) in paths.items():
        for i in range(c9.N_SIM):
            path_rows.append({"cau_hinh": name, "month": i + 1, "quarter": act.quarter.iloc[i],
                              "loan_rate": ln[i], "deposit_rate_data_basis": dp[i]})
    for name, (ln, dp) in naive.items():
        for j, mth in enumerate(range(c9.OOS_MONTHS[0], c9.OOS_MONTHS[1] + 1)):
            path_rows.append({"cau_hinh": name, "month": mth, "quarter": act.quarter.iloc[mth - 1],
                              "loan_rate": ln[j], "deposit_rate_data_basis": dp[j]})
    for i in range(c9.N_SIM):
        path_rows.append({"cau_hinh": "thuc_te", "month": i + 1, "quarter": act.quarter.iloc[i],
                          "loan_rate": act_loan[i], "deposit_rate_data_basis": act_dep[i]})
    pd.DataFrame(path_rows).to_csv(out / "paths_stage9b.csv", index=False, float_format="%.10g")

    # Ngưỡng, tăng trưởng tổng và LDR
    named = {"hieu_chinh_GD9b": best_params, "hieu_chinh_GD9": gd9_params, "GD8_chua_hieu_chinh": base}
    thr = []
    for name, q in named.items():
        t = c9.threshold_table(q, rows, cfg)
        t.insert(0, "cau_hinh", name)
        thr.append(t)
    thr = pd.concat(thr, ignore_index=True)
    thr.to_csv(out / "thresholds_stage9b.csv", index=False, float_format="%.10g")
    gl = c9.growth_ldr_table(named, rows, panel, cfg)
    gl.to_csv(out / "growth_ldr_stage9b.csv", index=False, float_format="%.10g")

    # YAML
    if not args.no_yaml:
        write_calibrated_yaml(NEW_CFG, best_params, best, growth[growth.bien_the == MAIN_VARIANT].iloc[0].to_dict(),
                              ldr_value, lam_in_ci, bu)
    cal_cfg = load_config(NEW_CFG)
    yaml_matches = all(cal_cfg["parameters"][k] == best_params[k] or
                       (isinstance(best_params[k], float) and abs(cal_cfg["parameters"][k] - best_params[k]) < 1e-9)
                       for k in c9.EXPLICIT_KEYS)
    lf, df_, _ = c9.simulate(dict(cal_cfg["parameters"]), rows, cfg=cfg)
    yaml_path_diff = float(max(np.abs(lf - l1).max(), np.abs(df_ - d1).max()))

    # Mục 6
    s6_new = c9.section6(cal_cfg, rows)
    s6_gd9 = c9.section6(load_config(GD9_CFG), rows)
    s6_base = c9.section6(cfg, rows)
    s6 = pd.DataFrame([{"cau_hinh": "scenarios_calibrated.yaml (GD9b)", **s6_new},
                       {"cau_hinh": "scenarios_calibrated_gd9.yaml (GD9)", **s6_gd9},
                       {"cau_hinh": "scenarios_macro.yaml (GĐ8)", **s6_base}])
    s6.to_csv(out / "section6_stage9b.csv", index=False, float_format="%.10g")

    conf_df, conf_text = confounding(out)

    meta = {"lambda_best": lam, "lambda_ci_stage7": c9.LAMBDA_CI_STAGE7, "lambda_in_ci": lam_in_ci,
            "scenario_A_deterministic_two_seeds": a_deterministic, "ldr_mean_window": ldr_value,
            "n_grid_per_variant": len(c9.grid_points(GRID_B)), "yaml_matches_best": bool(yaml_matches),
            "yaml_path_max_abs_diff": yaml_path_diff, "section6_pass_calibrated": s6_new["pass"],
            "bu_q7": bu, "boundary": bnd.to_dict("records")}
    (out / "meta_stage9b.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    write_summary(out, bu, growth, best_tbl, top10, prof, corr, diag, bnd, oos, thr, gl, s6, meta, conf_text)
    print(json.dumps(meta, indent=2, ensure_ascii=False))
    if not s6_new["pass"]:
        raise SystemExit("Nghiệm GD9b VI PHẠM mục 6 CLAUDE.md -> DỪNG")


def write_summary(out, bu, growth, best_tbl, top10, prof, corr, diag, bnd, oos, thr, gl, s6, meta, conf_text):
    md_table = c9.md_table
    o1 = oos[["cau_hinh", "chuoi", "RMSE_tho_ngoai_mau", "RMSE_khu_muc_ngoai_mau", "sai_so_tb_ngoai_mau",
              "bien_do_ngoai_mau_mo_hinh", "bien_do_ngoai_mau_thuc", "quy_day_ngoai_mau_mo_hinh",
              "quy_day_ngoai_mau_thuc"]]
    o2 = oos.dropna(subset=["RMSE_tho_trong_mau"])[["cau_hinh", "chuoi", "RMSE_tho_trong_mau", "RMSE_khu_muc_trong_mau",
                                                     "RMSE_tho_toan_chuoi", "RMSE_khu_muc_toan_chuoi",
                                                     "ty_le_giam_V_toan_chuoi", "ty_le_hoi_phuc_V_toan_chuoi",
                                                     "quy_day_toan_chuoi_mo_hinh", "quy_day_toan_chuoi_thuc"]]
    pw = prof.pivot_table(index="tham_so", values="bien_do_J_min", aggfunc="first").reset_index()
    bu_tbl = pd.DataFrame([{"chi_tieu": "tien_gui (depositor_base_growth)", "du_lieu": bu["g_D_du_lieu"],
                            "mo_hinh_A_GD9": bu["g_D_mo_hinh_GD9"], "delta": bu["delta_D"],
                            "base_GD9": bu["depositor_base_growth_GD9"], "base_moi": bu["depositor_base_growth_moi"]},
                           {"chi_tieu": "du_no (borrower_base_growth)", "du_lieu": bu["g_L_du_lieu"],
                            "mo_hinh_A_GD9": bu["g_L_mo_hinh_GD9"], "delta": bu["delta_L"],
                            "base_GD9": bu["borrower_base_growth_GD9"], "base_moi": bu["borrower_base_growth_moi"]}])
    glt = gl[gl.pham_vi.str.startswith("trong") | gl.pham_vi.str.startswith("ngoai")][
        ["cau_hinh", "pham_vi", "tang_truong_tien_gui_tb", "tang_truong_du_no_tb"]]
    ldr_t = gl[gl.pham_vi.str.startswith("LDR")].pivot_table(index="bank_id", columns=["cau_hinh", "pham_vi"], values="ldr")
    ldr_t = ldr_t.set_axis([f"{a}|{b}" for a, b in ldr_t.columns], axis=1).reset_index()
    md = [
        "# GD9b – Hiệu chỉnh lại GD9 theo D9 (Q6, Q7): sinh tự động",
        "",
        "> Sinh bởi `python -m src.calibration.calibrate_stage9b`. Phương pháp chốt trước: `DANG_KY_TRUOC_GD9b.md` (commit 1ab8201). "
        "Cửa sổ hiệu chỉnh 2023Q2–2025Q2 (month 1–9), ngoài mẫu 2025Q3–2026Q3 (month 10–14). Kịch bản A, tất định "
        f"(hai seed cho kết quả trùng: {'có' if meta['scenario_A_deterministic_two_seeds'] else 'KHÔNG'}). "
        "Mô hình và mốc ON cùng được cấp ON THỰC ngoài mẫu (lợi thế thông tin). Không phải dự báo, không phải tác động chính sách thực tế.",
        "",
        "## Q7 – Bù tăng trưởng (một lần, tại nghiệm GD9; `bu_tang_truong_stage9b.csv`)",
        md_table(bu_tbl, 10),
        "",
        "## Bước 1 – Tăng trưởng sau bù và ngưỡng chặn (giữ GD9)",
        md_table(growth, 6),
        "",
        "## Bước 2 – Bộ tốt nhất theo biến thể (trong mẫu)",
        md_table(best_tbl, 4),
        "",
        f"λ tốt nhất (biến thể chính) = {meta['lambda_best']}; CI GĐ7 (c) [{meta['lambda_ci_stage7'][0]}; "
        f"{meta['lambda_ci_stage7'][1]}]: {'TRONG' if meta['lambda_in_ci'] else 'NGOÀI'} CI. "
        f"LDR bình quân cửa sổ = {meta['ldr_mean_window']:.4f}. {meta['n_grid_per_variant']} bộ/biến thể.",
        "",
        "### Chạm biên lưới (nghiệm chính; giữ, không mở rộng lưới – D9)",
        md_table(bnd, 4),
        "",
        "### Top 10 (biến thể chính)",
        md_table(top10.drop(columns=["bien_the"]), 4),
        "",
        "### Hồ sơ hàm mục tiêu (min J theo từng giá trị; biên độ nhỏ = phẳng = khó nhận diện)",
        md_table(prof, 4),
        "",
        "Biên độ min J theo tham số:",
        md_table(pw, 4),
        "",
        "### Tương quan giữa tham số trong top 50 (ô trống = tham số hằng trong top 50)",
        md_table(corr, 3),
        "",
        "### Chẩn đoán (CHỈ báo cáo, không đổi bộ chính)",
        md_table(diag, 4),
        "",
        "## Ngoài mẫu 2025Q3–2026Q3 (so GD9, GĐ8, mốc ngây thơ)",
        md_table(o1, 4),
        "",
        "Trong mẫu và toàn chuỗi (chỉ cấu hình mô hình; tỷ lệ V = biên độ giảm/hồi phục mô hình ÷ thực):",
        md_table(o2, 4),
        "",
        "## Ngưỡng có đạt tới không, chạm biên (kịch bản A)",
        md_table(thr, 4),
        "",
        "Tăng trưởng tổng (TB/quý) kịch bản A so với dữ liệu:",
        md_table(glt, 4),
        "",
        "LDR theo ngân hàng cuối 2025Q2 / 2026Q3 (kịch bản A so với thực):",
        md_table(ldr_t, 3),
        "",
        f"## Mục 6 CLAUDE.md ({c9.N_RUNS_SECTION6} lần chạy A/B/C)",
        md_table(s6, 4),
        "",
        f"YAML hiệu chỉnh khớp bộ tốt nhất: {'có' if meta['yaml_matches_best'] else 'KHÔNG'}; sai lệch lớn nhất đường đi "
        f"khi đọc lại từ YAML = {meta['yaml_path_max_abs_diff']:.3g}.",
        "",
        conf_text,
    ]
    (out / "summary_stage9b.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
