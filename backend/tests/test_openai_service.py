"""Tests for OpenAI Service base (T017)."""

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import openai
import pytest

from app.core.exceptions import AppException
from app.models.interview_message import InterviewMessage
from app.services.openai_service import (
    OpenAIService,
    _load_prompt,
    format_conversation_history,
)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "app" / "prompts"


class TestPromptFiles:
    """Verify the 4 prompt files exist and match ARCHITECTURE §6 verbatim."""

    @pytest.mark.parametrize(
        "filename",
        [
            "interview_system_prompt.txt",
            "interview_first_question_prompt.txt",
            "interview_next_question_prompt.txt",
            "interview_report_prompt.txt",
        ],
    )
    def test_prompt_file_exists(self, filename: str) -> None:
        assert (PROMPTS_DIR / filename).is_file()

    def test_system_prompt_contains_required_placeholders(self) -> None:
        content = _load_prompt("interview_system_prompt.txt")
        assert "{job_role_name}" in content
        assert "{difficulty_label}" in content
        assert "{max_questions}" in content
        assert "简体中文" in content

    def test_first_question_prompt_content(self) -> None:
        content = _load_prompt("interview_first_question_prompt.txt")
        assert "第一个问题" in content
        assert "自我介绍" in content

    def test_next_question_prompt_contains_required_placeholders(self) -> None:
        content = _load_prompt("interview_next_question_prompt.txt")
        assert "{conversation_history}" in content
        assert "{question_count}" in content
        assert "{max_questions}" in content
        assert "[INTERVIEW_COMPLETE]" in content

    def test_report_prompt_contains_required_placeholders(self) -> None:
        content = _load_prompt("interview_report_prompt.txt")
        assert "{job_role_name}" in content
        assert "{difficulty_label}" in content
        assert "{conversation_history}" in content
        assert "{question_count}" in content
        assert "overallScore" in content
        assert "questionFeedback" in content

    def test_system_prompt_has_9_rules(self) -> None:
        content = _load_prompt("interview_system_prompt.txt")
        # Count numbered rules (1. through 9.)
        for i in range(1, 10):
            assert f"{i}." in content, f"Rule {i} missing from system prompt"


class TestFormatConversationHistory:
    """Verify conversation history formatting per ARCHITECTURE §6.5."""

    def test_empty_messages_returns_empty_string(self) -> None:
        assert format_conversation_history([]) == ""

    def test_single_interviewer_message(self) -> None:
        msg = InterviewMessage(
            role="interviewer",
            content="Tell me about yourself",
            sequence=1,
            session_id=uuid.uuid4(),
        )

        result = format_conversation_history([msg])
        assert result == "面试官：Tell me about yourself"

    def test_multiple_messages_ordered_by_sequence(self) -> None:
        sid = uuid.uuid4()
        msg1 = InterviewMessage(
            role="interviewer", content="Q1", sequence=1, session_id=sid
        )
        msg2 = InterviewMessage(
            role="candidate", content="A1", sequence=2, session_id=sid
        )
        msg3 = InterviewMessage(
            role="interviewer", content="Q2", sequence=3, session_id=sid
        )

        result = format_conversation_history([msg3, msg1, msg2])  # shuffled order
        expected = "面试官：Q1\n候选人：A1\n面试官：Q2"
        assert result == expected


class TestRetryLogic:
    """Verify retry behavior — 2 retries then raise 50201."""

    @pytest.mark.asyncio
    async def test_retry_exhausted_raises_50201(self) -> None:
        svc = OpenAIService()
        svc._max_retries = 2

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=openai.APITimeoutError(request=MagicMock())
        )
        svc._client = mock_client

        with patch("app.services.openai_service.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(AppException) as exc_info:
                await svc._chat_completion("system", "user")

        assert exc_info.value.code == 50201
        assert exc_info.value.status_code == 502
        # 3 attempts total (1 initial + 2 retries)
        assert mock_client.chat.completions.create.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_second_attempt(self) -> None:
        svc = OpenAIService()
        svc._max_retries = 2

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated question"

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=[
                openai.APITimeoutError(request=MagicMock()),
                mock_response,
            ]
        )
        svc._client = mock_client

        with patch("app.services.openai_service.asyncio.sleep", new_callable=AsyncMock):
            result = await svc._chat_completion("system", "user")

        assert result == "Generated question"
        assert mock_client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_no_retry_on_success(self) -> None:
        svc = OpenAIService()
        svc._max_retries = 2

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "OK"

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        svc._client = mock_client

        result = await svc._chat_completion("system", "user")
        assert result == "OK"
        assert mock_client.chat.completions.create.call_count == 1
