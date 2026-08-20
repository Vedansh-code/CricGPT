"""
LLM Answer Generator for CricGPT (Phase 3B.4).

This module implements LLMAnswerGenerator, converting verified structured execution
results into natural-language answers using a provider-agnostic LLM interface.
"""

import json
from typing import Any
from pydantic import BaseModel, field_validator

from orchestration.exceptions import FormattingError
from orchestration.llm.provider import LLMProvider
from orchestration.llm.prompts import SYSTEM_ANSWER_PROMPT
from orchestration.schemas import ExecutionResult


class LLMAnswerOutput(BaseModel):
    """
    Structured output model expected from LLMProvider for answer generation.
    """

    answer: str

    @field_validator("answer", mode="before")
    @classmethod
    def validate_answer(cls, v: Any) -> str:
        """Ensure answer is a non-empty string."""
        if not isinstance(v, str):
            raise ValueError("Answer must be a string.")
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Answer cannot be empty or whitespace only.")
        return cleaned


class LLMAnswerGenerator:
    """
    LLM-powered natural language answer generator for CricGPT.

    Translates verified ExecutionResult objects into natural language responses
    without performing database queries or analytics calculations.
    """

    def __init__(self, provider: LLMProvider) -> None:
        """
        Initialize LLMAnswerGenerator with an LLMProvider dependency.

        Args:
            provider: Concrete implementation of LLMProvider.

        Raises:
            TypeError: If provider is not an instance of LLMProvider.
        """
        if provider is None or not isinstance(provider, LLMProvider):
            raise TypeError("provider must be an instance of LLMProvider.")
        self._provider = provider

    def generate_answer(self, question: str, execution_result: ExecutionResult) -> str:
        """
        Generate a natural language answer from a user question and ExecutionResult.

        Args:
            question: Natural language user question string.
            execution_result: Verified ExecutionResult returned by CapabilityExecutor.

        Returns:
            Natural language answer string.

        Raises:
            FormattingError: If input is invalid, provider invocation fails, or output is malformed/empty.
        """
        if not question or not isinstance(question, str) or not question.strip():
            raise FormattingError("Question must be a non-empty string.")

        if not isinstance(execution_result, ExecutionResult):
            raise FormattingError("Input must be an ExecutionResult instance.")

        payload = {
            "question": question.strip(),
            "intent": execution_result.intent.value,
            "result": execution_result.result,
            "metadata": execution_result.metadata,
        }

        try:
            user_prompt = json.dumps(payload, default=str, indent=2)
        except Exception as exc:
            raise FormattingError(f"Failed to serialize execution result payload: {exc}") from exc

        try:
            raw_output = self._provider.generate_structured(
                system_prompt=SYSTEM_ANSWER_PROMPT,
                user_prompt=user_prompt,
                response_model=LLMAnswerOutput,
            )
        except Exception as exc:
            raise FormattingError(f"LLM answer generation failed: {exc}") from exc

        if not isinstance(raw_output, LLMAnswerOutput):
            try:
                raw_output = LLMAnswerOutput.model_validate(raw_output)
            except Exception as exc:
                raise FormattingError(f"Invalid LLM output payload: {exc}") from exc

        answer = raw_output.answer.strip()
        if not answer:
            raise FormattingError("LLM answer generator returned an empty answer.")

        return answer

    def generate(self, question: str, execution_result: ExecutionResult) -> str:
        """
        Convenience alias for generate_answer.
        """
        return self.generate_answer(question, execution_result)
