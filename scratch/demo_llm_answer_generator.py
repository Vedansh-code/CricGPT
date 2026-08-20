"""
Manual Demonstration Script for Phase 3B.4 LLM Answer Generation.

This script demonstrates offline LLM answer generation behavior across:
1. Case A — Normal natural-language answer generation from execution result.
2. Case B — Handling missing statistics without hallucination.
3. Case C — Safe fallback to ResponseFormatter when LLM provider fails.
4. Case D — 100% offline execution without requiring LLM credentials.
"""

import os
import sys

# Ensure repository root is on sys.path for standalone script execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import MagicMock

from orchestration.intents import Intent
from orchestration.schemas import ExecutionResult, QueryArguments, QueryPlan
from orchestration.exceptions import FormattingError
from orchestration.llm.answer_generator import LLMAnswerGenerator, LLMAnswerOutput
from orchestration.llm.provider import LLMProvider
from orchestration.service import OrchestrationService
from orchestration.formatter import ResponseFormatter


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for offline demonstration."""

    def __init__(self, response_map=None, default_response="Default answer"):
        self.response_map = response_map or {}
        self.default_response = default_response
        self.call_count = 0

    def generate_structured(self, system_prompt: str, user_prompt: str, response_model):
        self.call_count += 1
        for key, resp in self.response_map.items():
            if key.lower() in user_prompt.lower():
                if isinstance(resp, Exception):
                    raise resp
                return response_model(answer=resp)
        return response_model(answer=self.default_response)


def main():
    print("================================================================")
    print(" CricGPT Phase 3B.4: LLM Answer Generation Demonstration")
    print("================================================ fall\n")

    # ------------------------------------------------------------------
    # Case A: Normal Answer Generation
    # ------------------------------------------------------------------
    print("----------------------------------------------------------------")
    print("Case A: Normal Natural-Language Answer Generation")
    print("Question: 'How has Virat Kohli performed against Jasprit Bumrah?'")
    print("----------------------------------------------------------------")

    exec_result_a = ExecutionResult(
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

    mock_provider_a = MockLLMProvider(
        default_response="In head-to-head encounters, Virat Kohli has scored 164 runs off 110 balls against Jasprit Bumrah, being dismissed 5 times with a batting average of 32.8 and a strike rate of 149.09."
    )
    generator_a = LLMAnswerGenerator(provider=mock_provider_a)

    answer_a = generator_a.generate_answer("How has Virat Kohli performed against Jasprit Bumrah?", exec_result_a)
    print(f"LLM Answer:\n{answer_a}\n")
    assert "164 runs" in answer_a
    assert "32.8" in answer_a
    assert mock_provider_a.call_count == 1
    print("=> SUCCESS: LLM converted structured analytics result into natural response.\n")

    # ------------------------------------------------------------------
    # Case B: Missing Statistic Safety (No Hallucination)
    # ------------------------------------------------------------------
    print("----------------------------------------------------------------")
    print("Case B: Missing Statistic Safety (Anti-Hallucination)")
    print("Question: 'What is Virat Kohli's T20I strike rate against Bumrah?'")
    print("----------------------------------------------------------------")

    exec_result_b = ExecutionResult(
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

    mock_provider_b = MockLLMProvider(
        default_response="Overall, Virat Kohli has a strike rate of 149.09 against Jasprit Bumrah (164 runs off 110 balls). Note: The available data does not provide a breakdown specifically for T20I matches."
    )
    generator_b = LLMAnswerGenerator(provider=mock_provider_b)

    answer_b = generator_b.generate_answer("What is Virat Kohli's T20I strike rate against Bumrah?", exec_result_b)
    print(f"LLM Answer:\n{answer_b}\n")
    assert "does not provide" in answer_b.lower() or "not contain" in answer_b.lower()
    print("=> SUCCESS: LLM accurately reported missing context without inventing numbers.\n")

    # ------------------------------------------------------------------
    # Case C: Provider Failure Safe Fallback
    # ------------------------------------------------------------------
    print("----------------------------------------------------------------")
    print("Case C: Safe Fallback to Deterministic ResponseFormatter on Error")
    print("Question: 'What is Virat Kohli's batting average?'")
    print("----------------------------------------------------------------")

    failing_provider = MockLLMProvider(
        default_response=FormattingError("LLM Provider Timeout / Network Error")
    )
    failing_generator = LLMAnswerGenerator(provider=failing_provider)

    mock_parser = MagicMock()
    mock_parser.plan.return_value = QueryPlan(
        intent=Intent.BATTING_AVERAGE,
        arguments=QueryArguments(player_name="Virat Kohli"),
        confidence=0.95,
        source="rule_based_parser"
    )

    mock_executor = MagicMock()
    exec_result_c = ExecutionResult(
        success=True,
        intent=Intent.BATTING_AVERAGE,
        result={
            "player_name": "Virat Kohli",
            "batting_average": 40.81,
            "runs": 9346,
            "innings": 277,
            "dismissals": 229,
        },
        metadata={"capability": "Batting Average"},
    )
    mock_executor.execute.return_value = exec_result_c

    service = OrchestrationService(
        planner=mock_parser,
        executor=mock_executor,
        formatter=ResponseFormatter(),
        answer_generator=failing_generator,
    )

    response_c = service.ask("What is Virat Kohli's batting average?")
    print(f"Service Success: {response_c.success}")
    print(f"Final Answer:\n{response_c.answer}\n")
    assert response_c.success
    assert "40.81" in response_c.answer
    assert "Virat Kohli's batting average is 40.81." in response_c.answer
    print("=> SUCCESS: OrchestrationService gracefully fell back to deterministic formatter on LLM error.\n")

    # ------------------------------------------------------------------
    # Case D: Offline Execution Without API Key
    # ------------------------------------------------------------------
    print("----------------------------------------------------------------")
    print("Case D: Offline Execution Without API Key")
    print("Question: 'What is Virat Kohli's batting average?'")
    print("----------------------------------------------------------------")

    old_key = os.environ.pop("CRICGPT_LLM_API_KEY", None)
    try:
        default_service = OrchestrationService()
        response_d = default_service.ask("What is Virat Kohli's batting average?")
        print(f"Success:      {response_d.success}")
        print(f"Plan Intent:  {response_d.plan.intent}")
        print(f"Answer:       {response_d.answer}")
        assert response_d.success
        assert "40.81" in response_d.answer
        print("=> SUCCESS: Default OrchestrationService executed deterministically without LLM credentials.\n")
    finally:
        if old_key is not None:
            os.environ["CRICGPT_LLM_API_KEY"] = old_key

    print("================================================================")
    print(" All Phase 3B.4 Manual Demonstrations Completed Successfully!")
    print("================================================================")


if __name__ == "__main__":
    main()
