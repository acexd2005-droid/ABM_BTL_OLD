"""Giai đoạn 9: hiệu chỉnh bằng mô phỏng (kịch bản A) và kiểm định ngoài mẫu lịch sử.

Phương pháp chốt TRƯỚC khi chạy: reports/calibration/stage9/DANG_KY_TRUOC.md. Tóm tắt:
  Bước 1 (quy tắc, không tối ưu): tăng trưởng nền = trung bình tăng trưởng quý của TỔNG 8 NH trong cửa sổ
          2023Q2–2025Q2; ngưỡng chặn = phân vị 2.5%/97.5% theo ngân hàng-quý. Bốn biến thể:
          {bất đối xứng (chính) | đối xứng} × {đủ dữ liệu (chính) | loại quan sát bất thường đã biết}.
  Bước 2 (lưới, kịch bản A, tất định): λ × biên tổng × base_step × δ × ngưỡng LDR = 1536 bộ / biến thể.
          Hàm mục tiêu J = 0.5·RMSE_L + 0.5·RMSE_D (RMSE thô, month 1–9, cơ sở dữ liệu cho huy động).
  Bước 3 (ngoài mẫu, month 10–14): so bộ tốt nhất với cấu hình GĐ8 và hai mốc ngây thơ.
  Bước 4: ghi configs/scenarios_calibrated.yaml; mục 6 CLAUDE.md (A/B/C, 10 lần chạy); ngưỡng có đạt tới không.

Đây là đối chiếu lịch sử; mô hình (và mốc ON) được cấp ON THỰC trong cửa sổ ngoài mẫu (lợi thế thông tin),
nên RMSE ngoài mẫu không phải dự báo thật. A/B/C không phải tác động chính sách thực tế.

Chạy: python -m src.calibration.calibrate_stage9 [--outdir reports/calibration/stage9] [--no-yaml]
Tất định (A không dùng số ngẫu nhiên; B/C dùng seed = base_seed + i); chạy lại cho file giống hệt.
"""

import argparse
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..analysis.compare_deposit_basis import actual_series
from ..analysis.experiments import load_config
from ..core.model import ABMModel

ROOT = Path(__file__).resolve().parents[2]
BANKS = ROOT / "data/clean/abm_initial_8nganhang_2023Q1.csv"
PANEL = ROOT / "data/clean/abm_panel_8nganhang_2023Q1_2026Q3.csv"
MACRO_CFG = ROOT / "configs/scenarios_macro.yaml"
CALIBRATED_CFG = ROOT / "configs/scenarios_calibrated.yaml"
OUTDIR = ROOT / "reports/calibration/stage9"
OUTLIERS = ROOT / "reports/calibration/outliers_stage7.csv"

INITIAL = pd.Period("2023Q1", freq="Q")
WINDOW = (pd.Period("2023Q2", freq="Q"), pd.Period("2025Q2", freq="Q"))   # month 1..9
OOS = (pd.Period("2025Q3", freq="Q"), pd.Period("2026Q3", freq="Q"))      # month 10..14
CAL_MONTHS = (1, 9)
OOS_MONTHS = (10, 14)
N_SIM = 14
# Quan sát bất thường đã biết (outliers_stage7.csv, nhãn "HDBank 2023Q2 / MB Bank quý 4") nằm trong cửa sổ
KNOWN_ANOMALIES = (("HDBank", "2023Q2"), ("MB Bank", "2023Q4"), ("MB Bank", "2024Q4"))
NAIVE_ON_COEF = 0.45          # LO_TRINH GD9 Bước 3 (iii): hệ số dài hạn ON, cùng giá trị Giai đoạn 7 (d1)
LAMBDA_CI_STAGE7 = (0.158, 0.395)   # estimates_stage7.md, PT1 biến thể (c), CI bootstrap 95%
N_RUNS_SECTION6 = 10
SECOND_SEED_OFFSET = 7        # seed thứ hai để kiểm tra A tất định

GRID = {
    "pass_through": (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45),
    "total_margin": (3.8, 4.0, 4.2, 4.4, 4.6, 4.8),
    "base_deposit_rate_step": (0.0, 0.006, 0.012, 0.018),
    "deposit_competition": (0.07, 0.3, 0.7, 1.2),
    "ldr_choice": ("0.82", "ldr_mean"),
}
# Phụ lục DANG_KY_TRUOC.md (thêm sau lưới chính, CHỈ chẩn đoán): lưới mở rộng quanh biên
GRID_EXT = {
    "pass_through": tuple(round(0.10 + 0.05 * i, 2) for i in range(19)),   # 0.10 .. 1.00
    "total_margin": (3.0, 3.2, 3.4, 3.6, 3.8),
    "base_deposit_rate_step": (0.0,),
    "deposit_competition": (0.0, 0.035, 0.07),
    "ldr_choice": ("ldr_mean",),
}
VARIANTS = {   # khóa: (bất đối xứng?, loại bất thường?)
    "batdoixung_daydu": (True, False),
    "doixung_daydu": (False, False),
    "batdoixung_loaibatthuong": (True, True),
    "doixung_loaibatthuong": (False, True),
}
MAIN_VARIANT = "batdoixung_daydu"
GROWTH_KEYS = ("depositor_base_growth", "depositor_min_growth", "depositor_max_growth",
               "borrower_base_growth", "borrower_growth_min", "borrower_growth_max")
# Khóa GD9a + khóa giai đoạn 9 ghi tường minh trong scenarios_calibrated.yaml (không dựa vào mặc định code)
EXPLICIT_KEYS = ("target_margin", "funding_cost_add", "deposit_ldr_target", "demand_pressure_cap",
                 "depositor_base_growth", "depositor_max_growth", "depositor_min_growth",
                 "borrower_growth_min", "borrower_growth_max", "borrower_base_growth",
                 "compliance_pressure_coef", "compliance_pressure_center", "compliance_margin_coef",
                 "compliance_prob_min", "compliance_prob_max",
                 "pass_through", "base_deposit_rate_step", "deposit_competition", "loan_spread_add",
                 "depositor_sensitivity", "borrower_elasticity", "borrower_reference_rate",
                 "policy_month", "policy_pressure", "policy_step", "deposit_cap_factor", "max_loan_to_deposit",
                 "margin_floor", "macro_driver", "macro_dep_speed", "macro_dep_spread", "macro_on_path",
                 "macro_lending_on_coef", "macro_lending_on_ref", "deposit_rate_basis", "adaptive_learning")


