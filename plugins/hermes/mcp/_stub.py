"""Shared P0 stub helper for Hermes MCP servers.

Every P0 MCP server (`hermes-memory`, `hermes-terminal`, ...) registers
ONE placeholder tool called `<name>_status` that returns
`{"status": "not_implemented", "phase": "P0", "server": "hermes-<name>"}`.
Real implementations land in P1, at which point each server file replaces
its `make_stub_server(...)` call with concrete tool registrations.

The wrapper exists because `claude_agent_sdk.create_sdk_mcp_server`
(0.2.82) returns a `McpSdkServerConfig` dict — not a server object with
a `.tools` attribute or a `run_stdio()` method. The test surface and
the `python -m plugins.hermes.mcp.<name>.server` invocation pattern
need a uniform shape.
"""
from __future__ import annotations

import asyncio
from typing import Any

from claude_agent_sdk import SdkMcpTool, create_sdk_mcp_server, tool


class _ServerStub:
    """Thin wrapper around McpSdkServerConfig.

    Exposes:
      .tools       — list of SdkMcpTool instances (used by test assertions)
      .run_stdio() — coroutine that runs the underlying server over stdio
    """

    def __init__(self, name: str, version: str, tools: list[SdkMcpTool]) -> None:  # type: ignore[type-arg]
        self._sdk_config = create_sdk_mcp_server(name=name, version=version, tools=tools)
        self.tools = tools
        self.name = name

    async def run_stdio(self) -> None:
        from mcp.server.stdio import stdio_server

        instance = self._sdk_config["instance"]
        async with stdio_server() as (read_stream, write_stream):
            init_opts = instance.create_initialization_options()
            await instance.run(read_stream, write_stream, init_opts)


def make_stub_server(name: str) -> _ServerStub:
    """Build a P0 stub server with one `<name>_status` placeholder tool.

    `name` is the bare server label without the `hermes-` prefix
    (e.g., `"memory"`, `"terminal"`).
    """

    @tool(f"{name}_status", f"Return the current Hermes {name} subsystem status.", {})
    async def status_tool(args: dict[str, Any]) -> dict[str, Any]:
        return {
            "content": [{
                "type": "text",
                "text": f'{{"status": "not_implemented", "phase": "P0", "server": "hermes-{name}"}}',
            }],
        }

    return _ServerStub(
        name=f"hermes-{name}",
        version="0.0.0",
        tools=[status_tool],
    )


def stub_main(server: _ServerStub) -> None:
    """Module-level `main()` that every stub server delegates to."""
    asyncio.run(server.run_stdio())
