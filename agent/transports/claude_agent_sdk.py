"""Claude Agent SDK transport.

Phase 1 scope: behaviorally identical to AnthropicTransport (same wire format,
same response normalization) but registered under a separate api_mode so that
`provider: claude-sdk` in config.yaml routes here. Future phases (predecessor
spec Phase 4) swap the underlying call site to the SDK's headless-mode agent
loop with MCP-server tool registration.

The wire layer in Phase 1 is intentionally unchanged from the AnthropicTransport
because Phase 1's acceptance criterion is round-trip parity (see
specs/2026-05-18-convert-hermes-to-claude-code-sdk.md Phase 1).
"""

from typing import Any, Dict, List, Optional

from agent.transports.anthropic import AnthropicTransport
from agent.transports.base import ProviderTransport
from agent.transports.types import NormalizedResponse


class ClaudeAgentSdkTransport(ProviderTransport):
    """Transport for api_mode='claude_agent_sdk'.

    Phase 1: delegates every method to AnthropicTransport so behavior is
    indistinguishable. The separate api_mode + class identity exists so that
    future phases can change the underlying agent-loop semantics on the
    Anthropic path without disturbing the existing AnthropicTransport callers.
    """

    def __init__(self) -> None:
        self._inner = AnthropicTransport()

    @property
    def api_mode(self) -> str:
        return "claude_agent_sdk"

    def convert_messages(self, messages: List[Dict[str, Any]], **kwargs) -> Any:
        return self._inner.convert_messages(messages, **kwargs)

    def convert_tools(self, tools: List[Dict[str, Any]]) -> Any:
        return self._inner.convert_tools(tools)

    def build_kwargs(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **params,
    ) -> Dict[str, Any]:
        return self._inner.build_kwargs(model, messages, tools, **params)

    def normalize_response(self, response: Any, **kwargs) -> NormalizedResponse:
        return self._inner.normalize_response(response, **kwargs)

    def validate_response(self, response: Any) -> bool:
        return self._inner.validate_response(response)

    def extract_cache_stats(self, response: Any) -> Optional[Dict[str, int]]:
        return self._inner.extract_cache_stats(response)

    def map_finish_reason(self, raw_reason: str) -> str:
        return self._inner.map_finish_reason(raw_reason)


# Auto-register on import (must come AFTER the class is defined)
from agent.transports import register_transport  # noqa: E402

register_transport("claude_agent_sdk", ClaudeAgentSdkTransport)
