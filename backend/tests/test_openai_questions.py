"""Tests for OpenAI first/next question generation (T018)."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.interview_message import InterviewMessage
from app.services.openai_service import OpenAIService


class TestGenerateFirstQuestion:
    """Tests for generate_first_question()."""

    @pytest.mark.asyncio
    async def test_returns_non_empty_string(self) -> None:
        """First question should return a non-empty string."""
        svc = OpenAIService()

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "请简单做一下自我介绍。"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        svc._client = mock_client

        result = await svc.generate_first_question(
            job_role_name="前端工程师",
            difficulty="junior",
            max_questions=8,
        )

        assert isinstance(result, str)
        assert len(result) > 0
        assert result == "请简单做一下自我介绍。"

    @pytest.mark.asyncio
    async def test_uses_job_role_name_in_prompt(self) -> None:
        """System prompt should include the job role name."""
        svc = OpenAIService()

        mock_client = AsyncMock()
        # Capture the call arguments
        mock_client.chat.completions.create = AsyncMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "请自我介绍。"
        mock_client.chat.completions.create.return_value = mock_response
        svc._client = mock_client

        await svc.generate_first_question(
            job_role_name="后端工程师",
            difficulty="mid",
            max_questions=5,
        )

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        system_msg = call_kwargs["messages"][0]["content"]
        assert "后端工程师" in system_msg
        assert "中级（1-3年经验）" in system_msg

    @pytest.mark.asyncio
    async def test_difficulty_labels_map_correctly(self) -> None:
        """Verify difficulty values map to correct Chinese labels."""
        svc = OpenAIService()

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "问题"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        svc._client = mock_client

        test_cases = [
            ("junior", "初级（应届生/1年以内）"),
            ("mid", "中级（1-3年经验）"),
            ("senior", "高级（3年以上经验）"),
        ]

        for difficulty, expected_label in test_cases:
            await svc.generate_first_question(
                job_role_name="测试",
                difficulty=difficulty,
                max_questions=8,
            )
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            system_msg = call_kwargs["messages"][0]["content"]
            assert expected_label in system_msg, (
                f"Expected '{expected_label}' in prompt for difficulty '{difficulty}'"
            )


class TestGenerateNextQuestion:
    """Tests for generate_next_question()."""

    @pytest.mark.asyncio
    async def test_is_finished_when_question_count_gte_max(self) -> None:
        """Should return is_finished=True when question_count >= max_questions."""
        svc = OpenAIService()

        # No OpenAI call should be made for this short-circuit
        mock_client = AsyncMock()
        svc._client = mock_client

        text, is_finished = await svc.generate_next_question(
            job_role_name="前端工程师",
            difficulty="junior",
            max_questions=8,
            question_count=8,
            messages=[],
        )

        assert is_finished is True
        assert text == ""
        # Should not call OpenAI at all
        mock_client.chat.completions.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_is_finished_when_question_count_exceeds_max(self) -> None:
        """Should also handle question_count > max_questions gracefully."""
        svc = OpenAIService()

        mock_client = AsyncMock()
        svc._client = mock_client

        text, is_finished = await svc.generate_next_question(
            job_role_name="前端工程师",
            difficulty="junior",
            max_questions=8,
            question_count=10,
            messages=[],
        )

        assert is_finished is True
        assert text == ""

    @pytest.mark.asyncio
    async def test_is_finished_when_llm_outputs_complete_signal(self) -> None:
        """Should detect [INTERVIEW_COMPLETE] in LLM response."""
        svc = OpenAIService()

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "[INTERVIEW_COMPLETE]"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        svc._client = mock_client

        sid = uuid.uuid4()
        messages = [
            InterviewMessage(role="interviewer", content="Q1", sequence=1, session_id=sid),
            InterviewMessage(role="candidate", content="A1", sequence=2, session_id=sid),
        ]

        text, is_finished = await svc.generate_next_question(
            job_role_name="算法工程师",
            difficulty="senior",
            max_questions=8,
            question_count=2,
            messages=messages,
        )

        assert is_finished is True
        assert text == ""

    @pytest.mark.asyncio
    async def test_returns_next_question_normally(self) -> None:
        """Should return (question_text, False) for normal continuation."""
        svc = OpenAIService()

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "请描述一下你最近做过的项目。"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        svc._client = mock_client

        sid = uuid.uuid4()
        messages = [
            InterviewMessage(role="interviewer", content="Q1", sequence=1, session_id=sid),
            InterviewMessage(role="candidate", content="A1", sequence=2, session_id=sid),
        ]

        text, is_finished = await svc.generate_next_question(
            job_role_name="全栈工程师",
            difficulty="mid",
            max_questions=8,
            question_count=2,
            messages=messages,
        )

        assert is_finished is False
        assert isinstance(text, str)
        assert len(text) > 0
        assert text == "请描述一下你最近做过的项目。"

    @pytest.mark.asyncio
    async def test_question_count_below_max_but_llm_signals_complete(self) -> None:
        """LLM can signal completion before question_count reaches max."""
        svc = OpenAIService()

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "  [INTERVIEW_COMPLETE]  "
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        svc._client = mock_client

        sid = uuid.uuid4()
        messages = [
            InterviewMessage(role="interviewer", content="Q1", sequence=1, session_id=sid),
            InterviewMessage(role="candidate", content="A1", sequence=2, session_id=sid),
        ]

        text, is_finished = await svc.generate_next_question(
            job_role_name="产品经理",
            difficulty="mid",
            max_questions=8,
            question_count=3,
            messages=messages,
        )

        assert is_finished is True
        assert text == ""
