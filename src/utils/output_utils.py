
from pathlib import Path
from datetime import datetime


ROOT = Path(__file__).resolve().parents[2]


def create_run_folder(run_type="KichBan"):
    """Tạo thư mục riêng cho mỗi lần chạy chương trình."""

    output_root = ROOT / "outputs"
    output_root.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S_%f"
    )

    folder = output_root / f"{timestamp}_{run_type}"

    # Không ghi đè thư mục đã tồn tại
    folder.mkdir(parents=True, exist_ok=False)

    return folder