# ======================================================================
# Dữ liệu
# ======================================================================

def load_panel():
    p = pd.read_csv(PANEL, encoding="utf-8-sig")
    p["per"] = pd.PeriodIndex(p["period"], freq="Q")
    p = p.sort_values(["bank_id", "per"]).reset_index(drop=True)
    g = p.groupby("bank_id")
    p["g_dep"] = g["deposits"].pct_change()
    p["g_loan"] = g["loans"].pct_change()
    p["ldr"] = p["loans"] / p["deposits"]
    p["anomaly"] = [(b, str(q)) in KNOWN_ANOMALIES for b, q in zip(p.bank_id, p.per)]
    return p


def check_anomalies_listed():
    """Các quan sát bất thường dùng ở đây phải nằm trong outliers_stage7.csv (nhãn yêu cầu kiểm tra)."""
    o = pd.read_csv(OUTLIERS)
    listed = set(zip(o.bank_id, o.period))
    missing = [a for a in KNOWN_ANOMALIES if a not in listed]
    if missing:
        raise ValueError(f"Quan sát bất thường không có trong outliers_stage7.csv: {missing}")


def in_window(per):
    return (per >= WINDOW[0]) & (per <= WINDOW[1])


def aggregate_growth(p, col, exclude):
    """Tăng trưởng quý của tổng 8 NH (sum_t/sum_{t-1} − 1). Loại bất thường: bỏ NH đó ở cả t và t−1 của quý đó."""
    out = []
    for per in pd.period_range(WINDOW[0], WINDOW[1], freq="Q"):
        cur = p[p.per == per]
        if exclude:
            cur = cur[~cur.anomaly]
        prev = p[(p.per == per - 1) & p.bank_id.isin(cur.bank_id)]
        out.append(cur[col].sum() / prev[col].sum() - 1)
    return np.array(out)


def growth_rules(p, asymmetric, exclude):
    w = p[in_window(p.per)]
    if exclude:
        w = w[~w.anomaly]
    dep_lo, dep_hi = (float(x) for x in np.percentile(w.g_dep, [2.5, 97.5]))
    loan_lo, loan_hi = (float(x) for x in np.percentile(w.g_loan, [2.5, 97.5]))
    params = {
        "depositor_base_growth": float(aggregate_growth(p, "deposits", exclude).mean()),
        "borrower_base_growth": float(aggregate_growth(p, "loans", exclude).mean()),
        "borrower_growth_min": loan_lo,
        "borrower_growth_max": loan_hi,
    }
    if asymmetric:
        params["depositor_min_growth"] = dep_lo
        params["depositor_max_growth"] = dep_hi
    else:
        params["depositor_min_growth"] = None
        params["depositor_max_growth"] = max(abs(dep_lo), abs(dep_hi))
    stats = {"n_obs": int(len(w)), "dep_p025": dep_lo, "dep_p975": dep_hi, "loan_p025": loan_lo,
             "loan_p975": loan_hi, "dep_mean_bank_quarter": float(w.g_dep.mean()),
             "loan_mean_bank_quarter": float(w.g_loan.mean())}
    return params, stats


def ldr_mean(p):
    return float(p[in_window(p.per)].ldr.mean())


def on_series():
    on = pd.read_csv(ROOT / "data/raw/sbv_lnh_qua_dem_theo_quy.csv")
    return dict(zip(on.quy, on.bq_gian_don.astype(float)))


# ======================================================================
# Mô phỏng
# ======================================================================

def base_params():
    cfg = load_config(MACRO_CFG)
    return cfg, dict(cfg["parameters"])


def simulate(params, rows, scenario="A", seed=None, n=N_SIM, cfg=None):
    """Trả (loan_rate gia quyền dư nợ, deposit_rate cơ sở dữ liệu gia quyền tiền gửi), mảng theo month 1..n."""
    seed = int(cfg["base_seed"]) if seed is None else seed
    m = ABMModel(scenario, n, seed, params, rows)
    m.run()
    loan = np.array([h["loan_rate"] for h in m.history])
    num = np.zeros(n)
    den = np.zeros(n)
    for b in m.bank_history:
        k = b["month"] - 1
        num[k] += b["deposit_rate"] * (1 - b["casa_ratio"]) * b["deposits"]
        den[k] += b["deposits"]
    return loan, num / den, m


def rmse(e):
    e = np.asarray(e, float)
    return float(np.sqrt((e ** 2).mean()))


def objective(loan, dep, act_loan, act_dep):
    a, b = CAL_MONTHS
    sl = slice(a - 1, b)
    rl = rmse(loan[sl] - act_loan[sl])
    rd = rmse(dep[sl] - act_dep[sl])
    return 0.5 * rl + 0.5 * rd, rl, rd


def grid_points(grid=GRID):
    keys = list(grid)
    return [dict(zip(keys, v)) for v in itertools.product(*(grid[k] for k in keys))]


def apply_point(params, point, ldr_value):
    q = dict(params)
    q["pass_through"] = point["pass_through"]
    q["target_margin"] = round(point["total_margin"] - float(q["loan_spread_add"]), 10)
    q["base_deposit_rate_step"] = point["base_deposit_rate_step"]
    q["deposit_competition"] = point["deposit_competition"]
    q["deposit_ldr_target"] = 0.82 if point["ldr_choice"] == "0.82" else ldr_value
    return q


