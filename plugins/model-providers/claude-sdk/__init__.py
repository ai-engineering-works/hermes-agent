"""Claude Agent SDK provider profile.

Same wire as native Anthropic — separate api_mode so the new transport
(agent/transports/claude_agent_sdk.py) is selected when users opt in
via ``provider: claude-sdk`` in config.yaml.
"""

from providers import register_provider
from providers.base import ProviderProfile


claude_sdk = ProviderProfile(
    name="claude-sdk",
    aliases=("claude-agent-sdk",),
    api_mode="claude_agent_sdk",
    env_vars=("ANTHROPIC_API_KEY", "ANTHROPIC_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN"),
    base_url="https://api.anthropic.com",
    auth_type="api_key",
    default_aux_model="claude-haiku-4-5-20251001",
)

register_provider(claude_sdk)
