"""Giai đoạn 9 (vòng sửa 2): định lượng nhiễu lẫn tuân thủ và độ tin cậy của B−A / C−A.

So hai cấu hình (macro GĐ8 và hiệu chỉnh GD9), 10 seed (base_seed + 0..9), quý 15–18 (sau chính sách).
Xuất vào reports/calibration/stage9/:
  confounding_stage9.csv      mức trung bình theo cấu hình (trung bình theo seed rồi theo quý 15–18)
  ldr_cap_stage9.csv          tỷ lệ ngân hàng-quý chạm trần LDR theo kịch bản và theo month
  ldr_cap_2026q3_stage9.csv   khởi đầu từ abm_initial_8nganhang_2026Q3.csv (kịch bản A, 18 quý)
  confounding_stage9.md       bảng tóm tắt (được nhúng vào summary_stage9.md)
"max(B−A)" là max theo quý và seed, không phải mức trung bình. Đây là số của mô hình, không phải tác động chính sách thực tế.

Chạy: python -m src.calibration.confounding_stage9
"""

from pathlib import Path

import numpy as np
import pandas as pd

from ..analysis.experiments import load_config
from ..core.model import ABMModel

ROOT = Path(__file__).resolve().parents[2]
BANKS = ROOT / "data/clean/abm_initial_8nganhang_2023Q1.csv"
BANKS_2026Q3 = ROOT / "data/clean/abm_initial_8nganhang_2026Q3.csv"
OUTDIR = ROOT / "reports/calibration/stage9"
CONFIGS = {"macro_GD8": ROOT / "configs/scenarios_macro.yaml",
           "hieu_chinh_GD9": ROOT / "configs/scenarios_calibrated.yaml"}
N_SEEDS = 10
REL_TOL = 1e-9


def run_all(cfg, rows, n_seeds=N_SEEDS):
    p = dict(cfg["parameters"])
    cap = float(p["max_loan_to_deposit"])
    pol_q = int(p["policy_month"]) + 1
    hist, bank = [], []
    for i in range(n_seeds):
        for sc in "ABC":
            m = ABMModel(sc, int(cfg["n_months"]), int(cfg["base_seed"]) + i, p, rows)
            m.run()
            h = pd.DataFrame(m.history).assign(seed=i, sc=sc)
            b = pd.DataFrame(m.bank_history).assign(seed=i, sc=sc)
            b["hit_cap"] = b.loans >= b.deposits * cap * (1 - REL_TOL)
            hist.append(h)
            bank.append(b)
    return pd.concat(hist, ignore_index=True), pd.concat(bank, ignore_index=True), pol_q


def summarize(name, cfg, rows):
    h, b, q = run_all(cfg, rows)
    post = h[h.month >= q]
    lr = post.groupby(["seed", "sc"]).loan_rate.mean().unstack()
    nim = post.groupby(["seed", "sc"]).nim_proxy.mean().unstack()
    qs = post.pivot_table(index=["seed", "month"], columns="sc", values="loan_rate")
    bp = b[(b.month >= q) & (b.sc != "A")]
    prob = bp.groupby("sc").policy_probability.mean()
    cut = bp.groupby("sc").policy_cut.mean() if "policy_cut" in bp else None
    hit = b[b.month >= q].groupby("sc").hit_cap.mean()
    row = {"cau_hinh": name, "n_seed": N_SEEDS, "quy_sau_CS": f"{q}-{int(cfg['n_months'])}",
           "BmA_tb": float((lr.B - lr.A).mean()), "CmA_tb": float((lr.C - lr.A).mean()),
           "CmB_tb": float((lr.C - lr.B).mean()),
           "BmA_sd_theo_seed": float((lr.B - lr.A).std(ddof=1)),
           "max_BmA_theo_quy_va_seed": float((qs.B - qs.A).max()),
           "max_CmA_theo_quy_va_seed": float((qs.C - qs.A).max()),
           "loan_rate_A_sau_CS": float(lr.A.mean()), "loan_rate_B_sau_CS": float(lr.B.mean()),
           "loan_rate_C_sau_CS": float(lr.C.mean()),
           "nim_A_sau_CS": float(nim.A.mean()), "nim_B_sau_CS": float(nim.B.mean()), "nim_C_sau_CS": float(nim.C.mean()),
           "xs_tuan_thu_tb_B": float(prob.B), "xs_tuan_thu_tb_C": float(prob.C),
           "ty_le_tran_LDR_A_sau_CS": float(hit.A), "ty_le_tran_LDR_B_sau_CS": float(hit.B),
           "ty_le_tran_LDR_C_sau_CS": float(hit.C)}
    cap_rows = []
    for (sc, mth), g in b.groupby(["sc", "month"]):
        cap_rows.append({"cau_hinh": name, "kich_ban": sc, "month": int(mth), "ty_le_chạm_tran": float(g.hit_cap.mean())})
    capdf = pd.DataFrame(cap_rows).rename(columns={"ty_le_chạm_tran": "ty_le_cham_tran"})
    # tỷ lệ chạm trần của A theo giai đoạn (trung bình theo ngân hàng-quý)
    a = b[b.sc == "A"]
    row["tran_LDR_A_month_1_10"] = float(a[a.month <= 10].hit_cap.mean())
    row["tran_LDR_A_month_11_15"] = float(a[(a.month >= 11) & (a.month <= 15)].hit_cap.mean())
    row["tran_LDR_A_month_16_18"] = float(a[a.month >= 16].hit_cap.mean())
    return row, capdf


