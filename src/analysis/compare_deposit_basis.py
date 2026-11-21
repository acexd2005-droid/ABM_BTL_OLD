"""Bước 8a: so sánh cơ sở lãi suất huy động `total` (cũ) và `term` (chia 1 - casa) khi khởi tạo.

Chạy A/B/C, n_runs lần (mặc định 60 theo configs/scenarios.yaml), dữ liệu 8 ngân hàng thật,
khởi tạo 2023Q1, cùng seed cho hai cơ sở. KHÔNG đổi mặc định của dự án sang `term`.
Chạy: python -m src.analysis.compare_deposit_basis [--runs 60] [--outdir reports/stage8a]

Đơn vị: lãi suất %/năm. Dữ liệu là chi phí lãi sổ sách trên TỔNG tiền gửi ("cơ sở total"). Cột `deposit_rate`
của mô hình: ở `total` đã cùng cơ sở với dữ liệu (dùng nguyên giá trị); ở `term` là lãi suất kỳ hạn nên quy đổi
`deposit_rate * (1 - casa)` mới so được với dữ liệu. Kết quả quy đổi đặt tên *_total_basis.
RMSE là đối chiếu trong mẫu, không phải dự báo ngoài mẫu và không phải tác động chính sách thực tế.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from ..core.model import ABMModel
from .advanced_analysis import prepare_actual_from_panel
from .experiments import load_config

ROOT = Path(__file__).resolve().parents[2]
BANKS = ROOT / "data/clean/abm_initial_8nganhang_2023Q1.csv"
PANEL = ROOT / "data/clean/abm_panel_8nganhang_2023Q1_2026Q3.csv"
TERM_OVERRIDE = ROOT / "configs/scenarios_term.yaml"
BASES = ("total", "term")


def actual_series(outdir):
    """Chuỗi thực 2023Q2-2026Q3 (month 1..14): lãi suất cho vay gia quyền theo dư nợ (hàm có sẵn)
    và lãi suất huy động gia quyền theo tiền gửi (cơ sở total, cùng cơ sở với dữ liệu)."""
    banks = pd.read_csv(BANKS)
    loan = prepare_actual_from_panel(PANEL, outdir, "2023Q1", expected_banks=set(banks.bank_id))
    p = pd.read_csv(PANEL, encoding="utf-8-sig")
    p["per"] = pd.PeriodIndex(p["period"], freq="Q")
    start = pd.Period("2023Q1", freq="Q")
    p = p[p["per"] > start]
    p["month"] = p["per"].map(lambda q: q.ordinal - start.ordinal)
    p["w"] = p["deposit_rate_pct"] * p["deposits"]
    g = p.groupby("month")
    dep = (g["w"].sum() / g["deposits"].sum()).rename("deposit_rate").reset_index()
    out = loan.merge(dep, on="month").rename(columns={"loan_rate": "actual_loan_rate",
                                                      "deposit_rate": "actual_deposit_rate"})
    return out[["month", "quarter", "actual_loan_rate", "actual_deposit_rate"]]


def run_all(runs):
    rows = pd.read_csv(BANKS).to_dict("records")
    hist, bank = [], []
    init = []
    for basis in BASES:
        cfg = load_config(TERM_OVERRIDE if basis == "term" else None)
        params = dict(cfg["parameters"])
        assert params["deposit_rate_basis"] == basis
        for sc in "ABC":
            for r in range(runs):
                seed = int(cfg["base_seed"]) + r
                m = ABMModel(sc, int(cfg["n_months"]), seed, params, rows)
                if sc == "A" and r == 0:
                    init.append({"basis": basis,
                                 "mean_funding_cost": np.mean([b.funding_cost for b in m.banks]),
                                 "mean_deposit_rate_model": np.mean([b.deposit_rate for b in m.banks]),
                                 "learning_nim_threshold": m.learning_nim_threshold})
                h = m.run()
                b = pd.DataFrame(m.bank_history)
                for f, name in ((h, "h"), (b, "b")):
                    f["basis"], f["scenario"], f["run_id"] = basis, sc, r
                hist.append(h)
                bank.append(b)
    hist = pd.concat(hist, ignore_index=True)
    bank = pd.concat(bank, ignore_index=True)
    # Cơ sở total: deposit_rate mô hình đã là cơ sở dữ liệu (không nhân thêm 1-casa); term: quy đổi.
    bank["dep_total_basis"] = np.where(bank["basis"] == "term",
                                       bank["deposit_rate"] * (1 - bank["casa_ratio"]),
                                       bank["deposit_rate"])
    bank["w_dep"] = bank["dep_total_basis"] * bank["deposits"]
    agg = bank.groupby(["basis", "scenario", "run_id", "month"]).agg(
        w=("w_dep", "sum"), d=("deposits", "sum")).reset_index()
    agg["deposit_rate_total_basis"] = agg.w / agg.d
    hist = hist.merge(agg[["basis", "scenario", "run_id", "month", "deposit_rate_total_basis"]],
                      on=["basis", "scenario", "run_id", "month"])
    return hist, bank, pd.DataFrame(init)


def quarterly_table(hist, actual):
    q = (hist.groupby(["basis", "scenario", "month", "quarter"])
         [["loan_rate", "deposit_rate", "deposit_rate_total_basis"]].mean().reset_index())
    q = q.rename(columns={"deposit_rate": "deposit_rate_model_basis"})
    return q.merge(actual[["month", "actual_loan_rate", "actual_deposit_rate"]], on="month", how="left")


def effects_table(hist, bank, pm):
    n = hist.month.max()
    piv = hist.pivot_table(index=["basis", "run_id", "month"], columns="scenario",
                           values=["loan_rate", "deposit_rate_total_basis"])
    piv.columns = [f"{a}|{b}" for a, b in piv.columns]
    piv = piv.reset_index()
    rows = []
    for basis, g in piv.groupby("basis"):
        for label, sub in (("cuoi_ky", g[g.month == n]), ("tb_sau_chinh_sach", g[g.month > pm].groupby("run_id").mean(numeric_only=True))):
            for var, lab in (("loan_rate", "loan_rate"), ("deposit_rate_total_basis", "deposit_rate_total_basis")):
                for sc in "BC":
                    d = (sub[f"{var}|{sc}"] - sub[f"{var}|A"])
                    rows.append({"basis": basis, "thoi_diem": label, "bien": lab, "so_sanh": f"{sc}-A",
                                 "tb": d.mean(), "sd_giua_cac_lan_chay": d.std(ddof=1),
                                 "min": d.min(), "max": d.max()})
    eff = pd.DataFrame(rows)
    act = bank[bank.policy_active]
    comp = (act.groupby(["basis", "scenario", "run_id"])
            .agg(ty_le_tuan_thu=("policy_complied", "mean"), xac_suat_tb=("policy_probability", "mean"))
            .reset_index().groupby(["basis", "scenario"])
            .agg(ty_le_tuan_thu_tb=("ty_le_tuan_thu", "mean"), ty_le_tuan_thu_sd=("ty_le_tuan_thu", "std"),
                 xac_suat_tuan_thu_tb=("xac_suat_tb", "mean")).reset_index())
    return eff, comp


def fit_table(hist, actual):
    rows = []
    a = actual.set_index("month")
    m14 = a.index.max()
    for basis in BASES:
        g = hist[(hist.basis == basis) & (hist.scenario == "A") & (hist.month <= m14)]
        for var, col, act in (("loan_rate", "loan_rate", "actual_loan_rate"),
                              ("deposit_rate_total_basis", "deposit_rate_total_basis", "actual_deposit_rate")):
            per_run = []
            for r, h in g.groupby("run_id"):
                e = h.set_index("month")[col] - a[act]
                per_run.append((np.sqrt((e ** 2).mean()), e.abs().mean(), e.mean()))
            per_run = np.array(per_run)
            e_mean = g.groupby("month")[col].mean() - a[act]
            rows.append({"basis": basis, "bien": var, "so_quy": int(m14),
                         "RMSE_tb_cac_lan": per_run[:, 0].mean(), "RMSE_sd": per_run[:, 0].std(ddof=1),
                         "RMSE_duong_trung_binh": float(np.sqrt((e_mean ** 2).mean())),
                         "MAE_tb": per_run[:, 1].mean(), "sai_so_trung_binh(mo_hinh-thuc)": per_run[:, 2].mean()})
    return pd.DataFrame(rows)


def checks(hist, bank, cfg):
    pm = int(cfg["parameters"]["policy_month"])
    rows = []
    for basis in BASES:
        h = hist[hist.basis == basis]
        b = bank[bank.basis == basis]
        wide = h.pivot_table(index=["run_id", "month"], columns="scenario", values="loan_rate")
        pre = wide[wide.index.get_level_values("month") <= pm]
        post = wide[wide.index.get_level_values("month") > pm]
        rows.append({
            "basis": basis,
            "chenh_lech_toi_da_A_B_C_truoc_chinh_sach": float(max((pre["A"] - pre["B"]).abs().max(), (pre["A"] - pre["C"]).abs().max())),
            "so_vi_pham_B_cao_hon_A_sau_chinh_sach": int((post["B"] > post["A"] + 1e-12).sum()),
            "so_vi_pham_C_cao_hon_A_sau_chinh_sach": int((post["C"] > post["A"] + 1e-12).sum()),
            "loan_rate_min": float(b.loan_rate.min()), "loan_rate_max": float(b.loan_rate.max()),
            "deposit_rate_min": float(b.deposit_rate.min()), "deposit_rate_max": float(b.deposit_rate.max()),
            "ldr_toi_da": float(b.ldr.max()),
            "so_quan_sat_chan_tran_huy_dong_14": int((b.deposit_rate >= 14 - 1e-9).sum()),
        })
    return pd.DataFrame(rows)


def md_table(df, digits=4):
    cols = list(df.columns)
    out = "| " + " | ".join(cols) + " |\n|" + "|".join(["---"] * len(cols)) + "|\n"
    for _, r in df.iterrows():
        out += "| " + " | ".join(
            f"{v:.{digits}f}" if isinstance(v, (float, np.floating)) and v == v
            else ("" if isinstance(v, (float, np.floating)) else str(v)) for v in r) + " |\n"
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", type=int, default=None, help="mặc định: n_runs trong configs/scenarios.yaml (60)")
    ap.add_argument("--outdir", default=str(ROOT / "reports/stage8a"))
    args = ap.parse_args()
    cfg = load_config()
    runs = args.runs or int(cfg["n_runs"])
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    pm = int(cfg["parameters"]["policy_month"])

    actual = actual_series(out)
    hist, bank, init = run_all(runs)
    quarterly = quarterly_table(hist, actual)
    eff, comp = effects_table(hist, bank, pm)
    fit = fit_table(hist, actual)
    chk = checks(hist, bank, cfg)

    quarterly.to_csv(out / "quarterly_stage8a.csv", index=False)
    eff.to_csv(out / "effects_stage8a.csv", index=False)
    comp.to_csv(out / "compliance_stage8a.csv", index=False)
    fit.to_csv(out / "fit_vs_actual_stage8a.csv", index=False)
    chk.to_csv(out / "checks_stage8a.csv", index=False)
    init.to_csv(out / "initial_state_stage8a.csv", index=False)

    md = [f"# Bước 8a: cơ sở lãi suất huy động `total` so với `term` (sinh tự động)\n",
          f"> {runs} lần chạy mỗi kịch bản, seed = base_seed + run_id (cùng seed cho hai cơ sở), dữ liệu 8 ngân hàng thật, khởi tạo 2023Q1, 18 quý, chính sách từ bước {pm + 1} (Q4/2026). "
          "Mặc định của dự án vẫn là `total`; đổi sang `term` là quyết định của trưởng nhóm. "
          "RMSE là đối chiếu trong mẫu, không phải dự báo ngoài mẫu; chênh lệch A/B/C không phải tác động chính sách thực tế. "
          "Kịch bản A không dùng số ngẫu nhiên nên các lần chạy của A giống hệt nhau (sd RMSE = 0); số lần chạy chỉ có tác dụng với B và C (xác suất tuân thủ).\n",
          "`deposit_rate_total_basis` gia quyền theo tiền gửi, cùng cơ sở với dữ liệu (chi phí lãi sổ sách trên tổng tiền gửi): ở `total` bằng chính `deposit_rate` của mô hình; "
          "ở `term` bằng `deposit_rate × (1 − casa)` (cột `deposit_rate` gốc ở `term` là lãi suất kỳ hạn nên cao hơn).\n",
          "## Trạng thái khởi tạo\n", md_table(init),
          "## Độ khớp với chuỗi thực 2023Q2–2026Q3 (kịch bản A; 14 quý; trước chính sách A = B = C)\n", md_table(fit),
          "Lưu ý: `RMSE_sd` = 0 vì kịch bản A không dùng số ngẫu nhiên (các lần chạy giống hệt nhau), không phải do sai số được ước lượng chính xác. "
          "Hai cơ sở khởi tạo `deposit_rate` của mô hình ở mức khác nhau (`term` = dữ liệu/(1 − casa)); sau khi quy đổi về cơ sở dữ liệu, huy động của `term` xấp xỉ `total` (term nhỉnh hơn chút). Chênh lệch lớn nằm ở chi phí vốn và lãi suất cho vay, vì `total` trừ CASA hai lần ở `funding_cost`.\n",
          "## Tác động chính sách (B−A, C−A; chênh theo cặp cùng seed, điểm %/năm)\n", md_table(eff),
          "## Tuân thủ chỉ đạo (các quý có chính sách, theo ngân hàng-quý)\n", md_table(comp),
          "## Kiểm tra hợp lý kinh tế (mục 6 CLAUDE.md)\n", md_table(chk, 6)]
    for basis in BASES:
        q = quarterly[quarterly.basis == basis]
        wide = q.pivot(index=["month", "quarter"], columns="scenario",
                       values=["loan_rate", "deposit_rate_total_basis", "deposit_rate_model_basis"])
        wide.columns = [f"{a}_{b}" for a, b in wide.columns]
        wide = wide.reset_index().merge(
            actual[["month", "actual_loan_rate", "actual_deposit_rate"]], on="month", how="left")
        keep = ["month", "quarter", "actual_loan_rate", "loan_rate_A", "loan_rate_B", "loan_rate_C",
                "actual_deposit_rate", "deposit_rate_total_basis_A", "deposit_rate_total_basis_B",
                "deposit_rate_total_basis_C", "deposit_rate_model_basis_A"]
        md += [f"## Chuỗi theo quý — cơ sở `{basis}` (trung bình {runs} lần chạy)\n", md_table(wide[keep], 3)]
    md.append("File dữ liệu: quarterly_stage8a.csv, effects_stage8a.csv, compliance_stage8a.csv, fit_vs_actual_stage8a.csv, "
              "checks_stage8a.csv, initial_state_stage8a.csv, C_lai_suat_thuc_te_tu_panel.csv.\n")
    (out / "summary_stage8a.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Đã ghi kết quả vào {out}")


if __name__ == "__main__":
    main()
