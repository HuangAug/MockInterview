"""User-related Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True, alias_generator=to_camel
    )

    id: uuid.UUID
    email: str
    display_name: str
    target_job_role_id: uuid.UUID | None = None
    target_job_role_name: str | None = None
    avatar_url: str | None = None
    created_at: datetime


class UpdateUserRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    display_name: str | None = Field(default=None, min_length=1, max_length=50)
    target_job_role_id: uuid.UUID | None = None
