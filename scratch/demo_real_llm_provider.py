"""
Manual Verification Script: Real LLM Provider Integration Demo

This script demonstrates live end-to-end query planning using OpenAIProvider and LLMQueryPlanner.
It makes actual external API calls when executed directly with valid credentials.

Required Environment Variables:
  CRICGPT_LLM_API_KEY  - Required API key (e.g. OpenAI, Groq, OpenRouter key).
  CRICGPT_LLM_MODEL    - (Optional) Model name, e.g. 'gpt-4o-mini', 'gpt-4o', 'llama-3.3-70b-versatile'.
                         Default: 'gpt-4o-mini'.
  CRICGPT_LLM_BASE_URL - (Optional) Endpoint base URL, e.g. 'https://api.openai.com/v1'.
                         Default: 'https://api.openai.com/v1'.

Usage:
  export CRICGPT_LLM_API_KEY="sk-..."
  python scratch/demo_real_llm_provider.py
"""

import os
import sys

# Ensure repository root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from orchestration.exceptions import PlanningError
from orchestration.llm.planner import LLMQueryPlanner
from orchestration.llm.providers.openai import OpenAIProvider


def main():
    print("==========================================================")
    print("       CricGPT Phase 3B.2: Real LLM Provider Demo          ")
    print("==========================================================")

    api_key = os.environ.get("CRICGPT_LLM_API_KEY")
    model = os.environ.get("CRICGPT_LLM_MODEL", "gpt-4o-mini")
    base_url = os.environ.get("CRICGPT_LLM_BASE_URL", "https://api.openai.com/v1")

    if not api_key:
        print("\n[ERROR] CRICGPT_LLM_API_KEY environment variable is not set.")
        print("Please set CRICGPT_LLM_API_KEY before running this demo.")
        print("Example (PowerShell):")
        print('  $env:CRICGPT_LLM_API_KEY="your-api-key"')
        print('  python scratch/demo_real_llm_provider.py\n')
        sys.exit(1)

    print(f"Provider: OpenAIProvider")
    print(f"Model:    {model}")
    print(f"Base URL: {base_url}")
    print("----------------------------------------------------------\n")

    try:
        provider = OpenAIProvider(
            api_key=api_key,
            model=model,
            base_url=base_url,
        )
        planner = LLMQueryPlanner(provider=provider)
    except PlanningError as exc:
        print(f"[ERROR] Failed to initialize provider: {exc}")
        sys.exit(1)

    sample_questions = [
        "What is Virat Kohli's batting average?",
        "How has Virat Kohli performed against Jasprit Bumrah?",
        "Show me the scorecard for match 1304112.",
    ]

    for question in sample_questions:
        print(f"Question: \"{question}\"")
        try:
            plan = planner.plan(question)
            print(f"  -> Intent:                 {plan.intent}")
            print(f"  -> Arguments:              {plan.arguments.model_dump()}")
            print(f"  -> Confidence:             {plan.confidence}")
            print(f"  -> Requires Clarification: {plan.requires_clarification}")
            if plan.clarification_message:
                print(f"  -> Clarification Message:  {plan.clarification_message}")
            print(f"  -> Source:                 {plan.source}\n")
        except PlanningError as exc:
            print(f"  [PlanningError] {exc}\n")
        except Exception as exc:
            print(f"  [Unexpected Error] {exc}\n")

    print("Demo completed successfully.")


if __name__ == "__main__":
    main()
