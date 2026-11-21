"""Giai đoạn 7c: chỉ đạo lãi suất có làm biên cho vay hẹp lại không? (KHÔNG sửa mô hình, KHÔNG sửa configs).

Dữ liệu chỉ đạo: data/raw/chi_dao_lai_suat_2023_2026.csv (24 sự kiện; 2 sự kiện 2026Q4 nằm ngoài panel, để dành cho kiểm định
ngoài mẫu). Biến cường độ theo quý I_q:
    0 = không có văn bản; 1 = có văn bản yêu cầu giảm/ổn định lãi suất (mọi loại TRỪ `thay_doi_LS_dieu_hanh` và `cong_bo_LS_cho_vay`);
    2 = có mục tiêu ĐỊNH LƯỢNG cho lãi suất cho vay (cột muc_tieu_dinh_luong khác rỗng VÀ (loại = yeu_cau_giam_LS_cho_vay HOẶC nội dung
        mục tiêu có chữ "cho vay")). Nhiều văn bản trong quý: lấy giá trị lớn nhất.
Quy tắc dời quý (mặc định, "shift"): văn bản có ngày đầy đủ, ban hành sau ngày 15 của THÁNG CUỐI quý (3, 6, 9, 12) tính sang quý sau.
Ngày chỉ có tháng (không có ngày) không dời. Bản "noshift" giữ nguyên cột `quy` để kiểm tra độ nhạy.
Biến riêng DH_q = số quyết định thay đổi lãi suất điều hành trong quý (cùng quy tắc dời).

Biên thực m_{i,t} = loan_rate_pct_t − (deposit_rate_pct_{t-1} + 0.15)  (cơ sở term: c_{t-1} = deposit_rate_pct + 0.15).
Hồi quy FE ngân hàng (KHÔNG dùng FE quý vì sẽ hấp thụ I_q), kiểm soát ON_{t-1}:
    m_{i,t}  (hoặc Δr^L_{i,t}) = α_i + β0·I_t + β1·I_{t-1} + γ·ON_{t-1} [+ δ·DH_t] + ε
    dạng biến giả: I1_t = 1[I_t = 1], I2_t = 1[I_t = 2] (cơ sở I = 0); biên độ I=2 so với I=1: β(I2) − β(I1).
    phần dư PT1 (d1) của Giai đoạn 7 hồi quy lên I_t, I_{t-1} (hai bước, SE không hiệu chỉnh sai số bước một) và dạng một bước
    (PT1 d1 thêm I_t, I_{t-1}).
SE: CR1 theo ngân hàng (8 cụm) + wild-cluster bootstrap Webb cho hệ số I_t.
Kết quả chỉ là TƯƠNG QUAN: chỉ ~14 quý, I_q là biến chung theo quý, và chỉ đạo có thể nội sinh (ban hành khi lãi suất cao).

Chạy: python -m src.calibration.estimate_policy_margin
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from .estimate_equations import (
    FUNDING_CONST, T_CRIT, _codes, _demean, _row, eq_vars, fit, load_data, sample, wild_cluster_bootstrap,
)

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "data/raw/chi_dao_lai_suat_2023_2026.csv"
OUTDIR = ROOT / "reports/calibration"
EXCLUDED = {"thay_doi_LS_dieu_hanh", "cong_bo_LS_cho_vay"}
DH_TYPE = "thay_doi_LS_dieu_hanh"
LAST_PANEL_QUARTER = "2026Q3"


# ======================================================================
# 1. Biến cường độ
# ======================================================================

def load_events(path=POLICY):
    d = pd.read_csv(path)
    need = {"ngay", "quy", "loai", "muc_tieu_dinh_luong"}
    if need - set(d.columns):
        raise ValueError(f"Thiếu cột: {sorted(need - set(d.columns))}")
    ym, day = [], []
    for s in d["ngay"].astype(str):
        parts = s.split("-")
        if len(parts) not in (2, 3):
            raise ValueError(f"Ngày không hợp lệ: {s}")
        ym.append(f"{parts[0]}-{parts[1]}")
        day.append(int(parts[2]) if len(parts) == 3 else None)
    d["day"] = day
    d["month"] = [int(s.split("-")[1]) for s in ym]
    d["q_date"] = [str(pd.Period(s, freq="Q")) for s in ym]
    if (d["q_date"] != d["quy"]).any():
        bad = d.loc[d["q_date"] != d["quy"], ["ngay", "quy"]]
        raise ValueError(f"Cột quy không khớp ngày: {bad.to_dict('records')}")
    late = [(dy is not None) and (mo in (3, 6, 9, 12)) and (dy > 15) for dy, mo in zip(d["day"], d["month"])]
    d["quy_shift"] = [str(pd.Period(q, freq="Q") + 1) if l else q for q, l in zip(d["quy"], late)]
    d["dich_quy"] = late
    target = d["muc_tieu_dinh_luong"].fillna("").astype(str).str.strip()
    lending_target = (target != "") & ((d["loai"] == "yeu_cau_giam_LS_cho_vay") | target.str.lower().str.contains("cho vay"))
    d["lending_target"] = lending_target
    d["intensity_doc"] = np.where(d["loai"].isin(EXCLUDED), 0, np.where(lending_target, 2, 1))
    d["is_dh"] = d["loai"] == DH_TYPE
    return d


def quarterly_intensity(events, shift=True, last=LAST_PANEL_QUARTER, first="2023Q1"):
    col = "quy_shift" if shift else "quy"
    quarters = pd.period_range(first, last, freq="Q")
    rows = []
    for t, q in enumerate(quarters, start=1):
        e = events[events[col] == str(q)]
        rows.append({"t": t, "quy": str(q),
                     "I": int(e["intensity_doc"].max()) if len(e) else 0,
                     "n_van_ban": int((e["intensity_doc"] > 0).sum()),
                     "DH": int(e["is_dh"].sum())})
    out = pd.DataFrame(rows)
    out["I_lag"] = out["I"].shift()
    out["DH_lag"] = out["DH"].shift()
    return out


def intensity_table(events):
    a = quarterly_intensity(events, True).rename(columns={"I": "I_dich_quy", "n_van_ban": "n_van_ban_dich", "DH": "DH_dich"})
    b = quarterly_intensity(events, False).rename(columns={"I": "I_khong_dich", "n_van_ban": "n_van_ban_khong_dich", "DH": "DH_khong_dich"})
    return a[["t", "quy", "I_dich_quy", "n_van_ban_dich", "DH_dich"]].merge(
        b[["t", "I_khong_dich", "n_van_ban_khong_dich", "DH_khong_dich"]], on="t")


# ======================================================================
# 2. Dữ liệu hồi quy
# ======================================================================

def build_panel(events, shift):
    df = load_data()
    s = sample(df, 2).copy()
    qi = quarterly_intensity(events, shift).set_index("t")
    s["I"] = s["t"].map(qi["I"])
    s["I_lag"] = s["t"].map(qi["I_lag"])
    s["DH"] = s["t"].map(qi["DH"])
    s["I1"] = (s["I"] == 1).astype(float)
    s["I2"] = (s["I"] == 2).astype(float)
    s["margin"] = s["rL"] - s["c_main_lag"]
    s["ON1c"] = s["ON1"] - s["ON1"].mean()
    return df, s.reset_index(drop=True)


# ======================================================================
# 3. Ước lượng
# ======================================================================

def _linear_comb(cov, idx, w):
    w = np.asarray(w, float)
    return float(np.sqrt(w @ cov[np.ix_(idx, idx)] @ w))


def _rows(meta, names, res, n, kind):
    b, se, seo, cov = res["b"], res["se_cl"], res["se_ols"], res["cov_cl"]
    rows = [_row(meta, nm, b[j], se[j], seo[j], res["r2"], res["r2_common"], n, res["G"], {}, "") for j, nm in enumerate(names)]
    if kind == "lin":
        i0, i1 = names.index("I_t"), names.index("I_t-1")
        rows.append(_row(meta, "I_sum", b[i0] + b[i1], _linear_comb(cov, [i0, i1], [1, 1]), np.nan, res["r2"],
                         res["r2_common"], n, res["G"], {}, "β0 + β1: tác động tích lũy của +1 mức I giữ trong 2 quý"))
    elif kind == "dum":
        i1, i2 = names.index("I1_t"), names.index("I2_t")
        rows.append(_row(meta, "I2_minus_I1", b[i2] - b[i1], _linear_comb(cov, [i1, i2], [-1, 1]), np.nan, res["r2"],
                         res["r2_common"], n, res["G"], {}, "biên độ ngụ ý của I = 2 so với I = 1"))
    return rows


def design(s, outcome, kind, with_dh):
    """Trả (y, X, tên cột) cho một mô hình trên mẫu s (N = 112)."""
    if outcome in ("margin", "dRL"):
        y = s["margin" if outcome == "margin" else "dRL"].to_numpy()
        if kind == "lin":
            cols, names = ["I", "I_lag", "ON1"], ["I_t", "I_t-1", "ON_t-1"]
        else:
            cols, names = ["I1", "I2", "ON1"], ["I1_t", "I2_t", "ON_t-1"]
    elif outcome == "pt1_onestep":
        y, base = eq_vars("PT1", s, "main")
        x = [base["lambda"].to_numpy(), s["ON1c"].to_numpy()]
        if kind == "lin":
            return y, np.column_stack(x + [s["I"], s["I_lag"]] + ([s["DH"]] if with_dh else [])), \
                ["lambda", "ON_t-1c", "I_t", "I_t-1"] + (["DH_t"] if with_dh else [])
        return y, np.column_stack(x + [s["I1"], s["I2"]] + ([s["DH"]] if with_dh else [])), \
            ["lambda", "ON_t-1c", "I1_t", "I2_t"] + (["DH_t"] if with_dh else [])
    else:
        raise ValueError(outcome)
    X = s[cols].to_numpy(float)
    if with_dh:
        X = np.column_stack([X, s["DH"]])
        names = names + ["DH_t"]
    return y, X, names


def pt1_d1_residuals(s):
    """Phần dư (within) của PT1 biến thể (d1): Δr^L = α_i + λ(c_{t-1} − r_{t-1}) + θ·ON_{t-1} (tâm hóa) + u."""
    y, base = eq_vars("PT1", s, "main")
    X = np.column_stack([base["lambda"].to_numpy(), s["ON1c"].to_numpy()])
    res = fit(y, X, s["bank_id"], s["t"], "fe_bank")
    bc = _codes(s["bank_id"])
    G = bc.max() + 1
    u = _demean(y, bc, G) - _demean(X, bc, G) @ res["b"]
    return u, res


def estimate_all(events):
    out, boots = [], []
    for shift in (True, False):
        df, s = build_panel(events, shift)
        u, pt1 = pt1_d1_residuals(s)
        s = s.assign(u_pt1=u)
        for with_dh in (True, False):
            for kind in ("lin", "dum"):
                for outcome in ("margin", "dRL", "pt1_resid_2step", "pt1_onestep"):
                    meta = {"c_def": "main", "equation": outcome, "variant": "FE_NH",
                            "sample": f"N{len(s)}", "I_def": "dich_quy" if shift else "khong_dich",
                            "kiem_soat_DH": with_dh, "dang": kind, "lag_on": np.nan}
                    if outcome == "pt1_resid_2step":
                        cols = ["I", "I_lag"] if kind == "lin" else ["I1", "I2"]
                        names = ["I_t", "I_t-1"] if kind == "lin" else ["I1_t", "I2_t"]
                        X = s[cols].to_numpy(float)
                        if with_dh:
                            X = np.column_stack([X, s["DH"]])
                            names = names + ["DH_t"]
                        y = s["u_pt1"].to_numpy()
                    else:
                        y, X, names = design(s, outcome, kind, with_dh)
                    res = fit(y, X, s["bank_id"], s["t"], "fe_bank")
                    out += _rows(meta, names, res, len(s), kind)
                    # bootstrap cho hệ số I_t chính (dạng tuyến tính, có kiểm soát DH)
                    if kind == "lin" and with_dh:
                        j = names.index("I_t")
                        b = wild_cluster_bootstrap(y, X, s["bank_id"], s["t"], "fe_bank", j)
                        b.update({"equation": outcome, "I_def": meta["I_def"], "parameter": "I_t", "n": len(s),
                                  "ci_cr1_lo": b["coef"] - T_CRIT * b["se_cr1"], "ci_cr1_hi": b["coef"] + T_CRIT * b["se_cr1"]})
                        boots.append(b)
    est = pd.DataFrame(out)
    boot = pd.DataFrame(boots)[["equation", "I_def", "parameter", "coef", "se_cr1", "t_cr1", "ci_cr1_lo", "ci_cr1_hi",
                                "p_boot", "ci_boot_lo", "ci_boot_hi", "B", "seed", "n"]]
    return est, boot


SPECS = [
    ("I_t", ["I"]),
    ("I_t, I_t-1", ["I", "I_lag"]),
    ("I_t, ON", ["I", "ON1"]),
    ("I_t, I_t-1, ON", ["I", "I_lag", "ON1"]),
    ("I_t, ON, DH", ["I", "ON1", "DH"]),
    ("I_t, I_t-1, ON, DH (cơ sở)", ["I", "I_lag", "ON1", "DH"]),
    ("I_t, I_t-1, DH (không ON)", ["I", "I_lag", "DH"]),
]


def spec_sensitivity(events):
    """Hệ số của I_t theo đặc tả kiểm soát (có/không ON, DH, I_{t-1}); FE ngân hàng, N = 112."""
    rows = []
    for shift in (True, False):
        df, s = build_panel(events, shift)
        for outcome, col in (("margin", "margin"), ("dRL", "dRL")):
            for label, cols in SPECS:
                res = fit(s[col].to_numpy(), s[cols].to_numpy(float), s["bank_id"], s["t"], "fe_bank")
                j = cols.index("I")
                rows.append({"outcome": outcome, "I_def": "dich_quy" if shift else "khong_dich", "dac_ta": label,
                             "coef_I_t": res["b"][j], "se_cluster": res["se_cl"][j],
                             "ci95_lo": res["b"][j] - T_CRIT * res["se_cl"][j],
                             "ci95_hi": res["b"][j] + T_CRIT * res["se_cl"][j], "r2": res["r2"], "n": res["n"]})
    return pd.DataFrame(rows)


def quarterly_check(events, shift=True):
    """Kiểm tra chuỗi thời gian: biên bình quân gia quyền theo quý (T = 14) hồi quy OLS lên I_t, I_{t-1}, ON_{t-1}, DH_t.

    SE thường (không hiệu chỉnh), chỉ để tham khảo vì T quá ngắn."""
    df, s = build_panel(events, shift)
    g = s.groupby("t")
    q = pd.DataFrame({
        "margin": (s["margin"] * s["loans"]).groupby(s["t"]).sum() / g["loans"].sum(),
        "I": g["I"].first(), "I_lag": g["I_lag"].first(), "ON1": g["ON1"].first(), "DH": g["DH"].first()})
    X = np.column_stack([np.ones(len(q)), q["I"], q["I_lag"], q["ON1"], q["DH"]])
    y = q["margin"].to_numpy()
    XtXi = np.linalg.inv(X.T @ X)
    b = XtXi @ X.T @ y
    u = y - X @ b
    se = np.sqrt(np.diag((u @ u) / (len(y) - X.shape[1]) * XtXi))
    r2 = 1 - (u @ u) / ((y - y.mean()) ** 2).sum()
    names = ["const", "I_t", "I_t-1", "ON_t-1", "DH_t"]
    return pd.DataFrame({"parameter": names, "coef": b, "se_ols": se, "t": b / se, "T": len(y), "R2": r2,
                         "I_def": "dich_quy" if shift else "khong_dich"})


def descriptive(events):
    df, s = build_panel(events, True)
    g = s.groupby("t")
    q = pd.DataFrame({
        "quy": g["period"].first().astype(str),
        "I": g["I"].first(), "DH": g["DH"].first(), "ON_t-1": g["ON1"].first(),
        "bien_thuc_gia_quyen": (s["margin"] * s["loans"]).groupby(s["t"]).sum() / g["loans"].sum(),
        "dr_L_tb": g["dRL"].mean()}).reset_index()
    by_i = q.groupby("I").agg(so_quy=("t", "count"), bien_tb=("bien_thuc_gia_quyen", "mean"),
                              dr_L_tb=("dr_L_tb", "mean"), ON_tb=("ON_t-1", "mean")).reset_index()
    return q, by_i


# ======================================================================
# 4. Xuất bảng
# ======================================================================

def md_table(df, cols=None, digits=4):
    cols = cols or list(df.columns)
    out = "| " + " | ".join(cols) + " |\n|" + "|".join(["---"] * len(cols)) + "|\n"
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                cells.append("" if v != v else f"{v:.{digits}f}")
            else:
                cells.append(str(v))
        out += "| " + " | ".join(cells) + " |\n"
    return out


INTERPRETATION = """
## Diễn giải (viết tay sau khi xem kết quả; các con số lấy từ các bảng ở trên)

