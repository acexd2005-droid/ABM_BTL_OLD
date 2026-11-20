
"""Agent ngân hàng thương mại - Mesa 3.3.1.

Đây là mô hình minh họa, chưa hiệu chỉnh từ dữ liệu thực tế.
"""

from mesa import Agent


class Bank(Agent):
    def __init__(
        self,
        model,
        bank_id,
        group,
        deposits,
        loans,
        deposit_rate,
        loan_rate,
        target_margin=3.2,
        capital_ratio=0.10,
        npl_ratio=0.02,
        casa_ratio=0.20,
        lagged_funding_cost=4.5,
    ):
        super().__init__(model)

        self.bank_id = bank_id
        self.group = group

        self.deposits = float(deposits)
        self.loans = float(loans)

        self.deposit_rate = float(deposit_rate)
        self.loan_rate = float(loan_rate)

        self.target_margin = float(target_margin)
        self.capital_ratio = float(capital_ratio)
        self.npl_ratio = float(npl_ratio)
        self.casa_ratio = float(casa_ratio)

        self.lagged_funding_cost = float(
            lagged_funding_cost
        )

    @property
    def funding_cost(self):
        """Chi phí vốn xấp xỉ, đơn vị %/năm."""
        return (
            self.deposit_rate * (1 - self.casa_ratio)
            + 0.15
        )

    @property
    def nim_proxy(self):
        """Chênh lệch lãi suất, không phải NIM kế toán."""
        return self.loan_rate - self.funding_cost

    def step(self):
        """Ngân hàng điều chỉnh lãi suất mỗi quý."""
        model = self.model

        # 1. Áp lực huy động từ tỷ lệ cho vay/tiền gửi
        ldr = self.loans / self.deposits

        demand_pressure = max(
            -0.5,
            min(0.5, ldr - 0.82)
        )

        # base_deposit_rate_step: mức điều chỉnh cơ sở GIẢ ĐỊNH MỖI QUÝ (YAML).
        desired_increase = (
            model.base_deposit_rate_step
            + model.deposit_competition * demand_pressure
        )

        # 2. Kịch bản C hạn chế cạnh tranh huy động
        if (
            model.scenario == "C"
            and model.month >= model.policy_month
        ):
            desired_increase *= model.deposit_cap_factor

        self.deposit_rate = max(
            0.0,
            min(14.0, self.deposit_rate + desired_increase)
        )

        # 3. Lãi suất cho vay phản ứng với chi phí vốn trễ
        # loan_spread_add (điểm %) là giả định cố định, chưa hiệu chỉnh (YAML).
        target_rate = (
            self.lagged_funding_cost
            + self.target_margin
            + model.loan_spread_add
        )

        self.loan_rate += model.pass_through * (
            target_rate - self.loan_rate
        )

        
        # 4. Ghi nhận phản ứng chính sách
        self.policy_probability = 0.0
        self.policy_complied = False
        self.policy_cut = 0.0

        if model.regulator.policy_active:

            probability = (
                model.regulator.compliance_probability(
                    self.nim_proxy
                )
            )

            self.policy_probability = probability

            if model.random.random() < probability:
                self.policy_complied = True

                # Mức giảm do chỉ đạo
                old_rate = self.loan_rate

                self.loan_rate = max(
                    0.0,
                    self.loan_rate - model.policy_step
                )

                self.policy_cut = (
                    old_rate - self.loan_rate
                )

        # 5. Giữ lãi suất trong miền hợp lệ
        self.loan_rate = max(
            0.0,
            min(20.0, self.loan_rate)
        )

    def finish_month(self):
        """Cập nhật chi phí vốn trễ cuối quý. Giữ tên để tương thích."""
        self.lagged_funding_cost = self.funding_cost

        if self.model.adaptive_learning:
            self._learn_margin()

    def _learn_margin(self):
        """Học thích nghi: chỉnh target_margin cho quý sau theo kết quả quý này.

        - Thị phần dư nợ giảm -> giảm biên một bước learning_down_step.
        - Nếu không: tăng trưởng dư nợ >= g* và nim_proxy >= n* -> tăng biên
          một bước learning_up_step. Cả hai cùng xảy ra thì chỉ giảm.
        - Biên bị chặn trong [margin_min, margin_max]. Không dùng số ngẫu nhiên.
        """
        model = self.model

        total_loans = sum(b.loans for b in model.banks)
        share = self.loans / total_loans if total_loans > 0 else 0.0
        growth = (
            self.loans / self.prev_loans - 1
            if self.prev_loans > 0 else 0.0
        )

        share_fell = share < self.prev_loan_share
        doing_well = (
            growth >= model.learning_growth_threshold
            and self.nim_proxy >= model.learning_nim_threshold
        )

        if share_fell:
            self.target_margin -= model.learning_down_step
        elif doing_well:
            self.target_margin += model.learning_up_step

        self.target_margin = max(
            model.margin_min,
            min(model.margin_max, self.target_margin),
        )

        self.prev_loans = self.loans
        self.prev_loan_share = share