def run_grid(params, rows, act_loan, act_dep, ldr_value, cfg, grid=GRID):
    out = []
    for i, pt in enumerate(grid_points(grid)):
        q = apply_point(params, pt, ldr_value)
        loan, dep, _ = simulate(q, rows, cfg=cfg, n=CAL_MONTHS[1])
        j, rl, rd = objective(loan, dep, act_loan, act_dep)
        out.append({"grid_index": i, **pt, "target_margin": q["target_margin"],
                    "deposit_ldr_target": q["deposit_ldr_target"], "J": j, "RMSE_L_cal": rl, "RMSE_D_cal": rd})
    return pd.DataFrame(out)


def best_row(g):
    # argmin J; hòa thì lấy grid_index nhỏ nhất (thứ tự lưới)
    return g.sort_values(["J", "grid_index"], kind="mergesort").iloc[0]


def params_of(params, row, ldr_value):
    return apply_point(params, {k: row[k] for k in GRID}, ldr_value)


# ======================================================================
# Báo cáo lưới
# ======================================================================

def profiles(g):
    rows = []
    for k in GRID:
        best = g.groupby(k)["J"].min()
        for v, j in best.items():
            rows.append({"tham_so": k, "gia_tri": v, "J_min": j})
    df = pd.DataFrame(rows)
    spread = df.groupby("tham_so")["J_min"].agg(lambda s: s.max() - s.min()).rename("bien_do_J_min")
    return df.merge(spread, on="tham_so")


def top_corr(g, n=50):
    t = g.sort_values(["J", "grid_index"], kind="mergesort").head(n).copy()
    t["ldr_is_mean"] = (t.ldr_choice == "ldr_mean").astype(float)
    cols = ["pass_through", "total_margin", "base_deposit_rate_step", "deposit_competition", "ldr_is_mean"]
    c = t[cols].astype(float)
    # cột hằng (nếu có) cho tương quan NaN: giữ NaN, ghi chú trong md
    return c.corr().reset_index().rename(columns={"index": "tham_so"})


# ======================================================================
# Ngoài mẫu
# ======================================================================

def v_metrics(x, quarters):
    x = np.asarray(x, float)
    i = int(np.argmin(x))
    return {"giam": x[0] - x[i], "hoi_phuc": x[-1] - x[i], "quy_day": quarters[i]}


def naive_paths(act, on):
    """(ii) giữ 2025Q2; (iii) r_t = r_2025Q2 + 0.45·(ON_{t−1} − ON_2025Q1). Trả dict tên -> (loan, dep) cho month 10..14."""
    a = act.set_index("month")
    m0 = CAL_MONTHS[1]
    months = range(OOS_MONTHS[0], OOS_MONTHS[1] + 1)
    hold = (np.full(len(months), a.loc[m0, "actual_loan_rate"]), np.full(len(months), a.loc[m0, "actual_deposit_rate"]))
    on_ref = on[str(WINDOW[1] - 1)]
    shift = np.array([NAIVE_ON_COEF * (on[str(INITIAL + m - 1)] - on_ref) for m in months])
    onp = (hold[0] + shift, hold[1] + shift)
    return {"ngay_tho_giu_2025Q2": hold, "ngay_tho_ON": onp}


def oos_table(model_paths, naive, act):
    a = act.sort_values("month").reset_index(drop=True)
    quarters = list(a.quarter)
    lo, hi = OOS_MONTHS
    sl = slice(lo - 1, hi)
    oos_q = quarters[sl]
    rows = []
    series = {k: v for k, v in model_paths.items()}
    for name, (ln, dp) in naive.items():
        series[name] = (np.r_[np.full(lo - 1, np.nan), ln], np.r_[np.full(lo - 1, np.nan), dp])
    for name, (loan, dep) in series.items():
        for lab, x, acol in (("cho_vay", loan, "actual_loan_rate"), ("huy_dong", dep, "actual_deposit_rate")):
            y = a[acol].to_numpy()
            e = np.asarray(x)[sl] - y[sl]
            xo, yo = np.asarray(x)[sl], y[sl]
            row = {"cau_hinh": name, "chuoi": lab, "RMSE_tho_ngoai_mau": rmse(e),
                   "RMSE_khu_muc_ngoai_mau": float(np.std(e, ddof=0)), "sai_so_tb_ngoai_mau": float(e.mean()),
                   "bien_do_ngoai_mau_mo_hinh": float(xo.max() - xo.min()),
                   "bien_do_ngoai_mau_thuc": float(yo.max() - yo.min()),
                   "quy_day_ngoai_mau_mo_hinh": oos_q[int(np.argmin(xo))],
                   "quy_day_ngoai_mau_thuc": oos_q[int(np.argmin(yo))]}
            if not np.isnan(np.asarray(x)[0]):
                c = slice(CAL_MONTHS[0] - 1, CAL_MONTHS[1])
                ec = np.asarray(x)[c] - y[c]
                vm, va = v_metrics(x, quarters), v_metrics(y, quarters)
                row.update({"RMSE_tho_trong_mau": rmse(ec), "RMSE_khu_muc_trong_mau": float(np.std(ec, ddof=0)),
                            "RMSE_tho_toan_chuoi": rmse(np.asarray(x) - y),
                            "RMSE_khu_muc_toan_chuoi": float(np.std(np.asarray(x) - y, ddof=0)),
                            "ty_le_giam_V_toan_chuoi": vm["giam"] / va["giam"],
                            "ty_le_hoi_phuc_V_toan_chuoi": vm["hoi_phuc"] / va["hoi_phuc"],
                            "quy_day_toan_chuoi_mo_hinh": vm["quy_day"], "quy_day_toan_chuoi_thuc": va["quy_day"]})
            rows.append(row)
    return pd.DataFrame(rows)


# ======================================================================
# Ngưỡng có đạt tới không, chạm biên
# ======================================================================

