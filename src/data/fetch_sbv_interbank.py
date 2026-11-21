"""Tải lãi suất liên ngân hàng VND bình quân theo ngày từ Cổng TTĐT NHNN
và tính bình quân theo quý / tháng cho kỳ hạn qua đêm.

Nguồn: trang "Lãi suất thị trường liên ngân hàng" của NHNN
  https://sbv.gov.vn/vi/lãi-suất-thị-trường-liên-ngân-hàng
Trang này đọc dữ liệu từ API Liferay headless-delivery (content structure 3450260).
Mỗi bản ghi = một phiên: ngày áp dụng + lãi suất BQ và doanh số theo 7 kỳ hạn.

Cách xử lý (đã đối chiếu với số liệu công bố):
  - Ngày phiên = trường "ngayApDung" đổi sang giờ Việt Nam (UTC+7).
    KHÔNG dùng datePublished: từ cuối 2025 ngày đăng lệch ngày phiên.
  - Một ngày có nhiều bản ghi -> giữ bản ghi có id lớn nhất (mới nhất).
  - Bỏ bản ghi "lặp" (lãi suất và doanh số trùng hệt phiên liền trước):
    NHNN đăng lại số của phiên trước vào ngày nghỉ.
  - Bình quân giản đơn theo phiên và bình quân gia quyền theo doanh số.

Chạy:  python src/data/fetch_sbv_interbank.py --outdir data/raw
Cần: pandas. Chỉ dùng thư viện chuẩn để gọi mạng.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from datetime import timedelta, timezone
from pathlib import Path

import pandas as pd

BASE = "https://sbv.gov.vn/o/headless-delivery/v1.0/content-structures/3450260/structured-contents"
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (ABM_BTL research)",
    "Referer": "https://sbv.gov.vn/vi/l%C3%A3i-su%E1%BA%A5t-th%E1%BB%8B-tr%C6%B0%E1%BB%9Dng-li%C3%AAn-ng%C3%A2n-h%C3%A0ng",
}
VN = timezone(timedelta(hours=7))


def _num(s: str | None) -> float:
    """'1.032.230' -> 1032230 ; '4,68' -> 4.68"""
    if s in (None, ""):
        return float("nan")
    return float(str(s).replace(".", "").replace(",", "."))


def _get(url: str, retries: int = 5) -> dict:
    waits = [15, 30, 60, 120]
    for k in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            if k == retries - 1:
                raise
            w = waits[min(k, len(waits) - 1)]
            print(f"  lỗi ({e}), chờ {w}s rồi thử lại")
            time.sleep(w)
    raise RuntimeError("unreachable")


def fetch_month(y: int, m: int) -> list[dict]:
    a = f"{y}-{m:02d}-01T00:00:00.000Z"
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    b = f"{ny}-{nm:02d}-01T00:00:00.000Z"
    flt = f"datePublished ge {a} and datePublished lt {b}"
    rows, page = [], 1
    while True:
        url = f"{BASE}?filter={urllib.parse.quote(flt)}&pageSize=100&page={page}"
        j = _get(url)
        for it in j.get("items", []):
            f = it["contentFields"]
            ngay = next((x["contentFieldValue"].get("data", "") for x in f if x["name"] == "ngayApDung"), "")
            for x in f:
                if x["name"] != "laiSuatThiTruongNganHangs":
                    continue
                g = {y_["name"]: y_["contentFieldValue"].get("data", "") for y_ in x["nestedContentFields"]}
                rows.append({
                    "id": it["id"],
                    "date_published": it["datePublished"],
                    "ngay_ap_dung_utc": ngay,
                    "ky_han": g.get("thoihan", ""),
                    "lai_suat": _num(g.get("laiSuatBQLienNganHang")),
                    "doanh_so_ty": _num(g.get("doanhSo")),
                })
        if page >= j.get("lastPage", 1):
            break
        page += 1
    return rows


def months(frm: str, to: str):
    y, m = map(int, frm.split("-"))
    ty, tm = map(int, to.split("-"))
    while (y, m) <= (ty, tm):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def clean_overnight(raw: pd.DataFrame) -> pd.DataFrame:
    on = raw[raw["ky_han"] == "Qua đêm"].copy()
    on["ngay"] = (pd.to_datetime(on["ngay_ap_dung_utc"], utc=True)
                  .dt.tz_convert(VN).dt.date.astype(str))
    on = on.sort_values(["ngay", "id"], ascending=[True, False]).drop_duplicates("ngay")
    on = on.sort_values("ngay").reset_index(drop=True)
    same = (on["lai_suat"] == on["lai_suat"].shift()) & (on["doanh_so_ty"] == on["doanh_so_ty"].shift())
    on["lap_phien_truoc"] = same
    return on[["ngay", "lai_suat", "doanh_so_ty", "lap_phien_truoc", "id", "date_published"]]


def aggregate(on: pd.DataFrame, freq: str) -> pd.DataFrame:
    d = on[~on["lap_phien_truoc"]].copy()
    d["ky"] = pd.PeriodIndex(pd.to_datetime(d["ngay"]), freq=freq).astype(str)
    d["rv"] = d["lai_suat"] * d["doanh_so_ty"]
    g = d.groupby("ky")
    out = pd.DataFrame({
        "so_phien": g.size(),
        "bq_gian_don": g["lai_suat"].mean().round(3),
        "bq_gia_quyen_doanh_so": (g["rv"].sum() / g["doanh_so_ty"].sum()).round(3),
        "trung_vi": g["lai_suat"].median().round(2),
        "min": g["lai_suat"].min(),
        "max": g["lai_suat"].max(),
        "phien_dau": g["ngay"].min(),
        "phien_cuoi": g["ngay"].max(),
        "gia_tri_cuoi_ky": g["lai_suat"].last(),
    })
    return out.reset_index()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="frm", default="2022-12")
    ap.add_argument("--to", dest="to", default="2026-10")
    ap.add_argument("--outdir", default="data/raw")
    ap.add_argument("--start-date", default="2023-01-01")
    ap.add_argument("--end-date", default="2026-09-30")
    a = ap.parse_args()

    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    cache = out / "_cache_sbv"
    cache.mkdir(exist_ok=True)
    for y, m in months(a.frm, a.to):
        cf = cache / f"{y}-{m:02d}.json"
        if cf.exists():
            r = json.loads(cf.read_text())
            print(f"{y}-{m:02d}: {len(r)} dòng (cache)")
        else:
            r = fetch_month(y, m)
            cf.write_text(json.dumps(r, ensure_ascii=False))
            print(f"{y}-{m:02d}: {len(r)} dòng")
            time.sleep(3)
        rows += r
    raw = pd.DataFrame(rows)
    raw.to_csv(out / "sbv_lnh_tat_ca_ky_han_theo_ngay.csv", index=False)

    on = clean_overnight(raw)
    on.to_csv(out / "sbv_lnh_qua_dem_theo_ngay.csv", index=False)
    win = on[(on["ngay"] >= a.start_date) & (on["ngay"] <= a.end_date)]
    aggregate(win, "Q").rename(columns={"ky": "quy"}).to_csv(out / "sbv_lnh_qua_dem_theo_quy.csv", index=False)
    aggregate(win, "M").rename(columns={"ky": "thang"}).to_csv(out / "sbv_lnh_qua_dem_theo_thang.csv", index=False)
    print(f"Xong: {len(on)} phiên. Bỏ {int(on['lap_phien_truoc'].sum())} bản ghi lặp. File ở {out}/")


if __name__ == "__main__":
    main()
