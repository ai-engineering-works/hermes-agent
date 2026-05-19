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
