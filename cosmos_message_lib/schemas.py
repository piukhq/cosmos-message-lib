from datetime import datetime as dt
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

from .enums import ActivityType


class ActivitySchema(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    type: ActivityType
    datetime: dt
    underlying_datetime: dt
    summary: str
    reasons: list[str]
    activity_identifier: str
    user_id: UUID
    associated_value: str
    retailer: str
    campaigns: list[str]
    data: dict

    @validator("type")
    @classmethod
    def get_enum_name(cls, value: ActivityType) -> str:
        return value.name

    @validator("id", "user_id", always=True)
    @classmethod
    def uuid_to_str(cls, value: UUID) -> str:
        return str(value)
