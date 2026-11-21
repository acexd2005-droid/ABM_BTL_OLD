"""GD11: khung kiểm định ngoài mẫu sau chính sách (từ 2026Q4).

So dự báo A/B/C của cấu hình hiệu chỉnh với thực tế trong panel mở rộng (khi Minh bổ sung quý
sau 2026Q3; đặc tả định dạng: docs/ke_hoach/yeu_cau_du_lieu_Minh.md).

Chạy:
    python -m src.analysis.kiem_dinh_ngoai_mau --panel data/clean/abm_panel_8nganhang_2023Q1_2027Q1.csv
Tham số: --config (mặc định configs/scenarios_calibrated.yaml; KHÔNG hard-code giá trị tham số),
         --runs (mặc định lấy n_runs trong cấu hình), --outdir (mặc định reports/stage11).

Quy ước (ghi trước):
  - Mô hình khởi tạo 2023Q1 như thiết kế; quý ngoài mẫu = các quý sau (initial_period + policy_month).
  - Lãi suất cho vay thực = bình quân gia quyền theo dư nợ; lãi suất huy động thực = chi phí sổ sách trên
    TỔNG tiền gửi, gia quyền theo tiền gửi. Mô hình: deposit_rate*(1-casa) gia quyền theo tiền gửi.
  - Tiêu chí "kịch bản gần thực tế nhất": RMSE trung bình cộng của LS cho vay và LS huy động
    (trọng số bằng nhau, như hàm mục tiêu GD9). Bảng cũng báo từng LS riêng.
  - Thực tế Q4/2026 có chỉ đạo (CV 9608/9736) nên tương ứng nhánh B/C; A là phản thực tế (không có chỉ đạo).
    Vì vậy A "gần nhất" KHÔNG có nghĩa là chính sách vô hiệu; đây là đối chiếu mô tả, không phải tác động chính sách.
  - Nếu panel không có quý nào sau 2026Q3: dừng, chỉ ghi file trạng thái (không có bảng kết quả).
  - --gia-lap: dữ liệu giả lập dùng để thử script; mọi đầu ra bị đánh dấu GIA_LAP và không được ghi dưới data/.
  - Nguồn gốc: tag THUC chỉ khi panel nằm trong data/clean/ và tên file không chứa "gia_lap". Panel ngoài data/clean/
    hoặc tên chứa "gia_lap" mà thiếu --gia-lap thì bị TỪ CHỐI. meta ghi đường dẫn, sha256 đầy đủ, số dòng.
  - --panel-cu (mặc định panel hiện tại): mọi dòng của panel cũ phải có mặt và GIỐNG HỆT trong panel mới, nếu không báo lỗi.
  - Hướng: same_sign chỉ có ý nghĩa khi |hiệu ứng| lớn hơn nhiễu mô phỏng; báo thêm abs_effect, sd theo seed, tín hiệu/nhiễu
    (KHÔNG đặt ngưỡng kinh tế). Chỉ diễn giải hướng chính cho LS cho vay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..core.model import ABMModel
from .experiments import load_config

ROOT = Path(__file__).resolve().parents[1].parent
DEFAULT_CONFIG = ROOT / "configs/scenarios_calibrated.yaml"
DEFAULT_BANKS = ROOT / "data/clean/abm_initial_8nganhang_2023Q1.csv"
DEFAULT_PANEL = ROOT / "data/clean/abm_panel_8nganhang_2023Q1_2026Q3.csv"
DEFAULT_ON_EXTRA = ROOT / "data/raw/sbv_lnh_qua_dem_ngoai_mau.csv"
DEFAULT_OUT = ROOT / "reports/stage11"
SCENARIOS = ("A", "B", "C")
REQUIRED_COLS = ("bank_id", "period", "deposits", "loans", "loan_rate_pct", "deposit_rate_pct", "casa_ratio")
# Cột còn lại của panel hiện tại (kiểm tra đủ định dạng, giá trị không dùng ở đây).
FORMAT_COLS = ("nim_pct", "npl_amount", "npl_ratio", "issued_papers", "interbank_borrowing")


class NoOutOfSampleData(Exception):
    """Panel chưa có quý sau chính sách."""


def validate_panel(panel, bank_ids, initial_period):
    """Kiểm tra định dạng panel mở rộng; trả DataFrame đã chuẩn hóa (period kiểu Period)."""
    miss = [c for c in REQUIRED_COLS + FORMAT_COLS if c not in panel.columns]
    if miss:
        raise ValueError(f"Panel thiếu cột: {miss}")
    p = panel.copy()
    p["per"] = pd.PeriodIndex(p["period"].astype(str), freq="Q")
    for c in ("deposits", "loans", "loan_rate_pct", "deposit_rate_pct", "casa_ratio"):
        p[c] = pd.to_numeric(p[c], errors="raise")
        if p[c].isna().any():
            raise ValueError(f"Cột {c} có giá trị trống")
    if p.duplicated(["bank_id", "per"]).any():
        raise ValueError("Panel có dòng trùng (bank_id, period)")
    expected = set(bank_ids)
    if set(p["bank_id"]) != expected:
        raise ValueError(f"Mã ngân hàng không khớp 8 NH khởi tạo: {sorted(set(p['bank_id']) ^ expected)}")
    quarters = sorted(p["per"].unique())
    if quarters[0] != pd.Period(initial_period, freq="Q"):
        raise ValueError(f"Quý đầu của panel phải là {initial_period}, nhận {quarters[0]}")
    for a, b in zip(quarters, quarters[1:]):
        if b.ordinal - a.ordinal != 1:
            raise ValueError(f"Panel thiếu quý giữa {a} và {b}")
    cnt = p.groupby("per")["bank_id"].nunique()
    bad = cnt[cnt != len(expected)]
    if len(bad):
        raise ValueError(f"Quý thiếu ngân hàng: {list(map(str, bad.index))}")
    if ((p["casa_ratio"] < 0) | (p["casa_ratio"] > 1)).any():
        raise ValueError("casa_ratio ngoài [0, 1]")
    return p


def actual_oos(p, last_in_sample):
    """Chuỗi thực theo quý cho các quý sau last_in_sample, cộng mốc last_in_sample (để tính thay đổi)."""
    rows = []
    for per, g in p[p["per"] >= last_in_sample].groupby("per"):
        rows.append({
            "quarter": str(per),
            "actual_loan_rate": float((g["loan_rate_pct"] * g["loans"]).sum() / g["loans"].sum()),
            "actual_deposit_rate": float((g["deposit_rate_pct"] * g["deposits"]).sum() / g["deposits"].sum()),
        })
    return pd.DataFrame(rows)


def run_scenarios(cfg, bank_rows, runs):
    """Chạy A/B/C `runs` lần (seed = base_seed + r). Trả DataFrame dài: scenario, run_id, quarter, loan_rate, deposit_rate_total."""
    params = dict(cfg["parameters"])
    n = int(cfg["n_months"])
    out = []
    for sc in SCENARIOS:
        for r in range(runs):
            m = ABMModel(sc, n, int(cfg["base_seed"]) + r, params, bank_rows)
            m.run()
            num = np.zeros(n)
            den = np.zeros(n)
            for b in m.bank_history:
                k = b["month"] - 1
                num[k] += b["deposit_rate"] * (1 - b["casa_ratio"]) * b["deposits"]
                den[k] += b["deposits"]
            for h in m.history:
                k = h["month"] - 1
                out.append({"scenario": sc, "run_id": r, "month": h["month"], "quarter": h["quarter"],
                            "loan_rate": h["loan_rate"], "deposit_rate_total": num[k] / den[k]})
    return pd.DataFrame(out)


def _rmse(e):
    e = np.asarray(e, float)
    return float(np.sqrt((e ** 2).mean()))


def evaluate(sim, act, last_in_sample):
    """Tính bảng dự báo theo quý, bảng tóm tắt theo kịch bản và bảng hướng."""
    base_q = str(last_in_sample)
    oos_q = [q for q in act["quarter"] if q != base_q]
    a = act.set_index("quarter")
    mean = sim.groupby(["scenario", "quarter"])[["loan_rate", "deposit_rate_total"]].mean()
    p05 = sim.groupby(["scenario", "quarter"])[["loan_rate", "deposit_rate_total"]].quantile(0.05)
    p95 = sim.groupby(["scenario", "quarter"])[["loan_rate", "deposit_rate_total"]].quantile(0.95)

    fc = []
    for sc in SCENARIOS:
        for q in oos_q:
            if (sc, q) not in mean.index:
                raise ValueError(f"Mô hình không có quý {q} (tăng n_months trong cấu hình)")
            fc.append({
                "scenario": sc, "quarter": q,
                "loan_forecast": mean.loc[(sc, q), "loan_rate"],
                "loan_p05": p05.loc[(sc, q), "loan_rate"], "loan_p95": p95.loc[(sc, q), "loan_rate"],
                "loan_actual": a.loc[q, "actual_loan_rate"],
                "dep_forecast": mean.loc[(sc, q), "deposit_rate_total"],
                "dep_p05": p05.loc[(sc, q), "deposit_rate_total"], "dep_p95": p95.loc[(sc, q), "deposit_rate_total"],
                "dep_actual": a.loc[q, "actual_deposit_rate"],
            })
    fc = pd.DataFrame(fc)
    fc["loan_error"] = fc["loan_forecast"] - fc["loan_actual"]
    fc["dep_error"] = fc["dep_forecast"] - fc["dep_actual"]

    summ = []
    for sc in SCENARIOS:
        d = fc[fc["scenario"] == sc]
        rl, rd = _rmse(d["loan_error"]), _rmse(d["dep_error"])
        summ.append({
            "scenario": sc, "n_quarters": len(d),
            "loan_me": d["loan_error"].mean(), "loan_mae": d["loan_error"].abs().mean(), "loan_rmse": rl,
            "loan_rmse_demeaned": _rmse(d["loan_error"] - d["loan_error"].mean()) if len(d) > 1 else np.nan,
            "dep_me": d["dep_error"].mean(), "dep_mae": d["dep_error"].abs().mean(), "dep_rmse": rd,
            "dep_rmse_demeaned": _rmse(d["dep_error"] - d["dep_error"].mean()) if len(d) > 1 else np.nan,
            "rmse_combined": 0.5 * rl + 0.5 * rd,
        })
    summ = pd.DataFrame(summ)
    summ["rank_combined"] = summ["rmse_combined"].rank(method="min").astype(int)

    # Hướng: thay đổi so với quý cuối trong mẫu. Thực tế: act_t - act_base. Mô hình mỗi kịch bản: s_t - s_base.
    # Chênh thực so với phản thực tế A: (act_t - act_base) - (A_t - A_base); so dấu với B-A và C-A.
    dirs = []
    piv = {}
    for col in ("loan_rate", "deposit_rate_total"):
        piv[col] = sim.pivot_table(index=["quarter", "run_id"], columns="scenario", values=col)
    for q in oos_q:
        for var, col, acol in (("loan", "loan_rate", "actual_loan_rate"), ("deposit", "deposit_rate_total", "actual_deposit_rate")):
            d_act = a.loc[q, acol] - a.loc[base_q, acol]
            dA = mean.loc[("A", q), col] - mean.loc[("A", base_q), col]
            gap = d_act - dA
            for sc in ("B", "C"):
                eff = mean.loc[(sc, q), col] - mean.loc[("A", q), col]
                pr = piv[col].loc[q]
                sd = float((pr[sc] - pr["A"]).std(ddof=1)) if len(pr) > 1 else np.nan
                dirs.append({
                    "quarter": q, "variable": var, "scenario": sc,
                    "forecast_effect_vs_A": eff, "abs_effect": abs(eff), "sd_effect_across_seeds": sd,
                    "signal_to_noise": (abs(eff) / sd if sd and sd > 0 else np.nan),
                    "actual_change_vs_base": d_act, "A_change_vs_base": dA,
                    "actual_minus_A_change": gap,
                    "same_sign": (None if (eff == 0 or gap == 0) else bool(np.sign(eff) == np.sign(gap))),
                })
    return fc, summ, pd.DataFrame(dirs)


def check_old_unchanged(new_raw, old_raw):
    """Mọi dòng (bank_id, period) của panel cũ phải có trong panel mới với giá trị giống hệt (cột chung)."""
    cols = [c for c in old_raw.columns if c in new_raw.columns]
    if "bank_id" not in cols or "period" not in cols:
        raise ValueError("Panel cũ/mới thiếu cột bank_id hoặc period để đối chiếu")
    n = new_raw[cols].copy()
    o = old_raw[cols].copy()
    n["period"] = n["period"].astype(str)
    o["period"] = o["period"].astype(str)
    m = o.merge(n, on=["bank_id", "period"], how="left", suffixes=("_cu", "_moi"), indicator=True)
    if (m["_merge"] != "both").any():
        raise ValueError(f"Panel mới thiếu {(m['_merge'] != 'both').sum()} dòng của panel cũ")
    diff = []
    for c in cols:
        if c in ("bank_id", "period"):
            continue
        a, b = m[c + "_cu"], m[c + "_moi"]
        same = (a == b) | (a.isna() & b.isna())
        if not same.all():
            diff.append(f"{c}: {int((~same).sum())} dòng")
    if diff:
        raise ValueError("Số liệu cũ (2023Q1-2026Q3) bị thay đổi so với panel cũ: " + "; ".join(diff))
    return len(o)


def classify_panel(panel_path, gia_lap):
    """Trả tag 'THUC' hoặc 'GIA_LAP'; từ chối khi nguồn gốc không rõ ràng."""
    pp = Path(panel_path).resolve()
    clean = (ROOT / "data/clean").resolve()
    has_name = "gia_lap" in pp.name.lower()
    if gia_lap:
        return "GIA_LAP"
    if has_name:
        raise ValueError(f"Tên panel chứa 'gia_lap' nhưng thiếu --gia-lap: {pp.name}")
    if clean not in pp.parents:
        raise ValueError("Panel nằm ngoài data/clean/ nên không thể gắn tag THUC; dùng --gia-lap nếu là dữ liệu thử")
    return "THUC"


def on_quarter_status(on):
    """Thêm cột trạng thái: quý chưa kết thúc nếu phien_cuoi < ngày cuối quý (suy từ dữ liệu, không sửa file gốc). Nghiêm ngặt: cuối quý rơi vào cuối tuần cũng được coi là chưa kết thúc."""
    on = on.copy()
    st = []
    for _, r in on.iterrows():
        qend = pd.Period(str(r["quy"]), freq="Q").end_time.normalize()
        last = pd.Timestamp(str(r["phien_cuoi"]))
        st.append("đủ quý" if last >= qend else f"CHƯA KẾT THÚC (phiên cuối {last.date()} < cuối quý {qend.date()})")
    on["trang_thai"] = st
    return on


def load_on_extra(path):
    p = Path(path)
    if not p.exists():
        return None
    return pd.read_csv(p)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def _md(df, digits=4):
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(f"{v:.{digits}f}" if isinstance(v, (float, np.floating)) else str(v) for v in r) + " |")
    return "\n".join(out)


def _check_outdir(outdir, gia_lap):
    out = Path(outdir).resolve()
    data_dir = (ROOT / "data").resolve()
    if out == data_dir or data_dir in out.parents:
        raise ValueError("Không được ghi kết quả dưới data/")
    if gia_lap and out == DEFAULT_OUT.resolve():
        raise ValueError("Với --gia-lap phải chỉ định --outdir khác reports/stage11 (không trộn với kết quả thực)")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--panel", default=str(DEFAULT_PANEL))
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--banks", default=str(DEFAULT_BANKS))
    ap.add_argument("--runs", type=int, default=None, help="mặc định: n_runs trong cấu hình")
    ap.add_argument("--outdir", default=str(DEFAULT_OUT))
    ap.add_argument("--on-extra", default=str(DEFAULT_ON_EXTRA))
    ap.add_argument("--panel-cu", default=str(DEFAULT_PANEL), help="panel cũ để kiểm tra số cũ không đổi")
    ap.add_argument("--gia-lap", action="store_true", help="dữ liệu GIẢ LẬP (chỉ để thử script)")
    a = ap.parse_args(argv)

    out = _check_outdir(a.outdir, a.gia_lap)
    tag = classify_panel(a.panel, a.gia_lap)
    out.mkdir(parents=True, exist_ok=True)
    cfg = load_config(a.config)
    banks = pd.read_csv(a.banks)
    rows = banks.to_dict("records")
    init = pd.Period("2023Q1", freq="Q")   # ABMModel cố định kỳ khởi tạo 2023Q1
    last_in = init + int(cfg["parameters"]["policy_month"])
    raw = pd.read_csv(a.panel, encoding="utf-8-sig")
    p = validate_panel(raw, banks["bank_id"], str(init))
    n_old = check_old_unchanged(raw, pd.read_csv(a.panel_cu, encoding="utf-8-sig"))
    runs = int(cfg["n_runs"]) if a.runs is None else a.runs

    has_new = (p["per"] > last_in).any()
    if not has_new:
        msg = (f"Chưa có dữ liệu ngoài mẫu: panel kết thúc ở {p['per'].max()}, cần ít nhất {last_in + 1}. "
               "Không tạo kết quả.")
        (out / "trang_thai_stage11.md").write_text(
            f"# GD11 – trạng thái\n\n{msg}\n\nPanel: `{a.panel}`\n", encoding="utf-8")
        print(msg)
        return None

    act = actual_oos(p, last_in)
    sim = run_scenarios(cfg, rows, runs)
    fc, summ, dirs = evaluate(sim, act, last_in)

    fc.insert(0, "du_lieu", tag)
    summ.insert(0, "du_lieu", tag)
    dirs.insert(0, "du_lieu", tag)
    fc.to_csv(out / "oos_forecast_stage11.csv", index=False, encoding="utf-8-sig")
    summ.to_csv(out / "oos_summary_stage11.csv", index=False, encoding="utf-8-sig")
    dirs.to_csv(out / "oos_direction_stage11.csv", index=False, encoding="utf-8-sig")

    best = summ.sort_values("rmse_combined").iloc[0]["scenario"]
    on = load_on_extra(a.on_extra)
    meta = {"du_lieu": tag, "config": str(a.config), "config_sha256_16": _sha(a.config),
            "panel": str(Path(a.panel).resolve()), "panel_sha256": hashlib.sha256(Path(a.panel).read_bytes()).hexdigest(),
            "panel_sha256_16": _sha(a.panel), "panel_rows": int(len(raw)),
            "panel_cu": str(Path(a.panel_cu).resolve()), "panel_cu_rows_checked_unchanged": int(n_old), "runs": runs,
            "base_seed": int(cfg["base_seed"]), "last_in_sample": str(last_in),
            "oos_quarters": [q for q in act["quarter"] if q != str(last_in)], "closest_scenario": best}
    (out / "meta_stage11.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    fb = fc.pivot(index="quarter", columns="scenario")
    bc_loan = float((fb["loan_forecast"]["B"] - fb["loan_forecast"]["C"]).abs().max())
    bc_dep = float((fb["dep_forecast"]["B"] - fb["dep_forecast"]["C"]).abs().max())
    banner = ("> **DỮ LIỆU GIẢ LẬP** – chỉ để thử script, KHÔNG phải kết quả thực.\n\n" if tag == "GIA_LAP" else "")
    md = [f"# GD11 – Kiểm định ngoài mẫu sau chính sách ({tag})", "", banner.rstrip(), "",
          f"Cấu hình: `{a.config}` (sha {meta['config_sha256_16']}); panel `{a.panel}` (sha {meta['panel_sha256_16']}); "
          f"{runs} lần chạy/kịch bản; quý ngoài mẫu: {', '.join(meta['oos_quarters'])}.", "",
          "Cách đọc: thực tế sau 10/2026 có chỉ đạo (CV 9608/9736) nên tương ứng nhánh B/C; A là phản thực tế. "
          "Đây là đối chiếu mô tả với số ít quý, KHÔNG phải ước lượng tác động chính sách. "
          "Mô hình khởi tạo 2023Q1, kịch bản không dùng ON thực ngoài mẫu (ON giữ theo D3).", "",
          "## Sai số theo kịch bản (dự báo − thực tế; %/năm)", "", _md(summ.drop(columns="du_lieu")), "",
          f"Kịch bản gần thực tế nhất theo RMSE trung bình cộng (tiêu chí đặt trước): **{best}**.", "",
          "## Dự báo và thực tế theo quý", "", _md(fc.drop(columns="du_lieu")), "",
          "## Hướng: hiệu ứng dự báo (B−A, C−A) so với (thay đổi thực − thay đổi của A)", "",
          _md(dirs.drop(columns="du_lieu")), "",
          "`same_sign` = dấu dự báo trùng dấu chênh thực so với A (None nếu một bên bằng 0). Thay đổi tính so với quý cuối trong mẫu. "
          "Hướng CHỈ có ý nghĩa khi |hiệu ứng| (`abs_effect`) lớn hơn nhiễu mô phỏng (`sd_effect_across_seeds`, độ lệch chuẩn theo seed "
          "của hiệu ứng cùng seed; `signal_to_noise` = abs_effect/sd). Không đặt ngưỡng kinh tế; chỉ diễn giải hướng chính cho LS cho vay "
          "(hiệu ứng LS huy động rất nhỏ, dễ nằm trong nhiễu).", "",
          f"Phân biệt B với C: chênh |B−C| của LS cho vay dự báo tối đa {bc_loan:.4f}, của LS huy động {bc_dep:.4f} (%/năm) trên các quý ngoài mẫu. "
          "Vì cho vay B và C gần như trùng ở 1-2 quý đầu, `closest_scenario` giữa B và C gần như không có nội dung thông tin; "
          "B/C chỉ phân biệt được chủ yếu qua LS huy động."]
    if on is not None:
        md += ["", "## ON thực ngoài mẫu (thông tin, không đưa vào mô hình)", "", _md(on_quarter_status(on)[["quy", "so_phien", "bq_gian_don", "phien_cuoi", "trang_thai"]]),
               "", "`trang_thai` do script suy từ `phien_cuoi` so với ngày cuối quý (file gốc không sửa)."]
    (out / "summary_stage11.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Xong ({tag}); kịch bản gần nhất: {best}. Kết quả: {out}")
    return out


if __name__ == "__main__":
    main()
