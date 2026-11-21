
"""Agent đại diện cho khối người gửi tiền, tăng trưởng theo quý.

base_growth (mặc định 0.004) và max_growth (0.04) là giả định MỖI QUÝ, chưa hiệu chỉnh;
giá trị lấy từ YAML (depositor_base_growth, depositor_max_growth) qua ABMModel.
Lãi suất đầu vào có đơn vị %/năm; tăng trưởng tiền gửi theo quý.
"""

from mesa import Agent


class DepositorBlock(Agent):
    def __init__(
        self,
        model,
        sensitivity=0.035,
        base_growth=0.004,
        max_growth=0.04,
    ):
        super().__init__(model)

        self.sensitivity = float(sensitivity)
        self.base_growth = float(base_growth)
        self.max_growth = float(max_growth)

    def growth(self, bank_rate, market_rate):
        """Tốc độ tăng trưởng tiền gửi trong một quý."""
        raw = (
            self.base_growth
            + self.sensitivity * (
                bank_rate - market_rate
            )
        )

        return max(
            -self.max_growth,
            min(self.max_growth, raw)
        )

    def updated_deposits(
        self,
        deposits,
        bank_rate,
        market_rate,
    ):
        """Tính số dư tiền gửi mới."""
        growth_rate = self.growth(
            bank_rate,
            market_rate
        )

        return max(
            0.01,
            deposits * (1 + growth_rate)
        )

    def step(self):
        """Cập nhật tiền gửi ở tất cả ngân hàng."""
        market_rate = self.model.market_rate

        for bank in self.model.banks:
            bank.deposits = self.updated_deposits(
                deposits=bank.deposits,
                bank_rate=bank.deposit_rate,
                market_rate=market_rate,
            )
