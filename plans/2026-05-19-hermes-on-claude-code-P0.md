# Hermes-on-Claude-Code — Phase 0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the Hermes Claude Code plugin scaffold and verify the four assumptions Q3/Q4/Q5/Q7 of the spec rest on, so P1–P6 can proceed without rework.

**Architecture:** Create `plugins/hermes/` in the repo as a Claude Code plugin directory (plugin.json + .mcp.json + settings.json + skills + commands + agents + hooks + MCP server stubs). The in-process `AIAgent` remains the default runtime; nothing in the existing CLI / gateway / cron / kanban paths changes behaviorally. P0 ships only an *additive*, behavior-neutral plugin scaffold plus four assumption-verification scripts that gate P1.

**Tech Stack:** Python 3.11, `claude-agent-sdk` (Python) for MCP server skeletons, `pytest` via `scripts/run_tests.sh`, Claude Code CLI v2.1.143 (pinned for P0; bumped deliberately later).

**Spec reference:** `specs/2026-05-19-hermes-on-claude-code-design.md` §2.1, §2.2, §6 P0, §7 Q3/Q4/Q5/Q7.

---

## File Structure (what gets created or modified)

**Created:**

| Path | Responsibility |
|---|---|
| `plugins/hermes/plugin.json` | Plugin manifest: name, version, description, declared subagents, command-set, MCP-server names. |
| `plugins/hermes/.mcp.json` | Registers the 8 Hermes MCP servers (stubs in P0). |
| `plugins/hermes/settings.json` | Default permission allowlist and hook registration map (stubs in P0). |
| `plugins/hermes/README.md` | "This is the Hermes Claude Code plugin. P0 scaffolding only — see specs/2026-05-19-hermes-on-claude-code-design.md." |
| `plugins/hermes/CLAUDE_CODE_VERSION` | Pinned upstream version string (`2.1.143`). |
| `plugins/hermes/skills/` (directory) | Symlink target → repo's existing `skills/` (no copy — single source of truth during P0). |
| `plugins/hermes/commands/<verb>.md` × N | One file per Hermes slash command, generated from the canonical `hermes_cli/commands.py` registry. |
| `plugins/hermes/agents/orchestrator.md`, `agents/leaf.md` | Subagent type definitions matching today's `delegate_task` roles. |
| `plugins/hermes/mcp/{memory,terminal,recall,browser,aux,cron,kanban,curator}/server.py` × 8 | Each is a 30-line MCP-server stub that exposes one tool returning `{"status": "not_implemented", "phase": "P0"}`. |
| `plugins/hermes/mcp/__init__.py`, per-server `__init__.py` | Package markers. |
| `plugins/hermes/hooks/tirith_approval.py`, `osv_check.py`, `env_scrub.py`, `url_safety.py`, `skills_guard.py`, `subagent_depth.py`, `subagent_concurrency.py`, `redact.py`, `bootstrap.py`, `telemetry.py`, `session_index.py` × 11 | Each is a 20-line hook stub that reads its event from stdin and prints `{"decision": "allow"}` to stdout (or no-op for non-PreToolUse hooks). Real logic lands in P2. |
| `plugins/hermes/hooks/README.md` | Documents hook composition order. |
| `scripts/hermes_launcher.sh` | `exec claude --plugin-dir "$REPO/plugins/hermes" "$@"` (executable). |
| `scripts/verify_p0/q3_stop_hook_payload.py` | Runs a short Claude Code session with a Stop hook that dumps stdin; asserts transcript is present. |
| `scripts/verify_p0/q4_settings_override.py` | Spawns Claude Code with `--settings <tmpfile>` containing a recognizable value; asserts the value appears in the session's effective settings (probed via a side-channel MCP tool or hook). |
| `scripts/verify_p0/q5_task_child_env.py` | Spawns a Claude Code session that calls Task; asserts `HERMES_SUBAGENT_DEPTH` set on the parent appears in the child subagent's env (probed via a hook in the child). |
| `scripts/verify_p0/q7_socket_longpoll.py` | Registers a hook that blocks on a Unix-socket read for 60 seconds; asserts the hook is not killed by Claude Code's hook timeout and the agent loop continues normally after. |
| `scripts/verify_p0/run_all.py` | Driver that runs all four verifications, prints PASS/FAIL summary, exits non-zero if any fail. |
| `tests/plugin/test_plugin_smoke.py` | Spawns `claude --plugin-dir plugins/hermes --print "list your subagents" --output-format json` and asserts orchestrator + leaf appear. |
| `tests/plugin/test_plugin_manifest.py` | Static checks on `plugin.json`, `.mcp.json`, `settings.json` (valid JSON, required fields present, no unknown fields). |
| `tests/plugin/test_command_export.py` | Walks `plugins/hermes/commands/*.md` and asserts each canonical command in `hermes_cli/commands.py` has a corresponding file with correct frontmatter. |
| `tests/plugin/test_mcp_stubs.py` | Imports each of the 8 stub MCP servers and asserts they expose the placeholder tool with correct shape. |
| `tests/plugin/test_hook_stubs.py` | Invokes each hook stub with synthetic stdin and asserts default-allow behavior. |
| `tests/scripts/test_hermes_launcher.py` | Smoke-tests `scripts/hermes_launcher.sh --print "echo OK"` returns success. |

**Modified (minimal):**

| Path | Change |
|---|---|
| `pyproject.toml` | Add `claude-agent-sdk` to optional `[claude-code]` extra. No change to base install. |
| `MANIFEST.in` | Add `recursive-include plugins/hermes *` so packaging picks up the plugin tree. |
| `.gitignore` | Add `plugins/hermes/.runtime/` (per-session scratch). |
| `scripts/run_tests.sh` | No change. New tests live under `tests/plugin/` and `tests/scripts/` and are picked up by the default glob. |

**Not touched in P0:**

- `run_agent.py`, `model_tools.py`, `cli.py`, `gateway/`, `cron/`, `tools/`, all of `agent/` (except a single `tools/registry.py` schema-export helper added in Task 12 — additive only).

---

## Tasks

### Task 1 — Pin Claude Code version and create plugin directory skeleton

**Files:**
- Create: `plugins/hermes/CLAUDE_CODE_VERSION`
- Create: `plugins/hermes/README.md`
- Create: `plugins/hermes/.gitignore`
- Modify: `.gitignore` (top-level)

- [ ] **Step 1: Verify Claude Code version on dev machine**

Run: `claude --version`
Expected: `2.1.143 (Claude Code)` (any 2.1.x is acceptable; record the exact version observed).

- [ ] **Step 2: Create the plugin root and pin file**

```bash
mkdir -p plugins/hermes
echo "2.1.143" > plugins/hermes/CLAUDE_CODE_VERSION
```

- [ ] **Step 3: Create the README**

Create `plugins/hermes/README.md`:

```markdown
# Hermes — Claude Code plugin

Phase 0 scaffolding for the Hermes-on-Claude-Code port.

See `specs/2026-05-19-hermes-on-claude-code-design.md` for the design
and `plans/2026-05-19-hermes-on-claude-code-P0.md` for the current
implementation plan.

**Status:** P0 scaffolding only. The in-process AIAgent remains the default
runtime; this plugin directory is not loaded by `hermes` interactive or
`hermes gateway` until P3.

**Pinned upstream:** Claude Code `2.1.143` (see `CLAUDE_CODE_VERSION`).
```

- [ ] **Step 4: Create the per-plugin gitignore**

Create `plugins/hermes/.gitignore`:

```
.runtime/
*.completion.json
```

- [ ] **Step 5: Add the runtime exclusion to top-level .gitignore**

Append to `.gitignore`:

```
# Hermes plugin per-session scratch
plugins/hermes/.runtime/
```

- [ ] **Step 6: Commit**

```bash
git add plugins/hermes/CLAUDE_CODE_VERSION plugins/hermes/README.md plugins/hermes/.gitignore .gitignore
git commit -m "feat(plugin): scaffold Hermes Claude Code plugin directory (P0 task 1)"
```

---

### Task 2 — Manifest and static-validation test

**Files:**
- Create: `plugins/hermes/plugin.json`
- Create: `tests/plugin/__init__.py`
- Create: `tests/plugin/test_plugin_manifest.py`

- [ ] **Step 1: Write the failing test**

Create `tests/plugin/__init__.py` (empty file).

Create `tests/plugin/test_plugin_manifest.py`:

