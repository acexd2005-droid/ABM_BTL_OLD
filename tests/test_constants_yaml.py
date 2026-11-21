"""Giai đoạn 9a: hằng số hành vi còn lại được đưa ra YAML, thay đổi hành vi = 0.

- Mặc định trong code (p.get(..., mặc định) của ABMModel) trùng YAML cho MỌI khóa.
- Golden `term` và `golden_total` khớp bitwise (check_exact).
- Mỗi khóa mới thực sự có tác dụng; giá trị không hợp lệ bị từ chối.
"""

import ast
import inspect
from pathlib import Path

import pandas as pd
import pytest
import yaml

import src.core.model as model_module
from src.agents.bank import Bank
from src.agents.borrowers import BorrowerBlock
from src.agents.depositors import DepositorBlock
from src.agents.regulator import Regulator
from src.core.model import ABMModel

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests" / "golden"
GOLDEN_TOTAL = ROOT / "tests" / "golden_total"
SEEDS = (202611, 202612, 202613)
DATA = ROOT / "data/clean/abm_initial_8nganhang_2023Q1.csv"

# Khóa mới của Giai đoạn 9a và giá trị cũ cứng trong code
NEW_KEYS = {
    "target_margin": 3.2,
    "funding_cost_add": 0.15,
    "deposit_ldr_target": 0.82,
    "demand_pressure_cap": 0.5,
    "depositor_base_growth": 0.004,
    "depositor_max_growth": 0.04,
    "borrower_growth_min": -0.04,
    "borrower_growth_max": 0.035,
    "compliance_pressure_coef": 2.5,
    "compliance_pressure_center": 0.5,
    "compliance_margin_coef": 1.1,
    "compliance_prob_min": 0.02,
    "compliance_prob_max": 0.98,
}


def load_config():
    with open(ROOT / "configs/scenarios.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def rows():
    return pd.read_csv(DATA).to_dict("records")


def code_defaults():
    """Mọi lời gọi p.get("khóa", hằng) trong ABMModel.__init__ -> {khóa: hằng}."""
    tree = ast.parse(inspect.getsource(model_module))
    out = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "p"
            and len(node.args) == 2
        ):
            key = ast.literal_eval(node.args[0])
            out[key] = ast.literal_eval(node.args[1])
    return out


def test_new_keys_in_yaml_with_old_values():
    p = load_config()["parameters"]
    for key, old in NEW_KEYS.items():
        assert key in p, key
        assert p[key] == old, key


def test_code_defaults_equal_yaml_for_every_key():
    p = load_config()["parameters"]
    defaults = code_defaults()
    # Mọi khóa YAML đều được mô hình đọc, và mặc định code = YAML (kiểu và giá trị)
    assert set(p) <= set(defaults), set(p) - set(defaults)
    for key, value in p.items():
        assert defaults[key] == value, (key, defaults[key], value)
        assert type(defaults[key]) is type(value) or {type(defaults[key]), type(value)} <= {int, float}, key
    for key in NEW_KEYS:
        assert key in defaults, key


def test_agent_constructor_defaults_match_yaml():
    p = load_config()["parameters"]
    sig = lambda cls: inspect.signature(cls.__init__).parameters
    assert sig(Bank)["target_margin"].default == p["target_margin"]
    assert sig(DepositorBlock)["base_growth"].default == p["depositor_base_growth"]
    assert sig(DepositorBlock)["max_growth"].default == p["depositor_max_growth"]
    assert sig(BorrowerBlock)["growth_min"].default == p["borrower_growth_min"]
    assert sig(BorrowerBlock)["growth_max"].default == p["borrower_growth_max"]
    assert sig(BorrowerBlock)["base_growth"].default == p["borrower_base_growth"]
    assert sig(BorrowerBlock)["reference_rate"].default == p["borrower_reference_rate"]
    assert sig(Regulator)["pressure_coef"].default == p["compliance_pressure_coef"]
    assert sig(Regulator)["pressure_center"].default == p["compliance_pressure_center"]
    assert sig(Regulator)["margin_coef"].default == p["compliance_margin_coef"]
    assert sig(Regulator)["prob_min"].default == p["compliance_prob_min"]
    assert sig(Regulator)["prob_max"].default == p["compliance_prob_max"]
    assert sig(Regulator)["margin_floor"].default == p["margin_floor"]


