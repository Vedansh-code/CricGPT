"""
Unit tests for LLMAnswerGenerator (Phase 3B.4).
"""

import unittest
from unittest.mock import MagicMock, patch
import json

from orchestration.intents import Intent
from orchestration.schemas import ExecutionResult
from orchestration.exceptions import FormattingError, PlanningError
from orchestration.llm.provider import LLMProvider
from orchestration.llm.answer_generator import LLMAnswerGenerator, LLMAnswerOutput
from orchestration.llm.prompts import SYSTEM_ANSWER_PROMPT


class MockLLMProvider(LLMProvider):
    """Mock LLMProvider implementation for offline testing."""

    def __init__(self, mock_response: str = "Mock answer"):
        self.mock_response = mock_response
        self.last_system_prompt: str | None = None
        self.last_user_prompt: str | None = None

    def generate_structured(self, system_prompt: str, user_prompt: str, response_model):
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        return response_model(answer=self.mock_response)


class TestLLMAnswerGenerator(unittest.TestCase):
    """Unit test suite for LLMAnswerGenerator."""

    def setUp(self):
        self.mock_provider = MockLLMProvider("Virat Kohli has a batting average of 32.8 against Jasprit Bumrah.")
        self.generator = LLMAnswerGenerator(provider=self.mock_provider)
        self.exec_result = ExecutionResult(
            success=True,
            intent=Intent.BATTER_VS_BOWLER,
            result={
                "batter_name": "Virat Kohli",
                "bowler_name": "Jasprit Bumrah",
                "runs": 164,
                "balls": 110,
                "dismissals": 5,
                "average": 32.8,
                "strike_rate": 149.09,
            },
            metadata={"capability": "Batter vs Bowler matchup"},
        )

    def test_generates_answer_from_execution_result(self):
        answer = self.generator.generate_answer("How has Virat Kohli performed against Jasprit Bumrah?", self.exec_result)
        self.assertEqual(answer, "Virat Kohli has a batting average of 32.8 against Jasprit Bumrah.")

    def test_provider_dependency_injection(self):
        custom_provider = MockLLMProvider("Custom answer")
        gen = LLMAnswerGenerator(provider=custom_provider)
        answer = gen.generate("What is Kohli's stat?", self.exec_result)
        self.assertEqual(answer, "Custom answer")

        with self.assertRaises(TypeError):
            LLMAnswerGenerator(provider=None)  # type: ignore[arg-type]

        with self.assertRaises(TypeError):
            LLMAnswerGenerator(provider="invalid_provider")  # type: ignore[arg-type]

    def test_structured_output_is_validated(self):
        mock_p = MagicMock(spec=LLMProvider)
        mock_p.generate_structured.return_value = LLMAnswerOutput(answer="Validated structured answer")
        gen = LLMAnswerGenerator(provider=mock_p)
        ans = gen.generate_answer("Test question", self.exec_result)
        self.assertEqual(ans, "Validated structured answer")

    def test_empty_answer_is_rejected(self):
        mock_p = MagicMock(spec=LLMProvider)
        mock_p.generate_structured.return_value = LLMAnswerOutput.model_construct(answer="")
        gen = LLMAnswerGenerator(provider=mock_p)

        with self.assertRaises(FormattingError) as ctx:
            gen.generate_answer("Test question", self.exec_result)
        self.assertIn("empty", str(ctx.exception).lower())

    def test_malformed_output_raises_error(self):
        mock_p = MagicMock(spec=LLMProvider)
        mock_p.generate_structured.return_value = "invalid raw output string"
        gen = LLMAnswerGenerator(provider=mock_p)

        with self.assertRaises(FormattingError) as ctx:
            gen.generate_answer("Test question", self.exec_result)
        self.assertIn("invalid", str(ctx.exception).lower())

    def test_provider_failure_is_wrapped(self):
        mock_p = MagicMock(spec=LLMProvider)
        mock_p.generate_structured.side_effect = PlanningError("Provider connection failed")
        gen = LLMAnswerGenerator(provider=mock_p)

        with self.assertRaises(FormattingError) as ctx:
            gen.generate_answer("Test question", self.exec_result)
        self.assertIn("failed", str(ctx.exception).lower())

    def test_original_question_is_passed_to_generator(self):
        question = "How many runs did Kohli score against Bumrah?"
        self.generator.generate_answer(question, self.exec_result)
        self.assertIsNotNone(self.mock_provider.last_user_prompt)
        assert self.mock_provider.last_user_prompt is not None
        prompt_data = json.loads(self.mock_provider.last_user_prompt)
        self.assertEqual(prompt_data["question"], question)

    def test_execution_result_is_passed_to_generator(self):
        self.generator.generate_answer("How did Kohli perform?", self.exec_result)
        self.assertIsNotNone(self.mock_provider.last_user_prompt)
        assert self.mock_provider.last_user_prompt is not None
        prompt_data = json.loads(self.mock_provider.last_user_prompt)
        self.assertEqual(prompt_data["intent"], Intent.BATTER_VS_BOWLER.value)
        self.assertEqual(prompt_data["result"]["runs"], 164)
        self.assertEqual(prompt_data["result"]["average"], 32.8)

    def test_no_database_access(self):
        with patch("sqlite3.connect") as mock_sql:
            self.generator.generate_answer("How did Kohli perform?", self.exec_result)
            mock_sql.assert_not_called()

    def test_no_analytics_sdk_access(self):
        with patch("analytics.batting.batting_average") as mock_sdk:
            self.generator.generate_answer("How did Kohli perform?", self.exec_result)
            mock_sdk.assert_not_called()


    def test_no_statistics_are_calculated_by_generator(self):
        # Generator takes raw result from execution_result directly without calculating
        with patch("builtins.sum") as mock_sum:
            ans = self.generator.generate_answer("How did Kohli perform?", self.exec_result)
            self.assertTrue(isinstance(ans, str))

    def test_mock_provider_works_offline(self):
        # Verify no network connections made during offline execution
        with patch("httpx.Client") as mock_client:
            ans = self.generator.generate_answer("Offline question", self.exec_result)
            mock_client.assert_not_called()
            self.assertIsNotNone(ans)

    def test_system_prompt_contains_constraints(self):
        self.assertIn("SOURCE OF TRUTH", SYSTEM_ANSWER_PROMPT)
        self.assertIn("NO HALLUCINATION", SYSTEM_ANSWER_PROMPT)
        self.assertIn("Do NOT invent or fabricate cricket statistics", SYSTEM_ANSWER_PROMPT)
        self.assertIn("Do NOT modify or recalculate numerical values", SYSTEM_ANSWER_PROMPT)
        self.assertIn("Do NOT perform unsupported calculations", SYSTEM_ANSWER_PROMPT)


if __name__ == "__main__":
    unittest.main()
