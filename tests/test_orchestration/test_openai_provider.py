"""
Unit tests for OpenAIProvider (Phase 3B.2).

All tests run strictly offline using unittest.mock to mock httpx.Client calls.
"""

import json
import os
import unittest
from unittest.mock import MagicMock, patch
from pydantic import BaseModel, Field

import httpx

from orchestration.exceptions import PlanningError
from orchestration.intents import Intent
from orchestration.schemas import QueryArguments
from orchestration.llm.planner import LLMPlanOutput, LLMQueryPlanner
from orchestration.llm.providers.openai import OpenAIProvider


class CustomTestModel(BaseModel):
    title: str
    count: int = Field(default=0)


class TestOpenAIProvider(unittest.TestCase):
    """Test OpenAIProvider configuration, HTTP generation, structured output parsing, and error handling."""

    def setUp(self):
        self.api_key = "test-sk-1234567890"
        self.env_patcher = patch.dict(os.environ, {"CRICGPT_LLM_API_KEY": self.api_key})
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    def test_missing_api_key_raises_planning_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(PlanningError) as ctx:
                OpenAIProvider(api_key=None)
            self.assertIn("API key is not configured", str(ctx.exception))

    def test_default_timeout_is_30(self):
        provider = OpenAIProvider(api_key=self.api_key)
        self.assertEqual(provider.timeout, 30.0)

    def test_cricgpt_llm_timeout_env_var_respected(self):
        with patch.dict(os.environ, {"CRICGPT_LLM_API_KEY": self.api_key, "CRICGPT_LLM_TIMEOUT": "45.5"}):
            provider = OpenAIProvider()
            self.assertEqual(provider.timeout, 45.5)

    def test_explicit_timeout_overrides_env_var(self):
        with patch.dict(os.environ, {"CRICGPT_LLM_API_KEY": self.api_key, "CRICGPT_LLM_TIMEOUT": "45.5"}):
            provider = OpenAIProvider(timeout=10.0)
            self.assertEqual(provider.timeout, 10.0)

    def test_invalid_cricgpt_llm_timeout_raises_planning_error(self):
        with patch.dict(os.environ, {"CRICGPT_LLM_API_KEY": self.api_key, "CRICGPT_LLM_TIMEOUT": "not_a_number"}):
            with self.assertRaises(PlanningError) as ctx:
                OpenAIProvider()
            self.assertIn("Invalid CRICGPT_LLM_TIMEOUT environment variable value", str(ctx.exception))

    def test_invalid_explicit_timeout_raises_planning_error(self):
        with self.assertRaises(PlanningError) as ctx:
            OpenAIProvider(timeout="invalid")
        self.assertIn("Invalid timeout value", str(ctx.exception))

    @patch("httpx.Client")
    def test_httpx_client_created_with_resolved_timeout_when_no_client_injected(self, mock_client_cls):
        mock_client_inst = MagicMock()
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps({"intent": "BATTING_AVERAGE"})}}]
        }
        mock_client_inst.post.return_value = mock_response
        mock_client_cls.return_value = mock_client_inst

        with patch.dict(os.environ, {"CRICGPT_LLM_API_KEY": self.api_key, "CRICGPT_LLM_TIMEOUT": "25.0"}):
            provider = OpenAIProvider()
            provider.generate_structured("sys", "user", LLMPlanOutput)

        mock_client_cls.assert_called_once_with(timeout=25.0)

    @patch("httpx.Client")
    def test_injected_client_reused_and_no_new_client_created(self, mock_client_cls):
        injected_client = MagicMock()
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps({"intent": "BATTING_AVERAGE"})}}]
        }
        injected_client.post.return_value = mock_response

        provider = OpenAIProvider(api_key=self.api_key, client=injected_client)
        provider.generate_structured("sys", "user", LLMPlanOutput)

        mock_client_cls.assert_not_called()
        injected_client.post.assert_called_once()

    def test_environment_configuration(self):
        provider = OpenAIProvider(
            api_key="custom-key",
            model="gpt-4o",
            base_url="https://custom.api.endpoint/v1",
            timeout=15.0,
        )
        self.assertEqual(provider.api_key, "custom-key")
        self.assertEqual(provider.model, "gpt-4o")
        self.assertEqual(provider.base_url, "https://custom.api.endpoint/v1")
        self.assertEqual(provider.timeout, 15.0)

    def test_env_var_fallback_configuration(self):
        env_vars = {
            "CRICGPT_LLM_API_KEY": "env-key-999",
            "CRICGPT_LLM_MODEL": "gpt-3.5-turbo",
            "CRICGPT_LLM_BASE_URL": "https://env.api.com/v1/",
            "CRICGPT_LLM_TIMEOUT": "20.0",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            provider = OpenAIProvider()
            self.assertEqual(provider.api_key, "env-key-999")
            self.assertEqual(provider.model, "gpt-3.5-turbo")
            self.assertEqual(provider.base_url, "https://env.api.com/v1")
            self.assertEqual(provider.timeout, 20.0)

    def test_successful_structured_generation(self):
        mock_response_payload = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "intent": "BATTING_AVERAGE",
                                "arguments": {"player_name": "Virat Kohli"},
                                "confidence": 0.98,
                                "requires_clarification": False,
                                "clarification_message": None,
                            }
                        )
                    }
                }
            ]
        }

        mock_http_response = MagicMock(spec=httpx.Response)
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = mock_response_payload

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_http_response

        provider = OpenAIProvider(api_key=self.api_key, client=mock_client)
        result = provider.generate_structured(
            system_prompt="System instructions",
            user_prompt="What is Virat Kohli's batting average?",
            response_model=LLMPlanOutput,
        )

        self.assertIsInstance(result, LLMPlanOutput)
        self.assertEqual(result.intent, Intent.BATTING_AVERAGE)
        self.assertEqual(result.arguments.player_name, "Virat Kohli")
        self.assertEqual(result.confidence, 0.98)

        mock_client.post.assert_called_once()
        call_args, call_kwargs = mock_client.post.call_args
        self.assertEqual(call_args[0], "https://api.openai.com/v1/chat/completions")
        self.assertIn("Authorization", call_kwargs["headers"])
        self.assertEqual(call_kwargs["headers"]["Authorization"], f"Bearer {self.api_key}")
        self.assertEqual(call_kwargs["json"]["model"], "gpt-4o-mini")

    def test_custom_response_model_support(self):
        mock_payload = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({"title": "Test Title", "count": 42})
                    }
                }
            ]
        }

        mock_http_response = MagicMock(spec=httpx.Response)
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = mock_payload

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_http_response

        provider = OpenAIProvider(api_key=self.api_key, client=mock_client)
        result = provider.generate_structured(
            system_prompt="System prompt",
            user_prompt="User question",
            response_model=CustomTestModel,
        )

        self.assertIsInstance(result, CustomTestModel)
        self.assertEqual(result.title, "Test Title")
        self.assertEqual(result.count, 42)

    def test_authentication_failure_raises_planning_error(self):
        mock_http_response = MagicMock(spec=httpx.Response)
        mock_http_response.status_code = 401
        mock_http_response.text = "Unauthorized: Invalid API key"

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_http_response

        provider = OpenAIProvider(api_key=self.api_key, client=mock_client)
        with self.assertRaises(PlanningError) as ctx:
            provider.generate_structured("sys", "user", LLMPlanOutput)
        self.assertIn("authentication failure", str(ctx.exception).lower())

    def test_api_server_error_raises_planning_error(self):
        mock_http_response = MagicMock(spec=httpx.Response)
        mock_http_response.status_code = 500
        mock_http_response.text = "Internal Server Error"

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_http_response

        provider = OpenAIProvider(api_key=self.api_key, client=mock_client)
        with self.assertRaises(PlanningError) as ctx:
            provider.generate_structured("sys", "user", LLMPlanOutput)
        self.assertIn("API error", str(ctx.exception))

    def test_network_timeout_raises_planning_error(self):
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.side_effect = httpx.TimeoutException("Connection timed out")

        provider = OpenAIProvider(api_key=self.api_key, client=mock_client)
        with self.assertRaises(PlanningError) as ctx:
            provider.generate_structured("sys", "user", LLMPlanOutput)
        self.assertIn("network failure", str(ctx.exception).lower())

    def test_invalid_json_payload_raises_planning_error(self):
        mock_http_response = MagicMock(spec=httpx.Response)
        mock_http_response.status_code = 200
        mock_http_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_http_response

        provider = OpenAIProvider(api_key=self.api_key, client=mock_client)
        with self.assertRaises(PlanningError) as ctx:
            provider.generate_structured("sys", "user", LLMPlanOutput)
        self.assertIn("LLM provider returned malformed JSON response payload", str(ctx.exception))

    def test_pydantic_schema_validation_failure_raises_planning_error(self):
        mock_payload = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({"invalid_field": "unknown_value"})
                    }
                }
            ]
        }

        mock_http_response = MagicMock(spec=httpx.Response)
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = mock_payload

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_http_response

        provider = OpenAIProvider(api_key=self.api_key, client=mock_client)
        with self.assertRaises(PlanningError) as ctx:
            provider.generate_structured("sys", "user", LLMPlanOutput)
        self.assertIn("failed validation against LLMPlanOutput", str(ctx.exception))

    def test_integration_with_llm_query_planner(self):
        mock_payload = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "intent": "BATTER_VS_BOWLER",
                                "arguments": {
                                    "batter": "Virat Kohli",
                                    "bowler": "Jasprit Bumrah",
                                },
                                "confidence": 0.95,
                                "requires_clarification": False,
                                "clarification_message": None,
                            }
                        )
                    }
                }
            ]
        }

        mock_http_response = MagicMock(spec=httpx.Response)
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = mock_payload

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_http_response

        provider = OpenAIProvider(api_key=self.api_key, client=mock_client)
        planner = LLMQueryPlanner(provider=provider)

        plan = planner.plan("How has Virat Kohli performed against Jasprit Bumrah?")

        self.assertEqual(plan.intent, Intent.BATTER_VS_BOWLER)
        self.assertEqual(plan.arguments.batter, "Virat Kohli")
        self.assertEqual(plan.arguments.bowler, "Jasprit Bumrah")
        self.assertEqual(plan.source, "llm")
        self.assertEqual(plan.confidence, 0.95)


if __name__ == "__main__":
    unittest.main()