def test_model_reads_new_keys():
    cfg = load_config()
    m = ABMModel("A", 1, 1, dict(cfg["parameters"]), rows())
    assert m.funding_cost_add == 0.15
    assert m.deposit_ldr_target == 0.82
    assert m.demand_pressure_cap == 0.5
    assert m.initial_target_margin == 3.2
    assert all(b.target_margin == 3.2 for b in m.banks)
    assert m.depositor.base_growth == 0.004 and m.depositor.max_growth == 0.04
    assert m.borrower.growth_min == -0.04 and m.borrower.growth_max == 0.035
    r = m.regulator
    assert (r.pressure_coef, r.pressure_center, r.margin_coef, r.prob_min, r.prob_max) == (
        2.5, 0.5, 1.1, 0.02, 0.98
    )


def _run(scenario, seed, params, data=True, n=None):
    cfg = load_config()
    m = ABMModel(scenario, n or cfg["n_months"], seed, params, rows() if data else None)
    m.run()
    return pd.DataFrame(m.history), pd.DataFrame(m.bank_history)


@pytest.mark.parametrize("data", (True, False))
@pytest.mark.parametrize("scenario", "ABC")
def test_empty_parameters_equal_yaml_bitwise(scenario, data):
    """Bỏ hết khóa mới khỏi tham số => mặc định code cho kết quả y hệt YAML."""
    p = dict(load_config()["parameters"])
    stripped = {k: v for k, v in p.items() if k not in NEW_KEYS}
    for a, b in zip(_run(scenario, 202611, p, data), _run(scenario, 202611, stripped, data)):
        pd.testing.assert_frame_equal(a, b, check_exact=True)


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("scenario", "ABC")
@pytest.mark.parametrize("basis,folder", (("term", GOLDEN), ("total", GOLDEN_TOTAL)))
def test_golden_bitwise(scenario, seed, basis, folder):
    p = dict(load_config()["parameters"])
    p["deposit_rate_basis"] = basis
    history, bank_history = _run(scenario, seed, p)
    for name, frame in (("history", history), ("bank_history", bank_history)):
        expected = pd.read_csv(folder / f"{name}_{scenario}_{seed}.csv", float_precision="round_trip")
        pd.testing.assert_frame_equal(frame[list(expected.columns)], expected, check_exact=True)


def test_agent_sources_have_no_old_literals():
    """Các hằng số đã đưa ra YAML không còn xuất hiện trong công thức của agent."""
    def code(cls):
        src = inspect.getsource(cls)
        return "\n".join(line.split("#")[0] for line in src.splitlines())
    assert "0.82" not in code(Bank.step) and "0.5" not in code(Bank.step)
    fc = code(Bank.funding_cost.fget).split('"""')[-1]
    assert "0.15" not in fc and "funding_cost_add" in fc
    assert "0.04" not in code(BorrowerBlock.desired_growth) and "0.035" not in code(BorrowerBlock.desired_growth)
    body = code(Regulator.compliance_probability)
    for lit in ("2.5", "1.1", "0.02", "0.98"):
        assert lit not in body, lit


# ---------- Mỗi khóa mới có tác dụng ----------

def _params(**over):
    p = dict(load_config()["parameters"])
    p.update(over)
    return p


