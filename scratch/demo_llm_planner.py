"""
Manual demonstration of LLMQueryPlanner producing a structured QueryPlan.
"""

from orchestration import (
    LLMProvider,
    LLMQueryPlanner,
    Intent,
    QueryArguments,
    QueryPlan,
)
from orchestration.llm.planner import LLMPlanOutput


class DemoLLMProvider(LLMProvider):
    def generate_structured(self, system_prompt: str, user_prompt: str, response_model):
        return LLMPlanOutput(
            intent=Intent.BATTING_AVERAGE,
            arguments=QueryArguments(player_name="Virat Kohli"),
            confidence=0.95,
        )


def main():
    provider = DemoLLMProvider()
    planner = LLMQueryPlanner(provider=provider)
    plan = planner.plan("What is Virat Kohli's batting average?")
    print("Generated QueryPlan:")
    print(plan)


if __name__ == "__main__":
    main()
