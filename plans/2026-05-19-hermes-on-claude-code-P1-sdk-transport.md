# Hermes-on-Claude-Code — Phase 1 (SDK Transport) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Claude-Agent-SDK transport so users can opt into `provider: claude-sdk` and get a behaviorally-parity Anthropic message round-trip through Hermes' existing transport ABC. The work scaffolds the plumbing that later phases (predecessor-spec Phase 4) use to actually swap the agent loop on the Anthropic path.

**Architecture:** New `agent/transports/claude_agent_sdk.py` implements the `ProviderTransport` ABC, delegating wire-format conversion to `agent.anthropic_adapter` (same as `AnthropicTransport`) but registered under a separate `api_mode = "claude_agent_sdk"`. A new provider profile `claude-sdk` selects this transport via `provider: claude-sdk` in `config.yaml`. Phase 1 keeps semantics identical to native Anthropic — its value is the registration plumbing + parity test that future phases will diverge from when the SDK's headless-mode agent loop replaces the in-house loop on the Anthropic path. Multi-provider support is **preserved**: all existing transports (Anthropic native, OpenAI / chat_completions, Bedrock, Codex, etc.) stay unchanged.

**Tech Stack:** Python 3.11, `claude-agent-sdk` (already added as an optional dep in T5 of the P0 plan), `pytest` via `scripts/run_tests.sh`, the existing `ProviderTransport` ABC at `agent/transports/base.py`.

**Spec reference:** `specs/2026-05-18-convert-hermes-to-claude-code-sdk.md` Phase 1 (lines 28–37 of that spec). Companion reverse-engineered spec: `specs/2026-05-17-agent-transports-reverse-engineered.md` (the protocol-layer contract this transport must satisfy).

**Branch:** `feat/claude-code-plugin-p0` (the same branch holds T1–T11 from the now-superseded P0 plan, which map to predecessor-spec Phase 2).

---

## File Structure

**Created:**

| Path | Responsibility |
|---|---|
| `agent/transports/claude_agent_sdk.py` | The new transport. Implements `ProviderTransport`; delegates wire conversions to `agent.anthropic_adapter`; declares `api_mode = "claude_agent_sdk"`. |
| `plugins/model-providers/claude-sdk/__init__.py` | Registers a `ProviderProfile(name="claude-sdk", api_mode="claude_agent_sdk", …)` peer of the existing `anthropic` profile. |
| `plugins/model-providers/claude-sdk/plugin.yaml` | Plugin manifest matching the other model-provider plugins' schema. |
| `tests/agent/transports/test_claude_agent_sdk_transport.py` | Unit-test parity vs `AnthropicTransport` on a shared input matrix. |
| `tests/agent/transports/test_claude_agent_sdk_transport_live.py` | Live round-trip test against the real Anthropic API. Marked `@pytest.mark.live`. |
| `tests/providers/test_claude_sdk_profile.py` | E2E wiring — `provider: claude-sdk` resolves to api_mode `claude_agent_sdk` and to the new transport. |

**Modified:**

| Path | Change |
|---|---|
| `agent/transports/__init__.py` | Add `import agent.transports.claude_agent_sdk` to `_discover_transports()`. |
| `website/docs/user-guide/providers/anthropic.md` (or the providers index) | One-paragraph mention that `provider: claude-sdk` is now available as an alpha alternative path. (Skip if the docs site is not updated as part of this PR — flag as a follow-up.) |

**Not touched:**

- Any existing transport file (`anthropic.py`, `chat_completions.py`, `bedrock.py`, `codex*.py`).
- Any existing provider plugin under `plugins/model-providers/`.
- `run_agent.py`, `model_tools.py`, gateway, CLI, TUI — all untouched.

---

## Tasks

### Task 1 — Skeleton transport that delegates to AnthropicTransport

**Files:**
- Create: `agent/transports/claude_agent_sdk.py`

- [ ] **Step 1: Write the skeleton transport**

Create `agent/transports/claude_agent_sdk.py`:

```python
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
```

- [ ] **Step 2: Smoke-test that the module imports**

```bash
source .venv/bin/activate 2>/dev/null || source venv/bin/activate
python -c "from agent.transports.claude_agent_sdk import ClaudeAgentSdkTransport; t = ClaudeAgentSdkTransport(); print(t.api_mode)"
```

