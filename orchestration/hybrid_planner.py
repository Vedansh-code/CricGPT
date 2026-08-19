"""
Hybrid Query Planner for CricGPT (Phase 3B.3).

This module implements HybridQueryPlanner, which intelligently routes natural-language
cricket questions between a fast deterministic rule-based QueryParser (Phase 3A)
and a fallback LLMQueryPlanner (Phase 3B.1/3B.2).

Architecture & Isolation Rules:
- Responsible ONLY for routing and returning a QueryPlan.
- Does NOT execute SQL, access SQLite, call analytics SDK functions, or format responses.
- Preserves deterministic clarification requests without silent LLM resolution.
- Preserves provenance (`source`) of the returned QueryPlan without overwriting.
"""

from typing import Any, Optional

from orchestration.exceptions import PlanningError
from orchestration.intents import Intent
from orchestration.parser import QueryParser
from orchestration.schemas import QuestionRequest, QueryPlan


class HybridQueryPlanner:
    """
    Hybrid Query Planner combining deterministic rule-based parsing and LLM fallback.
    """

    def __init__(
        self,
        deterministic_parser: Optional[Any] = None,
        llm_planner: Optional[Any] = None,
    ) -> None:
        """
        Initialize HybridQueryPlanner.

        Args:
            deterministic_parser: Instance providing parse(question) or plan(question). Defaults to QueryParser().
            llm_planner: Optional instance providing plan(question). Created lazily if needed and None.
        """
        self._deterministic_parser = (
            deterministic_parser if deterministic_parser is not None else QueryParser()
        )
        self._llm_planner = llm_planner

    @property
    def deterministic_parser(self) -> Any:
        """Return the injected or default deterministic parser instance."""
        return self._deterministic_parser

    @property
    def llm_planner(self) -> Optional[Any]:
        """Return the injected or lazy LLM planner instance."""
        return self._llm_planner

    def _get_or_create_llm_planner(self) -> Optional[Any]:
        """
        Get the injected llm_planner or lazily instantiate LLMQueryPlanner with OpenAIProvider.
        Returns None if LLM provider cannot be configured (e.g., missing API key).
        """
        if self._llm_planner is not None:
            return self._llm_planner

        try:
            from orchestration.llm.planner import LLMQueryPlanner
            from orchestration.llm.providers.openai import OpenAIProvider

            provider = OpenAIProvider()
            self._llm_planner = LLMQueryPlanner(provider=provider)
            return self._llm_planner
        except PlanningError:
            # LLM provider is not configured or unavailable
            return None
        except Exception as exc:
            raise PlanningError(f"Failed to initialize LLM provider for fallback planning: {exc}") from exc

    def plan(self, question: str) -> QueryPlan:
        """
        Generate a QueryPlan for the given natural language question.

        Routing Strategy:
        1. Validate question using QuestionRequest schema.
        2. Attempt deterministic parsing via deterministic_parser.
        3. If deterministic parsing produces a valid executable plan (intent != UNKNOWN) OR
           a clarification request (requires_clarification=True), return it directly.
        4. If deterministic parsing produces Intent.UNKNOWN, fall back to LLMQueryPlanner.
        5. If LLM planner is available, return its resulting LLM QueryPlan directly (preserving source="llm").
        6. If LLM planner is unavailable or returns UNKNOWN, return deterministic plan or raise PlanningError.
        """
        # Step 1: Validate question contract
        try:
            req = QuestionRequest(question=question)
        except ValueError as ve:
            raise PlanningError(str(ve)) from ve

        clean_question = req.question

        # Step 2: Attempt deterministic parsing
        deterministic_plan: Optional[QueryPlan] = None
        try:
            if hasattr(self._deterministic_parser, "parse"):
                deterministic_plan = self._deterministic_parser.parse(clean_question)
            elif hasattr(self._deterministic_parser, "plan"):
                deterministic_plan = self._deterministic_parser.plan(clean_question)
        except PlanningError:
            deterministic_plan = None

        # Step 3: Check deterministic plan
        # If deterministic parser returned a valid intent OR a clarification request, return it directly.
        if (
            deterministic_plan is not None
            and isinstance(deterministic_plan, QueryPlan)
            and (deterministic_plan.intent != Intent.UNKNOWN or deterministic_plan.requires_clarification)
        ):
            return deterministic_plan

        # Step 4: Fallback to LLM planner when deterministic intent is UNKNOWN
        planner = self._get_or_create_llm_planner()
        if planner is None:
            # LLM provider is unconfigured/unavailable: fall back to deterministic plan
            if deterministic_plan is not None:
                return deterministic_plan
            raise PlanningError(f"Unable to generate query plan for question: '{clean_question}'")

        try:
            llm_plan = planner.plan(clean_question)

            if isinstance(llm_plan, QueryPlan):
                return llm_plan

            raise PlanningError(f"LLM planner returned non-QueryPlan response for '{clean_question}'.")
        except PlanningError:
            raise
        except Exception as exc:
            raise PlanningError(f"LLM planning fallback failed: {exc}") from exc

    def parse(self, question: str) -> QueryPlan:
        """
        Alias for plan() to maintain full compatibility with QueryParser interface.
        """
        return self.plan(question)
