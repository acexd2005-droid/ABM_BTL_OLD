"""Sinh dải độ nhạy quanh tham số cơ sở trong configs/scenarios.yaml.

Ba điểm thấp / cơ sở / cao. Đây là phân tích độ nhạy một tham số
(OAT), không phải khoảng tin cậy hay kết quả ước lượng.
"""

SENSITIVE_PARAMETERS = (
    "pass_through",
    "depositor_sensitivity",
    "policy_pressure",
)


def make_sensitivity_grid(config):
    """Dùng một nguồn YAML cho cả experiments và advanced_analysis."""
    p = config["parameters"]
    relative_width = float(config.get("sensitivity_relative_width", 0.30))
    if not 0 < relative_width < 1:
        raise ValueError("sensitivity_relative_width phải nằm trong (0, 1)")

    grid = {}
    for key in SENSITIVE_PARAMETERS:
        baseline = float(p[key])
        if not 0 < baseline < 1:
            raise ValueError(f"{key} phải nằm trong (0, 1): {baseline}")

        lower = max(0.0, baseline * (1 - relative_width))
        upper = min(1.0, baseline * (1 + relative_width))
        values = [lower, baseline, upper]
        if len(set(values)) != 3:
            raise ValueError(f"Không đủ 3 mức độ nhạy cho {key}")
        grid[key] = values
    return grid