Expected output: `claude_agent_sdk`

- [ ] **Step 3: Commit**

```bash
git add agent/transports/claude_agent_sdk.py
git commit -m "feat(transports): Claude Agent SDK transport skeleton (P1 task 1)"
```

---

### Task 2 — Register in `_discover_transports()`

**Files:**
- Modify: `agent/transports/__init__.py`

- [ ] **Step 1: Add the import**

Edit `agent/transports/__init__.py`. Inside `_discover_transports()`, append a new try/except block matching the existing pattern (the existing blocks import `anthropic`, `codex`, `chat_completions`, `bedrock`):

```python
    try:
        import agent.transports.claude_agent_sdk  # noqa: F401
    except ImportError:
        pass
```

Place it **after** the existing four blocks (order is not load-bearing but consistency helps reviewers).

- [ ] **Step 2: Smoke-test discovery**

```bash
python -c "from agent.transports import get_transport; t = get_transport('claude_agent_sdk'); print(type(t).__name__)"
```

Expected output: `ClaudeAgentSdkTransport`

- [ ] **Step 3: Commit**

```bash
git add agent/transports/__init__.py
git commit -m "feat(transports): register claude_agent_sdk in discovery (P1 task 2)"
```

---

### Task 3 — Parity unit tests

**Files:**
- Create: `tests/agent/transports/test_claude_agent_sdk_transport.py`

- [ ] **Step 1: Write the parity test**

