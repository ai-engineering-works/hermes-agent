#!/usr/bin/env python3
"""telemetry.py — P0 stub.

Real implementation lands in P2. See specs/2026-05-19-hermes-on-claude-code-design.md §2.2
for the responsibility this hook will own.
"""
import sys


def main() -> int:
    sys.stdin.read()
    return 0


if __name__ == "__main__":
    sys.exit(main())
