from dataclasses import dataclass

from infra.common.exceptions import UnprocessableEntity


@dataclass(frozen=True, slots=True)
class EntityApproval:
    value: str

    def __post_init__(self) -> None:
        clean = self.value.strip()
        if len(clean) > 2000:
            raise UnprocessableEntity("Reason cannot be longer than 2000 characters.")
        object.__setattr__(self, "value", clean)
