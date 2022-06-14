from datetime import datetime as dt
from datetime import timezone
from typing import Generator
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator
from pydantic.datetime_parse import parse_datetime

from .enums import ActivityType


# Adapted from StackOverflow: https://stackoverflow.com/questions/66548586/how-to-change-date-format-in-pydantic
class utc_datetime(dt):  # pylint: disable=invalid-name
    @classmethod
    def __get_validators__(cls) -> Generator:
        yield parse_datetime
        yield cls.ensure_tzinfo

    @classmethod
    def ensure_tzinfo(cls, v: dt) -> dt:

        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)

        return v.astimezone(timezone.utc)


class ActivitySchema(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    type: ActivityType
    datetime: utc_datetime
    underlying_datetime: utc_datetime
    summary: str
    reasons: list[str]
    activity_identifier: str
    user_id: UUID
    associated_value: str
    retailer: str
    campaigns: list[str]
    data: dict

    @validator("id", "user_id", always=True)
    @classmethod
    def uuid_to_str(cls, value: UUID) -> str:
        return str(value)
