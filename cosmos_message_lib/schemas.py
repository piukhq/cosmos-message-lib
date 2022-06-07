from datetime import datetime as dt
from uuid import UUID

from pydantic import BaseModel, validator

from .enums import ActivityType


class ActivitySchema(BaseModel):
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
    def convert_type(cls, value: ActivityType) -> str:
        return value.name

    @validator("user_id")
    @classmethod
    def convert_user_id(cls, value: UUID) -> str:
        return str(value)
