"""Giai đoạn 9a: kiểm tra sau khi đưa hằng số hành vi ra YAML (thay đổi hành vi = 0).

Sinh reports/stage9a/check_stage9a.json và .md:
  1. Bảng khóa mới: giá trị YAML, mặc định trong code (p.get), giá trị cũ cứng trong agent.
  2. Golden term và golden_total: so khớp bitwise (so sánh chính xác, không dung sai).
  3. Mục 6 CLAUDE.md cho configs/scenarios.yaml và configs/scenarios_macro.yaml (10 seed từ base_seed).

Chạy: python -m src.analysis.check_stage9a
Tất định (seed cố định); chạy lại cho file giống hệt.
"""

import ast
import inspect
import json
from pathlib import Path

import pandas as pd

import src.core.model as model_module
from src.analysis.experiments import load_config
from src.core.model import ABMModel

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports" / "stage9a"
DATA = ROOT / "data/clean/abm_initial_8nganhang_2023Q1.csv"
GOLDEN_SEEDS = (202611, 202612, 202613)
N_RUNS = 10

# Khóa mới và vị trí/giá trị cũ cứng trong code trước Giai đoạn 9a
NEW_KEYS = {
    "target_margin": ("bank.py: Bank(target_margin=3.2)", 3.2),
    "funding_cost_add": ("bank.py: funding_cost + 0.15", 0.15),
    "deposit_ldr_target": ("bank.py: ldr - 0.82", 0.82),
    "demand_pressure_cap": ("bank.py: max(-0.5, min(0.5, .))", 0.5),
    "depositor_base_growth": ("depositors.py: base_growth=0.004", 0.004),
    "depositor_max_growth": ("depositors.py: max_growth=0.04", 0.04),
    "borrower_growth_min": ("borrowers.py: max(-0.04, .)", -0.04),
    "borrower_growth_max": ("borrowers.py: min(0.035, .)", 0.035),
    "compliance_pressure_coef": ("regulator.py: 2.5 * (pressure - .)", 2.5),
    "compliance_pressure_center": ("regulator.py: (pressure - 0.5)", 0.5),
    "compliance_margin_coef": ("regulator.py: 1.1 * (margin - .)", 1.1),
    "compliance_prob_min": ("regulator.py: max(0.02, .)", 0.02),
    "compliance_prob_max": ("regulator.py: min(0.98, .)", 0.98),
}


def code_defaults():
    tree = ast.parse(inspect.getsource(model_module))
    out = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get" and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "p" and len(node.args) == 2
        ):
            out[ast.literal_eval(node.args[0])] = ast.literal_eval(node.args[1])
    return out


def rows():
    return pd.read_csv(DATA).to_dict("records")


def run(cfg, scenario, seed):
    m = ABMModel(scenario, cfg["n_months"], seed, dict(cfg["parameters"]), rows())
    m.run()
    return pd.DataFrame(m.history), pd.DataFrame(m.bank_history)


def golden_check():
    base = load_config()
    out = {}
    for basis, folder in (("term", "golden"), ("total", "golden_total")):
        n_ok = n = 0
        max_abs = 0.0
        for sc in "ABC":
            for seed in GOLDEN_SEEDS:
                cfg = json.loads(json.dumps(base))
                cfg["parameters"]["deposit_rate_basis"] = basis
                frames = dict(zip(("history", "bank_history"), run(cfg, sc, seed)))
                for name, frame in frames.items():
                    exp = pd.read_csv(ROOT / "tests" / folder / f"{name}_{sc}_{seed}.csv",
                                      float_precision="round_trip")
                    got = frame[list(exp.columns)]
                    n += 1
                    if got.equals(exp):
                        n_ok += 1
                    num = exp.select_dtypes("number").columns
                    max_abs = max(max_abs, float((got[num] - exp[num]).abs().max().max()))
        out[basis] = {"files": n, "bitwise_equal": n_ok, "max_abs_diff": max_abs}
    return out