**Không có bằng chứng ủng hộ giả thuyết “chỉ đạo làm biên cho vay hẹp lại”: hệ số của I_t lên biên thực ≥ 0 ở mọi đặc tả; lên Δ lãi suất cho vay, hệ số chỉ âm khi KHÔNG kiểm soát ON và đổi dấu (không có ý nghĩa) khi kiểm soát ON_{t−1}.**
- Biên thực (mức), bản dời quý, FE ngân hàng, kiểm soát ON_{t−1} và DH_t: β(I_t) = +0.217 (CR1 [0.095; 0.339]; bootstrap Webb p = 0.0012, CI [0.086; 0.345]), β(I_{t−1}) = +0.230, tổng +0.447. **Ở bản dời quý, hệ số lớn (≥ 0.2) chỉ có khi kiểm soát đồng thời ON_{t−1} và I_{t−1}**: không có ON thì gần 0 (0.028 khi chỉ có I_t; 0.043 khi có I_t, I_{t−1}), và chỉ I_t + ON cho 0.075 (xem bảng độ nhạy theo đặc tả). Bản không dời quý cho hệ số dương ở nhiều đặc tả hơn (kể cả không ON: 0.178 với I_t, I_{t−1}, DH). Trung bình thô theo mức I cũng không đơn điệu: biên 4.14 (I = 0), 3.96 (I = 1), 4.09 (I = 2). Nên kết luận là **không có bằng chứng biên hẹp hơn**, không phải “biên rộng hơn do chỉ đạo”.
- Δ lãi suất cho vay: β(I_t) = +0.082, không có ý nghĩa (bootstrap p = 0.265, CI [−0.078; 0.254]) khi kiểm soát ON_{t−1}. **Khi không kiểm soát ON, hệ số là ÂM và rõ: −0.22 (chỉ I_t; CR1 [−0.34; −0.10]) và −0.32 (thêm I_{t−1})**: lãi suất cho vay giảm nhiều hơn ở các quý có chỉ đạo, nhưng đó cũng là các quý lãi suất liên ngân hàng thấp (corr(I_t, ON_{t−1}) = −0.55) nên không tách được tác động của chỉ đạo khỏi chu kỳ lãi suất chung; dấu âm biến mất ngay khi thêm ON_{t−1}. Phần dư PT1 (d1): hai bước +0.058 (p = 0.327), một bước +0.133 (p = 0.085, CI [−0.026; 0.288]). Nếu chỉ đạo kéo lãi suất cho vay xuống ngoài phần chi phí vốn giải thích thì các hệ số này phải âm.
- Dạng biến giả: I = 1 so với 0: +0.007; I = 2 so với 0: +0.127. **Biên độ ngụ ý của I = 2 so với I = 1 là +0.12 điểm % (CR1 [−0.17; 0.41])**, tức không phải biên giảm; chỉ dựa trên 2 quý có I = 2 (2023Q3, 2024Q2).

