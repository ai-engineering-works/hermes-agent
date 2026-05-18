"""E2E wiring: `provider: claude-sdk` resolves through the registry to the new transport."""
from agent.transports import get_transport
from agent.transports.claude_agent_sdk import ClaudeAgentSdkTransport
from providers import get_provider_profile


def test_provider_profile_exists():
    p = get_provider_profile("claude-sdk")
    assert p is not None
    assert p.name == "claude-sdk"


def test_provider_profile_aliases_resolve():
    """The aliases declared in __init__.py should also resolve."""
    p = get_provider_profile("claude-agent-sdk")
    assert p is not None
    assert p.name == "claude-sdk"


def test_profile_api_mode_matches_transport():
    p = get_provider_profile("claude-sdk")
    transport = get_transport(p.api_mode)
    assert isinstance(transport, ClaudeAgentSdkTransport)


def test_does_not_collide_with_anthropic_profile():
    anth = get_provider_profile("anthropic")
    sdk = get_provider_profile("claude-sdk")
    assert anth.api_mode != sdk.api_mode
    # Native anthropic profile keeps its existing api_mode unchanged
    assert anth.api_mode == "anthropic_messages"
