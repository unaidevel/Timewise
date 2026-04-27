from dataclasses import dataclass
from decimal import Decimal

from infra.common.exceptions import UnprocessableEntity


@dataclass(frozen=True, slots=True)
class OvertimeRuleEntity:
    name: str
    multiplier: Decimal
    priority: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", self._validate_name(self.name))
        object.__setattr__(
            self, "multiplier", self._validate_multiplier(self.multiplier)
        )
        object.__setattr__(self, "priority", self._validate_priority(self.priority))

    @staticmethod
    def _validate_name(value: str) -> str:
        clean = value.strip()
        if not clean:
            raise UnprocessableEntity("Overtime rule name cannot be blank.")
        if len(clean) > 200:
            raise UnprocessableEntity(
                "Overtime rule name cannot be longer than 200 characters."
            )
        return clean

    @staticmethod
    def _validate_multiplier(value: Decimal) -> Decimal:
        if value < Decimal("1.0"):
            raise UnprocessableEntity("Multiplier must be at least 1.0.")
        exponent = value.as_tuple().exponent
        if isinstance(exponent, int) and exponent < -2:
            raise UnprocessableEntity(
                "Multiplier cannot have more than 2 decimal places."
            )
        return value

    @staticmethod
    def _validate_priority(value: int) -> int:
        if value < 0:
            raise UnprocessableEntity("Priority must be 0 or greater.")
        return value
