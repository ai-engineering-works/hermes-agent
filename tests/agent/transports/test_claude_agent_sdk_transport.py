"""Phase 1 parity tests for ClaudeAgentSdkTransport.

Acceptance criterion (predecessor spec §28): a single message round-trip
through the SDK transport returns identical tool calls + response shape
vs the Anthropic-native transport. We pin this by asserting equivalence
of each ProviderTransport method on a shared input matrix.
"""
from __future__ import annotations

from typing import Any

import pytest

from agent.transports.anthropic import AnthropicTransport
from agent.transports.claude_agent_sdk import ClaudeAgentSdkTransport


@pytest.fixture
def anthropic():
    return AnthropicTransport()


@pytest.fixture
def sdk():
    return ClaudeAgentSdkTransport()


def test_api_mode_differs(anthropic, sdk):
    """The whole point of a second transport is a distinct api_mode."""
    assert anthropic.api_mode == "anthropic_messages"
    assert sdk.api_mode == "claude_agent_sdk"


@pytest.mark.parametrize("messages", [
    [{"role": "user", "content": "hello"}],
    [
        {"role": "system", "content": "You are concise."},
        {"role": "user", "content": "say one word"},
    ],
    [
        {"role": "user", "content": "what is 2+2?"},
        {"role": "assistant", "content": "4"},
        {"role": "user", "content": "what is 3+3?"},
    ],
])
def test_convert_messages_parity(anthropic, sdk, messages):
    assert sdk.convert_messages(messages) == anthropic.convert_messages(messages)


def test_convert_tools_parity_empty(anthropic, sdk):
    assert sdk.convert_tools([]) == anthropic.convert_tools([])


def test_convert_tools_parity_one_tool(anthropic, sdk):
    tools = [{
        "type": "function",
        "function": {
            "name": "echo",
            "description": "echoes a string",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
    }]
    assert sdk.convert_tools(tools) == anthropic.convert_tools(tools)


def test_build_kwargs_parity(anthropic, sdk):
    messages = [{"role": "user", "content": "hi"}]
    a_kw = anthropic.build_kwargs(model="claude-sonnet-4-6", messages=messages)
    s_kw = sdk.build_kwargs(model="claude-sonnet-4-6", messages=messages)
    assert s_kw == a_kw


def test_normalize_response_parity_minimal(anthropic, sdk):
    """A fake Anthropic-shaped response normalizes identically through both."""

    class FakeBlock:
        def __init__(self, type_: str, **kw: Any) -> None:
            self.type = type_
            for k, v in kw.items():
                setattr(self, k, v)

    class FakeResponse:
        content = [FakeBlock("text", text="Hello world.")]
        stop_reason = "end_turn"
        usage = None

    a_norm = anthropic.normalize_response(FakeResponse())
    s_norm = sdk.normalize_response(FakeResponse())
    assert s_norm == a_norm


def test_normalize_response_parity_with_tool_call(anthropic, sdk):
    """A response containing a tool_use block normalizes identically."""

    class FakeBlock:
        def __init__(self, type_: str, **kw: Any) -> None:
            self.type = type_
            for k, v in kw.items():
                setattr(self, k, v)

    class FakeResponse:
        content = [
            FakeBlock("text", text="Let me check."),
            FakeBlock(
                "tool_use",
                id="toolu_01ABC",
                name="echo",
                input={"text": "hi"},
            ),
        ]
        stop_reason = "tool_use"
        usage = None

    a_norm = anthropic.normalize_response(FakeResponse())
    s_norm = sdk.normalize_response(FakeResponse())
    assert s_norm == a_norm


def test_finish_reason_map_parity(anthropic, sdk):
    for raw in ("end_turn", "tool_use", "max_tokens", "stop_sequence", "refusal"):
        assert sdk.map_finish_reason(raw) == anthropic.map_finish_reason(raw)


def test_validate_response_parity(anthropic, sdk):
    class FakeResponse:
        content = []
        stop_reason = "end_turn"

    assert sdk.validate_response(FakeResponse()) == anthropic.validate_response(FakeResponse())
    assert sdk.validate_response(None) == anthropic.validate_response(None)
