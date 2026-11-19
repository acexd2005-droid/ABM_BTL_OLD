
"""Kiểm tra logic và các đặc điểm mô phỏng ABM.

Đây là kiểm tra mô hình, không phải kiểm định
kinh tế lượng hoặc kiểm định dự báo ngoài mẫu.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..core.model import ABMModel
from .experiments import load_config


ROOT = Path(__file__).resolve().parents[2]

DEFAULT_BANKS = (
    ROOT
    / "data"
    / "clean"
    / "abm_initial_8nganhang_2023Q1.csv"
)


def run_validation(banks=None, config_path=None):

    cfg = load_config(config_path)

    params = dict(cfg["parameters"])
    n_steps = int(cfg["n_months"])
    policy_month = int(params["policy_month"])
    max_ratio = float(params["max_loan_to_deposit"])

    seed = int(cfg["base_seed"])

    # Mặc định ưu tiên dữ liệu 8 ngân hàng
    if banks is None and DEFAULT_BANKS.is_file():
        banks = DEFAULT_BANKS

    bank_rows = None

    if banks is not None:
        bank_rows = pd.read_csv(banks).to_dict("records")

    def run_scenario(scenario):
        model = ABMModel(
            scenario=scenario,
            n_months=n_steps,
            seed=seed,
            parameters=dict(params),
            initial_banks=bank_rows,
        )

        result = model.run().copy()

        return model, result

    # Chạy ba kịch bản với cùng seed
    model_a, a = run_scenario("A")
    model_b, b = run_scenario("B")
    model_c, c = run_scenario("C")

    # Chạy lặp lại A để kiểm tra tái lập
    _, a_repeat = run_scenario("A")

    # Giai đoạn trước khi chính sách kích hoạt
    before_a = a[a["month"] <= policy_month]
    before_b = b[b["month"] <= policy_month]
    before_c = c[c["month"] <= policy_month]

    # Giai đoạn sau khi chính sách kích hoạt
    after_a = a[a["month"] > policy_month]
    after_b = b[b["month"] > policy_month]
    after_c = c[c["month"] > policy_month]

    if after_a.empty:
        raise ValueError(
            "Thời gian mô phỏng chưa bao gồm "
            "giai đoạn sau chính sách."
        )

    def same_rates(left, right):
        return (
            len(left) == len(right)
            and np.allclose(
                left["loan_rate"].to_numpy(),
                right["loan_rate"].to_numpy(),
                rtol=0,
                atol=1e-10,
            )
        )

    def within_bounds(frame):
        values = frame[
            [
                "loan_rate",
                "deposit_rate",
                "loan_deposit_ratio",
            ]
        ].to_numpy(dtype=float)

        return bool(
            np.isfinite(values).all()
            and (frame["loan_rate"] >= 0).all()
            and (frame["deposit_rate"] >= 0).all()
            and (
                frame["loan_deposit_ratio"]
                <= max_ratio + 1e-8
            ).all()
        )

    checks = {
        "dung_so_buoc_mo_phong": bool(
            len(a) == n_steps
            and len(b) == n_steps
            and len(c) == n_steps
        ),

        "khong_can_thiep_truoc_chinh_sach": bool(
            same_rates(before_a, before_b)
            and same_rates(before_a, before_c)
        ),

        "kich_ban_B_giam_lai_suat_so_voi_A": bool(
            after_b["loan_rate"].mean()
            < after_a["loan_rate"].mean()
        ),

        "kich_ban_C_giam_lai_suat_huy_dong_so_voi_B": bool(
            after_c["deposit_rate"].mean()
            < after_b["deposit_rate"].mean()
        ),

        "kiem_tra_gioi_han_du_no_tien_gui": bool(
            all(
                within_bounds(x)
                for x in (a, b, c)
            )
        ),

        "co_the_tai_lap_cung_seed": bool(
            a.reset_index(drop=True).equals(
                a_repeat.reset_index(drop=True)
            )
        ),
    }

    if bank_rows is not None:
        checks["dung_so_ngan_hang_khoi_tao"] = bool(
            len(model_a.banks) == len(bank_rows)
        )

    output = ROOT / "outputs"
    output.mkdir(parents=True, exist_ok=True)

    report = {
        "loai_kiem_tra": "Kiem tra logic mo phong ABM",
        "nguon_du_lieu": (
            str(banks) if banks is not None
            else "Du lieu demo"
        ),
        "so_buoc_mo_phong": n_steps,
        "policy_month": policy_month,
        "buoc_chinh_sach_dau_tien": policy_month + 1,
        "so_ngan_hang": len(model_a.banks),
        "seed": seed,
        "gioi_han_du_no_tien_gui": max_ratio,
        "checks": checks,
        "all_passed": all(checks.values()),
        "ghi_chu": (
            "Ket qua chi xac nhan cac quy tac "
            "duoc kiem tra. Chua chung minh "
            "mo hinh phu hop voi du lieu thuc te."
        ),
    }

    report_path = (
        output / "validation_8_ngan_hang.json"
    )

    report_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\nKẾT QUẢ KIỂM TRA MÔ HÌNH ABM")
    print(f"Số ngân hàng: {len(model_a.banks)}")
    print(f"Số quý mô phỏng: {n_steps}")
    print(
        f"Chính sách bắt đầu tại bước: "
        f"{policy_month + 1}"
    )

    for name, passed in checks.items():
        status = "ĐẠT" if passed else "CHƯA ĐẠT"
        print(f"{status}: {name}")

    print("\nKết quả tổng hợp:", report["all_passed"])
    print("File kết quả:", report_path)

    return checks


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--banks",
        default=None,
        help="CSV khởi tạo các ngân hàng",
    )

    parser.add_argument(
        "--config",
        default=None,
        help="Đường dẫn đến scenarios.yaml",
    )

    args = parser.parse_args()

    run_validation(
        banks=args.banks,
        config_path=args.config,
    )


if __name__ == "__main__":
    main()
