"""
Orchestration Service for CricGPT (Phase 3A.6).

This module provides the central OrchestrationService coordinator that connects
QueryParser (3A.2), CapabilityExecutor (3A.4), and ResponseFormatter (3A.5)
into a unified entry point for processing natural-language cricket questions.
"""

from typing import Any, Optional

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
        parser: Optional[Any] = None,
        executor: Optional[CapabilityExecutor] = None,
        formatter: Optional[ResponseFormatter] = None,
        planner: Optional[Any] = None,
        answer_generator: Optional[Any] = None,
    ):
        """
        Initialize OrchestrationService with optional dependency injection.

        Precedence rules:
        1. If planner is explicitly supplied, use planner.
        2. Else if parser is explicitly supplied, use parser directly (preserving Phase 3A behavior).
        3. Else, default to HybridQueryPlanner().

        Args:
            parser: Custom QueryParser instance.
            executor: Custom CapabilityExecutor instance. Defaults to CapabilityExecutor().
            formatter: Custom ResponseFormatter instance. Defaults to ResponseFormatter().
            planner: Custom planner instance (e.g. HybridQueryPlanner or LLMQueryPlanner).
            answer_generator: Custom answer generator instance (e.g. LLMAnswerGenerator). Defaults to None.
        """
        if planner is not None:
            self.planner = planner
            self.parser = planner
            self._use_planner_method = True
        elif parser is not None:
            self.planner = parser
            self.parser = parser
            self._use_planner_method = False
        else:
            from orchestration.hybrid_planner import HybridQueryPlanner
            default_hybrid = HybridQueryPlanner()
            self.planner = default_hybrid
            self.parser = default_hybrid
            self._use_planner_method = True

        self.executor = executor if executor is not None else CapabilityExecutor()
        self.formatter = formatter if formatter is not None else ResponseFormatter()
        self.answer_generator = answer_generator

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

        # Step 1: Parse/plan question into QueryPlan according to precedence
        if self._use_planner_method and hasattr(self.planner, "plan"):
            plan = self.planner.plan(clean_question)
        else:
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

        # Step 4: Format ExecutionResult into human-readable answer (with LLM answer generator & fallback)
        answer = None
        if self.answer_generator is not None:
            try:
                if hasattr(self.answer_generator, "generate_answer"):
                    answer = self.answer_generator.generate_answer(clean_question, execution)
                elif hasattr(self.answer_generator, "generate"):
                    answer = self.answer_generator.generate(clean_question, execution)
            except Exception:
                # Safe Fallback to ResponseFormatter if LLM answer generator fails
                answer = None

        if answer is None:
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
