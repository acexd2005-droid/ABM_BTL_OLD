"""GD10b: độ nhạy `deposit_competition` và `policy_step` 0.375 trên cấu hình GD9b (D10, Q10).

Mỗi lần đổi MỘT tham số trong bộ nhớ (YAML chính không đổi), 30 lần chạy, seed base_seed + i.
Đây là ĐỘ NHẠY, không phải ước lượng. QUY TẮC ĐỌC ĐẶT TRƯỚC: báo cả 4 giá trị deposit_competition
(B−A, C−A, C−B, tỷ lệ chạm trần LDR); KHÔNG chọn giá trị nào làm bản chính; không dùng kết quả để sửa YAML.
Kết quả: reports/stage10/sensitivity_gd10b_stage10.csv, sensitivity_gd10b_section6_stage10.csv, summary_gd10b_stage10.md
Chạy: python -m src.analysis.sensitivity_gd10b
"""

import argparse
from pathlib import Path

import pandas as pd

from .robustness_stage10 import (BANKS, CFG_MAIN, N_SENS, OUTDIR, bank_rows, cfg_of, run_variant, section6, summarize)

DC_VALUES = (0.07, 0.3, 0.7, 1.2)   # LO_TRINH GD10b mục 1
STEP_VALUE = 0.375                  # LO_TRINH GD10b mục 1 (ánh xạ giả định CV 9608)


def build_variants(P):
    V = [("co_so_30", "co_so", dict(P), "cấu hình chính GD9b, 30 lần (đối chiếu, không phải biến thể)")]
    for v in DC_VALUES:
        tag = " (= giá trị YAML)" if abs(v - P["deposit_competition"]) < 1e-12 else ""
        V.append((f"deposit_competition_{v:g}", "deposit_competition", {**P, "deposit_competition": v},
                  f"deposit_competition = {v:g}{tag}"))
    V.append((f"policy_step_{STEP_VALUE:g}", "policy_step", {**P, "policy_step": STEP_VALUE},
              f"policy_step = {STEP_VALUE:g} điểm %/năm (ánh xạ giả định, không phải ước lượng)"))
    return V


COLS = ["cau_hinh", "nhom", "n_seed", "loan_rate_A_sau_CS", "BmA_tb", "BmA_cuoi_ky_q18", "CmA_tb", "CmA_cuoi_ky_q18",
        "CmB_tb", "CmB_ci95_nua_rong", "deposit_BmA_tb", "deposit_CmA_tb", "deposit_CmB_tb", "xs_tuan_thu_tb_B",
        "xs_tuan_thu_tb_C", "nim_proxy_A_sau_CS", "ty_le_cham_tran_LDR", "mo_ta"]


def fmt(x, nd=4):
    return f"{x:.{nd}f}"


def make_md(out, df):
    ref = df[df.cau_hinh == "co_so_30"].iloc[0]
    L = ["# GD10b – Độ nhạy `deposit_competition` và `policy_step` 0.375 (sinh tự động)", "",
         "Sinh bởi `python -m src.analysis.sensitivity_gd10b`. Cấu hình nền: `configs/scenarios_calibrated.yaml` (GD9b), "
         f"{int(ref.n_seed)} lần chạy, mỗi lần đổi một tham số trong bộ nhớ. **Đây là độ nhạy, không phải ước lượng**; "
         "không giá trị nào được chọn làm bản chính; YAML chính không đổi. Số là kết quả mô hình, không phải tác động chính sách thực tế.", "",
         "| Cấu hình | LS cho vay A sau CS | B−A TB | C−A TB | C−B TB | B−A cuối kỳ | C−A cuối kỳ | LS huy động C−B | tuân thủ B | nim_proxy A | tỷ lệ chạm trần LDR |",
         "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for _, r in df.iterrows():
        L.append(f"| {r.cau_hinh} | {fmt(r.loan_rate_A_sau_CS)} | {fmt(r.BmA_tb)} | {fmt(r.CmA_tb)} | {fmt(r.CmB_tb)} | "
                 f"{fmt(r.BmA_cuoi_ky_q18)} | {fmt(r.CmA_cuoi_ky_q18)} | {fmt(r.deposit_CmB_tb)} | {fmt(r.xs_tuan_thu_tb_B)} | "
                 f"{fmt(r.nim_proxy_A_sau_CS, 3)} | {fmt(r.ty_le_cham_tran_LDR)} |")
    L += ["", "Quý sau chính sách = 15–18 (Q4/2026–Q3/2027). `co_so_30` là cấu hình GD9b (deposit_competition 0.07, policy_step 0.28) "
          "chạy 30 lần để đối chiếu cùng số lần."]
    (Path(out) / "summary_gd10b_stage10.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def main(outdir=OUTDIR, n_seeds=N_SENS):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    rows = bank_rows()
    cfg = cfg_of(CFG_MAIN)
    P = dict(cfg["parameters"])
    res, s6 = [], []
    for name, grp, params, desc in build_variants(P):
        h, b = run_variant(cfg, params, rows, n_seeds)
        r = summarize(name, params, cfg, h, b)
        s = section6(name, params, cfg, rows, h, b)
        r["nhom"], r["mo_ta"], r["ty_le_cham_tran_LDR"] = grp, desc, s["ty_le_cham_tran_LDR"]
        res.append(r)
        s6.append(s)
    df = pd.DataFrame(res)[COLS]
    df.to_csv(out / "sensitivity_gd10b_stage10.csv", index=False, float_format="%.10g")
    pd.DataFrame(s6).to_csv(out / "sensitivity_gd10b_section6_stage10.csv", index=False, float_format="%.10g")
    make_md(out, df)
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=str(OUTDIR))
    a = ap.parse_args()
    main(a.outdir)
    print("xong ->", a.outdir)