**Kết quả rất mong manh, nên không diễn giải như một tác động.**
- *Nhạy với quy tắc dời quý của đúng một sự kiện:* bản không dời quý cho β(I_t) = +0.348 thay vì +0.217 (và PT1 một bước +0.210 với p = 0.0025 thay vì +0.133). Quy tắc dời chỉ đổi quý của hai sự kiện (Thông báo ổn định lãi suất 30/3/2026 và QĐ lãi suất điều hành 19/6/2023).
- *SE cụm theo ngân hàng không hợp lệ cho biến chung theo quý:* I_q chỉ có 14 giá trị khác nhau (mọi ngân hàng cùng giá trị trong một quý), nên thông tin hiệu dụng cỡ 14 điểm, không phải 112. Kiểm tra chuỗi thời gian (biên bình quân theo quý, T = 14, OLS, SE thường, vẫn lạc quan vì bỏ qua tự tương quan): β(I_t) = +0.138 (SE 0.162, t = 0.85) ở bản dời quý, +0.301 (t = 2.5) ở bản không dời. Các p-value rất nhỏ của bootstrap theo ngân hàng (0.0012) vì vậy **không nên đọc là có ý nghĩa**.
- *Cộng tuyến với ON:* corr(I_t, ON_{t−1}) = −0.55: chỉ đạo tập trung vào các quý lãi suất liên ngân hàng thấp. Dù đã kiểm soát ON_{t−1} tuyến tính, tách tác động của chỉ đạo khỏi chu kỳ lãi suất chung từ 14 điểm là không khả thi.
- *Nội sinh:* chỉ đạo có thể được ban hành khi lãi suất cho vay đang cao hoặc được kỳ vọng giảm; khi đó quan hệ ngược chiều (lãi suất/biên ảnh hưởng tới việc ban hành) có thể cho hệ số dương. Dữ liệu hiện có không phân biệt được các cách giải thích này. Kết quả là **tương quan**.
- *Phân bố I khác kỳ vọng ban đầu:* I_q không "gần như luôn ≥ 1": có 6 trong 14 quý ước lượng không có văn bản (I = 0), 6 quý I = 1 và chỉ 2 quý I = 2. Nhận diện đến từ cả chênh lệch 0 so với ≥ 1 lẫn 1 so với 2, nhưng mức I = 2 chỉ dựa trên hai quý.

