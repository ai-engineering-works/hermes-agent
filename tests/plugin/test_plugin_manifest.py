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
