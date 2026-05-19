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
