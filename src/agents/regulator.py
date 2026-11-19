
"""Agent NHNN - mô phỏng cơ chế chỉ đạo mềm."""

import math
from mesa import Agent


class Regulator(Agent):
    def __init__(
        self,
        model,
        pressure=0.65,
        margin_floor=2.2,
    ):
        super().__init__(model)

        self.pressure = float(pressure)
        self.margin_floor = float(margin_floor)
        self.policy_active = False

    def compliance_probability(self, margin):
        """Xác suất tuân thủ chỉ đạo."""
        x = (
            2.5 * (self.pressure - 0.5)
            + 1.1 * (margin - self.margin_floor)
        )

        probability = 1 / (1 + math.exp(-x))

        return max(0.02, min(0.98, probability))

    def step(self):
        """Kích hoạt chỉ đạo theo kịch bản và thời gian."""
        self.policy_active = (
            self.model.scenario in ("B", "C")
            and self.model.month >= self.model.policy_month
        )
