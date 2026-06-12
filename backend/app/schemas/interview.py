"""Interview-related Pydantic schemas."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class MessageResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True, alias_generator=to_camel
    )

    id: uuid.UUID
    session_id: uuid.UUID
    role: Literal["interviewer", "candidate"]
    content: str
    audio_url: str | None = None
    sequence: int
    created_at: datetime


class InterviewSessionResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True, alias_generator=to_camel
    )

    id: uuid.UUID
    job_role_id: uuid.UUID
    job_role_name: str | None = None
    difficulty: Literal["junior", "mid", "senior"]
    mode: Literal["text", "voice"]
    status: Literal["pending", "in_progress", "completed", "cancelled", "failed"]
    question_count: int
    max_questions: int
    report_status: Literal["pending", "generating", "ready", "failed"]
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] | None = None


class InterviewSessionListItem(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True, alias_generator=to_camel
    )

    id: uuid.UUID
    job_role_name: str | None = None
    difficulty: Literal["junior", "mid", "senior"]
    mode: Literal["text", "voice"]
    status: str
    question_count: int
    report_status: str
    overall_score: float | None = None
    created_at: datetime


class CreateInterviewRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    job_role_id: uuid.UUID
    difficulty: Literal["junior", "mid", "senior"]
    mode: Literal["text", "voice"]


class StartResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    session: InterviewSessionResponse
    question: MessageResponse


class SubmitAnswerRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    content: str = Field(min_length=1, max_length=5000)


class SubmitAnswerResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    answer: MessageResponse
    next_question: MessageResponse | None = None
    is_finished: bool
    question_count: int


class PaginationMeta(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    page: int
    page_size: int
    total: int
    total_pages: int


class PaginationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    items: list[InterviewSessionListItem]
    pagination: PaginationMeta
