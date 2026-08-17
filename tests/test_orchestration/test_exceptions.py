"""
Unit tests for orchestration exception hierarchy.
"""

import unittest

from orchestration import (
    OrchestrationError,
    PlanningError,
    UnsupportedIntentError,
    ClarificationRequired,
    ExecutionError,
    FormattingError,
)


class TestExceptions(unittest.TestCase):
    """Test cases for orchestration exception inheritance and initialization."""

    def test_hierarchy_inheritance(self):
        """Verify all custom exceptions inherit from OrchestrationError."""
        self.assertTrue(issubclass(PlanningError, OrchestrationError))
        self.assertTrue(issubclass(UnsupportedIntentError, OrchestrationError))
        self.assertTrue(issubclass(ClarificationRequired, OrchestrationError))
        self.assertTrue(issubclass(ExecutionError, OrchestrationError))
        self.assertTrue(issubclass(FormattingError, OrchestrationError))
        self.assertTrue(issubclass(OrchestrationError, Exception))

    def test_default_exception_messages(self):
        """Verify default error messages when no custom message is supplied."""
        err_base = OrchestrationError()
        self.assertEqual(str(err_base), "An orchestration error occurred.")

        err_plan = PlanningError()
        self.assertEqual(str(err_plan), "Failed to generate query plan.")

        err_intent = UnsupportedIntentError()
        self.assertEqual(str(err_intent), "The specified intent is unsupported.")

        err_clarify = ClarificationRequired()
        self.assertEqual(str(err_clarify), "Query requires clarification.")

        err_exec = ExecutionError()
        self.assertEqual(str(err_exec), "Intent execution failed.")

        err_fmt = FormattingError()
        self.assertEqual(str(err_fmt), "Result formatting failed.")

    def test_custom_exception_messages(self):
        """Verify custom error messages passed at construction."""
        msg = "Custom failure message."
        err = PlanningError(msg)
        self.assertEqual(str(err), msg)
        self.assertEqual(err.message, msg)

    def test_catch_by_base_class(self):
        """Verify derived exceptions can be caught by base OrchestrationError."""
        try:
            raise ExecutionError("Execution failed during query processing.")
        except OrchestrationError as e:
            self.assertIn("Execution failed", str(e))


if __name__ == "__main__":
    unittest.main()