def section6(config_name):
    cfg = load_config(ROOT / "configs" / config_name)
    p = cfg["parameters"]
    policy_q = int(p["policy_month"]) + 1          # cột month của quý kích hoạt đầu tiên
    res = {"config": config_name, "runs": N_RUNS, "policy_first_month": policy_q}
    worst_gap = {"B": -1e9, "C": -1e9}
    pre_max_diff = 0.0
    lo_rate = {"loan": 1e9, "deposit": 1e9}
    hi_rate = {"loan": -1e9, "deposit": -1e9}
    max_ldr_slack = -1e9
    mean_post = {"A": [], "B": [], "C": []}
    for i in range(N_RUNS):
        seed = int(cfg["base_seed"]) + i
        out = {sc: run(cfg, sc, seed) for sc in "ABC"}
        hA, bA = out["A"]
        for sc in "ABC":
            h, b = out[sc]
            post = h[h.month >= policy_q]
            mean_post[sc].append(float(post.loan_rate.mean()))
            if sc != "A":
                gap = (post.loan_rate.values - hA[hA.month >= policy_q].loan_rate.values).max()
                worst_gap[sc] = max(worst_gap[sc], float(gap))
                pre = b[b.month < policy_q].reset_index(drop=True)
                preA = bA[bA.month < policy_q].reset_index(drop=True)
                num = ["deposits", "loans", "deposit_rate", "loan_rate"]
                pre_max_diff = max(pre_max_diff, float((pre[num] - preA[num]).abs().max().max()))
            lo_rate["loan"] = min(lo_rate["loan"], float(b.loan_rate.min()))
            hi_rate["loan"] = max(hi_rate["loan"], float(b.loan_rate.max()))
            lo_rate["deposit"] = min(lo_rate["deposit"], float(b.deposit_rate.min()))
            hi_rate["deposit"] = max(hi_rate["deposit"], float(b.deposit_rate.max()))
            slack = (b.loans - b.deposits * float(p["max_loan_to_deposit"])).max()
            max_ldr_slack = max(max_ldr_slack, float(slack))
    # Độ trễ: quý đầu, loan_rate dùng chi phí vốn ĐẦU kỳ (lagged), không phải chi phí vốn cuối quý.
    m = ABMModel("A", 1, int(cfg["base_seed"]), dict(p), rows())
    lag0 = [b.lagged_funding_cost for b in m.banks]
    r0 = [b.loan_rate for b in m.banks]
    m.step()
    err_lag = err_now = 0.0
    for b, fc0, r in zip(m.banks, lag0, r0):
        pred_lag = r + m.pass_through * (fc0 + b.target_margin + m.loan_spread_add - r)
        pred_now = r + m.pass_through * (b.funding_cost + b.target_margin + m.loan_spread_add - r)
        err_lag = max(err_lag, abs(b.loan_rate - pred_lag))
        err_now = max(err_now, abs(b.loan_rate - pred_now))
    res.update({
        "max_B_minus_A_loan_rate_after_policy": worst_gap["B"],
        "max_C_minus_A_loan_rate_after_policy": worst_gap["C"],
        "mean_loan_rate_after_policy": {k: sum(v) / len(v) for k, v in mean_post.items()},
        "max_abs_diff_BC_vs_A_before_policy": pre_max_diff,
        "loan_rate_min": lo_rate["loan"], "loan_rate_max": hi_rate["loan"],
        "deposit_rate_min": lo_rate["deposit"], "deposit_rate_max": hi_rate["deposit"],
        "max_loans_minus_ldr_limit": max_ldr_slack,
        "lag_check_first_quarter_max_err_lagged": err_lag,
        "lag_check_first_quarter_max_err_current": err_now,
    })
    res["pass"] = bool(
        worst_gap["B"] <= 1e-12 and worst_gap["C"] <= 1e-12 and pre_max_diff == 0.0
        and 0 <= lo_rate["loan"] and hi_rate["loan"] <= 20
        and 0 <= lo_rate["deposit"] and hi_rate["deposit"] <= 14
        and max_ldr_slack <= 1e-9 and err_lag < 1e-12 and err_now > err_lag
    )
    return res


