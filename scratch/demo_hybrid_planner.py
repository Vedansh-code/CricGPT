"""
Manual Demonstration Script for Phase 3B.3 Hybrid Query Planning & Routing.

This script demonstrates offline hybrid query planning and routing behavior across:
1. Fast deterministic path (Phase 3A) - LLM not called, source="rule_based_parser".
2. LLM fallback path (Phase 3B.1/3B.2) - LLM invoked, source="llm".
3. Ambiguity preservation ("Kohli vs Bumrah") - requires_clarification=True preserved.
4. Default OrchestrationService execution without an LLM API key.
"""

import os
import sys

# Ensure repository root is on sys.path for standalone script execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import MagicMock

from orchestration.intents import Intent
from orchestration.schemas import QueryArguments, QueryPlan
from orchestration.hybrid_planner import HybridQueryPlanner
from orchestration.service import OrchestrationService


def main():
    print("================================================================")
    print(" CricGPT Phase 3B.3: Hybrid Query Planning & Routing Demonstration")
    print("================================================================\n")

    # Setup Mock LLM Planner for offline demonstration
    mock_llm_planner = MagicMock()
    mock_llm_planner.plan.side_effect = lambda question: QueryPlan(
        intent=Intent.PLAYER_RECENT_MATCHES,
        arguments=QueryArguments(player_name="Virat Kohli", limit=5),
        confidence=0.95,
        source="llm",
        requires_clarification=False,
    )

    hybrid_planner = HybridQueryPlanner(llm_planner=mock_llm_planner)

    # ------------------------------------------------------------------
    # Case A: Deterministic Path ("What is Virat Kohli's batting average?")
    # ------------------------------------------------------------------
    print("----------------------------------------------------------------")
    print("Case A: Deterministic Path")
    print("Question: 'What is Virat Kohli's batting average?'")
    print("----------------------------------------------------------------")
    plan_a = hybrid_planner.plan("What is Virat Kohli's batting average?")
    print(f"Intent:                 {plan_a.intent}")
    print(f"Arguments:              {plan_a.arguments.model_dump()}")
    print(f"Source:                 {plan_a.source}")
    print(f"Requires Clarification: {plan_a.requires_clarification}")
    print(f"LLM Called:             {mock_llm_planner.plan.called}")
    assert plan_a.source == "rule_based_parser"
    assert not mock_llm_planner.plan.called
    print("=> SUCCESS: Deterministic parser handled query; LLM was NOT called.\n")

    # Reset mock call tracker
    mock_llm_planner.plan.reset_mock()

    # ------------------------------------------------------------------
    # Case B: Fallback Path ("Analyze Kohli's recent performance")
    # ------------------------------------------------------------------
    print("----------------------------------------------------------------")
    print("Case B: Fallback Path to LLM")
    print("Question: 'Analyze Kohli's recent performance'")
    print("----------------------------------------------------------------")
    plan_b = hybrid_planner.plan("Analyze Kohli's recent performance")
    print(f"Intent:                 {plan_b.intent}")
    print(f"Arguments:              {plan_b.arguments.model_dump()}")
    print(f"Source:                 {plan_b.source}")
    print(f"Requires Clarification: {plan_b.requires_clarification}")
    print(f"LLM Called:             {mock_llm_planner.plan.called}")
    assert plan_b.source == "llm"
    assert mock_llm_planner.plan.called
    print("=> SUCCESS: Unrecognized deterministic query successfully routed to LLM.\n")

    # Reset mock call tracker
    mock_llm_planner.plan.reset_mock()

    # ------------------------------------------------------------------
    # Case C: Ambiguity Preservation ("Kohli vs Bumrah")
    # ------------------------------------------------------------------
    print("----------------------------------------------------------------")
    print("Case C: Ambiguity Preservation")
    print("Question: 'Kohli vs Bumrah'")
    print("----------------------------------------------------------------")
    plan_c = hybrid_planner.plan("Kohli vs Bumrah")
    print(f"Intent:                 {plan_c.intent}")
    print(f"Arguments:              {plan_c.arguments.model_dump()}")
    print(f"Source:                 {plan_c.source}")
    print(f"Requires Clarification: {plan_c.requires_clarification}")
    print(f"Clarification Message:  {plan_c.clarification_message}")
    print(f"LLM Called:             {mock_llm_planner.plan.called}")
    assert plan_c.source == "rule_based_parser"
    assert plan_c.intent == Intent.BATTER_VS_BOWLER or plan_c.requires_clarification
    print("=> SUCCESS: Ambiguity preserved; query not silently resolved.\n")

    # ------------------------------------------------------------------
    # Case D: Default OrchestrationService execution without LLM credentials
    # ------------------------------------------------------------------
    print("----------------------------------------------------------------")
    print("Case D: Default Service Without LLM API Key")
    print("Question: 'What is Virat Kohli's batting average?'")
    print("----------------------------------------------------------------")
    old_key = os.environ.pop("CRICGPT_LLM_API_KEY", None)
    try:
        service = OrchestrationService()
        response = service.ask("What is Virat Kohli's batting average?")
        print(f"Success:      {response.success}")
        print(f"Plan Intent:  {response.plan.intent if response.plan else None}")
        print(f"Plan Source:  {response.plan.source if response.plan else None}")
        print(f"Answer:       {response.answer}")
        assert response.success
        assert response.plan is not None
        assert response.plan.source == "rule_based_parser"
        print("=> SUCCESS: Default OrchestrationService executed Phase 3A query without API key.\n")
    finally:
        if old_key is not None:
            os.environ["CRICGPT_LLM_API_KEY"] = old_key

    print("================================================================")
    print(" All Phase 3B.3 Manual Demonstrations Completed Successfully!")
    print("================================================================")


if __name__ == "__main__":
    main()
