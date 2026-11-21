"""GD9b (vòng sửa 2): chẩn đoán THÊM SAU khi chạy lưới (đăng ký mục 7). KHÔNG đổi nghiệm, KHÔNG ghi YAML, KHÔNG chạy lại lưới.

Ba phần, tất cả từ mô phỏng của cấu hình đã có (GD9, GD9b) + một thí nghiệm "bỏ bù" chỉ để chẩn đoán:
  1. bo_bu: nghiệm GD9b nhưng cộng ngược Δ_D, Δ_L của bù Q7 (đọc từ bu_tang_truong_stage9b.csv), kịch bản A,
     so với GD9b có bù: tỷ lệ chạm trần LDR, LDR max, tăng trưởng TB.
  2. canh_tranh_huy_dong: GD9 so GD9b (cùng deposit_competition = 0.07): LDR đầu quý của A sau chính sách,
     tỷ lệ trên ngưỡng, chênh lãi suất huy động và nim_proxy C−B (10 seed, quý 15–18).
  3. bien_va_tang_truong: định nghĩa biên (loan_rate − chi phí vốn trễ so với loan_rate − deposit_rate) và
     khoảng cách tăng trưởng mô hình − dữ liệu (đọc growth_ldr_stage9b.csv).
Xuất vào reports/calibration/stage9b/: diag_gd9b.csv (dạng dài), diag_gd9b.md.
Chỉ là số của mô hình, không phải tác động chính sách thực tế.

Chạy: python -m src.calibration.diag_gd9b
"""

import argparse
from pathlib import Path

import pandas as pd

from ..analysis.experiments import load_config
from ..core.model import ABMModel
from . import calibrate_stage9 as c9
from . import calibrate_stage9b as c9b
from . import confounding_stage9 as cf9

OUTDIR = c9b.OUTDIR
NAMES = {"GD9b": c9b.NEW_CFG, "GD9": c9b.GD9_CFG}


def cap_stats(params, rows, cfg):
    """Kịch bản A (tất định): chạm trần LDR, LDR max, tăng trưởng TB (month 1–9, 10–14, 1–18)."""
    cap = float(params["max_loan_to_deposit"])
    m = ABMModel("A", int(cfg["n_months"]), int(cfg["base_seed"]), params, rows)
    m.run()
    h, b = pd.DataFrame(m.history), pd.DataFrame(m.bank_history)
    hit = b.loans >= b.deposits * cap * (1 - cf9.REL_TOL)
    out = {"ty_le_cham_tran_LDR_month_1_18": float(hit.mean()),
           "ty_le_cham_tran_LDR_month_15_18": float(hit[b.month >= 15].mean()),
           "ldr_max_month_1_18": float(b.ldr.max()),
           "ldr_tb_month_15_18": float(b[b.month >= 15].ldr.mean())}
    for lab, sl in (("1_9", slice(0, 9)), ("10_14", slice(9, 14)), ("1_18", slice(0, 18))):
        out[f"tang_truong_tien_gui_tb_{lab}"] = float(h.deposit_growth.iloc[sl].mean())
        out[f"tang_truong_du_no_tb_{lab}"] = float(h.credit_growth.iloc[sl].mean())
    return out


def competition_stats(name, cfg, rows):
    """10 seed, quý 15–18: LDR đầu quý của A, tỷ lệ trên ngưỡng; C−B của lãi suất huy động và nim_proxy."""
    h, b, q = cf9.run_all(cfg, rows)
    p = cfg["parameters"]
    thr = float(p["deposit_ldr_target"])
    a = b[b.sc == "A"].sort_values(["seed", "bank_id", "month"])
    # LDR đầu quý t = LDR cuối quý t−1 (month q..18 dùng month q−1..17)
    a = a.assign(ldr_dau_quy=a.groupby(["seed", "bank_id"]).ldr.shift(1))
    ap = a[a.month >= q].dropna(subset=["ldr_dau_quy"])
    post = b[b.month >= q]
    dep = post.groupby(["seed", "sc"]).deposit_rate.mean().unstack()
    nim = h[h.month >= q].groupby(["seed", "sc"]).nim_proxy.mean().unstack()
    return {"ngưỡng_LDR": thr, "deposit_competition": float(p["deposit_competition"]),
            "ldr_dau_quy_A_tb_sau_CS": float(ap.ldr_dau_quy.mean()),
            "ty_le_ldr_tren_nguong_A_sau_CS": float((ap.ldr_dau_quy > thr).mean()),
            "deposit_rate_C_tru_B_sau_CS": float((dep.C - dep.B).mean()),
            "nim_proxy_C_tru_B_sau_CS": float((nim.C - nim.B).mean())}


def margin_defs(params, rows, cfg):
    """Kịch bản A, month 1–14: hai định nghĩa biên (cùng phạm vi với thresholds_stage9b.csv)."""
    m = ABMModel("A", int(cfg["n_months"]), int(cfg["base_seed"]), params, rows)
    recs = []
    for _ in range(m.n_months):
        lfc = {bk.bank_id: bk.lagged_funding_cost for bk in m.banks}
        month = m.month + 1
        m.step()
        for bk in m.banks:
            recs.append({"month": month, "bien_chi_phi_von_tre": bk.loan_rate - lfc[bk.bank_id],
                         "bien_cho_vay_tru_huy_dong": bk.loan_rate - bk.deposit_rate})
    d = pd.DataFrame(recs)
    d = d[d.month <= c9.N_SIM]
    return {"muc_tieu_bien_tong": float(m.banks[0].target_margin + m.loan_spread_add),
            "bien_loan_rate_tru_chi_phi_von_tre_tb": float(d.bien_chi_phi_von_tre.mean()),
            "bien_loan_rate_tru_deposit_rate_tb": float(d.bien_cho_vay_tru_huy_dong.mean())}