def main():
    p = load_config()["parameters"]
    defaults = code_defaults()
    keys = [
        {"key": k, "old_location": loc, "old_value": old, "yaml": p.get(k), "code_default": defaults.get(k),
         "equal": p.get(k) == defaults.get(k) == old}
        for k, (loc, old) in NEW_KEYS.items()
    ]
    all_keys_equal = all(defaults.get(k) == v for k, v in p.items())
    result = {
        "new_keys": keys,
        "all_yaml_keys_code_default_equal": all_keys_equal,
        "n_yaml_parameter_keys": len(p),
        "golden": golden_check(),
        "section6": [section6("scenarios.yaml"), section6("scenarios_macro.yaml")],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "check_stage9a.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = ["# Giai đoạn 9a – kiểm tra hằng số đưa ra YAML (sinh tự động bởi `src/analysis/check_stage9a.py`)", "",
             "## 1. Khóa mới (giá trị YAML = mặc định code = giá trị cũ cứng trong agent)", "",
             "| Khóa | Vị trí cũ | Giá trị cũ | YAML | Mặc định code | Khớp |", "|---|---|---:|---:|---:|---|"]
    for r in keys:
        lines.append(f"| `{r['key']}` | {r['old_location']} | {r['old_value']} | {r['yaml']} | {r['code_default']} | "
                     f"{'có' if r['equal'] else 'KHÔNG'} |")
    lines += ["", f"Mọi {len(p)} khóa trong `parameters` của `configs/scenarios.yaml` có mặc định code trùng YAML: "
              f"{'có' if all_keys_equal else 'KHÔNG'}.", "", "## 2. Golden (so khớp chính xác từng bit)", "",
              "| Cơ sở | Số file | Khớp bitwise | Sai lệch tuyệt đối lớn nhất |", "|---|---:|---:|---:|"]
    for basis, g in result["golden"].items():
        lines.append(f"| {basis} | {g['files']} | {g['bitwise_equal']} | {g['max_abs_diff']:.3g} |")
    lines += ["", f"## 3. Mục 6 CLAUDE.md ({N_RUNS} seed từ base_seed, dữ liệu 8 NH 2023Q1)", "",
              "| Cấu hình | max(B−A) sau CS | max(C−A) sau CS | TB LS cho vay sau CS A / B / C | max lệch trước CS | "
              "LS cho vay [min; max] | LS huy động [min; max] | max(loans − LDR·deposits) | trễ: sai số dùng lagged / dùng hiện tại | ĐẠT |",
              "|---|---:|---:|---|---:|---|---|---:|---|---|"]
    for s in result["section6"]:
        mp = s["mean_loan_rate_after_policy"]
        lines.append(
            f"| `{s['config']}` | {s['max_B_minus_A_loan_rate_after_policy']:.4f} | {s['max_C_minus_A_loan_rate_after_policy']:.4f} | "
            f"{mp['A']:.4f} / {mp['B']:.4f} / {mp['C']:.4f} | {s['max_abs_diff_BC_vs_A_before_policy']:.3g} | "
            f"[{s['loan_rate_min']:.3f}; {s['loan_rate_max']:.3f}] | [{s['deposit_rate_min']:.3f}; {s['deposit_rate_max']:.3f}] | "
            f"{s['max_loans_minus_ldr_limit']:.4g} | {s['lag_check_first_quarter_max_err_lagged']:.2g} / "
            f"{s['lag_check_first_quarter_max_err_current']:.4f} | {'có' if s['pass'] else 'KHÔNG'} |")
    lines += ["", "Ghi chú: “sau CS” = các quý có `month` ≥ policy_month + 1 (từ 2026Q4). Kiểm tra trễ: ở quý đầu, "
              "`loan_rate` khớp công thức dùng `lagged_funding_cost` đầu kỳ (sai số ~0) và lệch nếu dùng chi phí vốn cuối quý.", ""]
    (OUT / "check_stage9a.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
