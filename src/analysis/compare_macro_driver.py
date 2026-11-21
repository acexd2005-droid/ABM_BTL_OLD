"""Giai đoạn 8: so sánh `macro_driver: none` với `exogenous` (neo lãi suất huy động về ON quý trước)
và `exogenous + macro_lending_on_coef = 0.45`, cơ sở `term`.

Chạy A/B/C, n_runs lần (60), dữ liệu 8 ngân hàng thật, khởi tạo 2023Q1. KHÔNG đổi mặc định của dự án.
Thước chính: RMSE khử mức (độ lệch chuẩn của sai số) của lãi suất cho vay và lãi suất huy động (cơ sở dữ liệu =
deposit_rate·(1−casa) gia quyền theo tiền gửi) 2023Q2–2026Q3, biên độ chữ V (tỷ lệ so với thực) và quý đáy.
Thước phụ: RMSE thô và sai số trung bình. Đây là kiểm tra TRONG MẪU, không phải dự báo ngoài mẫu và không phải
tác động chính sách thực tế.
Chạy: python -m src.analysis.compare_macro_driver [--runs 60] [--outdir reports/stage8]
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from ..core.model import ABMModel
from .compare_deposit_basis import actual_series
from .experiments import load_config

ROOT = Path(__file__).resolve().parents[2]
BANKS = ROOT / "data/clean/abm_initial_8nganhang_2023Q1.csv"

VARIANTS = {
    "none": ("Không có biến vĩ mô (none)", {}),
    "exogenous": ("exogenous (neo ON trong huy động)", {"macro_driver": "exogenous"}),
    "exogenous_lending045": ("exogenous + lending_on 0.45",
                             {"macro_driver": "exogenous", "macro_lending_on_coef": 0.45}),
    "ref_lending045_khong_tam_hoa": ("(tham khảo) lending_on 0.45 không tâm hóa (ref = 0)",
                                     {"macro_driver": "exogenous", "macro_lending_on_coef": 0.45,
                                      "macro_lending_on_ref": 0.0}),
}
COLORS = {"actual": "#0b0b0b", "none": "#2a78d6", "exogenous": "#eb6834", "exogenous_lending045": "#1baf7a"}


def run_all(runs):
    cfg = load_config()
    rows = pd.read_csv(BANKS).to_dict("records")
    base = dict(cfg["parameters"])
    hist, bank = [], []
    for key, (_, over) in VARIANTS.items():
        params = {**base, **over}
        for sc in "ABC":
            for r in range(runs):
                m = ABMModel(sc, int(cfg["n_months"]), int(cfg["base_seed"]) + r, params, rows)
                h = m.run()
                b = pd.DataFrame(m.bank_history)
                for f in (h, b):
                    f["variant"], f["scenario"], f["run_id"] = key, sc, r
                hist.append(h)
                bank.append(b)
    hist = pd.concat(hist, ignore_index=True)
    bank = pd.concat(bank, ignore_index=True)
    bank["dep_data_basis"] = bank["deposit_rate"] * (1 - bank["casa_ratio"])   # cơ sở term -> cơ sở dữ liệu
    bank["w"] = bank["dep_data_basis"] * bank["deposits"]
    agg = bank.groupby(["variant", "scenario", "run_id", "month"]).agg(w=("w", "sum"), d=("deposits", "sum")).reset_index()
    agg["deposit_rate_data_basis"] = agg.w / agg.d
    hist = hist.merge(agg[["variant", "scenario", "run_id", "month", "deposit_rate_data_basis"]],
                      on=["variant", "scenario", "run_id", "month"])
    return cfg, hist, bank


def v_metrics(x, quarters):
    x = np.asarray(x, float)
    i = int(np.argmin(x))
    return {"dau": x[0], "day": x[i], "quy_day": quarters[i], "thang_day": i + 1,
            "giam_tu_dau_den_day": x[0] - x[i], "hoi_phuc_tu_day_den_cuoi": x[-1] - x[i]}


def fit_table(hist, actual):
    a = actual.sort_values("month").reset_index(drop=True)
    n = len(a)
    q = list(a["quarter"])
    rows = []
    act_v = {"cho_vay": v_metrics(a["actual_loan_rate"], q), "huy_dong": v_metrics(a["actual_deposit_rate"], q)}
    for key in VARIANTS:
        g = hist[(hist.variant == key) & (hist.scenario == "A") & (hist.month <= n)]
        mean_path = g.groupby("month")[["loan_rate", "deposit_rate_data_basis"]].mean().reset_index()
        for lab, col, acol in (("cho_vay", "loan_rate", "actual_loan_rate"),
                               ("huy_dong", "deposit_rate_data_basis", "actual_deposit_rate")):
            x, y = mean_path[col].to_numpy(), a[acol].to_numpy()
            e = x - y
            vm, av = v_metrics(x, q), act_v[lab]
            rows.append({
                "bien_the": key, "chuoi": lab, "RMSE_khu_muc": float(e.std(ddof=0)),
                "RMSE_tho": float(np.sqrt((e ** 2).mean())), "sai_so_tb": float(e.mean()),
                "tuong_quan": float(np.corrcoef(x, y)[0, 1]),
                "giam_mo_hinh": vm["giam_tu_dau_den_day"], "giam_thuc": av["giam_tu_dau_den_day"],
                "ty_le_giam": vm["giam_tu_dau_den_day"] / av["giam_tu_dau_den_day"],
                "hoi_phuc_mo_hinh": vm["hoi_phuc_tu_day_den_cuoi"], "hoi_phuc_thuc": av["hoi_phuc_tu_day_den_cuoi"],
                "ty_le_hoi_phuc": vm["hoi_phuc_tu_day_den_cuoi"] / av["hoi_phuc_tu_day_den_cuoi"],
                "quy_day_mo_hinh": vm["quy_day"], "quy_day_thuc": av["quy_day"],
            })
    return pd.DataFrame(rows)


def effects_table(hist, pm):
    n = int(hist.month.max())
    out = []
    for key in VARIANTS:
        for var in ("loan_rate", "deposit_rate_data_basis"):
            w = hist[hist.variant == key].pivot_table(index=["run_id", "month"], columns="scenario", values=var).reset_index()
            for label, sub in (("cuoi_ky", w[w.month == n]),
                               ("tb_sau_chinh_sach", w[w.month > pm].groupby("run_id").mean(numeric_only=True))):
                for sc in "BC":
                    d = sub[sc] - sub["A"]
                    out.append({"bien_the": key, "thoi_diem": label, "bien": var, "so_sanh": f"{sc}-A",
                                "tb": d.mean(), "sd": d.std(ddof=1), "min": d.min(), "max": d.max()})
    return pd.DataFrame(out)


def compliance_table(bank):
    act = bank[bank.policy_active]
    per = act.groupby(["variant", "scenario", "run_id"]).agg(tl=("policy_complied", "mean"), xs=("policy_probability", "mean")).reset_index()
    return per.groupby(["variant", "scenario"]).agg(ty_le_tuan_thu_tb=("tl", "mean"), ty_le_tuan_thu_sd=("tl", "std"),
                                                    xac_suat_tb=("xs", "mean")).reset_index()


def checks_table(hist, bank, cfg):
    pm = int(cfg["parameters"]["policy_month"])
    rows = []
    for key in VARIANTS:
        h, b = hist[hist.variant == key], bank[bank.variant == key]
        w = h.pivot_table(index=["run_id", "month"], columns="scenario", values="loan_rate")
        pre = w[w.index.get_level_values("month") <= pm]
        post = w[w.index.get_level_values("month") > pm]
        rows.append({
            "bien_the": key,
            "chenh_toi_da_A_B_C_truoc_chinh_sach": float(max((pre["A"] - pre["B"]).abs().max(), (pre["A"] - pre["C"]).abs().max())),
            "vi_pham_B_cao_hon_A": int((post["B"] > post["A"] + 1e-12).sum()),
            "vi_pham_C_cao_hon_A": int((post["C"] > post["A"] + 1e-12).sum()),
            "loan_rate_min": float(b.loan_rate.min()), "loan_rate_max": float(b.loan_rate.max()),
            "deposit_rate_min": float(b.deposit_rate.min()), "deposit_rate_max": float(b.deposit_rate.max()),
            "quan_sat_chan_tran_huy_dong_14": int((b.deposit_rate >= 14 - 1e-9).sum()),
            "ldr_toi_da": float(b.ldr.max()),
        })
    return pd.DataFrame(rows)


def drift_table(bank, cfg):
    """Drift của desired_increase (trước số hạng neo ON) và mức cân bằng ngụ ý: ON + spread + drift/φ."""
    p = cfg["parameters"]
    A = bank[(bank.variant == "none") & (bank.scenario == "A") & (bank.run_id == 0)].sort_values(["bank_id", "month"])
    A["ldr_prev"] = A.groupby("bank_id")["ldr"].shift()
    A = A.dropna(subset=["ldr_prev"])        # tháng 2..18: LDR đầu quý = LDR cuối quý trước
    ldr_target, cap = p.get("deposit_ldr_target", 0.82), p.get("demand_pressure_cap", 0.5)
    drift = p["base_deposit_rate_step"] + p["deposit_competition"] * (A["ldr_prev"] - ldr_target).clip(-cap, cap)
    phi, spread = p["macro_dep_speed"], p["macro_dep_spread"]
    on = pd.read_csv(ROOT / p["macro_on_path"]).set_index("quy").bq_gian_don
    on_mean = float(on.loc["2023Q1":"2026Q2"].mean())
    d = float(drift.mean())
    return pd.DataFrame([{
        "drift_tb_desired_increase": d, "phi": phi, "drift_chia_phi": d / phi, "spread": spread,
        "ON_tb_2023Q1_2026Q2": on_mean, "ON_cuoi_2026Q3": float(on["2026Q3"]),
        "can_bang_ngu_y_ON_tb": on_mean + spread + d / phi,
        "can_bang_ngu_y_ON_2026Q3": float(on["2026Q3"]) + spread + d / phi,
        "r_D_term_tb_khoi_tao": float((bank[(bank.variant == "none") & (bank.scenario == "A") & (bank.run_id == 0) & (bank.month == 1)].deposit_rate).mean()),
    }])


def md_table(df, digits=3):
    cols = list(df.columns)
    out = "| " + " | ".join(cols) + " |\n|" + "|".join(["---"] * len(cols)) + "|\n"
    for _, r in df.iterrows():
        cells = []
        for v in r:
            if isinstance(v, (float, np.floating)):
                cells.append("" if v != v else f"{v:.{digits}f}")
            else:
                cells.append(str(v))
        out += "| " + " | ".join(cells) + " |\n"
    return out


def make_figure(hist, actual, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    surface, ink, ink2, grid = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
    a = actual.sort_values("month")
    nmax = int(hist.month.max())
    quarters = list(hist[(hist.variant == "none") & (hist.scenario == "A") & (hist.run_id == 0)].sort_values("month").quarter)
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.9), dpi=150, facecolor=surface)
    panels = (("loan_rate", "actual_loan_rate", "Lãi suất cho vay (%/năm)"),
              ("deposit_rate_data_basis", "actual_deposit_rate", "Lãi suất huy động, cơ sở dữ liệu (%/năm)"))
    for ax, (col, acol, title) in zip(axes, panels):
        ax.set_facecolor(surface)
        ax.axvspan(14.5, nmax + 0.5, color="#f1f0ec", lw=0)
        ax.grid(axis="y", color=grid, lw=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color(grid)
        ax.tick_params(colors=ink2, labelsize=8.5, length=0)
        ends = []
        for key in ("none", "exogenous", "exogenous_lending045"):
            g = hist[(hist.variant == key) & (hist.scenario == "A")].groupby("month")[col].mean()
            ax.plot(g.index, g.values, color=COLORS[key], lw=2, solid_capstyle="round", zorder=3)
            ax.plot([g.index[-1]], [g.values[-1]], "o", ms=8, color=COLORS[key], mec=surface, mew=2, zorder=4)
            ends.append((g.values[-1], key))
        ax.plot(a["month"], a[acol], color=COLORS["actual"], lw=2.4, solid_capstyle="round", zorder=5)
        ax.plot([a["month"].iloc[-1]], [a[acol].iloc[-1]], "o", ms=8, color=COLORS["actual"], mec=surface, mew=2, zorder=6)
        # nhãn trực tiếp ở cuối đường, tránh chồng nhau
        lo, hi = ax.get_ylim()
        gap = (hi - lo) * 0.055
        ends.sort()
        placed = []
        for y, key in ends:
            yy = y if not placed else max(y, placed[-1] + gap)
            placed.append(yy)
            ax.text(nmax + 0.75, yy, {"none": "none", "exogenous": "exogenous",
                                      "exogenous_lending045": "exo + cho vay 0.45"}[key],
                    color=ink, fontsize=8.5, va="center", ha="left")
        ax.text(a["month"].iloc[-1] + 0.35, a[acol].iloc[-1], "Thực", color=ink, fontsize=8.5, va="center", ha="left", fontweight="bold")
        ax.set_xticks([1, 4, 8, 12, 14, 18])
        ax.set_xticklabels([quarters[i - 1] for i in (1, 4, 8, 12, 14, 18)])
        ax.set_xlim(0.5, nmax + 4.2)
        ax.set_title(title, color=ink, fontsize=11, loc="left", pad=10)
        ax.text(15.6, lo + (hi - lo) * 0.02, "ngoài mẫu\n(chưa có dữ liệu thực)", color=ink2, fontsize=7.5, va="bottom")
    handles = [plt.Line2D([0], [0], color=COLORS[k], lw=2) for k in ("actual", "none", "exogenous", "exogenous_lending045")]
    fig.legend(handles, ["Thực (panel 8 ngân hàng)", "none", "exogenous", "exogenous + lending_on 0.45 (tâm hóa)"],
               loc="lower center", ncol=4, frameon=False, fontsize=9, labelcolor=ink2)
    fig.suptitle("Mô phỏng (kịch bản A, trung bình 60 lần chạy) so với chuỗi thực. Kiểm tra TRONG MẪU.",
                 color=ink2, fontsize=9.5, x=0.012, ha="left", y=0.99)
    fig.tight_layout(rect=(0, 0.07, 1, 0.95))
    fig.savefig(out, facecolor=surface)
    plt.close(fig)


DECISIONS = """
## Quyết định (trưởng nhóm, sau Giai đoạn 8)

