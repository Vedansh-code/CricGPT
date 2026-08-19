"""
CricGPT Orchestration Package.

This package provides the foundational orchestration models, intent definitions,
and exception hierarchy for CricGPT query processing pipeline.
"""

from orchestration.intents import Intent
from orchestration.schemas import (
    QuestionRequest,
    QueryArguments,
    QueryPlan,
    ExecutionResult,
    OrchestrationResponse,
)
from orchestration.exceptions import (
    OrchestrationError,
    PlanningError,
    UnsupportedIntentError,
    ClarificationRequired,
    ExecutionError,
    FormattingError,
)
from orchestration.parser import QueryParser
from orchestration.registry import (
    Capability,
    CapabilityRegistry,
    get_default_registry,
)
from orchestration.executor import CapabilityExecutor
from orchestration.formatter import ResponseFormatter
from orchestration.service import OrchestrationService, get_default_service
from orchestration.llm import LLMProvider, LLMQueryPlanner

__all__ = [
    # Service
    "OrchestrationService",
    "get_default_service",
    # LLM Planner & Provider Abstraction
    "LLMProvider",
    "LLMQueryPlanner",
    # Formatter
    "ResponseFormatter",
    # Executor
    "CapabilityExecutor",
    # Registry
    "Capability",
    "CapabilityRegistry",
    "get_default_registry",
    # Parser
    "QueryParser",
    # Intents
    "Intent",
    # Schemas
    "QuestionRequest",
    "QueryArguments",
    "QueryPlan",
    "ExecutionResult",
    "OrchestrationResponse",
    # Exceptions
    "OrchestrationError",
    "PlanningError",
    "UnsupportedIntentError",
    "ClarificationRequired",
    "ExecutionError",
    "FormattingError",
]





