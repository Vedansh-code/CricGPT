"""
Orchestration Service for CricGPT (Phase 3A.6).

This module provides the central OrchestrationService coordinator that connects
QueryParser (3A.2), CapabilityExecutor (3A.4), and ResponseFormatter (3A.5)
into a unified entry point for processing natural-language cricket questions.
"""

from typing import Optional

from orchestration.schemas import QuestionRequest, OrchestrationResponse
from orchestration.parser import QueryParser
from orchestration.executor import CapabilityExecutor
from orchestration.formatter import ResponseFormatter


class OrchestrationService:
    """
    Central coordinator for CricGPT query processing pipeline.
    """

    def __init__(
        self,
        parser: Optional[QueryParser] = None,
        executor: Optional[CapabilityExecutor] = None,
        formatter: Optional[ResponseFormatter] = None,
    ):
        """
        Initialize OrchestrationService with optional dependency injection.

        Args:
            parser: Custom QueryParser instance. Defaults to QueryParser().
            executor: Custom CapabilityExecutor instance. Defaults to CapabilityExecutor().
            formatter: Custom ResponseFormatter instance. Defaults to ResponseFormatter().
        """
        self.parser = parser if parser is not None else QueryParser()
        self.executor = executor if executor is not None else CapabilityExecutor()
        self.formatter = formatter if formatter is not None else ResponseFormatter()

    def ask(self, question: str) -> OrchestrationResponse:
        """
        Process a natural language cricket question end-to-end.

        Args:
            question: User's natural language question string.

        Returns:
            OrchestrationResponse containing execution status, QueryPlan, ExecutionResult, and formatted answer.

        Raises:
            PlanningError: If question validation or parsing fails.
            UnsupportedIntentError: If intent is UNKNOWN or unregistered.
            ExecutionError: If execution fails due to missing arguments or handler error.
            FormattingError: If response formatting fails.
        """
        # Validate question using QuestionRequest schema
        try:
            req = QuestionRequest(question=question)
        except ValueError as ve:
            from orchestration.exceptions import PlanningError
            raise PlanningError(str(ve)) from ve

        clean_question = req.question


        # Step 1: Parse question into QueryPlan
        plan = self.parser.parse(clean_question)

        # Step 2: Handle Clarification Requirement
        if plan.requires_clarification:
            return OrchestrationResponse(
                success=False,
                question=clean_question,
                plan=plan,
                result=None,
                answer=plan.clarification_message,
            )

        # Step 3: Execute QueryPlan via CapabilityExecutor
        execution = self.executor.execute(plan)

        # Step 4: Format ExecutionResult into human-readable answer
        answer = self.formatter.format(execution)

        # Step 5: Return OrchestrationResponse
        return OrchestrationResponse(
            success=execution.success,
            question=clean_question,
            plan=plan,
            result=execution,
            answer=answer,
        )


def get_default_service() -> OrchestrationService:
    """
    Construct and return a default OrchestrationService instance.
    """
    return OrchestrationService()
