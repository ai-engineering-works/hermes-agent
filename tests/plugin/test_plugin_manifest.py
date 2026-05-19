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


SKILLS_LINK = PLUGIN_DIR / "skills"


def test_skills_is_symlink_to_repo_skills():
    assert SKILLS_LINK.is_symlink(), "plugins/hermes/skills must be a symlink during P0"
    target = SKILLS_LINK.resolve()
    expected = (REPO_ROOT / "skills").resolve()
    assert target == expected, f"skills symlink target {target} != {expected}"
