"""Report-related Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class QuestionFeedbackItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    sequence: int
    question: str
    answer_summary: str
    score: float
    feedback: str


class ReportResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True, alias_generator=to_camel
    )

    id: uuid.UUID
    session_id: uuid.UUID
    overall_score: float
    communication_score: float
    technical_score: float
    problem_solving_score: float
    structure_score: float
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]
    question_feedback: list[QuestionFeedbackItem]
    summary: str
    created_at: datetime


class ReportStatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    session_id: uuid.UUID
    report_status: str
