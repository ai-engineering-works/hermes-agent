"""hermes-memory MCP server — P0 stub.

Real implementation lands in P1. This stub exists so the .mcp.json
registration is exercisable end-to-end during P0 plugin-smoke tests.

SDK API note (claude-agent-sdk 0.2.82):
  `create_sdk_mcp_server` returns a `McpSdkServerConfig` dict
  (keys: "type", "name", "instance"), not a standalone stdio server.
  The `.instance` is a low-level `mcp.server.lowlevel.Server` whose
  `run()` method accepts a read/write stream pair, not `run_stdio()`.
  We therefore wrap the result in a small `_ServerStub` that exposes
  a `.tools` list (required by the parametrized stub test) and a
  `run_stdio()` convenience shim backed by `mcp.server.stdio.stdio_server`.
"""
from __future__ import annotations

import asyncio

from claude_agent_sdk import SdkMcpTool, create_sdk_mcp_server, tool


# ── Tool definition ──────────────────────────────────────────────────────────

@tool("memory_status", "Return the current Hermes memory subsystem status.", {})
async def memory_status(args: dict) -> dict:
    return {
        "content": [{
            "type": "text",
            "text": '{"status": "not_implemented", "phase": "P0", "server": "hermes-memory"}',
        }],
    }


# ── Server wrapper ───────────────────────────────────────────────────────────

class _ServerStub:
    """Thin wrapper around McpSdkServerConfig.

    Exposes:
      .tools     — list of SdkMcpTool instances (used by test assertions)
      .run_stdio() — coroutine that runs the MCP server over stdio
    """

    def __init__(self, name: str, version: str, tools: list[SdkMcpTool]) -> None:  # type: ignore[type-arg]
        self._sdk_config = create_sdk_mcp_server(name=name, version=version, tools=tools)
        self.tools = tools

    async def run_stdio(self) -> None:
        from mcp.server.stdio import stdio_server

        instance = self._sdk_config["instance"]
        async with stdio_server() as (read_stream, write_stream):
            init_opts = instance.create_initialization_options()
            await instance.run(read_stream, write_stream, init_opts)


server = _ServerStub(
    name="hermes-memory",
    version="0.0.0",
    tools=[memory_status],
)


def main() -> None:
    asyncio.run(server.run_stdio())


if __name__ == "__main__":
    main()
