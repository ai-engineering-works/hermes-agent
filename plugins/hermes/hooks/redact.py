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