def threshold_table(params, rows, cfg):
    """Kịch bản A, 18 quý (và riêng month 1..14). Ngưỡng LDR: LDR đầu quý so với deposit_ldr_target;
    biên mục tiêu: loan_rate − lagged_funding_cost (đầu quý) so với target_margin + loan_spread_add."""
    m = ABMModel("A", int(cfg["n_months"]), int(cfg["base_seed"]), params, rows)
    recs = []
    for _ in range(m.n_months):
        pre = {b.bank_id: (b.loans / b.deposits, b.lagged_funding_cost) for b in m.banks}
        pre_dep = {b.bank_id: b.deposits for b in m.banks}
        pre_loan = {b.bank_id: b.loans for b in m.banks}
        month = m.month + 1
        m.step()
        for b in m.banks:
            ldr0, lfc = pre[b.bank_id]
            recs.append({"month": month, "bank_id": b.bank_id, "ldr_dau_quy": ldr0,
                         "bien_thuc": b.loan_rate - lfc, "bien_muc_tieu": b.target_margin + m.loan_spread_add,
                         "g_dep": b.deposits / pre_dep[b.bank_id] - 1,
                         "g_loan_desired": m.borrower.desired_growth(b.loan_rate),
                         "g_loan": b.loans / pre_loan[b.bank_id] - 1,
                         "ldr_cuoi": b.loans / b.deposits})
    d = pd.DataFrame(recs)
    t, cap = m.deposit_ldr_target, m.demand_pressure_cap
    dep_lo = -m.depositor.max_growth if m.depositor.min_growth is None else m.depositor.min_growth
    eps = 1e-12
    out = []
    for lab, sub in (("month_1_14", d[d.month <= N_SIM]), ("month_1_18", d)):
        gap = sub.bien_thuc - sub.bien_muc_tieu
        out.append({
            "pham_vi": lab, "n_ngan_hang_quy": len(sub), "deposit_ldr_target": t,
            "ldr_dau_quy_min": sub.ldr_dau_quy.min(), "ldr_dau_quy_max": sub.ldr_dau_quy.max(),
            "ty_le_ldr_tren_nguong": float((sub.ldr_dau_quy > t).mean()),
            "so_ngan_hang_co_ca_hai_phia_nguong": int(sub.groupby("bank_id").ldr_dau_quy
                                                     .agg(lambda s: (s > t).any() and (s <= t).any()).sum()),
            "ty_le_ap_luc_cham_chan": float(((sub.ldr_dau_quy - t).abs() >= cap - eps).mean()),
            "bien_muc_tieu": float(sub.bien_muc_tieu.iloc[0]),
            "bien_thuc_tb": float(sub.bien_thuc.mean()), "bien_thuc_min": float(sub.bien_thuc.min()),
            "bien_thuc_max": float(sub.bien_thuc.max()),
            "chenh_bien_thuc_muc_tieu_tb": float(gap.mean()),
            "chenh_bien_tuyet_doi_tb_quy_cuoi": float(gap[sub.month == sub.month.max()].abs().mean()),
            "ty_le_bien_thuc_vuot_muc_tieu": float((gap >= 0).mean()),
            "ty_le_tg_cham_tran": float((sub.g_dep >= m.depositor.max_growth - eps).mean()),
            "ty_le_tg_cham_san": float((sub.g_dep <= dep_lo + eps).mean()),
            "ty_le_dn_mong_muon_cham_tran": float((sub.g_loan_desired >= m.borrower.growth_max - eps).mean()),
            "ty_le_dn_mong_muon_cham_san": float((sub.g_loan_desired <= m.borrower.growth_min + eps).mean()),
            "ty_le_cham_tran_ldr": float((sub.ldr_cuoi >= m.max_loan_to_deposit - 1e-9).mean()),
        })
    return pd.DataFrame(out)


def growth_ldr_table(configs, rows, panel, cfg):
    """Tăng trưởng tổng tiền gửi/dư nợ (TB theo quý) và LDR theo ngân hàng cuối 2025Q2/2026Q3: mô hình (A) so với thực."""
    agg = panel.groupby("per")[["deposits", "loans"]].sum()
    g = agg.pct_change()
    rows_out = []

    def add(name, dep_g, loan_g, ldr9, ldr14):
        for lab, sl in (("trong_mau_1_9", slice(0, 9)), ("ngoai_mau_10_14", slice(9, 14))):
            rows_out.append({"cau_hinh": name, "pham_vi": lab, "tang_truong_tien_gui_tb": float(np.mean(dep_g[sl])),
                             "tang_truong_du_no_tb": float(np.mean(loan_g[sl]))})
        for q, ldr in (("2025Q2", ldr9), ("2026Q3", ldr14)):
            for bank, v in sorted(ldr.items()):
                rows_out.append({"cau_hinh": name, "pham_vi": f"LDR_{q}", "bank_id": bank, "ldr": float(v)})

    per = pd.period_range(WINDOW[0], OOS[1], freq="Q")
    lp = panel.set_index(["per", "bank_id"]).ldr
    add("thuc_te", g.loc[per, "deposits"].to_numpy(), g.loc[per, "loans"].to_numpy(),
        lp.loc[WINDOW[1]].to_dict(), lp.loc[OOS[1]].to_dict())
    for name, params in configs.items():
        m = ABMModel("A", N_SIM, int(cfg["base_seed"]), params, rows)
        m.run()
        h = pd.DataFrame(m.history)
        b = pd.DataFrame(m.bank_history)
        add(name, h.deposit_growth.to_numpy(), h.credit_growth.to_numpy(),
            b[b.month == 9].set_index("bank_id").ldr.to_dict(), b[b.month == N_SIM].set_index("bank_id").ldr.to_dict())
    return pd.DataFrame(rows_out)