def start_2026q3(name, cfg):
    rows = pd.read_csv(BANKS_2026Q3).to_dict("records")
    p = dict(cfg["parameters"])
    cap = float(p["max_loan_to_deposit"])
    m = ABMModel("A", int(cfg["n_months"]), int(cfg["base_seed"]), p, rows)
    m.run()
    b = pd.DataFrame(m.bank_history)
    b["hit_cap"] = b.loans >= b.deposits * cap * (1 - REL_TOL)
    g = b.groupby("month").hit_cap.mean().reset_index()
    g.insert(0, "cau_hinh", name)
    g = g.rename(columns={"hit_cap": "ty_le_cham_tran"})
    return g


def main(outdir=OUTDIR):
    out = Path(outdir)
    rows = pd.read_csv(BANKS).to_dict("records")
    res, caps, starts = [], [], []
    for name, path in CONFIGS.items():
        cfg = load_config(path)
        r, c = summarize(name, cfg, rows)
        res.append(r)
        caps.append(c)
        starts.append(start_2026q3(name, cfg))
    df = pd.DataFrame(res)
    df.to_csv(out / "confounding_stage9.csv", index=False, float_format="%.10g")
    pd.concat(caps, ignore_index=True).to_csv(out / "ldr_cap_stage9.csv", index=False, float_format="%.10g")
    st = pd.concat(starts, ignore_index=True)
    st.to_csv(out / "ldr_cap_2026q3_stage9.csv", index=False, float_format="%.10g")

    m, c = df.iloc[0], df.iloc[1]
    last = st.groupby("cau_hinh").ty_le_cham_tran.last()
    lines = [
        "### Nhiễu lẫn tuân thủ và độ tin cậy của B−A / C−A (vòng sửa 2; `confounding_stage9.csv`, `ldr_cap_stage9.csv`, `ldr_cap_2026q3_stage9.csv`)",
        "",
        f"{N_SEEDS} seed (base_seed + 0..{N_SEEDS - 1}), trung bình theo seed rồi theo quý {c.quy_sau_CS}. "
        "`max(B−A)` ở mục 6 là max theo quý và seed, KHÔNG phải mức trung bình. Chênh lệch phần lớn là hiệu ứng mức "
        "và nhiễu lẫn tuân thủ; đây là số của mô hình, không phải tác động chính sách thực tế.",
        "",
        "| Chỉ tiêu (sau CS) | macro GĐ8 | hiệu chỉnh GD9 |", "|---|---:|---:|",
    ]
    for lab, k in [("B−A (TB)", "BmA_tb"), ("C−A (TB)", "CmA_tb"), ("C−B (TB)", "CmB_tb"),
                   ("độ lệch chuẩn B−A theo seed", "BmA_sd_theo_seed"),
                   ("max(B−A) theo quý và seed", "max_BmA_theo_quy_va_seed"),
                   ("max(C−A) theo quý và seed", "max_CmA_theo_quy_va_seed"),
                   ("LS cho vay A", "loan_rate_A_sau_CS"), ("LS cho vay B", "loan_rate_B_sau_CS"),
                   ("LS cho vay C", "loan_rate_C_sau_CS"),
                   ("nim_proxy A", "nim_A_sau_CS"), ("nim_proxy B", "nim_B_sau_CS"), ("nim_proxy C", "nim_C_sau_CS"),
                   ("xác suất tuân thủ TB, B", "xs_tuan_thu_tb_B"), ("xác suất tuân thủ TB, C", "xs_tuan_thu_tb_C"),
                   ("tỷ lệ ngân hàng-quý chạm trần LDR, A", "ty_le_tran_LDR_A_sau_CS"),
                   ("tỷ lệ chạm trần LDR, B", "ty_le_tran_LDR_B_sau_CS"),
                   ("tỷ lệ chạm trần LDR, C", "ty_le_tran_LDR_C_sau_CS"),
                   ("tỷ lệ chạm trần LDR, A, month 1–10", "tran_LDR_A_month_1_10"),
                   ("tỷ lệ chạm trần LDR, A, month 11–15", "tran_LDR_A_month_11_15"),
                   ("tỷ lệ chạm trần LDR, A, month 16–18", "tran_LDR_A_month_16_18")]:
        lines.append(f"| {lab} | {m[k]:.4f} | {c[k]:.4f} |")
    lines += ["", f"Khởi đầu từ `abm_initial_8nganhang_2026Q3.csv`, kịch bản A, 18 quý: tỷ lệ ngân hàng chạm trần LDR ở quý cuối = "
              f"{last['macro_GD8']:.3f} (macro GĐ8) và {last['hieu_chinh_GD9']:.3f} (hiệu chỉnh GD9)."]
    (out / "confounding_stage9.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    patch_summary(out, "\n".join(lines) + "\n")
    return df


MARK_A, MARK_B = "<!-- confounding:begin -->", "<!-- confounding:end -->"


def patch_summary(out, block):
    """Nhúng (idempotent) khối bảng vào summary_stage9.md, giữa hai dấu mốc; tạo mới nếu chưa có."""
    f = Path(out) / "summary_stage9.md"
    if not f.exists():
        return
    txt = f.read_text(encoding="utf-8")
    if MARK_A in txt:
        txt = txt[:txt.index(MARK_A)].rstrip("\n") + "\n"
    f.write_text(txt + "\n" + MARK_A + "\n" + block + MARK_B + "\n", encoding="utf-8")


if __name__ == "__main__":
    print(main().T.to_string())
