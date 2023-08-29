import sys
import uuid

from collections.abc import Generator
from datetime import UTC
from datetime import datetime as dt

try:
    from pydantic import BaseModel, Field, validator
    from pydantic.datetime_parse import parse_datetime
except ImportError:
    sys.exit("Pydantic extra not installed.")


# Adapted from StackOverflow: https://stackoverflow.com/questions/66548586/how-to-change-date-format-in-pydantic
class UTCDatetime(dt):
    @classmethod
    def __get_validators__(cls) -> Generator:
        yield parse_datetime
        yield cls.ensure_tzinfo

    @classmethod
    def ensure_tzinfo(cls, v: dt) -> dt:

        if v.tzinfo is None:
            return v.replace(tzinfo=UTC)

        return v.astimezone(UTC)


class ActivitySchema(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)  # noqa: A003
    type: str  # noqa: A003
    datetime: UTCDatetime
    underlying_datetime: UTCDatetime
    summary: str
    reasons: list[str]
    activity_identifier: str
    user_id: str
    associated_value: str
    retailer: str
    campaigns: list[str]
    data: dict

    @validator("id", always=True, pre=False)
    @classmethod
    def uuid_to_str(cls, value: uuid.UUID) -> str:
        return str(value)

    @validator("user_id", always=True, pre=True)
    @classmethod
    def parse_user_id(cls, value: uuid.UUID | str) -> str:
        if isinstance(value, uuid.UUID):
            return str(value)

        return value
