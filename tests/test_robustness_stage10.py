"""GD10: độ nhạy/độ vững. Chạy bản nhỏ (ít seed) để kiểm cấu trúc, tái lập byte, không đổi YAML, mục 6."""

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from src.analysis import robustness_stage10 as r10

ROOT = Path(__file__).resolve().parents[1]
FILES = ["abc_summary_stage10.csv", "abc_quarterly_stage10.csv", "diff_quarterly_stage10.csv", "sensitivity_stage10.csv",
         "section6_stage10.csv", "robustness_stage10.csv", "confounding_stage10.csv", "summary_stage10.md"]


def _md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def small(tmp_path_factory):
    yamls = [r10.CFG_MAIN, r10.CFG_GD9, r10.CFG_MACRO, r10.CFG_ORIG, r10.CFG_REL]
    before = {str(p): _md5(p) for p in yamls}
    a, b = tmp_path_factory.mktemp("a"), tmp_path_factory.mktemp("b")
    r10.main(a, n_main=3, n_sens=2)
    r10.main(b, n_main=3, n_sens=2)
    after = {str(p): _md5(p) for p in yamls}
    return a, b, before, after


def test_tai_lap_tung_byte_va_khong_doi_yaml(small):
    a, b, before, after = small
    for f in FILES:
        assert _md5(a / f) == _md5(b / f), f
    assert before == after


def test_bien_the_dung_thiet_ke(small):
    a, *_ = small
    s = pd.read_csv(a / "sensitivity_stage10.csv").set_index("cau_hinh")
    main = r10.cfg_of(r10.CFG_MAIN)["parameters"]
    for f in r10.PRESSURE_REL:
        assert s.loc[f"policy_pressure_x{f:g}"].mo_ta.startswith("policy_pressure")
    for st in r10.STEPS:
        assert f"policy_step_{st:g}" in s.index
    for lam in (*r10.LAMBDA_CI, r10.LAMBDA_IN_CI):
        assert f"pass_through_{lam:g}" in s.index
    assert f"macro_dep_spread_{r10.SPREAD_ALT:g}" in s.index
    for f in r10.SIGMA_EPS_REL:
        assert f"depositor_sensitivity_x{f:g}" in s.index and f"borrower_elasticity_x{f:g}" in s.index
    assert "GD9_lambda_0.45" in s.index and "hoc_relative" in s.index
    # cấu hình chính của YAML là nghiệm GD9b (λ 0.40, target_margin 2.05) và học tắt
    assert main["pass_through"] == 0.4 and main["target_margin"] == 2.05 and main["adaptive_learning"] is False


def test_muc6_cau_hinh_chinh_va_tuan_thu_co_dinh(small):
    a, *_ = small
    s6 = pd.read_csv(a / "section6_stage10.csv").set_index("cau_hinh")
    assert bool(s6.loc["hieu_chinh_GD9b (chinh)"].dat_tat_ca)
    conf = pd.read_csv(a / "confounding_stage10.csv")
    fx = conf[conf.loai == "tuan_thu_co_dinh"]
    assert len(fx) == 4
    assert fx.xs_tuan_thu_tb_B.nunique() == 1 and fx.xs_tuan_thu_tb_C.nunique() == 1
    abc = pd.read_csv(a / "abc_summary_stage10.csv")
    assert abs(fx.xs_tuan_thu_tb_B.iloc[0] - abc.xs_tuan_thu_tb_B.iloc[0]) < 1e-9


def test_so_lieu_bao_cao_khop_file_ket_qua():
    """Nếu reports/stage10 đã sinh (60/30 lần), cấu hình chính khớp section6 mục 6 và B−A ≤ 0."""
    f = r10.OUTDIR / "abc_summary_stage10.csv"
    if not f.exists():
        pytest.skip("chưa chạy robustness_stage10")
    abc = pd.read_csv(f)
    assert int(abc.n_seed.iloc[0]) == r10.N_MAIN
    assert abc.BmA_tb.iloc[0] < 0 and abc.CmA_tb.iloc[0] < 0
    s6 = pd.read_csv(r10.OUTDIR / "section6_stage10.csv")
    assert s6.dat_tat_ca.all()


def test_golden_cau_hinh_goc_khong_bi_sua():
    cfg = r10.cfg_of(r10.CFG_ORIG)
    assert cfg["parameters"]["macro_driver"] == "none"