**Dữ liệu cũng không đủ sức để bác bỏ một tác động của chỉ đạo** (thiếu đối chứng, nội sinh, 14 điểm): “không có bằng chứng” không phải “không có tác động”.

**Có đủ căn cứ để hiệu chỉnh `policy_pressure`, `policy_step` từ dữ liệu này không? Không.** (i) dấu của hệ số lên Δ lãi suất cho vay phụ thuộc vào việc kiểm soát ON (âm và rõ khi không kiểm soát, đúng dấu kỳ vọng của mô hình; dương/không có ý nghĩa khi kiểm soát), còn hệ số lên biên thực ≥ 0 ở mọi đặc tả: không nhất quán, và việc coi ON là biến kiểm soát chu kỳ chung hay là biến bị chính chỉ đạo tác động ngược là giả định kinh tế không quyết được bằng dữ liệu này; (ii) chỉ 14 quý, I_q là biến chung theo quý, mức I = 2 chỉ có 2 quý; (iii) kết quả đổi cỡ 60% khi dời quý một sự kiện; (iv) cộng tuyến với chu kỳ lãi suất và nội sinh; (v) chế độ trong dữ liệu (chỉ đạo gần như liên tục, 2023-2026) không có đối chứng \"không can thiệp\" tương ứng với kịch bản A của mô hình, và mô hình kích hoạt chính sách một lần từ Q4/2026. Báo cáo này không đề xuất giá trị tham số nào. Hai văn bản 2026Q4 (Công văn 9608/9736) nằm ngoài mẫu và có thể dùng cho kiểm định ngoài mẫu.

