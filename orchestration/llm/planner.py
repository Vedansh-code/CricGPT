"""
LLM Query Planner for CricGPT.

This module implements LLMQueryPlanner, converting natural-language cricket
questions into structured QueryPlan instances using a provider-agnostic LLM interface.
"""

from typing import Optional
from pydantic import BaseModel, Field, ValidationError

from orchestration.exceptions import PlanningError
from orchestration.intents import Intent
from orchestration.llm.provider import LLMProvider
from orchestration.llm.prompts import SYSTEM_PLANNING_PROMPT
from orchestration.schemas import QuestionRequest, QueryArguments, QueryPlan


class LLMPlanOutput(BaseModel):
    """
    Internal structured output schema expected from LLMProvider.
    """

    intent: Intent
    arguments: QueryArguments = Field(default_factory=QueryArguments)
    confidence: float = 1.0
    requires_clarification: bool = False
    clarification_message: Optional[str] = None


class LLMQueryPlanner:
    """
    Query planner that leverages an LLMProvider to translate natural-language
    questions into structured QueryPlan contracts.
    """

    def __init__(self, provider: LLMProvider) -> None:
        """
        Initialize LLMQueryPlanner with a provider dependency.

        Args:
            provider: Concrete implementation of LLMProvider.

        Raises:
            TypeError: If provider is not an instance of LLMProvider.
        """
        if provider is None or not isinstance(provider, LLMProvider):
            raise TypeError("provider must be an instance of LLMProvider.")
        self._provider = provider

    def plan(self, question: str) -> QueryPlan:
        """
        Convert a natural language question into a validated QueryPlan.

        Args:
            question: Natural language cricket question string.

        Returns:
            Validated QueryPlan instance with source="llm".

        Raises:
            ValueError: If input question is invalid, empty, or whitespace-only.
            PlanningError: If provider invocation or model output validation fails.
        """
        # Step 1: Validate input question using QuestionRequest schema
        req = QuestionRequest(question=question)

        # Step 2: Invoke provider for structured generation
        try:
            raw_output = self._provider.generate_structured(
                system_prompt=SYSTEM_PLANNING_PROMPT,
                user_prompt=req.question,
                response_model=LLMPlanOutput,
            )
        except PlanningError:
            raise
        except Exception as exc:
            raise PlanningError(f"LLM provider failed during plan generation: {exc}") from exc

        # Step 3: Ensure output type safety / validation
        if not isinstance(raw_output, LLMPlanOutput):
            try:
                raw_output = LLMPlanOutput.model_validate(raw_output)
            except Exception as exc:
                raise PlanningError(f"Invalid LLM output payload: {exc}") from exc

        # Step 4: Construct and validate final QueryPlan with source="llm"
        try:
            return QueryPlan(
                version="1.0",
                intent=raw_output.intent,
                arguments=raw_output.arguments,
                confidence=raw_output.confidence,
                source="llm",
                requires_clarification=raw_output.requires_clarification,
                clarification_message=raw_output.clarification_message,
            )
        except (ValidationError, ValueError) as exc:
            raise PlanningError(f"Failed to construct valid QueryPlan from LLM output: {exc}") from exc
