"""OpenAI adapter — client initialization, retry logic, and prompt utilities."""

import asyncio
import json
import logging
from pathlib import Path

import openai
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import AppException
from app.models.interview_message import InterviewMessage

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

_DIFFICULTY_LABELS = {
    "junior": "初级（应届生/1年以内）",
    "mid": "中级（1-3年经验）",
    "senior": "高级（3年以上经验）",
}


def _load_prompt(filename: str) -> str:
    """Load a prompt template from the prompts directory."""
    path = _PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8")


def format_conversation_history(messages: list[InterviewMessage]) -> str:
    """Format messages into the conversation_history string.

    Format (per ARCHITECTURE §6.5):
        面试官：{content}
        候选人：{content}
        ...
    """
    role_map = {"interviewer": "面试官", "candidate": "候选人"}
    lines = []
    for msg in sorted(messages, key=lambda m: m.sequence):
        role_label = role_map.get(msg.role, msg.role)
        lines.append(f"{role_label}：{msg.content}")
    return "\n".join(lines)


class OpenAIService:
    """OpenAI API adapter with retry logic and prompt management."""

    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout_seconds,
            max_retries=0,  # We handle retries ourselves
        )
        self._model = settings.openai_model
        self._max_retries = settings.openai_max_retries

    async def generate_first_question(
        self,
        job_role_name: str,
        difficulty: str,
        max_questions: int,
    ) -> str:
        """Generate the first interview question.

        Args:
            job_role_name: Display name of the job role (e.g. "前端工程师").
            difficulty: Enum value — "junior", "mid", or "senior".
            max_questions: Maximum number of questions for this session.

        Returns:
            The first question text.
        """
        difficulty_label = _DIFFICULTY_LABELS[difficulty]
        system_prompt = _load_prompt("interview_system_prompt.txt").format(
            job_role_name=job_role_name,
            difficulty_label=difficulty_label,
            max_questions=max_questions,
        )
        user_prompt = _load_prompt("interview_first_question_prompt.txt")

        return await self._chat_completion(system_prompt, user_prompt)

    async def generate_next_question(
        self,
        job_role_name: str,
        difficulty: str,
        max_questions: int,
        question_count: int,
        messages: list[InterviewMessage],
    ) -> tuple[str, bool]:
        """Generate the next interview question based on conversation history.

        Args:
            job_role_name: Display name of the job role.
            difficulty: Enum value — "junior", "mid", or "senior".
            max_questions: Maximum number of questions for this session.
            question_count: Number of questions already asked.
            messages: All messages in the session so far.

        Returns:
            A tuple of (question_text, is_finished).
            is_finished is True when the LLM signals completion or
            question_count >= max_questions.
        """
        # Short-circuit: max questions already reached
        if question_count >= max_questions:
            return ("", True)

        difficulty_label = _DIFFICULTY_LABELS[difficulty]
        system_prompt = _load_prompt("interview_system_prompt.txt").format(
            job_role_name=job_role_name,
            difficulty_label=difficulty_label,
            max_questions=max_questions,
        )
        conversation_history = format_conversation_history(messages)
        user_prompt = _load_prompt("interview_next_question_prompt.txt").format(
            conversation_history=conversation_history,
            question_count=question_count,
            max_questions=max_questions,
        )

        response = await self._chat_completion(system_prompt, user_prompt)

        # Check for completion signal
        if "[INTERVIEW_COMPLETE]" in response:
            return ("", True)

        return (response, False)

    async def _chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 500,
        response_format: dict | None = None,
    ) -> str:
        """Send a chat completion request with retry logic.

        Retries up to max_retries times on Timeout/RateLimit/APIError.
        Raises AppException(50201) after all retries are exhausted.
        """
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                kwargs: dict = {
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if response_format is not None:
                    kwargs["response_format"] = response_format

                response = await self._client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content
                if content is None:
                    raise openai.APIError(
                        message="Empty response from OpenAI",
                        request=response,  # type: ignore[arg-type]
                        body=None,
                    )
                return content.strip()

            except (
                openai.APITimeoutError,
                openai.RateLimitError,
                openai.APIError,
            ) as e:
                last_error = e
                if attempt < self._max_retries:
                    logger.warning(
                        "OpenAI attempt %d/%d failed: %s. Retrying...",
                        attempt + 1,
                        self._max_retries + 1,
                        e,
                    )
                    await asyncio.sleep(1)
                else:
                    logger.error(
                        "OpenAI all %d attempts failed: %s",
                        self._max_retries + 1,
                        e,
                    )

        raise AppException(
            code=50201,
            message="AI 服务暂时不可用",
            status_code=502,
        ) from last_error

    async def _chat_completion_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> dict:
        """Send a chat completion request expecting JSON output.

        Parses the response and returns a dict.
        Raises AppException(50201) if parsing fails.
        """
        content = await self._chat_completion(
            system_prompt,
            user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse OpenAI JSON response: %s", e)
            raise AppException(
                code=50201,
                message="AI 服务暂时不可用",
                status_code=502,
            ) from e
