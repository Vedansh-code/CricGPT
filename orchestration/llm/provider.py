"""
Abstract LLM Provider Interface for CricGPT.

This module defines the provider-agnostic contract for invoking Large Language
Models with structured output validation.
"""

from abc import ABC, abstractmethod
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """
    Abstract base class for provider-neutral LLM execution.

    Implementations translate structured schema generation requests into provider-specific
    API calls (e.g., OpenAI, Gemini, Anthropic, or local models).
    """

    @abstractmethod
    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> T:
        """
        Generate structured response matching the specified Pydantic response_model.

        Args:
            system_prompt: System context instructions for the LLM.
            user_prompt: User request / question.
            response_model: Expected Pydantic model class for output validation.

        Returns:
            An instance of response_model populated with output.

        Raises:
            PlanningError: If generation, provider call, or output validation fails.
        """
        pass