def growth_offset_diagnostic(best_params, gl, rows, act_loan, act_dep, cfg):
    """CHẨN ĐOÁN (không đổi bộ chính): cộng vào base_growth phần chênh tăng trưởng tổng trong mẫu (thực − mô hình),
    một lần, để xem độ khớp lãi suất và LDR có nhạy với lệch tăng trưởng tổng không."""
    t = gl[gl.pham_vi == "trong_mau_1_9"].set_index("cau_hinh")
    key = "hieu_chinh_" + MAIN_VARIANT
    dd = t.loc["thuc_te", "tang_truong_tien_gui_tb"] - t.loc[key, "tang_truong_tien_gui_tb"]
    dl = t.loc["thuc_te", "tang_truong_du_no_tb"] - t.loc[key, "tang_truong_du_no_tb"]
    out = []
    for name, q in (("bo_chinh", dict(best_params)),
                    ("bu_tang_truong", {**best_params,
                                        "depositor_base_growth": best_params["depositor_base_growth"] + dd,
                                        "borrower_base_growth": best_params["borrower_base_growth"] + dl})):
        loan, dep, m = simulate(q, rows, cfg=cfg)
        j, rl, rd = objective(loan, dep, act_loan, act_dep)
        h = pd.DataFrame(m.history)
        b = pd.DataFrame(m.bank_history)
        out.append({"chan_doan": name, "depositor_base_growth": q["depositor_base_growth"],
                    "borrower_base_growth": q["borrower_base_growth"], "J": j, "RMSE_L_cal": rl, "RMSE_D_cal": rd,
                    "tang_truong_tien_gui_tb_1_9": float(h.deposit_growth.iloc[:9].mean()),
                    "tang_truong_du_no_tb_1_9": float(h.credit_growth.iloc[:9].mean()),
                    "ldr_max_month_14": float(b[b.month == N_SIM].ldr.max()),
                    "ty_le_cham_tran_ldr_1_14": float((b.ldr >= m.max_loan_to_deposit - 1e-9).mean())})
    return pd.DataFrame(out)


# ======================================================================
# Mục 6 CLAUDE.md
# ======================================================================

def section6(cfg, rows):
    p = dict(cfg["parameters"])
    policy_q = int(p["policy_month"]) + 1
    worst = {"B": -1e9, "C": -1e9}
    pre_diff = 0.0
    lo = {"loan": 1e9, "dep": 1e9}
    hi = {"loan": -1e9, "dep": -1e9}
    slack = -1e9
    post_mean = {"A": [], "B": [], "C": []}
    for i in range(N_RUNS_SECTION6):
        seed = int(cfg["base_seed"]) + i
        res = {}
        for sc in "ABC":
            m = ABMModel(sc, int(cfg["n_months"]), seed, p, rows)
            m.run()
            res[sc] = (pd.DataFrame(m.history), pd.DataFrame(m.bank_history))
        hA, bA = res["A"]
        for sc in "ABC":
            h, b = res[sc]
            post = h[h.month >= policy_q]
            post_mean[sc].append(float(post.loan_rate.mean()))
            if sc != "A":
                worst[sc] = max(worst[sc], float((post.loan_rate.values - hA[hA.month >= policy_q].loan_rate.values).max()))
                num = ["deposits", "loans", "deposit_rate", "loan_rate"]
                pre = b[b.month < policy_q].reset_index(drop=True)[num]
                preA = bA[bA.month < policy_q].reset_index(drop=True)[num]
                pre_diff = max(pre_diff, float((pre - preA).abs().max().max()))
            lo["loan"] = min(lo["loan"], float(b.loan_rate.min()))
            hi["loan"] = max(hi["loan"], float(b.loan_rate.max()))
            lo["dep"] = min(lo["dep"], float(b.deposit_rate.min()))
            hi["dep"] = max(hi["dep"], float(b.deposit_rate.max()))
            slack = max(slack, float((b.loans - b.deposits * float(p["max_loan_to_deposit"])).max()))
    m = ABMModel("A", 1, int(cfg["base_seed"]), p, rows)
    lag0 = [b.lagged_funding_cost for b in m.banks]
    r0 = [b.loan_rate for b in m.banks]
    m.step()
    err_lag = err_now = 0.0
    for b, fc0, r in zip(m.banks, lag0, r0):
        pred_lag = r + m.pass_through * (fc0 + b.target_margin + m.loan_spread_add - r)
        pred_now = r + m.pass_through * (b.funding_cost + b.target_margin + m.loan_spread_add - r)
        err_lag = max(err_lag, abs(b.loan_rate - pred_lag))
        err_now = max(err_now, abs(b.loan_rate - pred_now))
    out = {
        "runs": N_RUNS_SECTION6, "max_B_minus_A_after": worst["B"], "max_C_minus_A_after": worst["C"],
        "mean_loan_after_A": float(np.mean(post_mean["A"])), "mean_loan_after_B": float(np.mean(post_mean["B"])),
        "mean_loan_after_C": float(np.mean(post_mean["C"])),
        "max_abs_diff_before": pre_diff, "loan_min": lo["loan"], "loan_max": hi["loan"],
        "dep_min": lo["dep"], "dep_max": hi["dep"], "max_loans_minus_limit": slack,
        "lag_err_lagged": err_lag, "lag_err_current": err_now,
    }
    out["pass"] = bool(worst["B"] <= 1e-12 and worst["C"] <= 1e-12 and pre_diff == 0.0
                       and 0 <= lo["loan"] and hi["loan"] <= 20 and 0 <= lo["dep"] and hi["dep"] <= 14
                       and slack <= 1e-9 and err_lag < 1e-12 and err_now > err_lag)
    return out


# ======================================================================
# Ghi YAML hiệu chỉnh
# ======================================================================

