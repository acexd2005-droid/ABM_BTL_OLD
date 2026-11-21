"""GD10b: độ nhạy deposit_competition/policy_step 0.375 và sai lệch mức trong mẫu GD9b (Q14)."""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

import src.analysis.sensitivity_gd10b as s10b
import src.calibration.mean_error_insample_stage9b as me
from src.analysis.experiments import load_config

ROOT = Path(__file__).resolve().parents[1]
S9B = ROOT / "reports/calibration/stage9b"
S10 = ROOT / "reports/stage10"
YAMLS = sorted((ROOT / "configs").glob("*.yaml"))


def md5s():
    return {p.name: hashlib.md5(p.read_bytes()).hexdigest() for p in YAMLS}


def test_mean_error_reproducible_bytes_and_yaml_unchanged(tmp_path):
    before = md5s()
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    me.main(a)
    me.main(b)
    assert a.read_bytes() == b.read_bytes()
    assert a.read_bytes() == (S9B / "mean_error_insample_stage9b.csv").read_bytes()
    assert md5s() == before


def test_mean_error_matches_oos_stage9b():
    me_df = pd.read_csv(S9B / "mean_error_insample_stage9b.csv")
    oos = pd.read_csv(S9B / "oos_stage9b.csv")
    pairs = {"GD9b": "hieu_chinh_GD9b_batdoixung_daydu", "GD9": "GD9_nghiem"}
    assert len(me_df) == 4
    for k, name in pairs.items():
        for ch in ("cho_vay", "huy_dong"):
            r = me_df[(me_df.cau_hinh == k) & (me_df.chuoi == ch)].iloc[0]
            o = oos[(oos.cau_hinh == name) & (oos.chuoi == ch)].iloc[0]
            assert abs(r.RMSE_tho_trong_mau - o.RMSE_tho_trong_mau) < 1e-8
            assert abs(r.RMSE_khu_muc_trong_mau - o.RMSE_khu_muc_trong_mau) < 1e-8
            # sqrt(thô² − khử mức²) = |sai số TB|
            assert abs(np.sqrt(r.RMSE_tho_trong_mau ** 2 - r.RMSE_khu_muc_trong_mau ** 2) - abs(r.sai_so_tb_co_dau_trong_mau)) < 1e-8


def test_sensitivity_variants_as_registered():
    P = dict(load_config(ROOT / "configs/scenarios_calibrated.yaml")["parameters"])
    V = s10b.build_variants(P)
    names = [v[0] for v in V]
    for v in (0.07, 0.3, 0.7, 1.2):
        assert f"deposit_competition_{v:g}" in names
    assert "policy_step_0.375" in names
    for name, _, params, _ in V:
        diff = {k for k in params if params[k] != P[k]}
        assert len(diff) <= 1, name        # mỗi lần đổi tối đa một tham số


def test_sensitivity_reproducible_and_yaml_unchanged(tmp_path):
    before = md5s()
    d1, d2 = tmp_path / "x", tmp_path / "y"
    s10b.main(d1, n_seeds=2)
    s10b.main(d2, n_seeds=2)
    for f in ("sensitivity_gd10b_stage10.csv", "sensitivity_gd10b_section6_stage10.csv", "summary_gd10b_stage10.md"):
        assert (d1 / f).read_bytes() == (d2 / f).read_bytes()
    assert md5s() == before


def test_committed_results_complete_and_section6():
    df = pd.read_csv(S10 / "sensitivity_gd10b_stage10.csv")
    assert set(df.nhom) == {"co_so", "deposit_competition", "policy_step"}
    assert (df.n_seed == 30).all()
    assert len(df[df.nhom == "deposit_competition"]) == 4
    s6 = pd.read_csv(S10 / "sensitivity_gd10b_section6_stage10.csv")
    assert s6.dat_tat_ca.all()
    # deposit_competition 0.07 = YAML → trùng cấu hình chính cùng số lần
    r0 = df[df.cau_hinh == "co_so_30"].iloc[0]
    r1 = df[df.cau_hinh == "deposit_competition_0.07"].iloc[0]
    assert r0.BmA_tb == r1.BmA_tb and r0.CmB_tb == r1.CmB_tb
    # đối chiếu với GD10: cấu hình chính 30 lần
    sens = pd.read_csv(S10 / "sensitivity_stage10.csv")
    ref = sens[sens.cau_hinh == "co_so_30"].iloc[0]
    assert abs(ref.BmA_tb - r0.BmA_tb) < 1e-8