1. **`macro_lending_on_coef` giữ 0.** Không dùng số hạng ON trực tiếp trong mục tiêu cho vay: nó làm xấu thước chính (RMSE khử mức của lãi suất cho vay 0.505 → 0.617, hồi phục vượt thực 126%, đáy lệch sớm 3 quý) và ON đã vào mô hình qua chi phí vốn (neo trong phương trình huy động).
2. **Cấu hình chuẩn cho các giai đoạn sau: `macro_driver: exogenous`**, đặt trong `configs/scenarios_macro.yaml` (file ghi đè). `configs/scenarios.yaml` giữ `macro_driver: none` để golden không đổi.
3. **`macro_dep_spread = 1.2723`** (Giai đoạn 7b, mẫu N = 112).
4. **ON sau 2026Q3 giữ 3.946 cho mọi kịch bản.** Không dùng ON thật của Q4/2026 trong kịch bản, vì có thể đã chịu tác động của Công văn 9608/9736; dữ liệu đó để dành cho kiểm định ngoài mẫu.
"""

INTERPRETATION = """
## Diễn giải (viết tay sau khi xem kết quả; các con số lấy từ các bảng ở trên)

**Kiểm tra TRONG MẪU, không phải kỹ năng dự báo.** φ = 0.177 và spread = 1.2723 được ước lượng ở Giai đoạn 7b trên chính dữ liệu 2023Q1-2026Q3 và ON là chuỗi thực; theo 7b, ON giải thích khoảng 62% phương sai within của Δr^D qua thành phần chung theo quý. Nên việc mô phỏng bám sát chuỗi thực hơn là kết quả được kỳ vọng, không phải bằng chứng ngoài mẫu.

