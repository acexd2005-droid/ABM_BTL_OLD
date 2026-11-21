"""Test chẩn đoán GD9b (vòng sửa 2): tái lập, không đổi YAML, và các quan hệ định tính của chẩn đoán."""
import filecmp
from pathlib import Path

import pandas as pd

from src.calibration import calibrate_stage9b as c9b
from src.calibration import diag_gd9b as dg

ROOT = Path(__file__).resolve().parents[1]


def test_diag_tai_lap_va_khong_doi_yaml(tmp_path):
    yml = ROOT / "configs/scenarios_calibrated.yaml"
    before = yml.read_bytes()
    # đầu vào (bu_tang_truong, growth_ldr) đọc từ thư mục kết quả đã có
    df = dg.main(tmp_path)
    assert yml.read_bytes() == before
    assert filecmp.cmp(tmp_path / "diag_gd9b.csv", c9b.OUTDIR / "diag_gd9b.csv", shallow=False)
    v = df.set_index(["phan", "cau_hinh", "chi_tieu"]).gia_tri
    # có bù: không chạm trần; bỏ bù: chạm trần (hệ quả của bù Q7)
    assert v["bo_bu", "GD9b_co_bu", "ty_le_cham_tran_LDR_month_1_18"] == 0
    assert v["bo_bu", "GD9b_bo_bu_CHAN_DOAN", "ty_le_cham_tran_LDR_month_1_18"] > 0.1
    # biên theo hai định nghĩa khác nhau
    b = v["bien", "GD9b", "bien_loan_rate_tru_chi_phi_von_tre_tb"]
    assert b > v["bien", "GD9b", "bien_loan_rate_tru_deposit_rate_tb"]
    # nhánh áp lực huy động: GD9b ít bị kích hoạt hơn GD9
    assert (v["canh_tranh_huy_dong", "GD9b", "ty_le_ldr_tren_nguong_A_sau_CS"]
            < v["canh_tranh_huy_dong", "GD9", "ty_le_ldr_tren_nguong_A_sau_CS"])
    assert (abs(v["canh_tranh_huy_dong", "GD9b", "deposit_rate_C_tru_B_sau_CS"])
            < abs(v["canh_tranh_huy_dong", "GD9", "deposit_rate_C_tru_B_sau_CS"]))