```python
"""Static validation of plugins/hermes/plugin.json — runs without spawning claude."""
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_DIR = REPO_ROOT / "plugins" / "hermes"
MANIFEST = PLUGIN_DIR / "plugin.json"


def _load_manifest() -> dict:
    return json.loads(MANIFEST.read_text())


def test_manifest_exists():
    assert MANIFEST.exists(), f"missing {MANIFEST}"


def test_manifest_is_valid_json():
    _load_manifest()  # raises on invalid JSON


def test_manifest_has_required_top_level_fields():
    m = _load_manifest()
    for key in ("name", "version", "description", "author", "license"):
        assert key in m, f"plugin.json missing '{key}'"


def test_manifest_name_is_hermes():
    assert _load_manifest()["name"] == "hermes"


def test_manifest_version_matches_pyproject():
    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    # crude single-line match — pyproject keeps "version = "0.14.0"" on one line
    for line in pyproject.splitlines():
        stripped = line.strip()
        if stripped.startswith("version") and "=" in stripped:
            py_ver = stripped.split("=", 1)[1].strip().strip('"').strip("'")
            break
    else:
        pytest.fail("could not find version in pyproject.toml")
    assert _load_manifest()["version"] == py_ver


def test_manifest_declares_mcp_servers_array():
    m = _load_manifest()
    assert isinstance(m.get("mcpServers"), list)
    assert set(m["mcpServers"]) == {
        "hermes-memory", "hermes-terminal", "hermes-recall", "hermes-browser",
        "hermes-aux", "hermes-cron", "hermes-kanban", "hermes-curator",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `scripts/run_tests.sh tests/plugin/test_plugin_manifest.py -v`
Expected: FAIL with "missing .../plugin.json" on `test_manifest_exists`.

- [ ] **Step 3: Write the manifest**

Create `plugins/hermes/plugin.json`:

```json
{
  "name": "hermes",
  "version": "0.14.0",
  "description": "Hermes Agent surfaces (gateway, memory providers, remote terminals, cron, kanban, curator, browser, auxiliary side-LLM) as a Claude Code plugin.",
  "author": "Nous Research",
  "license": "MIT",
  "homepage": "https://hermes-agent.nousresearch.com",
  "mcpServers": [
    "hermes-memory",
    "hermes-terminal",
    "hermes-recall",
    "hermes-browser",
    "hermes-aux",
    "hermes-cron",
    "hermes-kanban",
    "hermes-curator"
  ],
  "_hermes_phase": "P0-scaffold"
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `scripts/run_tests.sh tests/plugin/test_plugin_manifest.py -v`
Expected: 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/hermes/plugin.json tests/plugin/__init__.py tests/plugin/test_plugin_manifest.py
git commit -m "feat(plugin): plugin.json manifest with declared MCP servers (P0 task 2)"
```

---

### Task 3 — MCP server registration file and its test

**Files:**
- Create: `plugins/hermes/.mcp.json`
- Modify: `tests/plugin/test_plugin_manifest.py` (add `.mcp.json` checks)

- [ ] **Step 1: Extend the failing test**

Append to `tests/plugin/test_plugin_manifest.py`:

```python
MCP_REG = PLUGIN_DIR / ".mcp.json"


def _load_mcp() -> dict:
    return json.loads(MCP_REG.read_text())


def test_mcp_reg_exists():
    assert MCP_REG.exists(), f"missing {MCP_REG}"


def test_mcp_reg_is_valid_json():
    _load_mcp()


def test_mcp_reg_has_all_eight_servers():
    reg = _load_mcp()["mcpServers"]
    expected = {
        "hermes-memory", "hermes-terminal", "hermes-recall", "hermes-browser",
        "hermes-aux", "hermes-cron", "hermes-kanban", "hermes-curator",
    }
    assert set(reg.keys()) == expected


def test_mcp_reg_each_server_has_command_or_url():
    reg = _load_mcp()["mcpServers"]
    for name, cfg in reg.items():
        assert "command" in cfg or "url" in cfg, f"{name} has neither command nor url"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `scripts/run_tests.sh tests/plugin/test_plugin_manifest.py -v`
Expected: FAIL on `test_mcp_reg_exists`.

- [ ] **Step 3: Write the .mcp.json**

Create `plugins/hermes/.mcp.json`:

```json
{
  "mcpServers": {
    "hermes-memory":   {"command": "python", "args": ["-m", "plugins.hermes.mcp.memory.server"]},
    "hermes-terminal": {"command": "python", "args": ["-m", "plugins.hermes.mcp.terminal.server"]},
    "hermes-recall":   {"command": "python", "args": ["-m", "plugins.hermes.mcp.recall.server"]},
    "hermes-browser":  {"command": "python", "args": ["-m", "plugins.hermes.mcp.browser.server"]},
    "hermes-aux":      {"command": "python", "args": ["-m", "plugins.hermes.mcp.aux.server"]},
    "hermes-cron":     {"command": "python", "args": ["-m", "plugins.hermes.mcp.cron.server"]},
    "hermes-kanban":   {"command": "python", "args": ["-m", "plugins.hermes.mcp.kanban.server"]},
    "hermes-curator":  {"command": "python", "args": ["-m", "plugins.hermes.mcp.curator.server"]}
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `scripts/run_tests.sh tests/plugin/test_plugin_manifest.py -v`
Expected: 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/hermes/.mcp.json tests/plugin/test_plugin_manifest.py
git commit -m "feat(plugin): register eight Hermes MCP servers in .mcp.json (P0 task 3)"
```

---

### Task 4 — Settings.json scaffold (hook registrations only — bodies stubbed in later tasks)

**Files:**
- Create: `plugins/hermes/settings.json`
- Modify: `tests/plugin/test_plugin_manifest.py` (add settings checks)

- [ ] **Step 1: Extend the failing test**

Append to `tests/plugin/test_plugin_manifest.py`:

```python
SETTINGS = PLUGIN_DIR / "settings.json"


def _load_settings() -> dict:
    return json.loads(SETTINGS.read_text())


def test_settings_exists():
    assert SETTINGS.exists()


def test_settings_registers_eleven_hooks():
    s = _load_settings()
    hook_paths = []
    for event_hooks in s.get("hooks", {}).values():
        for matcher_block in event_hooks:
            for h in matcher_block.get("hooks", []):
                hook_paths.append(h["command"])
    expected_scripts = {
        "tirith_approval.py", "osv_check.py", "env_scrub.py", "url_safety.py",
        "skills_guard.py", "subagent_depth.py", "subagent_concurrency.py",
        "redact.py", "bootstrap.py", "telemetry.py", "session_index.py",
    }
    seen = {Path(p).name for p in hook_paths}
    assert seen == expected_scripts, f"hook set mismatch: {seen ^ expected_scripts}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `scripts/run_tests.sh tests/plugin/test_plugin_manifest.py -v`
Expected: FAIL on `test_settings_exists`.

- [ ] **Step 3: Write the settings**

Create `plugins/hermes/settings.json`:

```json
{
  "_hermes_generated_at": null,
  "hooks": {
    "PreToolUse": [
      {"matcher": "Bash",     "hooks": [
        {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/tirith_approval.py"},
        {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/osv_check.py"},
        {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/env_scrub.py"}
      ]},
      {"matcher": "WebFetch", "hooks": [
        {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/url_safety.py"}
      ]},
      {"matcher": "Write",    "hooks": [
        {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/skills_guard.py"}
      ]},
      {"matcher": "Edit",     "hooks": [
        {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/skills_guard.py"}
      ]},
      {"matcher": "Task",     "hooks": [
        {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/subagent_depth.py"},
        {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/subagent_concurrency.py"}
      ]}
    ],
    "UserPromptSubmit": [
      {"hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/redact.py"}]}
    ],
    "SessionStart": [
      {"hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/bootstrap.py"}]}
    ],
    "PostToolUse": [
      {"hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/telemetry.py"}]}
    ],
    "Stop": [
      {"hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session_index.py"}]}
    ]
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `scripts/run_tests.sh tests/plugin/test_plugin_manifest.py -v`
Expected: 11 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/hermes/settings.json tests/plugin/test_plugin_manifest.py
git commit -m "feat(plugin): register 11 hooks across 8 Claude Code events (P0 task 4)"
```

---

### Task 5 — MCP server stub: `hermes-memory` (template for the other seven)

**Files:**
- Create: `plugins/hermes/mcp/__init__.py`
- Create: `plugins/hermes/mcp/memory/__init__.py`
- Create: `plugins/hermes/mcp/memory/server.py`
- Create: `tests/plugin/test_mcp_stubs.py`
- Modify: `pyproject.toml` (add `claude-agent-sdk` to a new `[project.optional-dependencies] claude-code` extra)

- [ ] **Step 1: Add the SDK to the optional extra**

Edit `pyproject.toml`, in the `[project.optional-dependencies]` section, add:

```toml
claude-code = [
    "claude-agent-sdk>=0.1,<1",
]
```

(If a section with that exact name does not exist, add it at the bottom of `[project.optional-dependencies]`.)

- [ ] **Step 2: Install the extra locally**

Activate the venv per `AGENTS.md` (`.venv` preferred, `venv` fallback), then install:

```bash
source .venv/bin/activate 2>/dev/null || source venv/bin/activate
pip install -e ".[claude-code]"
```

Expected: installs `claude-agent-sdk` and prints `Successfully installed claude-agent-sdk-X.Y.Z` (or similar).

- [ ] **Step 3: Write the failing test**

Create `tests/plugin/test_mcp_stubs.py`:

```python
"""Each of the eight MCP server stubs exposes one placeholder tool."""
import importlib
import pytest

SERVERS = [
    "memory", "terminal", "recall", "browser", "aux", "cron", "kanban", "curator",
]


@pytest.mark.parametrize("name", SERVERS)
def test_stub_server_importable(name):
    mod = importlib.import_module(f"plugins.hermes.mcp.{name}.server")
    assert hasattr(mod, "server"), f"{name}/server.py must expose `server`"
    assert hasattr(mod, "main"),   f"{name}/server.py must expose `main()`"


@pytest.mark.parametrize("name", SERVERS)
def test_stub_server_has_placeholder_tool(name):
    mod = importlib.import_module(f"plugins.hermes.mcp.{name}.server")
    # claude-agent-sdk exposes registered tools on .tools or similar — adapt to the SDK
    # surface; tolerated either way as long as one tool is registered.
    tools = getattr(mod.server, "tools", None) or getattr(mod.server, "_tools", None)
    assert tools, f"{name}/server.py registered no tools"
    names = [t.name if hasattr(t, "name") else t["name"] for t in tools]
    assert any(n.startswith(f"{name}_") for n in names), f"{name}: no {name}_*_status tool found"
```

- [ ] **Step 4: Run test to verify it fails**

Run: `scripts/run_tests.sh tests/plugin/test_mcp_stubs.py -v`
Expected: FAIL with ModuleNotFoundError for `plugins.hermes.mcp.memory.server` (all 8 parametrized cases fail).

- [ ] **Step 5: Write the package markers and the memory stub**

Create `plugins/hermes/mcp/__init__.py` (empty).
Create `plugins/hermes/mcp/memory/__init__.py` (empty).
Create `plugins/hermes/mcp/memory/server.py`:

```python
"""hermes-memory MCP server — P0 stub.

Real implementation lands in P1. This stub exists so the .mcp.json
registration is exercisable end-to-end during P0 plugin-smoke tests.
"""
from claude_agent_sdk import create_sdk_mcp_server, tool


@tool("memory_status", "Return the current Hermes memory subsystem status.", {})
async def memory_status(args: dict) -> dict:
    return {
        "content": [{
            "type": "text",
            "text": '{"status": "not_implemented", "phase": "P0", "server": "hermes-memory"}',
        }],
    }


server = create_sdk_mcp_server(
    name="hermes-memory",
    version="0.0.0",
    tools=[memory_status],
)


def main() -> None:
    import asyncio
    asyncio.run(server.run_stdio())


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run the parametrized test focused on memory**

Run: `scripts/run_tests.sh "tests/plugin/test_mcp_stubs.py::test_stub_server_importable[memory]" -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml plugins/hermes/mcp/__init__.py plugins/hermes/mcp/memory/__init__.py plugins/hermes/mcp/memory/server.py tests/plugin/test_mcp_stubs.py
git commit -m "feat(plugin): hermes-memory MCP server stub + parametrized stub test (P0 task 5)"
```

---

### Task 6 — Replicate the stub for the remaining seven MCP servers

**Files:**
- Create: `plugins/hermes/mcp/<name>/__init__.py` × 7
- Create: `plugins/hermes/mcp/<name>/server.py` × 7

The 7 names are: `terminal`, `recall`, `browser`, `aux`, `cron`, `kanban`, `curator`.

- [ ] **Step 1: For each name in [terminal, recall, browser, aux, cron, kanban, curator], create the package marker and server file**

For each `<name>`, create:

`plugins/hermes/mcp/<name>/__init__.py` (empty).

`plugins/hermes/mcp/<name>/server.py`:

```python
"""hermes-<name> MCP server — P0 stub.

Real implementation lands in P1.
"""
from claude_agent_sdk import create_sdk_mcp_server, tool


@tool("<name>_status", "Return the current Hermes <name> subsystem status.", {})
async def status_tool(args: dict) -> dict:
    return {
        "content": [{
            "type": "text",
            "text": '{"status": "not_implemented", "phase": "P0", "server": "hermes-<name>"}',
        }],
    }


server = create_sdk_mcp_server(
    name="hermes-<name>",
    version="0.0.0",
    tools=[status_tool],
)


def main() -> None:
    import asyncio
    asyncio.run(server.run_stdio())


if __name__ == "__main__":
    main()
```

Replace `<name>` with the actual name in each file. The function-name `status_tool` is identical across the seven files — that's fine, each lives in its own module.

- [ ] **Step 2: Run the parametrized stub test across all 8**

Run: `scripts/run_tests.sh tests/plugin/test_mcp_stubs.py -v`
Expected: 16 tests PASS (8 names × 2 test functions).

- [ ] **Step 3: Commit**

```bash
git add plugins/hermes/mcp/terminal plugins/hermes/mcp/recall plugins/hermes/mcp/browser plugins/hermes/mcp/aux plugins/hermes/mcp/cron plugins/hermes/mcp/kanban plugins/hermes/mcp/curator
git commit -m "feat(plugin): stub the remaining 7 MCP servers (P0 task 6)"
```

---

### Task 7 — Hook stub template: `redact.py` (UserPromptSubmit)

**Files:**
- Create: `plugins/hermes/hooks/redact.py` (executable)
- Create: `tests/plugin/test_hook_stubs.py`

- [ ] **Step 1: Write the failing test**

Create `tests/plugin/test_hook_stubs.py`:

```python
"""Each hook stub reads JSON from stdin, writes a default-allow response to stdout, exits 0."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / "plugins" / "hermes" / "hooks"

HOOK_SCRIPTS = [
    "tirith_approval.py", "osv_check.py", "env_scrub.py", "url_safety.py",
    "skills_guard.py", "subagent_depth.py", "subagent_concurrency.py",
    "redact.py", "bootstrap.py", "telemetry.py", "session_index.py",
]


@pytest.mark.parametrize("script", HOOK_SCRIPTS)
def test_hook_stub_exists_and_executable(script):
    p = HOOKS_DIR / script
    assert p.exists(), f"missing {p}"
    assert os.access(p, os.X_OK), f"{p} not executable"


@pytest.mark.parametrize("script", HOOK_SCRIPTS)
def test_hook_stub_default_allow(script):
    p = HOOKS_DIR / script
    # synthetic PreToolUse payload — the stubs ignore the body
    payload = json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "echo hi"}})
    proc = subprocess.run(
        [sys.executable, str(p)], input=payload, capture_output=True, text=True, timeout=5,
    )
    assert proc.returncode == 0, f"{script} exited {proc.returncode}: stderr={proc.stderr}"
    # The hook is allowed to print nothing (default-allow) or to print a JSON object.
    if proc.stdout.strip():
        body = json.loads(proc.stdout)
        # default-allow is either no decision field or "allow"
        assert body.get("decision", "allow") in ("allow", None)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `scripts/run_tests.sh tests/plugin/test_hook_stubs.py -v`
Expected: FAIL — `missing .../plugins/hermes/hooks/redact.py` for all 11 parametrized cases.

- [ ] **Step 3: Write the redact hook stub**

Create `plugins/hermes/hooks/redact.py`:

```python
#!/usr/bin/env python3
"""redact.py — UserPromptSubmit hook stub.

P0: no-op. Real implementation lands in P2 (wraps agent/redact.py
and scrubs secrets / PII from user prompts before they reach the model).
"""
import sys


def main() -> int:
    # Drain stdin so Claude Code does not see a broken-pipe
    sys.stdin.read()
    # Default-allow: print nothing.
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Make it executable:

```bash
chmod +x plugins/hermes/hooks/redact.py
```

- [ ] **Step 4: Run the parametrized test focused on redact**

Run: `scripts/run_tests.sh "tests/plugin/test_hook_stubs.py::test_hook_stub_exists_and_executable[redact.py]" "tests/plugin/test_hook_stubs.py::test_hook_stub_default_allow[redact.py]" -v`
Expected: 2 PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/hermes/hooks/redact.py tests/plugin/test_hook_stubs.py
git commit -m "feat(plugin): redact UserPromptSubmit hook stub + parametrized hook test (P0 task 7)"
```

---

### Task 8 — Replicate the stub for the remaining 10 hooks

**Files:**
- Create: `plugins/hermes/hooks/<name>.py` × 10 (executable)

The 10 names are: `tirith_approval`, `osv_check`, `env_scrub`, `url_safety`, `skills_guard`, `subagent_depth`, `subagent_concurrency`, `bootstrap`, `telemetry`, `session_index`.

- [ ] **Step 1: For each name, create the script**

For each `<name>`, create `plugins/hermes/hooks/<name>.py`:

```python
#!/usr/bin/env python3
"""<name>.py — P0 stub.

Real implementation lands in P2. See specs/2026-05-19-hermes-on-claude-code-design.md §2.2
for the responsibility this hook will own.
"""
import sys


def main() -> int:
    sys.stdin.read()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Replace `<name>` with the actual filename root in the docstring.

After creating all 10, make them executable:

```bash
chmod +x plugins/hermes/hooks/tirith_approval.py \
         plugins/hermes/hooks/osv_check.py \
         plugins/hermes/hooks/env_scrub.py \
         plugins/hermes/hooks/url_safety.py \
         plugins/hermes/hooks/skills_guard.py \
         plugins/hermes/hooks/subagent_depth.py \
         plugins/hermes/hooks/subagent_concurrency.py \
         plugins/hermes/hooks/bootstrap.py \
         plugins/hermes/hooks/telemetry.py \
         plugins/hermes/hooks/session_index.py
```

- [ ] **Step 2: Run the parametrized hook test in full**

Run: `scripts/run_tests.sh tests/plugin/test_hook_stubs.py -v`
Expected: 22 tests PASS (11 hooks × 2 test functions).

- [ ] **Step 3: Commit**

```bash
git add plugins/hermes/hooks/
git commit -m "feat(plugin): stub the remaining 10 hooks (P0 task 8)"
```

---

### Task 9 — Hook composition documentation

**Files:**
- Create: `plugins/hermes/hooks/README.md`

- [ ] **Step 1: Write the documentation**

Create `plugins/hermes/hooks/README.md`:

```markdown
# Hermes hooks — composition order

This document is the authoritative composition order for Hermes' Claude Code hooks.
The Hermes invariant is **every PreToolUse hook must allow** — a single `deny`
short-circuits the chain. No hook can override another hook's `deny`.

## PreToolUse — Bash

Order (top to bottom; first to fire is at top):

1. `tirith_approval.py` — Tirith content scan + dangerous-pattern matcher + interactive approval flow.
2. `osv_check.py` — npx / uvx malware check.
3. `env_scrub.py` — strip provider tokens from the child env (ANTHROPIC_TOKEN, OPENAI_API_KEY, ...).

## PreToolUse — WebFetch

1. `url_safety.py` — SSRF guard + website-policy.

## PreToolUse — Write, Edit

1. `skills_guard.py` — scan skill content before write.

## PreToolUse — Task

1. `subagent_depth.py` — enforce `delegation.max_spawn_depth`.
2. `subagent_concurrency.py` — enforce `delegation.max_concurrent_children`.

## UserPromptSubmit

1. `redact.py` — secrets / PII scrubbing.

## SessionStart

1. `bootstrap.py` — regenerate `$HERMES_HOME/.claude/settings.json`; load personality + memory snapshot; run `tools/lazy_deps.py`; read pending `$HERMES_HOME/run/background_procs/*.completion.json` and append to system prompt.

## PostToolUse

1. `telemetry.py` — write per-turn cost / tokens / latency to insights SQLite + incremental turn-row to `recall.db`.

## Stop

1. `session_index.py` — write full transcript snapshot to `recall.db` (post-compact state).

## Phase status

P0: All hooks are no-op stubs (default-allow). Real bodies land in P2.
```

- [ ] **Step 2: Commit**

```bash
git add plugins/hermes/hooks/README.md
git commit -m "docs(plugin): document hook composition order (P0 task 9)"
```

---

### Task 10 — Subagent type definitions (orchestrator + leaf)

**Files:**
- Create: `plugins/hermes/agents/orchestrator.md`
- Create: `plugins/hermes/agents/leaf.md`
- Modify: `tests/plugin/test_plugin_manifest.py` (add agent-presence checks)

- [ ] **Step 1: Extend the failing test**

Append to `tests/plugin/test_plugin_manifest.py`:

```python
AGENTS_DIR = PLUGIN_DIR / "agents"


def test_agents_dir_has_orchestrator_and_leaf():
    assert (AGENTS_DIR / "orchestrator.md").exists()
    assert (AGENTS_DIR / "leaf.md").exists()


@pytest.mark.parametrize("name", ["orchestrator", "leaf"])
def test_agent_has_frontmatter(name):
    text = (AGENTS_DIR / f"{name}.md").read_text()
    assert text.startswith("---\n"), f"{name}.md missing YAML frontmatter"
    fm_end = text.index("---\n", 4)
    fm = text[4:fm_end]
    assert "name:" in fm
    assert "description:" in fm
```

- [ ] **Step 2: Run test to verify it fails**

Run: `scripts/run_tests.sh "tests/plugin/test_plugin_manifest.py::test_agents_dir_has_orchestrator_and_leaf" -v`
Expected: FAIL.

- [ ] **Step 3: Write the two agent files**

Create `plugins/hermes/agents/orchestrator.md`:

```markdown
---
name: orchestrator
description: Long-horizon planner that decomposes work into leaf subagents and aggregates their results. Use for multi-step tasks that benefit from parallel delegation.
tools: ["*"]
---

You are an orchestrator subagent. Decompose the parent task into independent sub-tasks
and delegate each to a leaf subagent via the Task tool. Aggregate their summaries; do
not duplicate work the leaves can do.

Constraints:
- Maximum spawn depth is enforced by the `subagent_depth` PreToolUse hook.
- Maximum concurrent children is enforced by the `subagent_concurrency` PreToolUse hook.
- Never call `delegate_task` (deprecated — use the Task tool instead).
```

Create `plugins/hermes/agents/leaf.md`:

```markdown
---
name: leaf
description: Focused worker that completes a single bounded task and returns a summary. Cannot delegate further.
tools: ["Read", "Edit", "Write", "Grep", "Glob", "Bash", "WebFetch", "WebSearch"]
---

You are a leaf subagent. Complete the single task in your prompt and return a concise
summary. Do not spawn additional subagents.

Constraints:
- The Task tool is unavailable to you (enforced by `subagent_depth` PreToolUse hook).
- Memory, clarify, and send_message are off-limits in leaf role.
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `scripts/run_tests.sh tests/plugin/test_plugin_manifest.py -v`
Expected: all previous tests still PASS plus 3 new tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/hermes/agents/orchestrator.md plugins/hermes/agents/leaf.md tests/plugin/test_plugin_manifest.py
git commit -m "feat(plugin): orchestrator + leaf subagent type definitions (P0 task 10)"
```

---

### Task 11 — Skills symlink (use the repo's existing `skills/` as the single source of truth during P0)

**Files:**
- Create: `plugins/hermes/skills` (symlink → `../../skills`)
- Modify: `tests/plugin/test_plugin_manifest.py` (add symlink check)

- [ ] **Step 1: Extend the failing test**

Append to `tests/plugin/test_plugin_manifest.py`:

```python
SKILLS_LINK = PLUGIN_DIR / "skills"


def test_skills_is_symlink_to_repo_skills():
    assert SKILLS_LINK.is_symlink(), "plugins/hermes/skills must be a symlink during P0"
    target = SKILLS_LINK.resolve()
    expected = (REPO_ROOT / "skills").resolve()
    assert target == expected, f"skills symlink target {target} != {expected}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `scripts/run_tests.sh "tests/plugin/test_plugin_manifest.py::test_skills_is_symlink_to_repo_skills" -v`
Expected: FAIL.

- [ ] **Step 3: Create the symlink**

```bash
ln -s ../../skills plugins/hermes/skills
```

- [ ] **Step 4: Run test to verify it passes**

Run: `scripts/run_tests.sh "tests/plugin/test_plugin_manifest.py::test_skills_is_symlink_to_repo_skills" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/hermes/skills tests/plugin/test_plugin_manifest.py
git commit -m "feat(plugin): symlink plugin skills to canonical repo skills/ during P0 (P0 task 11)"
```

---

### Task 12 — Slash command export — generator + tests

**Files:**
- Create: `scripts/export_slash_commands.py`
- Create: `plugins/hermes/commands/.gitkeep`
- Create: `tests/plugin/test_command_export.py`

- [ ] **Step 1: Write the failing test**

Create `tests/plugin/test_command_export.py`:

```python
"""Each canonical command in hermes_cli/commands.py has a corresponding .md file."""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMANDS_DIR = REPO_ROOT / "plugins" / "hermes" / "commands"


def _canonical_command_names():
    """Read COMMAND_REGISTRY without importing the whole CLI."""
    import sys
    sys.path.insert(0, str(REPO_ROOT))
    from hermes_cli.commands import COMMAND_REGISTRY
    return [c.name for c in COMMAND_REGISTRY]


def test_commands_dir_exists():
    assert COMMANDS_DIR.exists() and COMMANDS_DIR.is_dir()


@pytest.mark.parametrize("name", _canonical_command_names())
def test_every_canonical_command_has_md(name):
    md = COMMANDS_DIR / f"{name}.md"
    assert md.exists(), f"missing slash command file: {md}"
    text = md.read_text()
    assert text.startswith("---\n"), f"{md} missing YAML frontmatter"
    assert f"name: {name}" in text or f'name: "{name}"' in text


@pytest.mark.parametrize("name", _canonical_command_names())
def test_command_md_has_description(name):
    text = (COMMANDS_DIR / f"{name}.md").read_text()
    fm_end = text.index("---\n", 4)
    fm = text[4:fm_end]
    assert "description:" in fm
```

- [ ] **Step 2: Run test to verify it fails**

Run: `scripts/run_tests.sh tests/plugin/test_command_export.py -v`
Expected: FAIL — `COMMANDS_DIR` missing, parametrize fails to collect commands.

- [ ] **Step 3: Create the directory and gitkeep**

```bash
mkdir -p plugins/hermes/commands
touch plugins/hermes/commands/.gitkeep
```

- [ ] **Step 4: Write the export script**

Create `scripts/export_slash_commands.py`:

```python
#!/usr/bin/env python3
"""Export every canonical Hermes slash command to plugins/hermes/commands/<name>.md.

Idempotent — re-running overwrites existing files. The command body is a single
line pointing at the Hermes CLI dispatcher; real per-command bodies are
plugin/command-specific and out of scope for P0.

Run: python scripts/export_slash_commands.py
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from hermes_cli.commands import COMMAND_REGISTRY  # noqa: E402

OUT_DIR = REPO_ROOT / "plugins" / "hermes" / "commands"


def render(cmd) -> str:
    args_hint = (cmd.args_hint or "").strip()
    desc = cmd.description.replace('"', "'")
    return (
        "---\n"
        f"name: {cmd.name}\n"
        f'description: "{desc}"\n'
        + (f"args_hint: \"{args_hint}\"\n" if args_hint else "")
        + f"category: \"{cmd.category}\"\n"
        + ("aliases: [" + ", ".join(f'"{a}"' for a in cmd.aliases) + "]\n" if cmd.aliases else "")
        + "---\n\n"
        f"Dispatched through the Hermes plugin command bridge. P0 stub — real "
        f"slash command behavior lands in P2.\n"
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for cmd in COMMAND_REGISTRY:
        (OUT_DIR / f"{cmd.name}.md").write_text(render(cmd))
        written += 1
    print(f"wrote {written} slash command files to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run the export script**

Run: `python scripts/export_slash_commands.py`
Expected: prints `wrote N slash command files to .../plugins/hermes/commands`. N depends on the live `COMMAND_REGISTRY` length.

- [ ] **Step 6: Run the export test**

Run: `scripts/run_tests.sh tests/plugin/test_command_export.py -v`
Expected: all parametrized cases PASS.

- [ ] **Step 7: Commit**

```bash
git add scripts/export_slash_commands.py plugins/hermes/commands tests/plugin/test_command_export.py
git commit -m "feat(plugin): generate slash command files from canonical COMMAND_REGISTRY (P0 task 12)"
```

---

### Task 13 — Launcher script

**Files:**
- Create: `scripts/hermes_launcher.sh` (executable)
- Create: `tests/scripts/__init__.py`
- Create: `tests/scripts/test_hermes_launcher.py`

- [ ] **Step 1: Write the failing test**

Create `tests/scripts/__init__.py` (empty).

Create `tests/scripts/test_hermes_launcher.py`:

```python
"""scripts/hermes_launcher.sh execs `claude --plugin-dir <repo>/plugins/hermes`."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = REPO_ROOT / "scripts" / "hermes_launcher.sh"


@pytest.fixture(autouse=True)
def _require_claude():
    if shutil.which("claude") is None:
        pytest.skip("claude CLI not on PATH")


def test_launcher_exists_and_executable():
    assert LAUNCHER.exists()
    assert os.access(LAUNCHER, os.X_OK)


def test_launcher_passes_plugin_dir_flag():
    """Run a non-interactive `claude --help`-style invocation through the launcher."""
    # We can't easily intercept the exec target, but we can verify the launcher
    # produces a valid Claude Code invocation by checking that --print + a no-op
    # prompt returns success.
    result = subprocess.run(
        [str(LAUNCHER), "--print", "--output-format=text", "say only the word OK"],
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert result.returncode == 0, f"launcher exited {result.returncode}: {result.stderr}"
```

Note: this test makes a real Claude Code call. It is marked autouse-skipped if `claude` is not on PATH; for CI without an Anthropic key, mark it `pytest.mark.live` and exclude from default CI runs. Add the marker registration in step 3 below.

- [ ] **Step 2: Run test to verify it fails**

Run: `scripts/run_tests.sh tests/scripts/test_hermes_launcher.py -v`
Expected: FAIL — launcher does not exist.

- [ ] **Step 3: Add the `live` marker to pytest config**

Edit `pyproject.toml`, find `[tool.pytest.ini_options]`. If it has a `markers` list, append `"live: requires a real Claude Code session with network + auth"`. If no markers list exists, add:

```toml
[tool.pytest.ini_options]
markers = [
    "live: requires a real Claude Code session with network + auth",
]
```

Then update `tests/scripts/test_hermes_launcher.py` — change `def test_launcher_passes_plugin_dir_flag():` to:

```python
@pytest.mark.live
def test_launcher_passes_plugin_dir_flag():
```

- [ ] **Step 4: Write the launcher**

Create `scripts/hermes_launcher.sh`:

```bash
#!/usr/bin/env bash
# Hermes launcher — execs Claude Code with the Hermes plugin directory loaded.
#
# Resolves the plugin directory relative to this script's location so the
# launcher works whether invoked from a worktree, install path, or repo root.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PLUGIN_DIR="${REPO_ROOT}/plugins/hermes"

if [ ! -d "${PLUGIN_DIR}" ]; then
  echo "hermes_launcher: plugin dir not found at ${PLUGIN_DIR}" >&2
  exit 1
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "hermes_launcher: claude CLI not on PATH; install via https://docs.anthropic.com/en/docs/agents-and-tools/claude-code" >&2
  exit 127
fi

exec claude --plugin-dir "${PLUGIN_DIR}" "$@"
```

Make it executable:

```bash
chmod +x scripts/hermes_launcher.sh
```

- [ ] **Step 5: Run the executable-existence test (not the live one)**

Run: `scripts/run_tests.sh "tests/scripts/test_hermes_launcher.py::test_launcher_exists_and_executable" -v`
Expected: PASS.

- [ ] **Step 6: Manually smoke-test the launcher (live, not in CI)**

Run: `scripts/hermes_launcher.sh --print "respond with the single word OK"`
Expected: prints `OK` (or close to it) and exits 0. If it errors with an auth prompt, run `claude auth` first.

- [ ] **Step 7: Commit**

```bash
git add scripts/hermes_launcher.sh tests/scripts/__init__.py tests/scripts/test_hermes_launcher.py pyproject.toml
git commit -m "feat(plugin): hermes_launcher.sh execs claude with the Hermes plugin dir (P0 task 13)"
```

---

### Task 14 — End-to-end plugin smoke test (live)

**Files:**
- Create: `tests/plugin/test_plugin_smoke.py`

- [ ] **Step 1: Write the live smoke test**

Create `tests/plugin/test_plugin_smoke.py`:

```python
"""Live smoke test: claude --plugin-dir plugins/hermes starts and the plugin loads."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_DIR = REPO_ROOT / "plugins" / "hermes"


@pytest.fixture(autouse=True)
def _require_claude():
    if shutil.which("claude") is None:
        pytest.skip("claude CLI not on PATH")


@pytest.mark.live
def test_plugin_loads_no_error():
    """A minimal --print invocation against the plugin returns success."""
    result = subprocess.run(
        ["claude", "--plugin-dir", str(PLUGIN_DIR),
         "--print", "--output-format=text",
         "Say only the word OK."],
        capture_output=True, text=True, timeout=90,
    )
    assert result.returncode == 0, f"exit={result.returncode} stderr={result.stderr}"


@pytest.mark.live
def test_plugin_mcp_servers_resolve():
    """Stream-json output mentions at least one mcp__hermes_* tool when asked to list."""
    result = subprocess.run(
        ["claude", "--plugin-dir", str(PLUGIN_DIR),
         "--print", "--output-format=stream-json", "--include-hook-events",
         "List the names of every tool whose name starts with mcp__hermes_, then stop."],
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, f"exit={result.returncode} stderr={result.stderr}"
    # stream-json is newline-delimited JSON; look for hermes_-prefixed tool names anywhere
    body = result.stdout
    expected_servers = ["memory", "terminal", "recall", "browser", "aux", "cron", "kanban", "curator"]
    # MCP tool naming may sanitize hyphens to underscores or keep them; accept either.
    def _seen(s: str) -> bool:
        return any(
            tok in body
            for tok in (
                f"mcp__hermes-{s}__",
                f"mcp__hermes_{s}__",
                f"hermes-{s}",
            )
        )
    seen = [s for s in expected_servers if _seen(s)]
    assert len(seen) >= 4, f"expected ≥4 hermes MCP servers visible, saw {seen}; body[:2000]={body[:2000]}"
```

- [ ] **Step 2: Run the live smoke test**

Run: `scripts/run_tests.sh tests/plugin/test_plugin_smoke.py -v -m live`
Expected: both tests PASS (skipped if `claude` not on PATH).

If the second test fails, inspect the captured `body[:2000]` to learn the actual format Claude Code uses for tool-name reporting, and adjust the substring search to match.

- [ ] **Step 3: Commit**

```bash
git add tests/plugin/test_plugin_smoke.py
git commit -m "test(plugin): live smoke test for plugin load + MCP server visibility (P0 task 14)"
```

---

### Task 15 — Q3 verification: Stop hook stdin payload contains transcript

**Files:**
- Create: `scripts/verify_p0/__init__.py`
- Create: `scripts/verify_p0/q3_stop_hook_payload.py`
- Create: `scripts/verify_p0/q3_capture_hook.py`
- Create: `tests/verify_p0/test_q3_stop_hook.py`

- [ ] **Step 1: Write the failing verification test**

Create `tests/verify_p0/__init__.py` (empty).

Create `tests/verify_p0/test_q3_stop_hook.py`:

```python
"""Q3 verification: a Stop hook receives the session transcript on stdin."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VERIFY_SCRIPT = REPO_ROOT / "scripts" / "verify_p0" / "q3_stop_hook_payload.py"


@pytest.fixture(autouse=True)
def _require_claude():
    if shutil.which("claude") is None:
        pytest.skip("claude CLI not on PATH")


@pytest.mark.live
def test_q3_stop_hook_receives_transcript():
    result = subprocess.run(
        [sys.executable, str(VERIFY_SCRIPT)],
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, (
        f"q3 verification failed (exit={result.returncode}):\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `scripts/run_tests.sh tests/verify_p0/test_q3_stop_hook.py -v -m live`
Expected: FAIL — verify script does not exist.

- [ ] **Step 3: Write the capture-hook helper**

Create `scripts/verify_p0/__init__.py` (empty).

Create `scripts/verify_p0/q3_capture_hook.py`:

```python
#!/usr/bin/env python3
"""Stop hook that dumps its stdin payload to the path in env HERMES_Q3_DUMP."""
import os
import sys


def main() -> int:
    dump = os.environ.get("HERMES_Q3_DUMP")
    body = sys.stdin.read()
    if dump:
        with open(dump, "w") as fh:
            fh.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Make it executable:

```bash
chmod +x scripts/verify_p0/q3_capture_hook.py
```

- [ ] **Step 4: Write the verification driver**

Create `scripts/verify_p0/q3_stop_hook_payload.py`:

```python
#!/usr/bin/env python3
"""Q3 verification — does the Stop hook receive the transcript on stdin?

Spawns a Claude Code session with a Stop hook configured via --settings inline JSON.
Captures the hook's stdin payload to a tmp file. Asserts it is non-empty and contains
both the user prompt and the assistant response.

Exits 0 on success, 1 on failure, prints diagnostics either way.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CAPTURE_HOOK = REPO_ROOT / "scripts" / "verify_p0" / "q3_capture_hook.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        dump = Path(td) / "stop_payload.json"
        env = {**os.environ, "HERMES_Q3_DUMP": str(dump)}

        settings = {
            "hooks": {
                "Stop": [
                    {"hooks": [{"type": "command", "command": str(CAPTURE_HOOK)}]}
                ]
            }
        }
        settings_json = json.dumps(settings)

        # A short, deterministic round-trip — say something the model echoes back.
        prompt = "Reply with only the words 'Q3 SENTINEL' and stop."
        result = subprocess.run(
            ["claude", "--settings", settings_json,
             "--print", "--output-format=text", prompt],
            capture_output=True, text=True, timeout=90, env=env,
        )
        print(f"claude exit={result.returncode}")
        print(f"claude stdout[:500]={result.stdout[:500]!r}")
        print(f"claude stderr[:500]={result.stderr[:500]!r}")

        if not dump.exists():
            print(f"FAIL: Stop hook did not run — no dump at {dump}", file=sys.stderr)
            return 1

        body = dump.read_text()
        print(f"hook stdin size={len(body)} bytes")
        print(f"hook stdin[:400]={body[:400]!r}")

        if not body.strip():
            print("FAIL: Stop hook received empty stdin", file=sys.stderr)
            return 1

        # Try parsing as JSON — Claude Code documents hook stdin as JSON
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            print("FAIL: Stop hook stdin is not valid JSON", file=sys.stderr)
            return 1

        # Look for the transcript — accept any of a few likely schemas
        transcript_key = None
        for key in ("transcript", "messages", "session_transcript", "conversation"):
            if key in payload:
                transcript_key = key
                break

        if transcript_key is None:
            print(
                f"FAIL: no transcript field in payload. keys={list(payload.keys())}",
                file=sys.stderr,
            )
            return 1

        flat = json.dumps(payload[transcript_key]).lower()
        if "q3 sentinel" not in flat:
            print(
                f"FAIL: sentinel not in transcript. transcript[:1000]="
                f"{json.dumps(payload[transcript_key])[:1000]!r}",
                file=sys.stderr,
            )
            return 1

        print(f"PASS: Stop hook received transcript with field '{transcript_key}'.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run the verification directly first**

Run: `python scripts/verify_p0/q3_stop_hook_payload.py`
Expected: prints `PASS: Stop hook received transcript with field '<key>'.` and exits 0.

If it fails: read the diagnostic output, adjust the candidate field names in the verification driver, and re-run. If no transcript field appears at all, mark Q3 as **broken** and amend the spec — do not proceed to Task 16 until Q3 is resolved.

- [ ] **Step 6: Run the verification test**

Run: `scripts/run_tests.sh tests/verify_p0/test_q3_stop_hook.py -v -m live`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add scripts/verify_p0/ tests/verify_p0/__init__.py tests/verify_p0/test_q3_stop_hook.py
git commit -m "test(verify): Q3 — Stop hook receives transcript on stdin (P0 task 15)"
```

---

### Task 16 — Q4 verification: settings override controls the active settings tree

**Files:**
- Create: `scripts/verify_p0/q4_settings_override.py`
- Create: `scripts/verify_p0/q4_probe_hook.py`
- Create: `tests/verify_p0/test_q4_settings_override.py`

- [ ] **Step 1: Write the failing verification test**

Create `tests/verify_p0/test_q4_settings_override.py`:

```python
"""Q4 verification: --settings overrides effective hook registration."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VERIFY_SCRIPT = REPO_ROOT / "scripts" / "verify_p0" / "q4_settings_override.py"


@pytest.fixture(autouse=True)
def _require_claude():
    if shutil.which("claude") is None:
        pytest.skip("claude CLI not on PATH")


@pytest.mark.live
def test_q4_settings_override_takes_effect():
    result = subprocess.run(
        [sys.executable, str(VERIFY_SCRIPT)],
        capture_output=True, text=True, timeout=90,
    )
    assert result.returncode == 0, (
        f"q4 verification failed (exit={result.returncode}):\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `scripts/run_tests.sh tests/verify_p0/test_q4_settings_override.py -v -m live`
Expected: FAIL — verify script missing.

- [ ] **Step 3: Write the probe hook**

Create `scripts/verify_p0/q4_probe_hook.py`:

```python
#!/usr/bin/env python3
"""SessionStart hook that writes a sentinel to env HERMES_Q4_DUMP if invoked."""
import os
import sys


def main() -> int:
    dump = os.environ.get("HERMES_Q4_DUMP")
    if dump:
        with open(dump, "w") as fh:
            fh.write("q4-probe-ran")
    sys.stdin.read()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Make it executable:

```bash
chmod +x scripts/verify_p0/q4_probe_hook.py
```

- [ ] **Step 4: Write the verification driver**

Create `scripts/verify_p0/q4_settings_override.py`:

```python
#!/usr/bin/env python3
"""Q4 verification — does `--settings <json>` install the SessionStart hook we ask for?

Hermes' plan is to generate ~/.claude/settings.json from config.yaml on every
SessionStart. This verification confirms `claude --settings <inline-json>` is a
viable mechanism by:

1. Passing inline settings that register a probe SessionStart hook.
2. Running a one-shot --print invocation.
3. Asserting the probe hook wrote its sentinel file.

Exits 0 on success, 1 on failure.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROBE = REPO_ROOT / "scripts" / "verify_p0" / "q4_probe_hook.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        dump = Path(td) / "q4.sentinel"
        env = {**os.environ, "HERMES_Q4_DUMP": str(dump)}

        settings = {
            "hooks": {
                "SessionStart": [
                    {"hooks": [{"type": "command", "command": str(PROBE)}]}
                ]
            }
        }

        result = subprocess.run(
            ["claude", "--settings", json.dumps(settings),
             "--print", "--output-format=text",
             "Say only the word DONE."],
            capture_output=True, text=True, timeout=60, env=env,
        )
        print(f"claude exit={result.returncode}")
        print(f"claude stdout[:300]={result.stdout[:300]!r}")
        print(f"claude stderr[:300]={result.stderr[:300]!r}")

        if not dump.exists():
            print(f"FAIL: probe sentinel not written to {dump}", file=sys.stderr)
            return 1
        if dump.read_text() != "q4-probe-ran":
            print(f"FAIL: sentinel content unexpected: {dump.read_text()!r}", file=sys.stderr)
            return 1

        print("PASS: --settings inline JSON installs SessionStart hook.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run the verification directly**

Run: `python scripts/verify_p0/q4_settings_override.py`
Expected: prints `PASS: --settings inline JSON installs SessionStart hook.` and exits 0.

If the sentinel is not written: confirm `claude` accepts `--settings <json>` (older versions only accept a path). If only path is accepted, write the JSON to a tmp file and pass the path instead. Update the verification driver and rerun.

- [ ] **Step 6: Run the verification test**

Run: `scripts/run_tests.sh tests/verify_p0/test_q4_settings_override.py -v -m live`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add scripts/verify_p0/q4_probe_hook.py scripts/verify_p0/q4_settings_override.py tests/verify_p0/test_q4_settings_override.py
git commit -m "test(verify): Q4 — --settings override installs SessionStart hook (P0 task 16)"
```

---

### Task 17 — Q5 verification: Task tool propagates env to subagent

**Files:**
- Create: `scripts/verify_p0/q5_task_child_env.py`
- Create: `scripts/verify_p0/q5_child_probe.py`
- Create: `tests/verify_p0/test_q5_task_child_env.py`

- [ ] **Step 1: Write the failing verification test**

Create `tests/verify_p0/test_q5_task_child_env.py`:

```python
"""Q5 verification: a child subagent sees env vars propagated from the parent."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VERIFY_SCRIPT = REPO_ROOT / "scripts" / "verify_p0" / "q5_task_child_env.py"


@pytest.fixture(autouse=True)
def _require_claude():
    if shutil.which("claude") is None:
        pytest.skip("claude CLI not on PATH")


@pytest.mark.live
def test_q5_task_child_env_propagates():
    result = subprocess.run(
        [sys.executable, str(VERIFY_SCRIPT)],
        capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, (
        f"q5 verification failed (exit={result.returncode}):\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `scripts/run_tests.sh tests/verify_p0/test_q5_task_child_env.py -v -m live`
Expected: FAIL — verify script missing.

- [ ] **Step 3: Write the child probe**

Create `scripts/verify_p0/q5_child_probe.py`:

```python
#!/usr/bin/env python3
"""PreToolUse hook fired from a child subagent — dumps HERMES_SUBAGENT_DEPTH to env dump path."""
import json
import os
import sys


def main() -> int:
    dump = os.environ.get("HERMES_Q5_DUMP")
    if dump:
        with open(dump, "a") as fh:
            fh.write(f"depth={os.environ.get('HERMES_SUBAGENT_DEPTH', '<unset>')}\n")
    sys.stdin.read()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Make it executable:

```bash
chmod +x scripts/verify_p0/q5_child_probe.py
```

- [ ] **Step 4: Write the verification driver**

Create `scripts/verify_p0/q5_task_child_env.py`:

```python
#!/usr/bin/env python3
"""Q5 verification — does the Task tool propagate env vars from parent to child subagent?

Strategy:
- Spawn a Claude Code session with HERMES_SUBAGENT_DEPTH=0 in env.
- Configure a PreToolUse hook on EVERY tool that dumps HERMES_SUBAGENT_DEPTH.
- Prompt the agent to use Task with a leaf subagent that does a trivial Bash call.
- Inspect the dump file: it should contain at least one "depth=0" line from the
  parent and ideally another from the child. If only the parent line appears, env
  propagation is NOT automatic and we need a different mechanism (e.g., passing
  depth via prompt + middleware) — record this as a SPEC AMENDMENT.

Exits 0 if env propagated automatically; exits 2 if env did not propagate but the
test setup worked (this is informational — we will amend the spec); exits 1 on
infrastructure failure.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROBE = REPO_ROOT / "scripts" / "verify_p0" / "q5_child_probe.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        dump = Path(td) / "depths.txt"
        env = {**os.environ, "HERMES_Q5_DUMP": str(dump), "HERMES_SUBAGENT_DEPTH": "0"}

        settings = {
            "hooks": {
                "PreToolUse": [
                    {"hooks": [{"type": "command", "command": str(PROBE)}]}
                ]
            }
        }

        prompt = (
            "Use the Task tool to spawn one leaf subagent. The leaf subagent's "
            "only job is to call Bash to print 'q5-child'. Then return."
        )
        result = subprocess.run(
            ["claude", "--settings", json.dumps(settings),
             "--print", "--output-format=text", prompt],
            capture_output=True, text=True, timeout=180, env=env,
        )
        print(f"claude exit={result.returncode}")
        print(f"claude stdout[:600]={result.stdout[:600]!r}")
        print(f"claude stderr[:300]={result.stderr[:300]!r}")

        if not dump.exists():
            print("FAIL: probe never fired — infrastructure error", file=sys.stderr)
            return 1

        lines = [l.strip() for l in dump.read_text().splitlines() if l.strip()]
        print(f"depths captured: {lines}")
        if not lines:
            print("FAIL: empty dump", file=sys.stderr)
            return 1

        # Count occurrences of depth=0
        depth_zero = [l for l in lines if l == "depth=0"]
        if len(lines) > len(depth_zero):
            print("PARTIAL PASS: env propagated to child subagent (depth!=0 line found).")
            print("This is the expected case — proceed with the spec's plan.")
            return 0
        print("INFORMATIONAL: env did NOT propagate automatically to child subagent.")
        print("Hermes will need to inject HERMES_SUBAGENT_DEPTH via an alternate mechanism.")
        print("See spec §7 Q5 — flag SPEC AMENDMENT REQUIRED.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run the verification directly**

Run: `python scripts/verify_p0/q5_task_child_env.py`
Expected: prints either `PARTIAL PASS:` (exit 0) or `INFORMATIONAL:` (exit 2).

If exit 2: **stop and amend the spec** before continuing. Open `specs/2026-05-19-hermes-on-claude-code-design.md` §7 Q5 and add an amendment note: "Verification on Claude Code v2.1.143 showed env propagation to subagent children is NOT automatic. Alternative: HERMES_SUBAGENT_DEPTH passed via Task tool's `prompt` argument as an injected sentinel; the subagent's PreToolUse hooks read it from the most recent UserPromptSubmit payload. Implementation deferred to P2 with this caveat."

After amending the spec, commit the spec change separately, then proceed.

- [ ] **Step 6: Update the verification test to accept either exit 0 or exit 2**

Edit `tests/verify_p0/test_q5_task_child_env.py`, change the assertion to:

```python
assert result.returncode in (0, 2), (
    f"q5 verification produced infra failure (exit={result.returncode}):\n"
    f"stdout={result.stdout}\nstderr={result.stderr}"
)
```

(Exit 2 is "informational pass" — env didn't propagate but we now know that and have amended the spec.)

- [ ] **Step 7: Run the verification test**

Run: `scripts/run_tests.sh tests/verify_p0/test_q5_task_child_env.py -v -m live`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add scripts/verify_p0/q5_child_probe.py scripts/verify_p0/q5_task_child_env.py tests/verify_p0/test_q5_task_child_env.py
git commit -m "test(verify): Q5 — Task tool env propagation probe (P0 task 17)"
```

If the spec was amended in step 5, also commit that change with message:

```bash
git add specs/2026-05-19-hermes-on-claude-code-design.md
git commit -m "docs(specs): amend §7 Q5 — env propagation to subagents requires manual injection (P0 task 17)"
```

---

### Task 18 — Q7 verification: hook can long-poll a Unix socket without being killed

**Files:**
- Create: `scripts/verify_p0/q7_socket_longpoll.py`
- Create: `scripts/verify_p0/q7_blocking_hook.py`
- Create: `tests/verify_p0/test_q7_socket_longpoll.py`

- [ ] **Step 1: Write the failing verification test**

Create `tests/verify_p0/test_q7_socket_longpoll.py`:

```python
"""Q7 verification: a PreToolUse hook can block on a socket read without being killed."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VERIFY_SCRIPT = REPO_ROOT / "scripts" / "verify_p0" / "q7_socket_longpoll.py"


@pytest.fixture(autouse=True)
def _require_claude():
    if shutil.which("claude") is None:
        pytest.skip("claude CLI not on PATH")


@pytest.mark.live
def test_q7_socket_longpoll_survives():
    result = subprocess.run(
        [sys.executable, str(VERIFY_SCRIPT)],
        capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, (
        f"q7 verification failed (exit={result.returncode}):\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `scripts/run_tests.sh tests/verify_p0/test_q7_socket_longpoll.py -v -m live`
Expected: FAIL — verify script missing.

- [ ] **Step 3: Write the blocking hook**

Create `scripts/verify_p0/q7_blocking_hook.py`:

```python
#!/usr/bin/env python3
"""PreToolUse hook that opens a Unix domain socket and blocks until it receives 'ok'."""
import json
import os
import socket
import sys
import time


def main() -> int:
    sock_path = os.environ["HERMES_Q7_SOCK"]
    start = time.monotonic()
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(60.0)  # we expect the supervisor to write 'ok' well before this
    try:
        s.connect(sock_path)
        data = s.recv(64).decode()
        elapsed = time.monotonic() - start
        sys.stdin.read()
        # Write a JSON allow with a comment so we can see the elapsed time in the parent.
        out = {"decision": "allow", "_q7_elapsed_s": round(elapsed, 2), "_q7_recv": data}
        print(json.dumps(out))
        return 0
    except socket.timeout:
        sys.stdin.read()
        print(json.dumps({"decision": "deny", "reason": "q7_hook_timeout"}))
        return 0
    finally:
        s.close()


if __name__ == "__main__":
    sys.exit(main())
```

Make it executable:

```bash
chmod +x scripts/verify_p0/q7_blocking_hook.py
```

- [ ] **Step 4: Write the verification driver**

Create `scripts/verify_p0/q7_socket_longpoll.py`:

```python
#!/usr/bin/env python3
"""Q7 verification — can a PreToolUse hook block on a Unix socket for ≥10s?

This is the load-bearing assumption for the gateway approval-fifo design AND
the background-process notify socket. If hooks time out at, say, 30 seconds,
the approval flow's 300-second timeout cannot work.

Strategy:
- Spawn a Unix socket server in this process.
- Configure a PreToolUse hook on Bash that connects + blocks on recv.
- Invoke Claude Code with a prompt that uses Bash.
- After 10 seconds, write 'ok' to the socket — hook should unblock + allow.
- Assert: end-to-end claude invocation succeeds AND the hook reported elapsed ≥ 10s.

Exits 0 on success, 1 on failure.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / "scripts" / "verify_p0" / "q7_blocking_hook.py"

BLOCK_SECONDS = 10.0


def _server(sock_path: str, ready_evt: threading.Event) -> None:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        try:
            os.unlink(sock_path)
        except FileNotFoundError:
            pass
        s.bind(sock_path)
        s.listen(1)
        ready_evt.set()
        s.settimeout(60.0)
        conn, _ = s.accept()
        time.sleep(BLOCK_SECONDS)
        conn.sendall(b"ok")
        conn.close()
    finally:
        s.close()


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        sock_path = str(Path(td) / "q7.sock")
        env = {**os.environ, "HERMES_Q7_SOCK": sock_path}

        ready = threading.Event()
        server_thread = threading.Thread(target=_server, args=(sock_path, ready), daemon=True)
        server_thread.start()
        if not ready.wait(5):
            print("FAIL: socket server failed to bind", file=sys.stderr)
            return 1

        settings = {
            "hooks": {
                "PreToolUse": [
                    {"matcher": "Bash", "hooks": [
                        {"type": "command", "command": str(HOOK)}
                    ]}
                ]
            }
        }

        prompt = "Run `echo q7-bash-ran` using the Bash tool, then stop."
        start = time.monotonic()
        result = subprocess.run(
            ["claude", "--settings", json.dumps(settings),
             "--print", "--output-format=text",
             "--include-hook-events",
             prompt],
            capture_output=True, text=True, timeout=120, env=env,
        )
        elapsed = time.monotonic() - start
        print(f"claude exit={result.returncode} wall={elapsed:.1f}s")
        print(f"claude stdout[:600]={result.stdout[:600]!r}")
        print(f"claude stderr[:300]={result.stderr[:300]!r}")

        if result.returncode != 0:
            print("FAIL: claude exited non-zero", file=sys.stderr)
            return 1
        if elapsed < BLOCK_SECONDS:
            print(
                f"FAIL: wall time {elapsed:.1f}s < expected ≥{BLOCK_SECONDS}s — "
                "hook was killed before the block window completed.",
                file=sys.stderr,
            )
            return 1
        if "q7-bash-ran" not in result.stdout:
            print("FAIL: Bash tool never ran — hook may have denied or claude rejected", file=sys.stderr)
            return 1

        print(f"PASS: hook survived {elapsed:.1f}s of socket blocking, Bash tool ran.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run the verification directly**

Run: `python scripts/verify_p0/q7_socket_longpoll.py`
Expected: prints `PASS: hook survived NN.Ns of socket blocking, Bash tool ran.` and exits 0.

If it fails with `hook was killed before the block window completed`: Claude Code's hook timeout is shorter than expected. Mark **Q7 BROKEN — alternative design required**. Stop and amend the spec §7 Q7 with: "Verification on Claude Code v2.1.143 showed PreToolUse hook timeout is ~Xs. Approval-fifo design must use a non-blocking poll loop (return 'ask' decision with explicit re-invocation), OR move approval out of the hook layer entirely (e.g., via a wrapper subprocess that consumes the hook's deny and re-prompts the user). Implementation deferred to P3 with this constraint."

- [ ] **Step 6: Run the verification test**

Run: `scripts/run_tests.sh tests/verify_p0/test_q7_socket_longpoll.py -v -m live`
Expected: PASS (if spec is amended for failures, the test must be updated accordingly to accept the new design).

- [ ] **Step 7: Commit**

```bash
git add scripts/verify_p0/q7_blocking_hook.py scripts/verify_p0/q7_socket_longpoll.py tests/verify_p0/test_q7_socket_longpoll.py
git commit -m "test(verify): Q7 — PreToolUse hook can long-poll a Unix socket (P0 task 18)"
```

If the spec was amended in step 5, also commit that:

```bash
git add specs/2026-05-19-hermes-on-claude-code-design.md
git commit -m "docs(specs): amend §7 Q7 — hook timeout limits gateway approval design (P0 task 18)"
```

---

### Task 19 — All-verifications driver

**Files:**
- Create: `scripts/verify_p0/run_all.py`

- [ ] **Step 1: Write the driver**

Create `scripts/verify_p0/run_all.py`:

```python
#!/usr/bin/env python3
"""Run all four P0 verification scripts and report PASS/FAIL summary."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

CHECKS = [
    ("Q3 stop-hook payload",   HERE / "q3_stop_hook_payload.py"),
    ("Q4 settings override",   HERE / "q4_settings_override.py"),
    ("Q5 task child env",      HERE / "q5_task_child_env.py"),
    ("Q7 socket long-poll",    HERE / "q7_socket_longpoll.py"),
]


def main() -> int:
    results = []
    for label, script in CHECKS:
        print(f"\n=== {label} ===")
        r = subprocess.run([sys.executable, str(script)])
        results.append((label, r.returncode))

    print("\n=== summary ===")
    any_hard_fail = False
    for label, code in results:
        if code == 0:
            tag = "PASS"
        elif code == 2:
            tag = "PASS (informational — spec amended)"
        else:
            tag = "FAIL"
            any_hard_fail = True
        print(f"  {tag:>40}  {label}")

    return 1 if any_hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run the driver**

Run: `python scripts/verify_p0/run_all.py`
Expected: prints the 4-line summary; exits 0 if no hard failures.

- [ ] **Step 3: Commit**

```bash
git add scripts/verify_p0/run_all.py
git commit -m "test(verify): add P0 verification all-runner (P0 task 19)"
```

---

### Task 20 — Manifest packaging and final full-suite green

**Files:**
- Modify: `MANIFEST.in`

- [ ] **Step 1: Add the plugin tree to packaging**

Edit `MANIFEST.in`, append:

```
recursive-include plugins/hermes *
include plugins/hermes/plugin.json
include plugins/hermes/.mcp.json
include plugins/hermes/settings.json
include plugins/hermes/CLAUDE_CODE_VERSION
```

- [ ] **Step 2: Confirm the new plugin tree shows up in a sdist preview**

Run: `python -m build --sdist --no-isolation 2>&1 | tail -50` (skip if `build` isn't installed; alternative: `python setup.py sdist 2>&1 | tail -50` if a setup.py exists, otherwise inspect `MANIFEST.in` manually).

Expected: the listing mentions `plugins/hermes/plugin.json` and at least one hook + one MCP server.

- [ ] **Step 3: Run the full plugin test suite (non-live)**

Run: `scripts/run_tests.sh tests/plugin/ tests/scripts/ tests/verify_p0/ -v`
Expected: All non-live tests PASS; live tests are SKIPPED (or PASS if `claude` is on PATH and auth is set up).

- [ ] **Step 4: Run the full Hermes test suite (regression check)**

Run: `scripts/run_tests.sh -q`
Expected: All previously-passing tests still PASS. The plugin scaffold should be completely additive — no existing test should be affected.

- [ ] **Step 5: Commit**

```bash
git add MANIFEST.in
git commit -m "feat(packaging): include plugins/hermes/ in source distribution (P0 task 20)"
```

---

### Task 21 — P0 done — summary and handoff note

**Files:**
- Create: `plugins/hermes/P0_RESULTS.md`

- [ ] **Step 1: Re-run the verification driver and capture its output**

Run: `python scripts/verify_p0/run_all.py 2>&1 | tee /tmp/p0_verify.log`

This produces the authoritative outcome record. The next step pastes it into the results file.

- [ ] **Step 2: Write the P0 results file from the captured log**

Create `plugins/hermes/P0_RESULTS.md` with three sections — pinned version, the verbatim run_all.py output, and a one-line judgement:

```markdown
# P0 verification results

Pinned Claude Code version: see `CLAUDE_CODE_VERSION`.
Run on: <output of `date -u +%Y-%m-%dT%H:%M:%SZ`>

## Verification log

<paste the full contents of /tmp/p0_verify.log inside a fenced ``` block>

## Spec amendments

<list every commit SHA that amended specs/2026-05-19-hermes-on-claude-code-design.md
during P0 — one bullet per amendment with a one-sentence reason. If none, write
"None — all four assumptions held as written.">

## Ready for P1?

<one of: "YES — proceed to plans/2026-05-19-hermes-on-claude-code-P1.md"
       | "NO — blocking issue: <one-line description>; further work needed before P1">
```

Concrete steps the engineer runs:

```bash
date -u +%Y-%m-%dT%H:%M:%SZ                       # capture timestamp
git log --oneline -- specs/2026-05-19-hermes-on-claude-code-design.md
                                                  # capture any spec amendment SHAs from this branch
```

Replace each `<...>` placeholder in the template with the literal output from the corresponding command — the file ships with no `<...>` markers remaining.

- [ ] **Step 2: Commit**

```bash
git add plugins/hermes/P0_RESULTS.md
git commit -m "docs(plugin): P0 verification results template + completion handoff (P0 task 21)"
```

---

## Done with P0

After Task 21, P0 ships. The repo has:
- A complete (but no-op) Hermes Claude Code plugin at `plugins/hermes/`.
- All 8 MCP server stubs and all 11 hook stubs registered.
- A working `scripts/hermes_launcher.sh` that exec's Claude Code with the plugin loaded.
- Concrete verification of the four Q3/Q4/Q5/Q7 assumptions — with spec amendments if any assumption failed.
- No behavior change to existing `hermes` / `hermes gateway` runtimes.

**Next plan to write:** `plans/2026-05-19-hermes-on-claude-code-P1.md` — implement the 8 MCP servers with real shimmed Python bodies + `recall.db` schema. Do not start P1 until P0 is fully green and any spec amendments have been merged.