**1. Neo ON trong phương trình huy động (`exogenous`) cải thiện rõ hình dạng so với `none`.**
- RMSE khử mức: lãi suất cho vay 0.894 → 0.505, lãi suất huy động (cơ sở dữ liệu) 0.731 → 0.334. Tương quan với chuỗi thực: −0.16 → 0.94 (cho vay) và −0.14 → 0.90 (huy động).
- `none` hầu như không có chữ V (biên độ giảm bằng 0.5% biên độ thực với cho vay, 0% với huy động). `exogenous` tái tạo biên độ giảm bằng 45% (cho vay) và 69% (huy động) biên độ thực, hồi phục 43% và 86%.
- Quý đáy: huy động 2024Q2, trùng thực; cho vay 2024Q4, lệch sớm 1 quý so với thực (2025Q1).
- **Sai số mức vẫn còn:** sai số trung bình (mô hình − thực) là +0.97 điểm % (cho vay) và +0.49 (huy động); RMSE thô 1.09 và 0.59. Biên độ chữ V của lãi suất cho vay vẫn chỉ bằng khoảng 0.4-0.45 lần thực.

**2. Số hạng ON trực tiếp trong mục tiêu cho vay (`macro_lending_on_coef = 0.45`, đã tâm hóa) KHÔNG cải thiện thước chính.**
- RMSE khử mức của cho vay tăng từ 0.505 (chỉ `exogenous`) lên 0.617, tương quan giảm từ 0.94 xuống 0.71. Biên độ giảm bằng 79% thực nhưng **hồi phục bằng 126%** (vượt quá), và đáy lệch sớm tới 3 quý (2024Q2 so với 2025Q1). RMSE thô gần như không đổi (1.09 → 1.10).
- Lãi suất huy động hầu như không đổi so với `exogenous` (RMSE khử mức 0.337 so với 0.334).
- Không tâm hóa (ref = 0, chỉ để tham khảo) thêm khoảng 0.45 × 3.7 ≈ 1.7 điểm % vào mức: sai số trung bình +2.45, RMSE thô 2.57. Kết quả rất nhạy với lựa chọn tâm hóa (và với λ = `pass_through` chưa hiệu chỉnh); hệ số 0.45 ước lượng ở Giai đoạn 7 là cho ON đã trừ trung bình mẫu. Đây là một lựa chọn, không phải kiểm định.

