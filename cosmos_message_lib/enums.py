from enum import Enum, auto
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic.typing import CallableGenerator


class ActivityType(Enum):
    TX_HISTORY = auto()

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield cls._validate

    @classmethod
    def _validate(cls, v: Any) -> str:
        try:
            if isinstance(v, str):
                return cls[v].name

            return cls(v).name

        except KeyError:
            raise ValueError(f"{v} is not a valid {cls.__name__}")  # pylint: disable=raise-missing-from
