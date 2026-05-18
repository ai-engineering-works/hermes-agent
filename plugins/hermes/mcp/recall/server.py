"""hermes-recall MCP server — P0 stub.

Real implementation lands in P1.
"""
from plugins.hermes.mcp._stub import make_stub_server, stub_main

server = make_stub_server("recall")


def main() -> None:
    stub_main(server)


if __name__ == "__main__":
    main()