**3. Chênh lệch B−A, C−A ổn định giữa các biến thể của mô hình** (cùng ON thực, cùng dữ liệu, trong mẫu; không phải bằng chứng ngoài mô hình). B−A cuối kỳ là −0.506 (`none`), −0.519 (`exogenous`), −0.523 (+ cho vay 0.45); trung bình sau chính sách −0.411, −0.418, −0.423. C−A cuối kỳ −0.555, −0.570, −0.575. Mục 6 CLAUDE.md đạt ở mọi biến thể (B, C không cao hơn A; A = B = C trước chính sách; lãi suất trong miền; LDR tối đa 1.6). Tỷ lệ tuân thủ tăng nhẹ: 0.947 (`none`), 0.954 (`exogenous`), 0.966 (+ cho vay 0.45); nguyên nhân là `nim_proxy` thay đổi theo mức lãi suất (nhiễu lẫn nhỏ nhưng có thật). Cắt giảm huy động ở kịch bản C: −0.059 (sau chính sách, `exogenous`) so với −0.048 (`none`); khác biệt do số hạng neo ON không bị hạn chế bởi `deposit_cap_factor`.

**4. Mức cân bằng ngụ ý và vùng ngoài mẫu.** Giữ `base_step`, `deposit_competition` và ngưỡng 0.82, drift trung bình của `desired_increase` là 0.033 điểm %/quý, nên mức cân bằng của lãi suất huy động (cơ sở `term`) là `ON + 1.2723 + 0.186`: khoảng 5.20 khi ON bằng trung bình mẫu (3.746) và 5.40 khi ON = 3.946. Lãi suất huy động bình quân khởi tạo (6.39) cao hơn mức này nên giảm dần về phía neo; ở vùng ngoài mẫu (ON giữ 3.946, không có dữ liệu thực) lãi suất huy động (cơ sở dữ liệu) giảm từ 4.87 (2026Q3) xuống 4.58 (2027Q3) và lãi suất cho vay đi ngang khoảng 9.3-9.4. Phần này không đánh giá được bằng dữ liệu.

