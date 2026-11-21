
"""Agent NHNN - mô phỏng cơ chế chỉ đạo mềm."""

import math
from mesa import Agent


class Regulator(Agent):
    def __init__(
        self,
        model,
        pressure=0.65,
        margin_floor=2.2,
        pressure_coef=2.5,
        pressure_center=0.5,
        margin_coef=1.1,
        prob_min=0.02,
        prob_max=0.98,
    ):
        super().__init__(model)

        self.pressure = float(pressure)
        self.margin_floor = float(margin_floor)
        # Hệ số logistic tuân thủ (YAML compliance_*), giá trị cũ cứng trong code
        self.pressure_coef = float(pressure_coef)
        self.pressure_center = float(pressure_center)
        self.margin_coef = float(margin_coef)
        self.prob_min = float(prob_min)
        self.prob_max = float(prob_max)
        self.policy_active = False

    def compliance_probability(self, margin):
        """Xác suất tuân thủ chỉ đạo."""
        x = (
            self.pressure_coef * (self.pressure - self.pressure_center)
            + self.margin_coef * (margin - self.margin_floor)
        )

        probability = 1 / (1 + math.exp(-x))

        return max(self.prob_min, min(self.prob_max, probability))

    def step(self):
        """Kích hoạt chỉ đạo theo kịch bản và thời gian."""
        self.policy_active = (
            self.model.scenario in ("B", "C")
            and self.model.month >= self.model.policy_month
        )
