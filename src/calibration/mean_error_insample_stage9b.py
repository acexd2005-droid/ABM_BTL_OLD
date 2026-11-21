"""GD10b bước 4 (Q14): sai lệch mức TRONG MẪU (2023Q2–2025Q2, month 1–9) của GD9b và GD9, kịch bản A.

Chỉ đọc: không đổi nghiệm, không đổi YAML. Tính sai số trung bình có dấu (mô hình − thực), RMSE thô và RMSE khử mức
cho LS cho vay và LS huy động (cơ sở dữ liệu, gia quyền tiền gửi). Chuỗi mô phỏng/thực lấy đúng hàm của GD9
(`c9.simulate`, `actual_series`) nên khớp `oos_stage9b.csv` (cột *_trong_mau).
Ghi: reports/calibration/stage9b/mean_error_insample_stage9b.csv
Chạy: python -m src.calibration.mean_error_insample_stage9b
"""

import argparse
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from ..analysis.compare_deposit_basis import actual_series
from ..analysis.experiments import load_config
from . import calibrate_stage9 as c9

ROOT = c9.ROOT
OUT = ROOT / "reports/calibration/stage9b/mean_error_insample_stage9b.csv"
CONFIGS = {"GD9b": ROOT / "configs/scenarios_calibrated.yaml", "GD9": ROOT / "configs/scenarios_calibrated_gd9.yaml"}


def compute():
    rows = pd.read_csv(c9.BANKS).to_dict("records")
    with tempfile.TemporaryDirectory() as td:       # actual_series ghi một file phụ vào thư mục này
        act = actual_series(Path(td)).sort_values("month").reset_index(drop=True)
    act = act[act.month <= c9.N_SIM]
    a, b = c9.CAL_MONTHS
    sl = slice(a - 1, b)
    quarters = list(act.quarter)
    recs = []
    for name, path in CONFIGS.items():
        cfg = load_config(path)
        loan, dep, _ = c9.simulate(dict(cfg["parameters"]), rows, cfg=cfg)
        for lab, x, col in (("cho_vay", loan, "actual_loan_rate"), ("huy_dong", dep, "actual_deposit_rate")):
            e = np.asarray(x)[sl] - act[col].to_numpy()[sl]
            recs.append({"cau_hinh": name, "chuoi": lab, "cua_so": f"{quarters[a - 1]}-{quarters[b - 1]}", "n_quy": int(len(e)),
                         "sai_so_tb_co_dau_trong_mau": float(e.mean()),
                         "RMSE_tho_trong_mau": c9.rmse(e), "RMSE_khu_muc_trong_mau": float(np.std(e, ddof=0))})
    return pd.DataFrame(recs)


def main(out=OUT):
    df = compute()
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, float_format="%.10g")
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    print(main(a.out).to_string(index=False))