def test_funding_cost_add_effect():
    m = ABMModel("A", 1, 1, _params(funding_cost_add=0.40), rows())
    for b in m.banks:
        assert b.funding_cost == pytest.approx(b.deposit_rate * (1 - b.casa_ratio) + 0.40, abs=1e-12)
        assert b.lagged_funding_cost == pytest.approx(b.funding_cost, abs=1e-12)


def test_ldr_target_and_cap_effect():
    # demand_pressure_cap = 0 => deposit_competition không có tác dụng, lãi suất huy động tăng đúng base_step
    m = ABMModel("A", 1, 1, _params(demand_pressure_cap=0.0), rows())
    before = [b.deposit_rate for b in m.banks]
    m.step()
    for b, r0 in zip(m.banks, before):
        assert b.deposit_rate == pytest.approx(min(14.0, r0 + m.base_deposit_rate_step), abs=1e-12)
    # Ngưỡng LDR cao hơn => áp lực huy động thấp hơn => lãi suất huy động không cao hơn (thấp hơn ở NH chưa chạm chặn)
    base = ABMModel("A", 1, 1, _params(), rows())
    alt = ABMModel("A", 1, 1, _params(deposit_ldr_target=0.92), rows())
    base.step(); alt.step()
    for b0, b1 in zip(base.banks, alt.banks):
        assert b1.deposit_rate <= b0.deposit_rate + 1e-12
    assert any(b1.deposit_rate < b0.deposit_rate - 1e-6 for b0, b1 in zip(base.banks, alt.banks))


def test_depositor_growth_parameters_effect():
    m = ABMModel("A", 1, 1, _params(depositor_base_growth=0.01, depositor_max_growth=0.02), rows())
    assert m.depositor.growth(5.0, 5.0) == pytest.approx(0.01)
    assert m.depositor.growth(50.0, 0.0) == pytest.approx(0.02)
    assert m.depositor.growth(0.0, 50.0) == pytest.approx(-0.02)


def test_borrower_growth_bounds_effect():
    m = ABMModel("A", 1, 1, _params(borrower_growth_min=-0.01, borrower_growth_max=0.02), rows())
    assert m.borrower.desired_growth(0.0) == pytest.approx(0.02)
    assert m.borrower.desired_growth(20.0) == pytest.approx(-0.01)
    with pytest.raises(ValueError):
        ABMModel("A", 1, 1, _params(borrower_growth_min=0.05, borrower_growth_max=0.02), rows())


def test_compliance_parameters_effect():
    m = ABMModel("B", 1, 1, _params(compliance_prob_min=1.0, compliance_prob_max=1.0), rows())
    assert m.regulator.compliance_probability(-100.0) == 1.0
    m = ABMModel("B", 1, 1, _params(compliance_margin_coef=0.0, compliance_pressure_coef=0.0), rows())
    assert m.regulator.compliance_probability(10.0) == pytest.approx(0.5)
    m = ABMModel("B", 1, 1, _params(compliance_pressure_center=0.65, compliance_margin_coef=0.0), rows())
    assert m.regulator.compliance_probability(3.0) == pytest.approx(0.5)
    with pytest.raises(ValueError):
        ABMModel("B", 1, 1, _params(compliance_prob_min=0.9, compliance_prob_max=0.1), rows())


def test_target_margin_yaml_and_data_column():
    m = ABMModel("A", 1, 1, _params(target_margin=2.7), rows())
    assert all(b.target_margin == 2.7 for b in m.banks)
    data = rows()
    data[0]["target_margin"] = 4.0
    m = ABMModel("A", 1, 1, _params(target_margin=2.7), data)
    assert m.banks[0].target_margin == 4.0
    assert all(b.target_margin == 2.7 for b in m.banks[1:])


def test_invalid_caps_rejected():
    with pytest.raises(ValueError):
        ABMModel("A", 1, 1, _params(demand_pressure_cap=-0.1), rows())
    with pytest.raises(ValueError):
        ABMModel("A", 1, 1, _params(depositor_max_growth=-0.1), rows())
