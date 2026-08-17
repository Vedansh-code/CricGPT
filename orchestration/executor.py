"""
Capability Executor for CricGPT Orchestration (Phase 3A.4).

This module provides the CapabilityExecutor class, which executes a QueryPlan
by resolving its capability through CapabilityRegistry, validating argument contracts,
invoking the corresponding Phase 1 Analytics SDK callable, and returning an ExecutionResult.
"""

import inspect
from typing import Optional, Dict, Any

from orchestration.intents import Intent
from orchestration.schemas import QueryPlan, ExecutionResult
from orchestration.registry import CapabilityRegistry, get_default_registry
from orchestration.exceptions import (
    UnsupportedIntentError,
    ClarificationRequired,
    ExecutionError,
)

# Argument name mappings between QueryArguments fields and SDK parameter names
PARAM_NAME_MAP: Dict[str, str] = {
    "player_name": "name",
    "limit": "n",
    "batter": "batter_name",
    "bowler": "bowler_name",
}


def _map_kwargs_for_handler(handler: Any, raw_args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map QueryArguments fields to SDK handler signature parameters.
    """
    try:
        sig = inspect.signature(handler)
        handler_params = sig.parameters
    except (ValueError, TypeError):
        handler_params = {}

    kwargs: Dict[str, Any] = {}
    for arg_name, arg_val in raw_args.items():
        if arg_val is None:
            continue
        if handler_params:
            if arg_name in handler_params:
                kwargs[arg_name] = arg_val
            elif arg_name in PARAM_NAME_MAP and PARAM_NAME_MAP[arg_name] in handler_params:
                kwargs[PARAM_NAME_MAP[arg_name]] = arg_val
            else:
                kwargs[arg_name] = arg_val
        else:
            if arg_name in PARAM_NAME_MAP:
                kwargs[PARAM_NAME_MAP[arg_name]] = arg_val
            else:
                kwargs[arg_name] = arg_val

    # Default fallback for get_player_last_n_matches if n is required by SDK but limit was not provided
    if handler_params and "n" in handler_params and "n" not in kwargs:
        kwargs["n"] = 5

    return kwargs



class CapabilityExecutor:
    """
    Executor for resolving and invoking CricGPT capabilities.
    """

    def __init__(self, registry: Optional[CapabilityRegistry] = None):
        """
        Initialize CapabilityExecutor.

        Args:
            registry: Optional CapabilityRegistry instance. Defaults to get_default_registry().
        """
        self.registry = registry if registry is not None else get_default_registry()

    def execute(self, plan: QueryPlan) -> ExecutionResult:
        """
        Execute a QueryPlan and return an ExecutionResult.

        Args:
            plan: The QueryPlan to execute.

        Returns:
            ExecutionResult containing execution status, result payload, and metadata.

        Raises:
            ClarificationRequired: If plan requires user clarification.
            UnsupportedIntentError: If intent is UNKNOWN or unregistered.
            ExecutionError: If required arguments are missing or unexpected invocation failure occurs.
        """
        if not isinstance(plan, QueryPlan):
            raise ExecutionError("Invalid QueryPlan input.")

        # 1. Check clarification requirement
        if plan.requires_clarification:
            msg = plan.clarification_message or "Query requires clarification."
            raise ClarificationRequired(msg)

        # 2. Check UNKNOWN intent
        if plan.intent == Intent.UNKNOWN:
            raise UnsupportedIntentError("Cannot execute UNKNOWN intent.")

        # 3. Resolve capability from registry
        capability = self.registry.get(plan.intent)

        # 4. Validate required arguments
        missing_args = []
        for req_arg in capability.required_arguments:
            val = getattr(plan.arguments, req_arg, None)
            if val is None:
                missing_args.append(req_arg)

        if missing_args:
            raise ExecutionError(
                f"Missing required argument(s) {missing_args} for intent '{plan.intent.value}'."
            )

        # 5. Extract only declared arguments (required + optional)
        declared_args = set(capability.required_arguments + capability.optional_arguments)
        raw_kwargs: Dict[str, Any] = {}
        for arg_name in declared_args:
            val = getattr(plan.arguments, arg_name, None)
            if val is not None:
                raw_kwargs[arg_name] = val

        kwargs = _map_kwargs_for_handler(capability.handler, raw_kwargs)

        # 6. Invoke handler and wrap low-level unexpected errors
        try:
            sdk_result = capability.handler(**kwargs)
        except (ClarificationRequired, UnsupportedIntentError, ExecutionError):
            raise
        except Exception as e:
            mod_name = getattr(e.__class__, "__module__", "")
            if "analytics" in mod_name or e.__class__.__name__ in {
                "PlayerNotFoundError", "MatchNotFoundError", "TeamNotFoundError", "VenueNotFoundError"
            }:
                raise
            raise ExecutionError(f"Execution failed for capability '{capability.name}': {str(e)}") from e

        # 7. Return ExecutionResult
        return ExecutionResult(
            success=True,
            intent=plan.intent,
            result=sdk_result,
            metadata={
                "capability": capability.name,
                "source": "analytics_sdk",
            }
        )
