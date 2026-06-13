"""JobRole-related Pydantic schemas."""

import uuid

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class JobRoleResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True, alias_generator=to_camel
    )

    id: uuid.UUID
    code: str
    name_zh: str
    name_en: str
    description: str | None = None
    sort_order: int