**Hệ số DH_t** (+0.39 trong mô hình biên thực) chỉ dương ở ba quý đầu (2023Q1-Q3), trùng giai đoạn biên cao nhất (4.7), nên chủ yếu bắt xu hướng thời gian; không đọc như tác động của lãi suất điều hành.

**Hạn chế.** Biên thực `r^L − c_{t−1}` bao gồm cả chi phí vốn trễ và mức cho vay danh mục sổ sách (lợi suất sổ sách, trễ so với lãi suất cận biên); mã hóa cường độ I_q (0/1/2) là một thang thứ tự gán tay, không phải đo lường độ mạnh thực của chỉ đạo; `kiem_tra_thuc_hien` được tính là I = 1 theo quy tắc đã nêu; phần dư PT1 hai bước không hiệu chỉnh sai số của bước một.
"""


def write_outputs(events, est, boot, inten, qchk, qdesc, by_i, outdir=OUTDIR, specs=None):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    est.to_csv(outdir / "estimates_stage7c.csv", index=False)
    boot.to_csv(outdir / "bootstrap_stage7c.csv", index=False)
    inten.to_csv(outdir / "policy_intensity_stage7c.csv", index=False)
    if specs is not None:
        specs.to_csv(outdir / "spec_sensitivity_stage7c.csv", index=False)
    cols = ["equation", "I_def", "kiem_soat_DH", "parameter", "coef", "se_cluster", "t_cluster", "ci95_lo", "ci95_hi", "r2", "n"]

    def pick(form, params, shift=True, dh=True):
        d = est[(est.dang == form) & (est.parameter.isin(params)) & (est.I_def == ("dich_quy" if shift else "khong_dich"))
                & (est.kiem_soat_DH == dh)]
        return d[cols]

    lin_p = ["I_t", "I_t-1", "I_sum", "ON_t-1"]
    dum_p = ["I1_t", "I2_t", "I2_minus_I1", "ON_t-1"]
    md = ["# Giai đoạn 7c: chỉ đạo lãi suất có làm biên cho vay hẹp lại không? (sinh tự động)\n",
          "> Không sửa mô hình, không sửa `configs/`. Kết quả chỉ là **tương quan** trong mẫu, không phải tác động nhân quả của chỉ đạo và không phải tác động chính sách thực tế. "
          "Không đề xuất giá trị tham số.\n",
          "## Biến và quy tắc\n",
          "- Dữ liệu: `data/raw/chi_dao_lai_suat_2023_2026.csv` (24 sự kiện). Hai sự kiện 2026Q4 (Công văn 9608/9736) nằm ngoài panel (kết thúc 2026Q3) nên không dùng, để dành cho kiểm định ngoài mẫu.",
          "- **I_q:** 0 = không có văn bản; 1 = có văn bản yêu cầu giảm/ổn định lãi suất (mọi loại trừ `thay_doi_LS_dieu_hanh` và `cong_bo_LS_cho_vay`; kể cả `kiem_tra_thuc_hien`); "
          "2 = có mục tiêu định lượng cho lãi suất cho vay (cột `muc_tieu_dinh_luong` khác rỗng và loại `yeu_cau_giam_LS_cho_vay` hoặc nội dung mục tiêu có chữ \"cho vay\"). Nhiều văn bản trong quý: lấy giá trị lớn nhất.",
          "- **Dời quý (mặc định):** văn bản có ngày đầy đủ ban hành **sau ngày 15 của tháng cuối quý** (3, 6, 9, 12) tính sang quý sau; ngày chỉ có tháng không dời. Chạy thêm bản **không dời** (`khong_dich`) để kiểm tra độ nhạy. Quy tắc này chỉ dời 2 sự kiện: Thông báo ổn định lãi suất 30/3/2026 (2026Q1 → 2026Q2) và QĐ thay đổi lãi suất điều hành 19/6/2023 (2023Q2 → 2023Q3).",
          "- **DH_q:** số quyết định thay đổi lãi suất điều hành (`thay_doi_LS_dieu_hanh`) trong quý (cùng quy tắc dời); đưa vào như biến kiểm soát riêng.",
          "- **Biên thực** `m_{i,t} = loan_rate_pct_t − (deposit_rate_pct_{t−1} + 0.15)` (cơ sở `term`). Mẫu: 8 ngân hàng × 14 quý (2023Q2-2026Q3), N = 112.",
          "- Mô hình: FE ngân hàng (**không** FE quý vì sẽ hấp thụ I_q), kiểm soát `ON_{t−1}`; SE CR1 theo ngân hàng (8 cụm, t với 7 bậc tự do) và wild-cluster bootstrap Webb (B = 9999) cho hệ số `I_t`.\n",
          "## Bảng cường độ I_q theo quý\n", md_table(inten, digits=0),
          "Phân bố I (bản dời quý) trên 15 quý: " + ", ".join(f"I = {k}: {int(v)} quý" for k, v in inten["I_dich_quy"].value_counts().sort_index().items())
          + ". **Khác với kỳ vọng ban đầu \"I_q gần như luôn ≥ 1\"**: có " + str(int((inten["I_dich_quy"] == 0).sum())) + " quý không có văn bản (I = 0) và chỉ "
          + str(int((inten["I_dich_quy"] == 2).sum())) + " quý có mục tiêu định lượng (I = 2: 2023Q3, 2024Q2). Nhận diện vì thế đến từ cả chênh lệch 0 so với ≥ 1 lẫn 1 so với 2, nhưng mức \"I = 2\" chỉ dựa trên hai quý.\n",
          "### Mô tả: biên thực theo mức I\n", md_table(by_i),
          f"Tương quan theo quý (T = 14): corr(I_t, ON_{{t−1}}) = {np.corrcoef(qdesc['I'], qdesc['ON_t-1'])[0, 1]:.2f}; corr(I_t, biên thực) = {np.corrcoef(qdesc['I'], qdesc['bien_thuc_gia_quyen'])[0, 1]:.2f}. "
          "Chỉ đạo tập trung vào các quý lãi suất liên ngân hàng thấp (2023Q3-2025Q1), nên I_t và ON_{t−1} cộng tuyến đáng kể.\n",
          "### Mô tả theo quý\n", md_table(qdesc, digits=3),
          "## Hệ số: dạng tuyến tính (I_t, I_{t−1}), bản dời quý, có kiểm soát DH\n"]
    for outcome, title in (("margin", "Biên thực (mức)"), ("dRL", "Δ lãi suất cho vay"), ("pt1_resid_2step", "Phần dư PT1 (d1), hai bước"),
                           ("pt1_onestep", "PT1 (d1) thêm I_t, I_{t−1}, một bước")):
        md += [f"### {title}\n", md_table(pick("lin", lin_p + (["lambda", "ON_t-1c", "DH_t"] if outcome == "pt1_onestep" else ["DH_t"]))[
            lambda d: d.equation == outcome].drop(columns=["equation"]))]
    md.append("## Hệ số: dạng biến giả (I = 1, I = 2 so với I = 0); biên độ ngụ ý I = 2 so với I = 1\n")
    for outcome, title in (("margin", "Biên thực (mức)"), ("dRL", "Δ lãi suất cho vay"), ("pt1_resid_2step", "Phần dư PT1 (d1), hai bước")):
        md += [f"### {title}\n", md_table(pick("dum", dum_p)[lambda d: d.equation == outcome].drop(columns=["equation"]))]
    if specs is not None:
        scols = ["outcome", "dac_ta", "coef_I_t", "se_cluster", "ci95_lo", "ci95_hi", "r2"]
        md.append("## Độ nhạy theo đặc tả kiểm soát: hệ số của I_t (FE ngân hàng, N = 112)\n")
        md.append("Ở bản dời quý, hệ số dương và lớn (≥ 0.2) của I_t lên biên thực chỉ xuất hiện khi kiểm soát đồng thời `ON_{t−1}` và `I_{t−1}`; không có ON thì gần 0 (I_t và ON_{t−1} tương quan −0.55 và ON_{t−1} có hệ số dương lên biên). Bản không dời quý cho hệ số dương ở nhiều đặc tả hơn. "
                  "Vì vậy hệ số dương KHÔNG đọc được như tác động của biến chỉ đạo thô. Với Δ lãi suất cho vay, hệ số ÂM khi không kiểm soát ON là kết quả đáng lưu ý (phù hợp với giả thuyết chỉ đạo kéo lãi suất xuống), chỉ là không tách được khỏi chu kỳ lãi suất chung.\n")
        md.append(md_table(specs[specs.I_def == "dich_quy"][scols]))
        md.append("Bản không dời quý:\n")
        md.append(md_table(specs[specs.I_def == "khong_dich"][scols]))
    md.append("## Độ nhạy: không dời quý\n")
    for outcome, title in (("margin", "Biên thực (mức)"), ("dRL", "Δ lãi suất cho vay")):
        md += [f"### {title}, tuyến tính, không dời quý\n",
               md_table(pick("lin", lin_p, shift=False)[lambda d: d.equation == outcome].drop(columns=["equation"]))]
    md.append("## Wild-cluster bootstrap Webb cho hệ số I_t (có kiểm soát DH)\n")
    md.append(f"WCR-t, trọng số Webb 6 điểm, B = {int(boot.B.iloc[0])}, seed = {int(boot.seed.iloc[0])}. Với 8 cụm nhưng I_q là biến chung theo quý, **thông tin hiệu dụng cỡ 14 điểm**: bootstrap theo ngân hàng không khắc phục được điều này. `p_boot = 0.0000` nghĩa là p < 1/9999.\n")
    md.append(md_table(boot, ["equation", "I_def", "coef", "se_cr1", "ci_cr1_lo", "ci_cr1_hi", "p_boot", "ci_boot_lo", "ci_boot_hi"]))
    md.append("## Kiểm tra chuỗi thời gian (biên bình quân gia quyền theo quý, T = 14, OLS, SE thường)\n")
    md.append(md_table(qchk))
    md.append(INTERPRETATION)
    md.append("\nFile: estimates_stage7c.csv, bootstrap_stage7c.csv, policy_intensity_stage7c.csv, spec_sensitivity_stage7c.csv.\n")
    (outdir / "estimates_stage7c.md").write_text("\n".join(md), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outdir", default=str(OUTDIR))
    args = ap.parse_args()
    events = load_events()
    est, boot = estimate_all(events)
    inten = intensity_table(events)
    qchk = pd.concat([quarterly_check(events, True), quarterly_check(events, False)], ignore_index=True)
    qdesc, by_i = descriptive(events)
    write_outputs(events, est, boot, inten, qchk, qdesc, by_i, args.outdir, spec_sensitivity(events))
    print(f"Đã ghi kết quả vào {args.outdir}")


if __name__ == "__main__":
    main()
