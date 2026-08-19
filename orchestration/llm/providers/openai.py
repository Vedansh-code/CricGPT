"""
OpenAI LLM Provider implementation for CricGPT.

This module implements concrete OpenAI (and OpenAI-compatible) structured output calls
using the provider-agnostic LLMProvider interface.
"""

import json
import os
from typing import Any, Optional, Type, TypeVar, Union, cast
import httpx
from pydantic import BaseModel, ValidationError

from orchestration.exceptions import PlanningError
from orchestration.llm.provider import LLMProvider

T = TypeVar("T", bound=BaseModel)


class OpenAIProvider(LLMProvider):
    """
    Concrete LLM Provider connecting to OpenAI or OpenAI-compatible APIs.

    Supports structured output JSON schema generation and maps API/network/validation
    failures to standard CricGPT PlanningError exceptions.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[Union[float, str]] = None,
        client: Optional[httpx.Client] = None,
    ) -> None:
        """
        Initialize OpenAIProvider.

        Args:
            api_key: OpenAI API key. Defaults to CRICGPT_LLM_API_KEY environment variable.
            model: Model identifier. Defaults to CRICGPT_LLM_MODEL environment variable or 'gpt-4o-mini'.
            base_url: API base URL. Defaults to CRICGPT_LLM_BASE_URL environment variable or 'https://api.openai.com/v1'.
            timeout: Request timeout in seconds. Defaults to CRICGPT_LLM_TIMEOUT environment variable or 30.0.
            client: Optional httpx.Client instance for dependency injection or testing.
        """
        resolved_api_key = api_key or os.environ.get("CRICGPT_LLM_API_KEY")
        if not resolved_api_key:
            raise PlanningError(
                "LLM provider API key is not configured. Please set the CRICGPT_LLM_API_KEY environment variable."
            )

        self.api_key = resolved_api_key
        self.model = model or os.environ.get("CRICGPT_LLM_MODEL", "gpt-4o-mini")
        self.base_url = (base_url or os.environ.get("CRICGPT_LLM_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        
        # Timeout Precedence: explicit timeout > CRICGPT_LLM_TIMEOUT env var > default 30.0 seconds
        if timeout is not None:
            try:
                resolved_timeout = float(timeout)
            except (ValueError, TypeError) as exc:
                raise PlanningError(f"Invalid timeout value '{timeout}'. Must be a valid number.") from exc
        elif "CRICGPT_LLM_TIMEOUT" in os.environ and os.environ["CRICGPT_LLM_TIMEOUT"].strip():
            raw_env_timeout = os.environ["CRICGPT_LLM_TIMEOUT"].strip()
            try:
                resolved_timeout = float(raw_env_timeout)
            except (ValueError, TypeError) as exc:
                raise PlanningError(
                    f"Invalid CRICGPT_LLM_TIMEOUT environment variable value '{raw_env_timeout}'. Must be a valid number."
                ) from exc
        else:
            resolved_timeout = 30.0

        if resolved_timeout <= 0:
            raise PlanningError(f"Timeout must be greater than 0, got {resolved_timeout}.")

        self.timeout = resolved_timeout
        self._client = client

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> T:
        """
        Generate structured output adhering to response_model using OpenAI Chat Completions API.

        Args:
            system_prompt: System context instructions for the LLM.
            user_prompt: User request / question.
            response_model: Expected Pydantic model class for output validation.

        Returns:
            An instance of response_model populated with LLM output.

        Raises:
            PlanningError: If provider configuration, network request, authentication, API,
                           or output validation fails.
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "schema": response_model.model_json_schema(),
                    "strict": True,
                },
            },
        }

        client_created = False
        client = self._client
        if client is None:
            client = httpx.Client(timeout=self.timeout)
            client_created = True

        try:
            try:
                response = client.post(url, headers=headers, json=payload)
            except (httpx.TimeoutException, httpx.NetworkError, httpx.RequestError) as exc:
                raise PlanningError(f"LLM provider network failure: {exc}") from exc
            except Exception as exc:
                raise PlanningError(f"LLM provider request failure: {exc}") from exc

            if response.status_code in (401, 403):
                raise PlanningError(
                    f"LLM provider authentication failure (HTTP {response.status_code}). Please verify your API key."
                )

            if response.status_code != 200:
                raise PlanningError(
                    f"LLM provider API error (HTTP {response.status_code}): {response.text}"
                )

            try:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
            except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
                raise PlanningError(f"LLM provider returned malformed JSON response payload: {exc}") from exc

            try:
                validated_output = response_model.model_validate_json(content)
                return cast(T, validated_output)
            except ValidationError as exc:
                raise PlanningError(f"LLM provider output failed validation against {response_model.__name__}: {exc}") from exc
            except Exception as exc:
                raise PlanningError(f"Failed to parse LLM structured output: {exc}") from exc

        finally:
            if client_created and client is not None:
                client.close()
