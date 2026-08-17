"""
Orchestration Exception Hierarchy for CricGPT.

This module defines the standard exception classes used across the CricGPT
orchestration pipeline (parsing, planning, execution, and formatting).
"""


class OrchestrationError(Exception):
    """Base exception class for all CricGPT orchestration errors."""

    def __init__(self, message: str = "An orchestration error occurred."):
        super().__init__(message)
        self.message = message


class PlanningError(OrchestrationError):
    """Raised when query parsing or plan generation fails."""

    def __init__(self, message: str = "Failed to generate query plan."):
        super().__init__(message)


class UnsupportedIntentError(OrchestrationError):
    """Raised when an intent cannot be handled by the registry or executor."""

    def __init__(self, message: str = "The specified intent is unsupported."):
        super().__init__(message)


class ClarificationRequired(OrchestrationError):
    """Raised when a query is ambiguous and requires user clarification."""

    def __init__(self, message: str = "Query requires clarification."):
        super().__init__(message)


class ExecutionError(OrchestrationError):
    """Raised when intent execution against SDK or backend services fails."""

    def __init__(self, message: str = "Intent execution failed."):
        super().__init__(message)


class FormattingError(OrchestrationError):
    """Raised when formatting execution results into natural language fails."""

    def __init__(self, message: str = "Result formatting failed."):
        super().__init__(message)
