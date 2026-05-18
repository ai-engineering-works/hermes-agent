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