Create `tests/agent/transports/test_claude_agent_sdk_transport.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it passes**

Run: `scripts/run_tests.sh tests/agent/transports/test_claude_agent_sdk_transport.py -v`
Expected: all tests PASS — these are pure delegation parity checks; if any fail, the skeleton in Task 1 has a typo.

- [ ] **Step 3: Commit**

```bash
git add tests/agent/transports/test_claude_agent_sdk_transport.py
git commit -m "test(transports): claude_agent_sdk parity vs anthropic (P1 task 3)"
```

---

### Task 4 — Provider profile `claude-sdk`

**Files:**
- Create: `plugins/model-providers/claude-sdk/__init__.py`
- Create: `plugins/model-providers/claude-sdk/plugin.yaml`

- [ ] **Step 1: Read the existing Anthropic provider plugin for shape**

Read `plugins/model-providers/anthropic/__init__.py` and `plugins/model-providers/anthropic/plugin.yaml`. The new `claude-sdk` profile follows the same shape — only the `name`, `aliases`, and `api_mode` differ.

- [ ] **Step 2: Create `plugins/model-providers/claude-sdk/plugin.yaml`**

Mirror the anthropic plugin.yaml verbatim, then change the values that differ. The exact required fields are visible in the anthropic plugin.yaml — copy that schema. As a minimum, the file should include:

```yaml
name: claude-sdk
kind: model-provider
version: 0.14.0
description: "Anthropic via Claude Agent SDK transport (Phase 1: behavior-parity with native Anthropic; future phases enable SDK-headless-mode agent loop)."
```

If anthropic/plugin.yaml has additional fields (such as `python_module:` or `entry_point:`), reproduce them with the claude-sdk equivalent. Run `cat plugins/model-providers/anthropic/plugin.yaml` first to see the full schema.

- [ ] **Step 3: Create `plugins/model-providers/claude-sdk/__init__.py`**

Mirror the Anthropic provider profile registration:

```python
"""Claude Agent SDK provider profile.

Same wire as native Anthropic — separate api_mode so the new transport
(agent/transports/claude_agent_sdk.py) is selected when users opt in
via `provider: claude-sdk` in config.yaml.
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
```

(If the existing AnthropicProfile in `plugins/model-providers/anthropic/__init__.py` subclasses `ProviderProfile` to override `fetch_models`, you can either subclass the same way for `claude-sdk` or import and reuse the Anthropic subclass — choose whichever keeps duplication minimal. If the latter, replace the `ProviderProfile(...)` call above with an instance of the imported subclass parameterized differently.)

- [ ] **Step 4: Smoke-test discovery**

```bash
python -c "from providers import get_provider_profile; p = get_provider_profile('claude-sdk'); print(p.name, p.api_mode)"
```

Expected output: `claude-sdk claude_agent_sdk`

- [ ] **Step 5: Commit**

```bash
git add plugins/model-providers/claude-sdk/
git commit -m "feat(providers): claude-sdk profile mapping to claude_agent_sdk api_mode (P1 task 4)"
```

---

### Task 5 — E2E wiring test: `provider: claude-sdk` selects the new transport

**Files:**
- Create: `tests/providers/test_claude_sdk_profile.py`

- [ ] **Step 1: Write the wiring test**

Create `tests/providers/test_claude_sdk_profile.py`:

```python
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
```

- [ ] **Step 2: Run the test**

Run: `scripts/run_tests.sh tests/providers/test_claude_sdk_profile.py -v`
Expected: 4 PASS.

If `get_provider_profile("claude-sdk")` returns None, the discovery mechanism in `providers/__init__.py::_discover_providers()` didn't pick up the new directory. Check that the file is placed under `plugins/model-providers/claude-sdk/` exactly (note: hyphen, not underscore) and that the `plugin.yaml` `kind:` field is `model-provider`.

- [ ] **Step 3: Commit**

```bash
git add tests/providers/test_claude_sdk_profile.py
git commit -m "test(providers): e2e wiring for provider:claude-sdk → claude_agent_sdk transport (P1 task 5)"
```

---

### Task 6 — Live smoke test (real Anthropic API call)

**Files:**
- Create: `tests/agent/transports/test_claude_agent_sdk_transport_live.py`

- [ ] **Step 1: Write the live test**

Create `tests/agent/transports/test_claude_agent_sdk_transport_live.py`:

```python
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
```

- [ ] **Step 2: Register the `live` marker if not already registered**

Check `pyproject.toml` `[tool.pytest.ini_options]`. If `markers` is missing or does not include `live`, add it (mirror what the P0 plan introduced in Task 13 — if that change was committed, this step is a no-op; if it was retracted along with the rest of the aggressive variant, add it back):

```toml
[tool.pytest.ini_options]
markers = [
    "live: requires a real API call or live external service",
]
```

If `[tool.pytest.ini_options]` already has a `markers` list with other entries, append to it rather than replace.

- [ ] **Step 3: Run the live test**

```bash
scripts/run_tests.sh tests/agent/transports/test_claude_agent_sdk_transport_live.py -v -m live
```

If `ANTHROPIC_API_KEY` is set: expected PASS.
If unset: expected SKIPPED (not failed).

- [ ] **Step 4: Commit**

```bash
git add tests/agent/transports/test_claude_agent_sdk_transport_live.py pyproject.toml
git commit -m "test(transports): live round-trip smoke for claude_agent_sdk (P1 task 6)"
```

(If `pyproject.toml` wasn't modified — because `live` was already registered — drop it from the `git add` line.)

---

### Task 7 — Full regression + documentation

**Files:**
- Modify: a small documentation paragraph (location depends on what's already in `website/docs/`)

- [ ] **Step 1: Run the full Hermes test suite**

```bash
scripts/run_tests.sh -q
```

Expected: no regressions. The new transport is *additive* — no existing test should be affected. If anything fails, inspect the failure: if it's caused by `_discover_transports()` raising on the new import (e.g., circular import), fix the import order; if it's a flake, retry once.

- [ ] **Step 2: Add a documentation paragraph**

Locate the providers docs (likely `website/docs/user-guide/providers/` or similar — `ls website/docs/user-guide/` to find it). Add a short paragraph either as a new file `claude-sdk.md` or as a section in the providers index:

```markdown
### `claude-sdk` — Alpha

`provider: claude-sdk` routes Anthropic traffic through Hermes' `ClaudeAgentSdkTransport` instead of the native `AnthropicTransport`. As of Phase 1 (released YYYY-MM-DD), the two transports are behaviorally identical — same Anthropic Messages API, same wire format, same response shape. The separate transport exists so that future phases can swap the underlying agent-loop semantics on the Anthropic path (running the Claude Agent SDK's headless agent loop with Hermes' tools registered as MCP servers) without disturbing the native transport. Treat `claude-sdk` as opt-in alpha until that Phase 4 work lands.
```

If the docs site has not yet been touched for this feature and the project's convention is to land docs in a separate PR, skip this step but record it as a follow-up TODO in the PR description for this branch.

- [ ] **Step 3: Commit**

```bash
git add website/docs/...   # whatever path applies
git commit -m "docs(providers): document provider:claude-sdk alpha (P1 task 7)"
```

(If Step 2 was skipped, also skip the commit.)

---

### Task 8 — Final review + branch merge readiness

**Files:**
- None new.

- [ ] **Step 1: Verify the branch state**

```bash
git log --oneline main..HEAD
```

Expected: shows the T1–T11 commits from the predecessor-spec-Phase-2 prep work (`ccc91f8c1`..`404752751`) PLUS the new commits from T1–T7 of this plan. Total commit count: ~18.

- [ ] **Step 2: Final code review via Agent**

Dispatch the `superpowers:code-reviewer` agent over the full diff between `main` and `HEAD`. The agent's checklist should include:

- The `ClaudeAgentSdkTransport` is genuinely a 1:1 delegation in Phase 1 (no behavior drift hidden inside).
- The `claude-sdk` provider profile is registered correctly and discoverable.
- No existing test was modified in a way that would mask a regression.
- The plugin scaffold from T1–T11 + the SDK transport from T1–T7 of THIS plan are internally consistent (the plugin's `.mcp.json` declares the 8 MCP servers; the SDK transport doesn't *use* them yet in Phase 1, but it's the future consumer).

If the reviewer raises issues, dispatch the relevant implementer to fix them. Repeat until the reviewer approves.

- [ ] **Step 3: Hand off to `superpowers:finishing-a-development-branch`**

Once the reviewer approves, invoke the `superpowers:finishing-a-development-branch` skill to manage merge or PR creation. Do not merge to `main` without the user's explicit consent.

---

## Acceptance criteria for P1

- [ ] `agent/transports/claude_agent_sdk.py` exists, implements `ProviderTransport`, registered for `api_mode = "claude_agent_sdk"`.
- [ ] `get_transport("claude_agent_sdk")` returns a `ClaudeAgentSdkTransport` instance.
- [ ] `get_provider_profile("claude-sdk")` returns a profile with `api_mode = "claude_agent_sdk"`.
- [ ] All parity-test assertions in `tests/agent/transports/test_claude_agent_sdk_transport.py` pass.
- [ ] Live round-trip test passes when `ANTHROPIC_API_KEY` is set; skips otherwise.
- [ ] Full Hermes test suite passes (no existing test regressed).
- [ ] No file outside `agent/transports/`, `plugins/model-providers/claude-sdk/`, `tests/`, and optionally `pyproject.toml` + `website/docs/` is modified.

## Non-goals

- **No headless-mode SDK agent loop yet.** Phase 1 keeps semantics identical to native Anthropic. The SDK's `ClaudeSDKClient` / `query` interface is not invoked. That work is the predecessor spec's Phase 4.
- **No MCP server wiring on the SDK path yet.** The plugin scaffold from T1–T11 declares the 8 Hermes MCP servers, but the SDK transport does not pass them to Claude Code in Phase 1. Phase 3 of the predecessor spec wires hooks + MCP servers into the SDK path.
- **No deletion of any existing code.** Multi-provider is preserved. `run_agent.py`, `cli.py`, `ui-tui/`, `acp_adapter/`, every non-Anthropic provider plugin — all stay.
- **No replacement of Anthropic-native transport.** Both transports coexist; users opt into `claude-sdk` explicitly.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| `_discover_transports()` import order changes break loading | The new import is the last try/except in the function; if it raises, only the new transport is missing — others keep working. The test in Task 5 catches this. |
| `ProviderProfile` schema diverges from anthropic's expected shape | Task 4 Step 1 reads the existing anthropic plugin before writing the new one — divergences surface immediately. |
| Providers-registry discovery is lazy and order-dependent | Task 5's wiring test calls `get_provider_profile("claude-sdk")` cold; if discovery is broken, the test fails. |
| Phase 1 looks like "two transports that do the same thing" — reviewer rejects as pointless | The PR description must spell out that Phase 1 is *scaffolding* for Phase 4's behavioral divergence; without Phase 1 done first, Phase 4 cannot land incrementally. |

## What ships when P1 is done

Users can set `provider: claude-sdk` in `~/.hermes/config.yaml` and observe behavior identical to `provider: anthropic`. The opt-in costs nothing and gains nothing in Phase 1 — it exists to prove the plumbing works so Phase 4 can swap behavior without rewriting registration code. Existing users (any provider, including `anthropic`) are completely unaffected; the new transport is dormant unless explicitly selected.