def _fmt(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return v
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    return repr(float(v))   # đủ chữ số: đọc lại cho đúng bộ tốt nhất


def write_calibrated_yaml(path, params, best, stats, ldr_value, lam_in_ci):
    src = {
        "pass_through": f"GD9 lưới (argmin J, cửa sổ 2023Q2-2025Q2); CI GĐ7 (c) [0.158; 0.395]: {'trong' if lam_in_ci else 'NGOÀI'} CI",
        "target_margin": f"GD9 lưới: biên tổng {best['total_margin']} − loan_spread_add 1.35",
        "base_deposit_rate_step": "GD9 lưới (argmin J)",
        "deposit_competition": "GD9 lưới (argmin J)",
        "deposit_ldr_target": ("GD9 lưới: LDR bình quân ngân hàng-quý 2023Q2-2025Q2 = " + f"{ldr_value:.6f}"
                               if best["ldr_choice"] == "ldr_mean" else "GD9 lưới: giữ 0.82"),
        "depositor_base_growth": "GD9 Bước 1: TB tăng trưởng quý tổng tiền gửi 8 NH 2023Q2-2025Q2 (quy tắc, không tối ưu)",
        "depositor_min_growth": f"GD9 Bước 1: P2.5 tăng trưởng tiền gửi ngân hàng-quý (N = {stats['n_obs']}); khóa tùy chọn GD9",
        "depositor_max_growth": f"GD9 Bước 1: P97.5 tăng trưởng tiền gửi ngân hàng-quý (N = {stats['n_obs']})",
        "borrower_base_growth": "GD9 Bước 1: TB tăng trưởng quý tổng dư nợ 8 NH 2023Q2-2025Q2 (tại borrower_reference_rate)",
        "borrower_growth_min": f"GD9 Bước 1: P2.5 tăng trưởng dư nợ ngân hàng-quý (N = {stats['n_obs']})",
        "borrower_growth_max": f"GD9 Bước 1: P97.5 tăng trưởng dư nợ ngân hàng-quý (N = {stats['n_obs']})",
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
        "# FILE GHI ĐÈ lên scenarios.yaml (sinh tự động bởi `python -m src.calibration.calibrate_stage9`, KHÔNG sửa tay).",
        "# Bộ tham số hiệu chỉnh Giai đoạn 9 (D5). Nền: scenarios.yaml + scenarios_macro.yaml (D2).",
        "# Phương pháp: reports/calibration/stage9/DANG_KY_TRUOC.md; kết quả: reports/calibration/stage9/summary_stage9.md.",
        "# Hàm mục tiêu: J = 0.5*RMSE thô LS cho vay + 0.5*RMSE thô LS huy động (cơ sở dữ liệu), kịch bản A, 2023Q2-2025Q2.",
        "# Mọi khóa hành vi (gồm 13 khóa GD9a) ghi TƯỜNG MINH ở đây, không dựa vào mặc định trong code.",
        "# Đây là đối chiếu trong mẫu; không phải dự báo và không phải tác động chính sách thực tế.",
        "# Chạy: python main.py --config configs/scenarios_calibrated.yaml",
        "parameters:",
    ]
    for k in EXPLICIT_KEYS:
        note = src.get(k) or assumption.get(k) or kept
        lines.append(f"  {k}: {_fmt(params[k])}    # {note}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ======================================================================
# Chính
# ======================================================================

def md_table(df, digits=4):
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        cells = []
        for v in r:
            if isinstance(v, (float, np.floating)):
                cells.append("" if v != v else f"{v:.{digits}f}")
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outdir", default=str(OUTDIR))
    ap.add_argument("--no-yaml", action="store_true", help="không ghi configs/scenarios_calibrated.yaml")
    args = ap.parse_args()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    check_anomalies_listed()
    cfg, base = base_params()
    rows = pd.read_csv(BANKS).to_dict("records")
    panel = load_panel()
    act = actual_series(out).sort_values("month").reset_index(drop=True)
    act = act[act.month <= N_SIM]
    act_loan, act_dep = act.actual_loan_rate.to_numpy(), act.actual_deposit_rate.to_numpy()
    ldr_value = ldr_mean(panel)
    on = on_series()

    # Bước 1
    growth_rows, variant_params = [], {}
    for key, (asym, excl) in VARIANTS.items():
        gp, st = growth_rules(panel, asym, excl)
        variant_params[key] = {**base, **gp}
        growth_rows.append({"bien_the": key, "bat_doi_xung": asym, "loai_bat_thuong": excl, **gp, **st})
    growth = pd.DataFrame(growth_rows)
    growth["ldr_binh_quan_cua_so"] = ldr_value
    growth.to_csv(out / "growth_rules_stage9.csv", index=False)

    # Bước 2
    grids = []
    for key in VARIANTS:
        g = run_grid(variant_params[key], rows, act_loan, act_dep, ldr_value, cfg)
        g.insert(0, "bien_the", key)
        grids.append(g)
    grid = pd.concat(grids, ignore_index=True)
    grid.to_csv(out / "grid_stage9.csv", index=False, float_format="%.10g")

    gm = grid[grid.bien_the == MAIN_VARIANT]
    top10 = gm.sort_values(["J", "grid_index"], kind="mergesort").head(10)
    top10.to_csv(out / "top10_stage9.csv", index=False, float_format="%.10g")
    prof = profiles(gm)
    prof.to_csv(out / "profile_stage9.csv", index=False, float_format="%.10g")
    corr = top_corr(gm)
    corr.to_csv(out / "corr_top50_stage9.csv", index=False, float_format="%.6g")

    bests = {key: best_row(grid[grid.bien_the == key]) for key in VARIANTS}
    best_tbl = pd.DataFrame([{"bien_the": k, **{c: r[c] for c in list(GRID) + ["target_margin", "deposit_ldr_target",
                                                                                  "J", "RMSE_L_cal", "RMSE_D_cal"]}}
                             for k, r in bests.items()])
    best_tbl.to_csv(out / "best_by_variant_stage9.csv", index=False, float_format="%.10g")
    best = bests[MAIN_VARIANT]
    best_params = params_of(variant_params[MAIN_VARIANT], best, ldr_value)
    lam = float(best["pass_through"])
    lam_in_ci = LAMBDA_CI_STAGE7[0] <= lam <= LAMBDA_CI_STAGE7[1]

    # Phụ lục 1: bộ tốt nhất với λ trong CI GĐ7 (chỉ báo cáo)
    in_ci = gm[(gm.pass_through >= LAMBDA_CI_STAGE7[0]) & (gm.pass_through <= LAMBDA_CI_STAGE7[1])]
    best_ci = best_row(in_ci)
    # Phụ lục 2: lưới mở rộng chẩn đoán (chỉ báo cáo)
    ext = run_grid(variant_params[MAIN_VARIANT], rows, act_loan, act_dep, ldr_value, cfg, GRID_EXT)
    ext.to_csv(out / "grid_ext_stage9.csv", index=False, float_format="%.10g")
    best_ext = best_row(ext)
    diag = pd.DataFrame([{"chan_doan": name, **{c: r[c] for c in list(GRID) + ["target_margin", "J", "RMSE_L_cal",
                                                                                 "RMSE_D_cal"]}}
                         for name, r in (("luoi_chinh_tot_nhat", best), ("lambda_trong_CI_GD7", best_ci),
                                         ("luoi_mo_rong_tot_nhat", best_ext))])
    diag.to_csv(out / "diagnostics_stage9.csv", index=False, float_format="%.10g")
    ext_prof = profiles(ext)

    # Kiểm tra A tất định với seed khác
    l1, d1, _ = simulate(best_params, rows, cfg=cfg)
    l2, d2, _ = simulate(best_params, rows, seed=int(cfg["base_seed"]) + SECOND_SEED_OFFSET, cfg=cfg)
    a_deterministic = bool(np.array_equal(l1, l2) and np.array_equal(d1, d2))

    # Bước 3
    paths = {"hieu_chinh_" + MAIN_VARIANT: (l1, d1)}
    for key in VARIANTS:
        if key != MAIN_VARIANT:
            ln, dp, _ = simulate(params_of(variant_params[key], bests[key], ldr_value), rows, cfg=cfg)
            paths["hieu_chinh_" + key] = (ln, dp)
    ln, dp, _ = simulate(params_of(variant_params[MAIN_VARIANT], best_ci, ldr_value), rows, cfg=cfg)
    paths["chan_doan_lambda_trong_CI"] = (ln, dp)
    ln, dp, _ = simulate(params_of(variant_params[MAIN_VARIANT], best_ext, ldr_value), rows, cfg=cfg)
    paths["chan_doan_luoi_mo_rong"] = (ln, dp)
    ln, dp, _ = simulate(base, rows, cfg=cfg)
    paths["GD8_chua_hieu_chinh"] = (ln, dp)
    ln, dp, _ = simulate(variant_params[MAIN_VARIANT], rows, cfg=cfg)
    paths["GD8_chi_buoc1_tang_truong"] = (ln, dp)
    naive = naive_paths(act, on)
    oos = oos_table(paths, naive, act)
    oos.to_csv(out / "oos_stage9.csv", index=False, float_format="%.10g")
    path_rows = []
    for name, (ln, dp) in paths.items():
        for i in range(N_SIM):
            path_rows.append({"cau_hinh": name, "month": i + 1, "quarter": act.quarter.iloc[i],
                              "loan_rate": ln[i], "deposit_rate_data_basis": dp[i]})
    for name, (ln, dp) in naive.items():
        for j, mth in enumerate(range(OOS_MONTHS[0], OOS_MONTHS[1] + 1)):
            path_rows.append({"cau_hinh": name, "month": mth, "quarter": act.quarter.iloc[mth - 1],
                              "loan_rate": ln[j], "deposit_rate_data_basis": dp[j]})
    for i in range(N_SIM):
        path_rows.append({"cau_hinh": "thuc_te", "month": i + 1, "quarter": act.quarter.iloc[i],
                          "loan_rate": act_loan[i], "deposit_rate_data_basis": act_dep[i]})
    pd.DataFrame(path_rows).to_csv(out / "paths_stage9.csv", index=False, float_format="%.10g")

    # Bước 4
    thr = threshold_table(best_params, rows, cfg)
    thr.insert(0, "cau_hinh", "hieu_chinh_" + MAIN_VARIANT)
    thr_base = threshold_table(base, rows, cfg)
    thr_base.insert(0, "cau_hinh", "GD8_chua_hieu_chinh")
    thr = pd.concat([thr, thr_base], ignore_index=True)
    thr.to_csv(out / "thresholds_stage9.csv", index=False, float_format="%.10g")
    gl = growth_ldr_table({"hieu_chinh_" + MAIN_VARIANT: best_params, "GD8_chua_hieu_chinh": base}, rows, panel, cfg)
    gl.to_csv(out / "growth_ldr_stage9.csv", index=False, float_format="%.10g")
    dg = growth_offset_diagnostic(best_params, gl, rows, act_loan, act_dep, cfg)
    dg.to_csv(out / "diag_growth_stage9.csv", index=False, float_format="%.10g")
    if not args.no_yaml:
        write_calibrated_yaml(CALIBRATED_CFG, best_params, best, growth.iloc[0].to_dict(), ldr_value, lam_in_ci)
    cal_cfg = load_config(CALIBRATED_CFG)
    yaml_matches = all(cal_cfg["parameters"][k] == best_params[k] or
                       (isinstance(best_params[k], float) and abs(cal_cfg["parameters"][k] - best_params[k]) < 1e-6)
                       for k in EXPLICIT_KEYS)
    s6_cal = section6(cal_cfg, rows)
    s6_base = section6(cfg, rows)
    s6 = pd.DataFrame([{"cau_hinh": "scenarios_calibrated.yaml", **s6_cal},
                       {"cau_hinh": "scenarios_macro.yaml (GĐ8)", **s6_base}])
    s6.to_csv(out / "section6_stage9.csv", index=False, float_format="%.10g")
    # đường đi hiệu chỉnh đọc từ file YAML (6 chữ số) so với đường đi của bộ tốt nhất trong bộ nhớ
    lf, df_, _ = simulate(dict(cal_cfg["parameters"]), rows, cfg=cfg)
    yaml_path_diff = float(max(np.abs(lf - l1).max(), np.abs(df_ - d1).max()))

    meta = {"lambda_best": lam, "lambda_ci_stage7": LAMBDA_CI_STAGE7, "lambda_in_ci": lam_in_ci,
            "scenario_A_deterministic_two_seeds": a_deterministic, "ldr_mean_window": ldr_value,
            "n_grid_per_variant": len(grid_points()), "yaml_matches_best": bool(yaml_matches),
            "yaml_path_max_abs_diff": yaml_path_diff, "section6_pass_calibrated": s6_cal["pass"]}
    (out / "meta_stage9.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    write_summary(out, growth, top10, prof, corr, best_tbl, oos, thr, s6, meta, diag, ext_prof, gl, dg)
    from .confounding_stage9 import main as confounding_main   # vòng sửa 2: nhiễu lẫn tuân thủ, nhúng vào summary
    confounding_main(out)
    print(json.dumps(meta, indent=2, ensure_ascii=False))
    if not s6_cal["pass"]:
        raise SystemExit("Bộ tốt nhất VI PHẠM mục 6 CLAUDE.md -> DỪNG")


def write_summary(out, growth, top10, prof, corr, best_tbl, oos, thr, s6, meta, diag, ext_prof, gl, dg):
    o1 = oos[["cau_hinh", "chuoi", "RMSE_tho_ngoai_mau", "RMSE_khu_muc_ngoai_mau", "sai_so_tb_ngoai_mau",
              "bien_do_ngoai_mau_mo_hinh", "bien_do_ngoai_mau_thuc", "quy_day_ngoai_mau_mo_hinh",
              "quy_day_ngoai_mau_thuc"]]
    o2 = oos.dropna(subset=["RMSE_tho_trong_mau"])[["cau_hinh", "chuoi", "RMSE_tho_trong_mau", "RMSE_khu_muc_trong_mau",
                                                     "RMSE_tho_toan_chuoi", "RMSE_khu_muc_toan_chuoi",
                                                     "ty_le_giam_V_toan_chuoi", "ty_le_hoi_phuc_V_toan_chuoi",
                                                     "quy_day_toan_chuoi_mo_hinh", "quy_day_toan_chuoi_thuc"]]
    pw = prof.pivot_table(index="tham_so", values="bien_do_J_min", aggfunc="first").reset_index()
    md = [
        "# Giai đoạn 9 – Hiệu chỉnh bằng mô phỏng và kiểm định ngoài mẫu lịch sử (sinh tự động)",
        "",
        "> Sinh bởi `python -m src.calibration.calibrate_stage9`. Phương pháp chốt trước: `DANG_KY_TRUOC.md`. "
        "Cửa sổ hiệu chỉnh 2023Q2–2025Q2 (month 1–9), ngoài mẫu 2025Q3–2026Q3 (month 10–14). Kịch bản A, tất định "
        f"(hai seed cho kết quả trùng: {'có' if meta['scenario_A_deterministic_two_seeds'] else 'KHÔNG'}). "
        "Mô hình được cấp ON THỰC ngoài mẫu (lợi thế thông tin). Không phải dự báo, không phải tác động chính sách thực tế.",
        "",
        "## Bước 1 – Tăng trưởng (quy tắc, không tối ưu)",
        md_table(growth, 4),
        "",
        "## Bước 2 – Bộ tốt nhất theo biến thể Bước 1 (trong mẫu)",
        md_table(best_tbl, 4),
        "",
        f"λ tốt nhất (biến thể chính) = {meta['lambda_best']}; CI GĐ7 (c) [{meta['lambda_ci_stage7'][0]}; "
        f"{meta['lambda_ci_stage7'][1]}]: {'TRONG' if meta['lambda_in_ci'] else 'NGOÀI'} CI. "
        f"LDR bình quân cửa sổ = {meta['ldr_mean_window']:.4f}. {meta['n_grid_per_variant']} bộ/biến thể.",
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
        "### Tương quan giữa tham số trong top 50 (biến thể chính; ô trống = tham số hằng trong top 50)",
        md_table(corr, 3),
        "",
        "### Chẩn đoán (phụ lục DANG_KY_TRUOC.md, CHỈ báo cáo, không đổi bộ chính)",
        md_table(diag, 4),
        "",
        "Hồ sơ min J trên lưới mở rộng (λ 0.10–1.00, biên tổng 3.0–3.8, δ 0–0.07, base_step 0, LDR bình quân):",
        md_table(ext_prof, 4),
        "",
        "## Bước 3 – Ngoài mẫu 2025Q3–2026Q3",
        md_table(o1, 4),
        "",
        "Trong mẫu và toàn chuỗi (chỉ cấu hình mô hình; tỷ lệ V = biên độ giảm/hồi phục mô hình ÷ thực):",
        md_table(o2, 4),
        "",
        "## Bước 4 – Ngưỡng có đạt tới không, chạm biên (kịch bản A)",
        md_table(thr, 4),
        "",
        "Tăng trưởng tổng (TB/quý) và LDR theo ngân hàng (kịch bản A so với thực):",
        md_table(gl[gl.pham_vi.str.startswith("trong") | gl.pham_vi.str.startswith("ngoai")]
                 [["cau_hinh", "pham_vi", "tang_truong_tien_gui_tb", "tang_truong_du_no_tb"]], 4),
        "",
        md_table(gl[gl.pham_vi.str.startswith("LDR")].pivot_table(index="bank_id", columns=["cau_hinh", "pham_vi"],
                                                                  values="ldr").pipe(
            lambda t: t.set_axis([f"{a}|{b}" for a, b in t.columns], axis=1)).reset_index(), 3),
        "",
        "Chẩn đoán (KHÔNG đổi bộ chính): bù một lần phần lệch tăng trưởng tổng trong mẫu vào base_growth:",
        md_table(dg, 4),
        "",
        f"## Mục 6 CLAUDE.md ({N_RUNS_SECTION6} lần chạy A/B/C)",
        md_table(s6, 4),
        "",
        f"YAML hiệu chỉnh khớp bộ tốt nhất: {'có' if meta['yaml_matches_best'] else 'KHÔNG'}; sai lệch lớn nhất đường đi "
        f"khi đọc lại từ YAML = {meta['yaml_path_max_abs_diff']:.3g}.",
        "",
    ]
    (out / "summary_stage9.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
