"""Live smoke test: ClaudeAgentSdkTransport round-trips a single message
end-to-end against the real Anthropic API. Skipped without an API key.
Marked @pytest.mark.live so the default CI suite (which scrubs API keys)
ignores it.
"""
from __future__ import annotations

import os

import pytest

from agent.transports.claude_agent_sdk import ClaudeAgentSdkTransport


pytestmark = pytest.mark.live


@pytest.fixture(autouse=True)
def _require_anthropic_key():
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_TOKEN")):
        pytest.skip("ANTHROPIC_API_KEY / ANTHROPIC_TOKEN not in env")


def test_live_round_trip_one_word():
    """Send one message; expect a normalized response with text content."""
    import anthropic

    client = anthropic.Anthropic()
    transport = ClaudeAgentSdkTransport()

    messages = [{"role": "user", "content": "Reply with only the word OK."}]
    kwargs = transport.build_kwargs(
        model="claude-haiku-4-5-20251001",
        messages=messages,
        max_tokens=32,
    )

    response = client.messages.create(**kwargs)
    normalized = transport.normalize_response(response)

    assert normalized.content, f"empty content; finish={normalized.finish_reason}, response={response}"
    assert "OK" in normalized.content
    assert normalized.finish_reason == "stop"
    assert normalized.tool_calls is None