**Hạn chế.** (i) Trong mẫu như trên. (ii) `macro_dep_spread` lấy từ mẫu N = 112 của 7b (1.272); mẫu N = 104 và 96 cho 1.08 và 1.14, độ nhạy của kết quả theo giá trị này chưa được đo. (iii) Tâm hóa `macro_lending_on_ref` là lựa chọn của người thực hiện để khớp cách ước lượng hệ số 0.45; yêu cầu gốc không nêu. (iv) Sai số mức (+0.97 điểm % ở cho vay) và biên độ chữ V còn thiếu của lãi suất cho vay cần hiệu chỉnh λ, biên mục tiêu, base_step, base_growth và ngưỡng chặn ở Giai đoạn 9; không chỉnh ở đây. (v) Biến vĩ mô ngoại sinh chỉ có một chuỗi ON chung cho mọi ngân hàng. (vi) Hệ số 0.45 là θ/λ của biến thể (d1) với λ = 0.3145 và ước lượng trên khoảng 14 điểm theo quý; (d1) bác bỏ ràng buộc b+γ=1 nên không còn là PT1 của mô hình; mô hình dùng `pass_through = 0.48` nên tác động ON mỗi quý là 0.48 × 0.45 = 0.216 chứ không phải 0.142. Đồng bộ λ và hệ số này là việc của Giai đoạn 9.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", type=int, default=None)
    ap.add_argument("--outdir", default=str(ROOT / "reports/stage8"))
    args = ap.parse_args()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    cfg0 = load_config()
    runs = args.runs or int(cfg0["n_runs"])
    pm = int(cfg0["parameters"]["policy_month"])

    actual = actual_series(out)
    cfg, hist, bank = run_all(runs)
    fit = fit_table(hist, actual)
    eff = effects_table(hist, pm)
    comp = compliance_table(bank)
    chk = checks_table(hist, bank, cfg)
    drift = drift_table(bank, cfg)
    q = hist.groupby(["variant", "scenario", "month", "quarter"])[["loan_rate", "deposit_rate", "deposit_rate_data_basis"]].mean().reset_index()
    q = q.rename(columns={"deposit_rate": "deposit_rate_term_basis"}).merge(
        actual[["month", "actual_loan_rate", "actual_deposit_rate"]], on="month", how="left")

    q.to_csv(out / "quarterly_stage8.csv", index=False)
    fit.to_csv(out / "fit_vs_actual_stage8.csv", index=False)
    eff.to_csv(out / "effects_stage8.csv", index=False)
    comp.to_csv(out / "compliance_stage8.csv", index=False)
    chk.to_csv(out / "checks_stage8.csv", index=False)
    drift.to_csv(out / "drift_equilibrium_stage8.csv", index=False)
    make_figure(hist, actual, out / "fig_mo_phong_vs_thuc.png")

    labels = {k: v[0] for k, v in VARIANTS.items()}
    md = ["# Giai đoạn 8: biến vĩ mô ngoại sinh trong phương trình huy động (sinh tự động)\n",
          f"> {runs} lần chạy mỗi kịch bản, seed = base_seed + run_id (cùng seed cho mọi biến thể), dữ liệu 8 ngân hàng thật, khởi tạo 2023Q1, cơ sở `term`, 18 quý, chính sách từ bước {pm + 1} (Q4/2026). "
          "**Mặc định của dự án vẫn là `macro_driver: none`.** Tham số chưa hiệu chỉnh lại (λ, δ, base_step, base_growth, ngưỡng chặn: Giai đoạn 9). "
          "Mọi so sánh với chuỗi thực là **kiểm tra TRONG MẪU** (φ, spread lấy từ chính dữ liệu 2023Q1-2026Q3 ở Giai đoạn 7b), không phải dự báo ngoài mẫu và không phải tác động chính sách thực tế.\n",
          "Biến thể: " + "; ".join(f"`{k}` = {v}" for k, v in labels.items()) + ". "
          "Biến thể cuối chỉ để tham khảo vì tôi chọn tâm hóa số hạng ON cho cho vay (hệ số 0.45 ước lượng trên ON đã trừ trung bình mẫu); nó KHÔNG phải biến thể được yêu cầu.\n",
          "Lãi suất huy động ở cơ sở dữ liệu = `deposit_rate × (1 − casa)` gia quyền theo tiền gửi (cột `deposit_rate` của mô hình ở cơ sở `term` là lãi suất kỳ hạn). "
          "Kịch bản A không dùng số ngẫu nhiên nên 60 lần chạy A giống hệt nhau; chuỗi A trước chính sách trùng B, C.\n",
          "## Độ khớp với chuỗi thực 2023Q2-2026Q3 (14 quý; thước chính: RMSE khử mức, biên độ chữ V, quý đáy)\n",
          "`RMSE_khu_muc` = độ lệch chuẩn của sai số (đã bỏ sai số trung bình); `ty_le_giam` và `ty_le_hoi_phuc` = biên độ của mô hình chia biên độ thực (giảm từ quý đầu xuống đáy; hồi phục từ đáy tới 2026Q3). "
          "Thước phụ: `RMSE_tho`, `sai_so_tb` (mô hình − thực).\n",
          md_table(fit),
          "![Mô phỏng so với thực](fig_mo_phong_vs_thuc.png)\n",
          "## Tác động chính sách (B−A, C−A; chênh theo cặp cùng seed, điểm %/năm)\n", md_table(eff, 4),
          "## Tuân thủ chỉ đạo (các quý có chính sách)\n", md_table(comp, 4),
          "## Kiểm tra hợp lý kinh tế (mục 6 CLAUDE.md)\n", md_table(chk, 6),
          "## Drift và mức cân bằng ngụ ý khi giữ nguyên base_step và deposit_competition\n",
          "Với `macro_driver: exogenous` mức cân bằng của lãi suất huy động (cơ sở `term`) là `ON + spread + drift/φ`, trong đó drift là trung bình của "
          "`desired_increase = base_step + deposit_competition·clip(LDR − 0.82, ±0.5)` (trước số hạng neo ON). Giữ drift thì mức cân bằng cao hơn `ON + spread` một khoảng `drift/φ`.\n",
          md_table(drift, 4)]
    for key in ("none", "exogenous", "exogenous_lending045"):
        sub = q[(q.variant == key) & (q.scenario == "A")].sort_values("month")
        md += [f"## Chuỗi theo quý, kịch bản A: `{key}`\n",
               md_table(sub[["month", "quarter", "actual_loan_rate", "loan_rate", "actual_deposit_rate",
                             "deposit_rate_data_basis", "deposit_rate_term_basis"]], 3)]
    md.append(INTERPRETATION)
    md.append(DECISIONS)
    md.append("\nFile: quarterly_stage8.csv, fit_vs_actual_stage8.csv, effects_stage8.csv, compliance_stage8.csv, checks_stage8.csv, drift_equilibrium_stage8.csv, fig_mo_phong_vs_thuc.png, C_lai_suat_thuc_te_tu_panel.csv.\n")
    (out / "summary_stage8.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Đã ghi kết quả vào {out}")


if __name__ == "__main__":
    main()
