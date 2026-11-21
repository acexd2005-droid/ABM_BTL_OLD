
"""Mô hình ABM dùng Mesa 3.3.1, một bước = một quý.

Tên kỹ thuật month/n_months được giữ để không phá API và CSV cũ.
Các tham số chưa hiệu chỉnh, các tốc độ tăng trưởng là giả định mỗi quý.
"""

from pathlib import Path

import warnings
import pandas as pd
from mesa import Model

from ..agents.bank import Bank
from ..agents.regulator import Regulator
from ..agents.depositors import DepositorBlock
from ..agents.borrowers import BorrowerBlock


GROUPS = (
    "quoc_doanh",
    "co_phan_lon",
    "co_phan_nho",
)

HAS_MESA = True

ROOT = Path(__file__).resolve().parents[2]


class ABMModel(Model):
    def __init__(
        self,
        scenario="A",
        n_months=24,
        seed=42,
        parameters=None,
        initial_banks=None,
    ):
        super().__init__(seed=seed)

        if scenario not in ("A", "B", "C"):
            raise ValueError("Kịch bản phải là A, B hoặc C")

        self.scenario = scenario
        self.n_months = int(n_months)
        self.seed = int(seed)
        self.month = 0

        # Ky khoi tao tu du lieu BCTC
        self.initial_period = pd.Period(
            "2023Q1", freq="Q"
        )
        self.time_unit = "quarter"


        p = dict(parameters or {})

        self.pass_through = float(
            p.get("pass_through", 0.48)
        )
        self.policy_step = float(
            p.get("policy_step", 0.28)
        )
        self.policy_month = int(
            p.get("policy_month", 14)
        )
        self.deposit_competition = float(
            p.get("deposit_competition", 0.07)
        )
        self.deposit_cap_factor = float(
            p.get("deposit_cap_factor", 0.25)
        )
        self.max_loan_to_deposit = float(
            p.get("max_loan_to_deposit", 1.60)
        )

        # Hằng số hành vi trước đây cứng trong agent (giá trị giữ nguyên)
        self.base_deposit_rate_step = float(
            p.get("base_deposit_rate_step", 0.018)
        )
        self.loan_spread_add = float(
            p.get("loan_spread_add", 1.35)
        )

        # Giai đoạn 9a: các hằng số hành vi còn lại trước đây cứng trong agent (giá trị giữ nguyên, GIẢ ĐỊNH)
        # Bank: chi phí vốn = deposit_rate*(1-casa) + funding_cost_add; áp lực huy động
        # demand_pressure = clip(LDR - deposit_ldr_target, ±demand_pressure_cap); biên mục tiêu ban đầu target_margin
        # (chỉ dùng khi dữ liệu ngân hàng không có cột target_margin).
        self.funding_cost_add = float(p.get("funding_cost_add", 0.15))
        self.deposit_ldr_target = float(p.get("deposit_ldr_target", 0.82))
        self.demand_pressure_cap = float(p.get("demand_pressure_cap", 0.5))
        self.initial_target_margin = float(p.get("target_margin", 3.2))
        if self.demand_pressure_cap < 0:
            raise ValueError("demand_pressure_cap phải không âm")

        # Cơ sở của deposit_rate trong dữ liệu ngân hàng nạp vào (mặc định "term" từ Bước A):
        #  term : quy đổi deposit_rate = deposit_rate_dữ_liệu / (1 - casa_ratio) khi nạp dữ liệu, để
        #         funding_cost = deposit_rate_dữ_liệu + 0.15. Chỉ áp dụng cho dữ liệu nạp vào, không cho bộ giả lập.
        #  total: hành vi cũ trước Bước A: dùng nguyên giá trị dữ liệu làm deposit_rate
        #         (funding_cost trừ CASA lần nữa, tức CASA bị trừ hai lần). Giữ để đối chiếu lịch sử.
        self.deposit_rate_basis = str(p.get("deposit_rate_basis", "term"))
        if self.deposit_rate_basis not in ("total", "term"):
            raise ValueError("deposit_rate_basis phải là total hoặc term")

        # Biến vĩ mô ngoại sinh (Giai đoạn 8, mặc định TẮT = "none"):
        #  exogenous: lãi suất huy động neo về lãi suất liên ngân hàng qua đêm của quý LIỀN TRƯỚC (ON_{t-1})
        #             deposit_rate += macro_dep_speed * (ON_{t-1} + macro_dep_spread - deposit_rate_{t-1}).
        self.macro_driver = str(p.get("macro_driver", "none"))
        if self.macro_driver not in ("none", "exogenous"):
            raise ValueError("macro_driver phải là none hoặc exogenous")
        self.macro_dep_speed = float(p.get("macro_dep_speed", 0.177))
        self.macro_dep_spread = float(p.get("macro_dep_spread", 1.2723))
        self.macro_lending_on_coef = float(p.get("macro_lending_on_coef", 0.0))
        self.macro_lending_on_ref = float(p.get("macro_lending_on_ref", 3.7461))
        self.macro_on_path = str(
            p.get("macro_on_path", "data/raw/sbv_lnh_qua_dem_theo_quy.csv")
        )
        if not 0.0 <= self.macro_dep_speed <= 1.0:
            raise ValueError("macro_dep_speed phải nằm trong [0, 1]")
        if self.macro_driver == "none" and self.macro_lending_on_coef != 0.0:
            raise ValueError("macro_lending_on_coef khác 0 cần macro_driver: exogenous")
        self._macro_on = (
            self._load_macro_on(self.macro_on_path)
            if self.macro_driver == "exogenous" else None
        )

        # Học thích nghi (tùy chọn, mặc định TẮT để tái lập kết quả cũ)
        self.adaptive_learning = bool(
            p.get("adaptive_learning", False)
        )
        self.learning_up_step = float(
            p.get("learning_up_step", 0.05)
        )
        self.learning_down_step = float(
            p.get("learning_down_step", 0.10)
        )
        self.learning_growth_threshold = float(
            p.get("learning_growth_threshold", 0.006)
        )
        # n* mặc định cho cơ sở "term" (nim_i = loan_rate - (deposit_rate_dữ_liệu + 0.15))
        self.learning_nim_threshold = float(
            p.get("learning_nim_threshold", 4.6331)
        )
        # n* cho cơ sở "total" (nim_i = loan_rate - (deposit_rate*(1-casa) + 0.15)); dùng khi basis = total
        self.learning_nim_threshold_total = float(
            p.get("learning_nim_threshold_total", 5.5875)
        )
        if self.deposit_rate_basis == "total":
            self.learning_nim_threshold = self.learning_nim_threshold_total
        # Quy tắc học "relative": so sánh với mốc bình quân hệ thống (mặc định TẮT)
        self.learning_rule = str(p.get("learning_rule", "absolute"))
        self.learning_deadband = float(
            p.get("learning_deadband", 0.005)
        )
        self.learning_benchmark = str(
            p.get("learning_benchmark", "simple")
        )
        self.learning_nim_condition = bool(
            p.get("learning_nim_condition", True)
        )
        self.margin_min = float(p.get("margin_min", 2.2))
        self.margin_max = float(p.get("margin_max", 4.2))

        if self.learning_rule not in ("absolute", "relative"):
            raise ValueError("learning_rule phải là absolute hoặc relative")
        if self.learning_benchmark not in ("simple", "weighted"):
            raise ValueError("learning_benchmark phải là simple hoặc weighted")
        if self.learning_deadband < 0:
            raise ValueError("learning_deadband phải không âm")
        self._learning_stats_cache = None

        if self.margin_min > self.margin_max:
            raise ValueError("margin_min không được lớn hơn margin_max")
        if self.learning_up_step < 0 or self.learning_down_step < 0:
            raise ValueError("Bước học phải không âm")

        if self.n_months <= 0:
            raise ValueError("n_months phải dương")

        if self.max_loan_to_deposit <= 0:
            raise ValueError(
                "Giới hạn kỹ thuật dư nợ/tiền gửi phải lớn hơn 0"
            )

        # Tạo agent NHNN
        self.regulator = Regulator(
            self,
            pressure=float(
                p.get("policy_pressure", 0.65)
            ),
            margin_floor=float(
                p.get("margin_floor", 2.2)
            ),
            pressure_coef=float(p.get("compliance_pressure_coef", 2.5)),
            pressure_center=float(p.get("compliance_pressure_center", 0.5)),
            margin_coef=float(p.get("compliance_margin_coef", 1.1)),
            prob_min=float(p.get("compliance_prob_min", 0.02)),
            prob_max=float(p.get("compliance_prob_max", 0.98)),
        )
        if not 0 <= self.regulator.prob_min <= self.regulator.prob_max <= 1:
            raise ValueError("Cần 0 <= compliance_prob_min <= compliance_prob_max <= 1")

        # Tạo agent người gửi tiền gộp
        self.depositor = DepositorBlock(
            self,
            sensitivity=float(
                p.get("depositor_sensitivity", 0.035)
            ),
            base_growth=float(
                p.get("depositor_base_growth", 0.004)
            ),
            max_growth=float(
                p.get("depositor_max_growth", 0.04)
            ),
            # Giai đoạn 9 (TÙY CHỌN): sàn riêng của tăng trưởng tiền gửi; None = -depositor_max_growth (hành vi cũ)
            min_growth=p.get("depositor_min_growth", None),
        )
        if self.depositor.max_growth < 0:
            raise ValueError("depositor_max_growth phải không âm")
        if (
            self.depositor.min_growth is not None
            and self.depositor.min_growth > self.depositor.max_growth
        ):
            raise ValueError("depositor_min_growth không được lớn hơn depositor_max_growth")
        if self.depositor.min_growth is not None and self.depositor.min_growth > 0:
            # Sàn dương = ép mọi ngân hàng có tiền gửi tăng tối thiểu mỗi quý; cho phép nhưng cảnh báo rõ.
            warnings.warn(
                "depositor_min_growth > 0: sàn dương ép tiền gửi mọi ngân hàng tăng tối thiểu mỗi quý "
                "(thường sàn phải <= 0)",
                UserWarning,
                stacklevel=2,
            )

        # Tạo agent người vay gộp
        self.borrower = BorrowerBlock(
            self,
            elasticity=float(
                p.get("borrower_elasticity", 0.012)
            ),
            reference_rate=float(
                p.get("borrower_reference_rate", 9.5)
            ),
            base_growth=float(
                p.get("borrower_base_growth", 0.006)
            ),
            growth_min=float(
                p.get("borrower_growth_min", -0.04)
            ),
            growth_max=float(
                p.get("borrower_growth_max", 0.035)
            ),
        )
        if self.borrower.growth_min > self.borrower.growth_max:
            raise ValueError("borrower_growth_min không được lớn hơn borrower_growth_max")

        # Tạo các agent ngân hàng
        self.banks = self._make_banks(initial_banks)

        self.market_rate = 0.0
        self.history = []
        self.bank_history = []
    def _load_macro_on(self, path):
        """Đọc ON (cột bq_gian_don) theo quý, liên tục từ quý khởi tạo tới quý cuối của file.

        Thiếu quý lịch sử (kể cả quý khởi tạo) hoặc có khoảng trống => raise ValueError.
        Chỉ số i ứng với quý initial_period + i.
        """
        f = Path(path)
        f = f if f.is_absolute() else ROOT / f
        if not f.is_file():
            raise ValueError(f"Không tìm thấy dữ liệu ON: {f}")
        data = pd.read_csv(f)
        if not {"quy", "bq_gian_don"} <= set(data.columns):
            raise ValueError("File ON cần cột quy và bq_gian_don")
        data["per"] = pd.PeriodIndex(data["quy"], freq="Q")
        series = dict(zip(data["per"].astype(int), data["bq_gian_don"].astype(float)))
        start = int(self.initial_period.ordinal)
        if start not in series:
            raise ValueError("Thiếu ON của quý khởi tạo")
        last = max(series)
        missing = [q for q in range(start, last + 1) if q not in series]
        if missing:
            raise ValueError(
                f"Thiếu ON của {len(missing)} quý lịch sử (vd {pd.Period(ordinal=missing[0], freq='Q')})"
            )
        values = [series[q] for q in range(start, last + 1)]
        if any(v != v for v in values):
            raise ValueError("Dữ liệu ON có giá trị thiếu")
        return values

    def macro_on_previous(self):
        """ON của quý liền trước quý đang mô phỏng.

        Bước đầu (month = 0, mô phỏng Q2/2023) dùng ON của Q1/2023 = quý khởi tạo.
        Sau quý cuối có dữ liệu (2026Q3) giữ nguyên giá trị đó cho mọi kịch bản.
        """
        values = self._macro_on
        return values[min(self.month, len(values) - 1)]

    def _make_banks(self, initial):
        """Khởi tạo ngân hàng từ dữ liệu hoặc bộ giả lập."""
        from_data = initial is not None
        if initial is None:
            initial = []

            for i in range(9):
                deposits = 1000 + 140 * i

                initial.append({
                    "bank_id": f"DEMO_{i + 1:02d}",
                    "group": GROUPS[i // 3],
                    "deposits": deposits,
                    "loans": deposits * 0.82,
                    "deposit_rate": 5.0 + 0.12 * (i % 3),
                    "loan_rate": 9.2 + 0.15 * (i % 3),
                    "casa_ratio": 0.27 - 0.05 * (i // 3),
                })

        required = {
            "bank_id",
            "group",
            "deposits",
            "loans",
            "deposit_rate",
            "loan_rate",
        }

        banks = []

        for item in initial:
            if not required.issubset(item):
                missing = required - set(item)

                raise ValueError(
                    f"Thiếu cột ngân hàng: {missing}"
                )

            d = dict(item)
            # Biên mục tiêu ban đầu từ YAML nếu dữ liệu không có cột target_margin (giá trị cũ = 3.2, mặc định của Bank)
            d.setdefault("target_margin", self.initial_target_margin)

            # Quy đổi cơ sở lãi suất huy động (chỉ với dữ liệu nạp vào)
            if from_data and self.deposit_rate_basis == "term":
                casa = float(d.get("casa_ratio", 0.20))   # 0.20 = mặc định của Bank
                if not 0 <= casa < 1:
                    raise ValueError("casa_ratio phải nằm trong [0, 1)")
                d["deposit_rate"] = float(d["deposit_rate"]) / (1 - casa)

            if d["deposits"] <= 0 or d["loans"] < 0:
                raise ValueError(
                    "Dữ liệu số dư không hợp lệ"
                )

            bank = Bank(self, **d)

            # Chi phí vốn ban đầu
            bank.lagged_funding_cost = (
                bank.funding_cost
            )

            banks.append(bank)

        if not banks:
            raise ValueError(
                "Danh sách ngân hàng không được rỗng"
            )

        # Trạng thái đầu kỳ cho học thích nghi (không dùng số ngẫu nhiên)
        total_loans = sum(b.loans for b in banks)
        for bank in banks:
            bank.prev_loans = bank.loans
            bank.prev_loan_share = (
                bank.loans / total_loans if total_loans > 0 else 0.0
            )

        return banks

    def step(self):
        """Thực hiện một bước mô phỏng = một quý."""

        # 1. Lưu dữ liệu đầu kỳ
        rates_before = [
            bank.deposit_rate for bank in self.banks
        ]

        self.market_rate = (
            sum(rates_before) / len(rates_before)
        )

        old_deposits = sum(
            bank.deposits for bank in self.banks
        )

        old_loans = sum(
            bank.loans for bank in self.banks
        )

        # 2. Kích hoạt NHNN
        self.agents_by_type[Regulator].do("step")

        # 3. Kích hoạt ngân hàng
        self.agents_by_type[Bank].do("step")

        # 4. Kích hoạt người gửi tiền
        self.agents_by_type[DepositorBlock].do("step")

        # 5. Kích hoạt người vay
        self.agents_by_type[BorrowerBlock].do("step")

        # 6. Kiểm tra các ràng buộc
        for bank in self.banks:
            bank.finish_month()

            assert 0 <= bank.loan_rate <= 20
            assert 0 <= bank.deposit_rate <= 14

            assert bank.deposits > 0
            assert bank.loans >= 0

            assert (
                bank.loans
                <= bank.deposits
                * self.max_loan_to_deposit
                + 1e-9
            )

            assert 0 <= bank.casa_ratio <= 1
            assert 0 <= bank.npl_ratio <= 1

            # Ghi nhận trạng thái ngân hàng cuối quý
            self.bank_history.append({
                "month": self.month + 1,
                "bank_id": bank.bank_id,
                "group": bank.group,

                # Đặc điểm tài chính
                "casa_ratio": bank.casa_ratio,
                "deposits": bank.deposits,
                "loans": bank.loans,

                # Lãi suất và biên lãi
                "deposit_rate": bank.deposit_rate,
                "loan_rate": bank.loan_rate,
                "nim_proxy": bank.nim_proxy,

                # Thanh khoản
                "ldr": bank.loans / bank.deposits,

                # Thông tin chính sách
                "policy_active": (
                    self.regulator.policy_active
                ),
                "policy_probability": (
                    bank.policy_probability
                ),
                "policy_complied": (
                    bank.policy_complied
                ),
                "policy_cut": bank.policy_cut,

                # Biên mục tiêu áp dụng cho quý kế tiếp (cột mới)
                "target_margin": bank.target_margin,
            })

        # 7. Tổng hợp trạng thái toàn hệ thống
        new_deposits = sum(
            bank.deposits for bank in self.banks
        )

        new_loans = sum(
            bank.loans for bank in self.banks
        )

        weighted_deposit_rate = sum(
            bank.deposit_rate * bank.deposits
            for bank in self.banks
        ) / new_deposits

        weighted_loan_rate = sum(
            bank.loan_rate * bank.loans
            for bank in self.banks
        ) / new_loans

        weighted_nim_proxy = sum(
            bank.nim_proxy * bank.loans
            for bank in self.banks
        ) / new_loans

        # 8. Lưu kết quả theo quý
        self.history.append({
            "month": self.month + 1,
            "quarter": str(
                self.initial_period + self.month + 1
            ),
            "scenario": self.scenario,
            "seed": self.seed,
            "deposit_rate": weighted_deposit_rate,
            "loan_rate": weighted_loan_rate,
            "nim_proxy": weighted_nim_proxy,
            "credit_growth": (
                new_loans / old_loans - 1
            ),
            "deposit_growth": (
                new_deposits / old_deposits - 1
            ),
            "loan_deposit_ratio": (
                new_loans / new_deposits
            ),
            "total_loans": new_loans,
            "total_deposits": new_deposits,
        })

        self.month += 1

    def run(self):
        """Chạy mô phỏng đến hết số quý đã định."""
        for _ in range(self.n_months):
            self.step()

        return pd.DataFrame(self.history)

    @staticmethod
    def from_clean_csv(path, **kwargs):
        """Khởi tạo ngân hàng từ CSV dạng wide."""
        data = pd.read_csv(path)

        banks = data.to_dict("records")

        return ABMModel(
            initial_banks=banks,
            **kwargs
        )