def growth_gaps():
    g = pd.read_csv(OUTDIR / "growth_ldr_stage9b.csv")
    g = g[g.pham_vi.isin(["trong_mau_1_9", "ngoai_mau_10_14"])].set_index(["cau_hinh", "pham_vi"])
    rows = []
    for name in ("hieu_chinh_GD9b", "hieu_chinh_GD9"):
        for pv in ("trong_mau_1_9", "ngoai_mau_10_14"):
            for col, lab in (("tang_truong_tien_gui_tb", "tien_gui"), ("tang_truong_du_no_tb", "du_no")):
                mo, th = g.loc[(name, pv), col], g.loc[("thuc_te", pv), col]
                rows.append((name, f"khoang_cach_{lab}_{pv}", mo - th))
                rows.append((name, f"ty_so_mo_hinh_tren_thuc_{lab}_{pv}", mo / th))
    return rows


def main(outdir=OUTDIR):
    out = Path(outdir)
    rows = pd.read_csv(c9.BANKS).to_dict("records")
    cfg = load_config(c9b.NEW_CFG)
    bu = pd.read_csv(Path(c9b.OUTDIR) / "bu_tang_truong_stage9b.csv")
    bu = bu.iloc[0] if "delta_D" in bu.columns else dict(zip(bu.iloc[:, 0], bu.iloc[:, 1]))
    d_d, d_l = float(bu["delta_D"]), float(bu["delta_L"])
    p_b = dict(cfg["parameters"])
    p_nb = dict(p_b)
    p_nb["depositor_base_growth"] = p_b["depositor_base_growth"] - d_d      # cộng ngược Δ (chỉ chẩn đoán)
    p_nb["borrower_base_growth"] = p_b["borrower_base_growth"] - d_l

    recs = []

    def add(section, name, stats):
        for k, v in stats.items():
            recs.append({"phan": section, "cau_hinh": name, "chi_tieu": k, "gia_tri": v})

    add("bo_bu", "GD9b_co_bu", cap_stats(p_b, rows, cfg))
    add("bo_bu", "GD9b_bo_bu_CHAN_DOAN", cap_stats(p_nb, rows, cfg))
    for name, path in NAMES.items():
        c = load_config(path)
        add("canh_tranh_huy_dong", name, competition_stats(name, c, rows))
        add("bien", name, margin_defs(dict(c["parameters"]), rows, c))
    for name, k, v in growth_gaps():
        recs.append({"phan": "tang_truong", "cau_hinh": name, "chi_tieu": k, "gia_tri": v})
    df = pd.DataFrame(recs)
    df.to_csv(out / "diag_gd9b.csv", index=False, float_format="%.10g")

    def piv(sec):
        return df[df.phan == sec].pivot(index="chi_tieu", columns="cau_hinh", values="gia_tri")
    lines = ["# Chẩn đoán GD9b (vòng sửa 2; phụ lục đăng ký mục 7, thêm SAU khi chạy lưới; `diag_gd9b.csv`)", "",
             "Số của mô hình, không phải tác động chính sách thực tế. Thí nghiệm \"bỏ bù\" chỉ để chẩn đoán, không ghi vào YAML, "
             f"không đổi nghiệm. Δ_D = {d_d:+.6f}, Δ_L = {d_l:+.6f} (`bu_tang_truong_stage9b.csv`).", ""]
    for sec, title in (("bo_bu", "1. Nghiệm GD9b có bù và bỏ bù Q7 (kịch bản A)"),
                       ("canh_tranh_huy_dong", "2. Áp lực huy động và C−B (deposit_competition như nhau; 10 seed, quý 15–18)"),
                       ("bien", "3a. Hai định nghĩa biên (A, month 1–14)"),
                       ("tang_truong", "3b. Khoảng cách tăng trưởng mô hình − dữ liệu và tỷ số")):
        t = piv(sec)
        lines += [f"### {title}", "", "| chỉ tiêu | " + " | ".join(t.columns) + " |", "|---|" + "---:|" * len(t.columns)]
        for k, r in t.iterrows():
            lines.append(f"| {k} | " + " | ".join("" if pd.isna(v) else f"{v:.4f}" for v in r) + " |")
        lines.append("")
    (out / "diag_gd9b.md").write_text("\n".join(lines), encoding="utf-8")
    patch_summary(out, "\n".join(lines[2:]) + "\n")
    return df


MARK_A, MARK_B = "<!-- diag_gd9b:begin -->", "<!-- diag_gd9b:end -->"


def patch_summary(out, block):
    """Nhúng (idempotent) khối chẩn đoán vào summary_stage9b.md giữa hai dấu mốc; bỏ qua nếu chưa có summary."""
    f = Path(out) / "summary_stage9b.md"
    if not f.exists():
        return
    txt = f.read_text(encoding="utf-8")
    if MARK_A in txt:
        txt = txt[:txt.index(MARK_A)].rstrip("\n") + "\n"
    f.write_text(txt + "\n" + MARK_A + "\n## Phụ lục chẩn đoán (thêm sau khi chạy lưới, vòng sửa 2)\n\n" + block + MARK_B + "\n",
                 encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outdir", default=str(OUTDIR))
    print(main(ap.parse_args().outdir).to_string())
