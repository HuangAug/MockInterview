"""Auth-related Pydantic schemas (register, login, refresh, tokens)."""

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel


class RegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    email: EmailStr
    password: str = Field(min_length=8, max_length=64)
    display_name: str = Field(min_length=1, max_length=50)


class LoginRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    refresh_token: str


class TokenResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900


class AuthUserResponse(BaseModel):
    """User object embedded in auth responses."""

    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True, alias_generator=to_camel
    )

    id: uuid.UUID
    email: str
    display_name: str
    target_job_role_id: uuid.UUID | None = None
    target_job_role_name: str | None = None
    avatar_url: str | None = None
    created_at: str


class RegisterResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    user: AuthUserResponse
    tokens: TokenResponse


class LoginResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    user: AuthUserResponse
    tokens: TokenResponse
