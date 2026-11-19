
"""Agent đại diện cho khối người vay, tăng trưởng dư nợ theo quý.

Giả định: base_growth=0.006, biên [-0.04,0.035] MỖI QUÝ.
Lãi suất cho vay đầu vào theo %/năm; không tự chia cho bốn.
"""

from mesa import Agent


class BorrowerBlock(Agent):
    def __init__(
        self,
        model,
        elasticity=0.012,
        reference_rate=9.5,
        base_growth=0.006,
    ):
        super().__init__(model)

        self.elasticity = float(elasticity)
        self.reference_rate = float(reference_rate)
        self.base_growth = float(base_growth)

    def desired_growth(self, lending_rate):
        """Tăng trưởng dư nợ mong muốn trong một quý."""
        raw = (
            self.base_growth
            - self.elasticity * (
                lending_rate - self.reference_rate
            )
        )

        return max(-0.04, min(0.035, raw))

    def desired_loans(
        self,
        old_loans,
        lending_rate,
    ):
        """Tính dư nợ tín dụng mong muốn."""
        growth = self.desired_growth(lending_rate)

        return max(
            0.01,
            old_loans * (1 + growth)
        )

    def step(self):
        """Cập nhật dư nợ cho từng ngân hàng."""
        for bank in self.model.banks:
            desired = self.desired_loans(
                old_loans=bank.loans,
                lending_rate=bank.loan_rate,
            )

            limit = (
                bank.deposits
                * self.model.max_loan_to_deposit
            )

            bank.loans = min(desired, limit)
