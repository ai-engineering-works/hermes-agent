# Hermes on Claude Code — design spec

> ⚠️ **SUPERSEDED — 2026-05-19.** After self-critique and reconsideration, this aggressive "Claude Code is the brain, drop multi-provider" variant was retracted in favor of the predecessor's more conservative shape. Multi-provider is core to Nous Research's identity; deleting it is a brand strangle, not a refactor. The active design is `specs/2026-05-18-convert-hermes-to-claude-code-sdk.md` — Claude Agent SDK is **one transport among many**, Hermes' unique surfaces are exposed as MCP servers consumable by any SDK-based agent (including a vanilla `claude` session), and `run_agent.py` / `cli.py` / `ui-tui/` / `acp_adapter/` / non-Anthropic providers all STAY. This file is preserved for historical reference; do not use it as the source of truth.
>
> The plugin scaffold work landed on branch `feat/claude-code-plugin-p0` (commits `ccc91f8c1`..`404752751`, T1–T11) maps cleanly to the predecessor spec's **Phase 2** ("mirror Hermes tools as MCP servers"). Nothing is rewound. The new implementation plan is at `plans/2026-05-19-hermes-on-claude-code-P1-sdk-transport.md`.

---

**Ticket:** none
**Status:** SUPERSEDED — see banner above
**Created:** 2026-05-19
**Superseded:** 2026-05-19 (same day) — see top of file
**Originally claimed to supersede:** `specs/2026-05-18-convert-hermes-to-claude-code-sdk.md` — that claim is retracted; the 2026-05-18 spec remains the active design.
**Inputs:**
- The predecessor spec and all 49 reverse-engineered specs under `specs/`.
- The Claude Code plugin surface (plugin.json, .mcp.json, settings.json, hooks, commands, agents, skills).
- The Claude Agent SDK (used in-process by the MCP server implementations only).

---

## §1 — Strategic shape

Hermes stops being an agent runtime. It becomes **a Claude Code plugin plus a thin gateway daemon**. Claude Code (the CLI) owns the conversation loop, model calls, tool dispatch, context compression, planning, slash commands, skill loading, hooks, and MCP host duties. Hermes contributes the surfaces Claude Code does not have natively:

- the messaging gateway (Telegram / Discord / WhatsApp / Slack / Matrix / Signal / Feishu / DingTalk / API server / email / SMS / Mattermost),
- pluggable memory backends (Honcho / mem0 / supermemory / byterover / hindsight / holographic / openviking / retaindb),
- remote terminal backends (Docker / SSH / Modal / Daytona / Singularity / Vercel Sandbox),
- Camofox stealth browser automation,
- an auxiliary cheaper-model router for vision / web-extract summary / session-search summary,
- cron-scheduled autonomous jobs (3-minute hard interrupt invariant),
- kanban multi-agent boards with board-level isolation,
- skill curator (provenance + usage telemetry + auto-archive),
- per-turn cost / token / latency telemetry across messaging platforms,
- cross-session FTS5 transcript search.

The `hermes` CLI shrinks to a launcher that exec's `claude --plugin hermes`, plus admin subcommands (`hermes gateway`, `hermes setup`, `hermes cron`, `hermes kanban`, `hermes curator`, `hermes tools`, `hermes skills`, `hermes update`, `hermes doctor`). Multi-provider support, the in-house agent loop, the Ink TUI, the ACP adapter, and the OpenAI-shaped tool dispatch are deleted.

Why this shape (instead of the predecessor spec's "SDK as transport" approach):
- The user's directive was to "ride on top of Claude Code" and "leverage the wider range of tools, skills, commands that are working so well in Claude Code." That payoff requires Claude Code to actually own the loop, not be one option among 25 providers.
- Two parallel agent cores forever (the predecessor's choice) is the worst of both worlds: half the deletion, full ongoing maintenance.
- The plugin path inherits Claude Code's full ecosystem — every plugin in the marketplace, every skill, every command, every future Claude Code feature — for free.

---

## §2 — Components and deletions

### 2.1 The Hermes Claude Code plugin (`plugins/hermes/`)

```
plugins/hermes/
├── plugin.json                  # name, version, description, author, license
├── .mcp.json                    # registers the Hermes MCP servers below
├── settings.json                # default permissions, hook registrations
├── commands/                    # slash commands (.md, Claude Code format)
│   ├── personality.md           # /personality <name>
│   ├── memory.md                # /memory <verb>
│   ├── recall.md                # /recall <query>
│   ├── skin.md                  # /skin <name>  (only if skin survives — see §2.5)
│   ├── cron.md                  # /cron <verb>
│   ├── kanban.md                # /kanban <verb>
│   └── ...                      # rest of the existing slash registry
├── skills/                      # ported from existing skills/ (frontmatter already compatible)
├── agents/                      # subagent type definitions (.md, replaces delegate roles)
│   ├── orchestrator.md          # replaces delegate_task role="orchestrator"
│   ├── leaf.md                  # replaces delegate_task role="leaf"
│   └── ...                      # role-specific specialist agents
├── hooks/                       # hook scripts (Python, invoked by Claude Code)
│   ├── README.md                # documents hook composition order
│   ├── tirith_approval.py
│   ├── osv_check.py
│   ├── env_scrub.py
│   ├── url_safety.py
│   ├── skills_guard.py
│   ├── redact.py
│   ├── bootstrap.py
│   ├── telemetry.py
│   └── session_index.py
└── mcp/                         # MCP server implementations (Python)
    ├── memory/server.py         # hermes-memory   — Honcho/mem0/supermemory/etc.
    ├── terminal/server.py       # hermes-terminal — Docker/SSH/Modal/Daytona/Singularity
    ├── recall/server.py         # hermes-recall   — FTS5 cross-session search + telemetry write
    ├── browser/server.py        # hermes-browser  — Camofox stealth, CDP, vision-driven
    ├── aux/server.py            # hermes-aux      — vision_analyze, web_extract_summary, summarize_session
    ├── cron/server.py           # hermes-cron     — schedule/list/edit jobs
    ├── kanban/server.py         # hermes-kanban   — durable multi-agent board
    └── curator/server.py        # hermes-curator  — skill provenance + usage + auto-archive
```

Each MCP server is a thin Python module that imports existing Hermes Python code and re-wraps it as MCP tools. **No tool logic is rewritten — only protocol-wrapped.** This keeps the diff small and lets the existing per-tool tests carry over (renamed and re-targeted at the MCP entry points).

### 2.2 Hooks — replace Hermes' Python interception layer

| Hook event | Script | Wraps existing Hermes code |
|---|---|---|
| `PreToolUse` (Bash) | `tirith_approval.py` | `tools/tirith_security.py` + `tools/approval.py` + dangerous-pattern matcher |
| `PreToolUse` (Bash with `npx`/`uvx`) | `osv_check.py` | `tools/osv_check.py` |
| `PreToolUse` (Bash env) | `env_scrub.py` | `tools/env_passthrough.py` (blocks `ANTHROPIC_TOKEN`, provider API keys, etc.) |
| `PreToolUse` (WebFetch) | `url_safety.py` | `tools/url_safety.py` + `tools/website_policy.py` |
| `PreToolUse` (Write/Edit on `**/SKILL.md`) | `skills_guard.py` | `tools/skills_guard.py` |
| `PreToolUse` (Task) | `subagent_depth.py` | enforces `delegation.max_spawn_depth` via `HERMES_SUBAGENT_DEPTH` env counter (see §7 Q5) |
| `PreToolUse` (Task) | `subagent_concurrency.py` | enforces `delegation.max_concurrent_children` via lockfile at `$HERMES_HOME/run/subagent_concurrency.lock` (see §7 Q5) |
| `UserPromptSubmit` | `redact.py` | `agent/redact.py` + scrub PII |
| `SessionStart` | `bootstrap.py` | regenerates `$HERMES_HOME/.claude/settings.json` from `config.yaml` (see §7 Q4); loads personality + memory snapshot; runs `tools/lazy_deps.py`; reads pending `$HERMES_HOME/run/background_procs/*.completion.json` and appends to system prompt (see §7 Q7 interactive path) |
| `PostToolUse` | `telemetry.py` | writes per-turn cost / tokens / latency to insights SQLite; incremental turn-row write to `recall.db` (see §7 Q3) |
| `Stop` | `session_index.py` | writes full transcript snapshot to `recall.db` (post-compact state captured here; see §7 Q3) |

Composition rule: hooks fire in `hooks/README.md`-documented order. PreToolUse hooks short-circuit on `deny`; an explicit `allow` from any one hook does NOT bypass the others — every hook must allow. This matches the existing Hermes invariant that approval, Tirith, and dangerous-pattern checks all gate independently.

### 2.3 The gateway daemon (`gateway/`, kept and re-skinned)

`gateway/run.py` retains the platform adapter loop (`gateway/platforms/*`) and platform-specific config (cwd, personality, skills, tool gating). The only swap is the per-chat session handler.

Before:
```python
agent = AIAgent(provider=…, session_id=chat_session_id, …)
response = agent.run_conversation(user_message, …)
```

After:
```python
proc = claude_session_manager.spawn(
    args=["-p", user_message,
          "--session-id", chat_session_id,
          "--plugin", "hermes",
          "--output-format", "stream-json",
          "--cwd", terminal_cwd],
    env={
        **profile_env(),
        "HERMES_PLATFORM": platform,
        "HERMES_CHAT_ID": chat_id,
        "HERMES_GATEWAY_APPROVAL_FIFO": fifo_path,
    },
)
async for event in proc.stream_json():
    await gateway_adapter.emit(event)   # stream-json → platform-specific message events
```

A new `gateway/claude_session_manager.py` owns:
- subprocess lifecycle (spawn, resume by `--session-id`, cancel via SIGTERM to process group),
- stream-json parsing into `gateway_adapter` events,
- approval fifo (when `HERMES_GATEWAY_APPROVAL_FIFO` is set, the `tirith_approval` hook writes the approval request to the fifo and waits with the existing 300-second `threading.Event` semantics; the gateway runner reads the fifo, posts an approval prompt on the platform, parses `/approve` / `/deny`, writes the answer back),
- crash recovery (stderr captured, surfaced to platform, chat-session-map row marked stale so the next message starts fresh),
- background notify socket (see §7 Q7 — `gateway/notify_listener.py` listens on `$HERMES_HOME/run/gateway_notify.sock`; on completion events it spawns a new `claude` subprocess with a synthesized message and the originating chat's `session_id`).

The spawn env additionally carries `HERMES_GATEWAY_NOTIFY_SOCK` and `CLAUDE_HOME=$HERMES_HOME/.claude` (see §7 Q4 — profile-scoped Claude Code state).

`hermes_state.SessionDB` shrinks to a single table: `(platform, chat_id, thread_id) → claude_session_id`. The full message-history columns and FTS5 transcript index move to the `hermes-recall` MCP server.

Per-platform behavior, command sets, gating, and approval semantics are unchanged from the user's perspective — every existing test that exercises platform behavior should continue to pass after Phase 3.

### 2.4 Concrete deletion list

**Agent core — delete entirely:**

- `run_agent.py` (~12k LOC AIAgent loop and orchestrator)
- `model_tools.py` (tool dispatch — Claude Code dispatches via MCP and built-ins)
- `toolsets.py` (replaced by `.mcp.json` server lists per platform)
- `batch_runner.py` (use Claude Code's headless batch mode)
- `trajectory_compressor.py` (Claude Code handles compaction)
- `mini_swe_runner.py` (research artifact, no SDK analog needed)
- `mcp_serve.py` (Claude Code is the MCP host now)
- `agent/context_handling.py` ContextCompressor 5-phase algorithm
- `agent/error_handling.py` FailoverReason taxonomy
- `agent/transports/*` (all of them — including `claude_agent_sdk.py` if the predecessor spec's Phase 1 landed first; the gateway calls the CLI subprocess instead)
- `agent/provider_adapters/*` (all of them)
- `agent/prompt_builder.py` (system prompt becomes `plugin.json` system-message + skill loading)
- `agent/memory_manager.py` orchestrator (hermes-memory MCP takes over)

**CLI surface — delete:**

- `cli.py` HermesCLI class (~11k LOC)
- `ui-tui/` Ink/React TUI (Claude Code is the TUI)
- `tui_gateway/` JSON-RPC server
- `acp_adapter/`, `acp_registry/` (Claude Code has its own ACP integration)
- `agent/skill_commands.py` (Claude Code loads skills natively)
- `hermes_cli/skin_engine.py` and `_BUILTIN_SKINS` (Claude Code has its own theming)

**Tools — delete (Claude Code built-in equivalents):**

| Hermes file | Replaced by |
|---|---|
| `tools/file_tools.py`, `tools/file_operations.py`, `tools/file_state.py` | Read / Edit / Write |
| `tools/patch_parser.py`, `tools/fuzzy_match.py` | Edit |
| `tools/web_tools.py`, `tools/x_search_tool.py` | WebSearch / WebFetch |
| `tools/todo_tool.py` | TodoWrite |
| `tools/delegate_tool.py` | Task (with subagent_type) |
| `tools/clarify_tool.py` | ExitPlanMode + plan mode |
| `tools/code_execution_tool.py` | Bash |
| `tools/session_search_tool.py` (LLM dispatch side) | `/recall` slash command → hermes-recall MCP |
| `tools/skill_manager_tool.py` (LLM dispatch side) | `/skill` slash command + Claude Code skill loader (backend stays under hermes-curator MCP for write operations) |
| `tools/computer_use_tool.py`, `tools/computer_use/` | Claude Code computer use beta |
| `tools/mixture_of_agents_tool.py` | subagent fan-out via Task |
| `tools/send_message_tool.py` (LLM dispatch side) | Gateway tools exposed via hermes-gateway MCP (only used by cron/kanban code paths that need to deliver to a different platform) |

**Provider plugins — delete (multi-provider goes away):**

- `plugins/model-providers/openai/`, `openrouter/`, `gemini/`, `bedrock/`, `azure-foundry/`, `gmi/`, `nvidia/`, `xai/`, `deepseek/`, `kimi-coding/`, `minimax/`, `novita/`, `xiaomi/`, `zai/`, `stepfun/`, `arcee/`, `qwen-oauth/`, `kilocode/`, `huggingface/`, `ai-gateway/`, `alibaba/`, `alibaba-coding-plan/`, `copilot/`, `copilot-acp/`, `custom/`, `nous/`, `ollama-cloud/`, `openai-codex/`, `opencode-zen/`
- `plugins/model-providers/anthropic/` is deleted last (Claude Code handles Anthropic auth itself); keep nothing under `plugins/model-providers/` at the end.
- `providers/registry.py` and the `agent/auxiliary_client.py::_resolve_auto` provider-routing logic. The auxiliary client keeps a tiny Anthropic-only client used by `hermes-aux` MCP for vision / extract / summary.

### 2.5 What stays unchanged

- All of `gateway/platforms/*` (12+ adapters: telegram, discord, slack, whatsapp, signal, matrix, homeassistant, mattermost, email, sms, dingtalk, wecom, weixin, feishu, qqbot, bluebubbles, yuanbao, webhook, api_server)
- `cron/jobs.py`, `cron/scheduler.py` (backend for hermes-cron MCP — 3-minute hard interrupt invariant preserved)
- Memory backends in `plugins/memory/*` (backend for hermes-memory MCP)
- `tools/environments/*` (Docker / SSH / Modal / Daytona / Singularity backends for hermes-terminal MCP)
- `tools/browser_*.py` and `tools/browser_providers/` (backend for hermes-browser MCP)
- `agent/curator.py`, `agent/curator_backup.py`, `tools/skill_provenance.py`, `tools/skill_usage.py` (backend for hermes-curator MCP)
- `agent/auxiliary_client.py` (trimmed to Anthropic-only side-LLM client; backend for hermes-aux MCP)
- `agent/insights.py`, `agent/account_usage.py`, `agent/usage_pricing.py` (telemetry written via PostToolUse hook)
- `hermes_state.SessionDB` — schema trimmed: keep `(platform, chat_id, thread_id) → claude_session_id` map; the FTS5 transcript index moves under hermes-recall MCP's own DB at `~/.hermes/recall.db`
- `hermes_constants.py`, `hermes_logging.py`, `hermes_time.py` (profile support, log paths, timezone helpers)
- `tools/mcp_oauth.py`, `tools/mcp_oauth_manager.py` (Hermes' MCP OAuth is more sophisticated than Claude Code's; bridge via SessionStart hook that writes resolved tokens into Claude Code's `~/.claude/mcp_oauth.json` before the session starts)
- `tools/skills_hub.py` (`hermes skills install` installs into `~/.hermes/plugins/hermes/skills/`)
- `tools/credential_files.py` (used by hermes-terminal MCP for sandbox mounts)
- `tools/tool_result_storage.py` (used by every Hermes MCP server for oversize-output truncation + spillover)

### 2.6 Sketch of impact

| Area | Before | After (est.) |
|---|---|---|
| `agent/` LOC | ~24k | ~7k (-70%) |
| `tools/` LOC | ~59k | ~25k (-55%) |
| `cli.py` + `ui-tui/` + `tui_gateway/` + `acp_adapter/` | ~25k | 0 (-100%) |
| `plugins/model-providers/*` | ~30 dirs | 0 (-100%) |
| `agent/transports/*` + `agent/provider_adapters/*` | ~15 files | 0 (-100%) |
| Test count | ~17k | ~8.5k (-50%) (delete tests covering deleted code) |
| Total top-level Python LOC | ~150k | ~60k (-60%) |

---

## §3 — Data flow

### 3.1 Interactive (terminal user)

```
User runs: hermes  (a 5-line bash launcher that exec's `claude --plugin hermes`)
   ↓
Claude Code starts, loads the hermes plugin (skills, agents, commands, hooks, MCP servers)
   ↓
SessionStart hook fires: bootstraps personality, memory snapshot, lazy-deps install
   ↓
User types message → UserPromptSubmit hook scrubs / redacts
   ↓
Claude Code chooses tools (built-ins or mcp__hermes_*__*)
   ↓
PreToolUse hooks gate (Tirith / approval / url_safety / skills_guard / osv / env_scrub)
   ↓
Tool runs → PostToolUse hook writes telemetry to insights SQLite
   ↓
Loop until Claude responds with no tool calls
   ↓
Stop hook indexes session transcript for FTS5 recall
```

### 3.2 Messaging (Telegram example — identical for all platforms)

```
User sends Telegram message → gateway/platforms/telegram.py receives
   ↓
gateway/run.py maps (telegram, chat_id, thread_id) → claude_session_id (SessionDB)
   ↓
gateway/claude_session_manager.py spawns or resumes:
   claude -p "<msg>" --session-id <id> --plugin hermes
          --output-format stream-json --cwd <terminal.cwd>
          --env HERMES_PLATFORM=telegram HERMES_CHAT_ID=…
                HERMES_GATEWAY_APPROVAL_FIFO=/tmp/hermes-approval-<pid>
                HERMES_GATEWAY_NOTIFY_SOCK=$HERMES_HOME/run/gateway_notify.sock
                HERMES_SUBAGENT_DEPTH=0
                CLAUDE_HOME=$HERMES_HOME/.claude
   ↓
Claude Code runs the full plugin pipeline (same as interactive)
   ↓
stream-json events → gateway adapter translates to platform messages
   ↓
Approval needed → tirith_approval hook writes to fifo → gateway posts /approve prompt
                  → user replies → gateway writes answer to fifo → hook unblocks
                  (300s timeout invariant preserved)
   ↓
Session persists across messages (--session-id resumes Claude Code's session DB row)
```

### 3.3 Cron-triggered job

```
cron/scheduler.py tick → spawns
   claude -p "<cron_prompt>" --session-id cron-<job_id>-<runtime>
          --plugin hermes --skills <job.skills> --output-format stream-json
          --env HERMES_CRON_MODE=1   (PreToolUse hooks auto-approve safe ops in cron mode)
                HERMES_SKIP_MEMORY=1 (preserves existing invariant)
   ↓
3-minute hard interrupt: scheduler sends SIGTERM to process group on deadline (invariant preserved)
   ↓
Output piped to job.delivery_target (any gateway platform — same delivery code path)
```

### 3.4 Kanban worker

```
Gateway-embedded dispatcher (kanban.dispatch_in_gateway=true) claims a task →
   spawns: claude -p "<task_body>" --session-id kanban-<task_id>
                  --plugin hermes --skills <task.profile_skills>
                  --env HERMES_KANBAN_TASK=<id> HERMES_KANBAN_BOARD=<id>
   ↓
Worker has access to mcp__hermes_kanban__* tools (gated by HERMES_KANBAN_TASK env var)
   ↓
On completion / heartbeat → worker calls mcp__hermes_kanban__complete
```

---

## §4 — Error handling

| Failure | Owner | Behavior |
|---|---|---|
| Anthropic API error (rate limit, 5xx) | Claude Code | SDK retries; if exhausted, the subprocess exits non-zero — gateway surfaces error to platform with platform-appropriate formatting. No fallback transport (multi-provider is gone). |
| Claude Code subprocess crash | `gateway/claude_session_manager.py` | Capture stderr, surface to platform; mark chat-session-map row stale; next message starts a fresh session. |
| MCP server crash | Claude Code's MCP supervisor | Auto-restart; if persistent, that capability becomes unavailable for the rest of the session (Claude is told via system message); telemetry hook logs. |
| Hook timeout (e.g., approval not answered in 300s) | hook script | Hook returns `deny`; Claude Code declines the tool call; loop continues with the denial as input — same UX as today. |
| Tool result spillover (oversize output) | the MCP server | Each Hermes MCP server keeps `tools/tool_result_storage.py` truncation + spillover behavior — unchanged. |
| Subprocess interrupt (Ctrl+C interactive, `/stop` from gateway) | gateway / Claude Code | Sends SIGTERM to process group; Claude Code's own cancellation flushes; session_id stays valid for resume. |
| Memory provider failure (Honcho down) | `hermes-memory` MCP | Tool returns error JSON; agent receives in transcript and decides to continue without; no agent-loop failure. |
| Approval fifo broken (gateway died mid-call) | `tirith_approval` hook | Falls back to `deny` after 300s; logs; subprocess exits cleanly. |
| Plugin install corrupted | Claude Code plugin loader | Refuses to load the plugin; `hermes doctor` detects and recommends `claude plugin reinstall hermes`. |

Failures that no longer exist on this path: provider failover (no other providers), context-window overflow handling (`/compact` is automatic in Claude Code), in-house retry orchestration, OpenAI-shaped tool-call parsing errors.

---

## §5 — Testing strategy

### 5.1 Test surfaces

| Layer | Test type | Location |
|---|---|---|
| Each Hermes MCP server | Schema parity + dispatch parity vs the legacy Python tool | `tests/mcp/test_hermes_<server>.py` |
| Each hook | PreToolUse / PostToolUse / UserPromptSubmit / Stop contract — input JSON, output JSON, exit code | `tests/hooks/test_<hook>.py` |
| Hook composition | Multi-hook PreToolUse ordering + short-circuit on deny + all-must-allow | `tests/hooks/test_composition.py` |
| Gateway subprocess manager | Spawn, stream-json bridge, approval fifo round-trip, session resume, crash recovery | `tests/gateway/test_claude_session_manager.py` |
| Per-platform regression | One message round-trip per platform on the new path | `tests/gateway/test_<platform>_claude_path.py` |
| Cron + kanban runners | End-to-end job run under the new subprocess shape — 3-minute hard interrupt fires; kanban worker MCP gating works | `tests/cron/test_cron_under_claude.py`, `tests/kanban/test_worker_under_claude.py` |
| Plugin install | Plugin loads in a vanilla `claude` session, MCP servers come up, skills / commands / agents visible | `tests/plugin/test_plugin_smoke.py` |
| Memory bridge | `/remember` slash command writes to the active provider (Honcho / mem0 / …); `mcp__hermes_memory__*` reads round-trip | `tests/mcp/test_memory_bridge.py` |
| Recall bridge | FTS5 search returns historical turns; `PostToolUse` writes incremental turn rows; `Stop` writes full transcript snapshot; pre-compact and post-compact transcripts both retrievable (§7 Q3) | `tests/mcp/test_recall_bridge.py` |
| Settings.json generator | `bootstrap.py` writes the expected JSON from `config.yaml`; manual edits to `settings.json` are clobbered on next session; profile-scoped paths honored (§7 Q4) | `tests/hooks/test_bootstrap_settings.py` |
| Subagent depth + concurrency | `subagent_depth.py` and `subagent_concurrency.py` deny at the configured limits; HERMES_SUBAGENT_DEPTH env propagates correctly; orchestrator role gating works (§7 Q5) | `tests/hooks/test_subagent_gates.py` |
| Background notify (gateway) | Background process completion writes to notify socket; gateway listener synthesizes a new turn; originating chat receives the completion message via the platform adapter with `source=background_watcher` (§7 Q7) | `tests/gateway/test_notify_listener.py` |
| Background notify (interactive) | `bootstrap.py` reads pending `*.completion.json`, injects into system prompt, deletes files after consumption (§7 Q7) | `tests/hooks/test_bootstrap_background_completion.py` |
| Security invariants | Every invariant from existing security specs — Tirith content scan, approval hardline + dangerous patterns, OSV malware block, URL safety SSRF block, skill content scan, env scrub — holds via hook composition | `tests/hooks/test_security_invariants.py` |

### 5.2 Deletions

Every test that exercises the in-house agent loop, provider transports, context_handling compressor, error_handling failover, OpenAI / Bedrock / Gemini adapters, CLI's HermesCLI dispatch, Ink TUI rendering, ACP adapter — roughly half the existing ~17k test count is removed. Reviewers must check each test deletion against the deletion list in §2.4 and flag any test that covers behavior NOT also covered by the new MCP / hook / gateway tests.

---

## §6 — Phasing

| Phase | Goal | Ships when |
|---|---|---|
| **P0 — Plugin scaffold + verify Claude Code assumptions** | `plugins/hermes/plugin.json`, `.mcp.json`, empty MCP server stubs, hooks stubs, port existing `skills/` and slash commands into the plugin layout. The `hermes` launcher (`exec claude --plugin hermes`) lands but the in-process AIAgent is still the default. **Also: pin Claude Code version and verify the four assumptions Q3/Q4/Q5/Q7 rest on** — Stop hook stdin payload contains transcript (Q3); env var or flag controls Claude Code state root (Q4); Task tool supports child env propagation (Q5); plugin can long-poll a Unix socket without being killed by hook timeouts (Q7). If any assumption fails, the spec is amended before P1 starts. | Vanilla `claude --plugin hermes` starts and lists Hermes' skills, commands, subagents. No behavior change for existing users. Q3/Q4/Q5/Q7 assumption-verification scripts pass against the pinned Claude Code version. |
| **P1 — Hermes-unique MCP servers + recall schema** | Implement `hermes-memory`, `hermes-terminal`, `hermes-recall`, `hermes-browser`, `hermes-aux`, `hermes-cron`, `hermes-kanban`, `hermes-curator`. Each is a shim over existing Python code. `hermes-recall` lands the `recall.db` schema from §7 Q3. `hermes-terminal` lands the background process registry and `*.completion.json` write path from §7 Q7. | All eight MCP servers pass parity tests against their legacy Python counterparts. A vanilla `claude --plugin hermes` session can use every Hermes-unique capability. |
| **P2 — Hooks port + Q3/Q4/Q5/Q7 enforcement** | Port `tirith_security`, `approval`, `url_safety`, `osv_check`, `skills_guard`, `env_passthrough`, `redact`, `website_policy`, telemetry writer, session_index writer into hook scripts. Add the four resolved-question hooks: `subagent_depth.py`, `subagent_concurrency.py` (Q5), `bootstrap.py` settings.json regen (Q4), `bootstrap.py` background-completion reader (Q7 interactive), `session_index.py` recall.db writer (Q3). `plugins/hermes/hooks/README.md` documents composition. | Hook composition tests pass; every safety invariant test from existing security specs passes on the plugin path; the four Q3/Q4/Q5/Q7 test surfaces in §5.1 all pass. |
| **P3 — Gateway swap** | `gateway/run.py` replaces in-process `AIAgent` with `gateway/claude_session_manager.py` spawning the CLI subprocess. `SessionDB` schema migration to the trimmed map. Approval fifo bridge. **`gateway/notify_listener.py` lands the Unix-socket listener and synthesized-turn dispatch from §7 Q7 gateway path.** Per-platform smoke regression. | All 12+ platforms pass smoke tests on the new path; `hermes gateway start` no longer imports `run_agent`; background-process completion delivers a synthesized turn end-to-end through a real platform. Existing Telegram bots configured today continue to work without user re-setup. |
| **P4 — CLI collapse** | The `hermes` CLI becomes `exec claude --plugin hermes` for interactive; admin verbs (`gateway`, `setup`, `cron`, `kanban`, `curator`, `tools`, `skills`, `update`, `doctor`, `claw migrate`) remain as thin operations on plugin internals. Delete `cli.py` HermesCLI, `ui-tui/`, `tui_gateway/`, `acp_adapter/`, `agent/skill_commands.py`, `hermes_cli/skin_engine.py`. | Interactive `hermes` matches Claude Code feature-parity; admin verbs unchanged in behavior. |
| **P5 — Bulk deletion** | Delete every file listed in §2.4: `run_agent.py`, `model_tools.py`, `toolsets.py`, `batch_runner.py`, `trajectory_compressor.py`, `mcp_serve.py`, `mini_swe_runner.py`, all `agent/transports/*`, all `agent/provider_adapters/*`, all `plugins/model-providers/*`, all redundant `tools/*`, `agent/context_handling.py`, `agent/error_handling.py`, `agent/prompt_builder.py`, `agent/memory_manager.py` orchestrator. Delete corresponding tests. | LOC reduction targets in §2.6 met; test suite green on the reduced surface; one full release-cycle dogfood on the main author's daily setup. |
| **P6 — Polish & publish** | `settings.json` generator from `config.yaml` (Hermes config remains the single source of truth, generates Claude Code settings on plugin load); plugin marketplace publishing; docs site rewrite; `hermes claw migrate` adds the claude-code-migration path so OpenClaw users land on the new shape. | Marketplace listing live; users can `claude plugin install hermes` against a registry. |

Each phase is shippable. If any phase reveals a blocker (MCP performance, Claude Code SDK feature gap, an invariant the SDK does not let us reproduce), the previous phase remains the steady state.

---

## §7 — Resolved load-bearing decisions

These four were the load-bearing ones that determine whether data flow, delegation, and background work actually function. Resolved decisions below; cross-references back into the relevant component sections.

### Q3 (resolved) — Hermes-recall vs Claude Code's own session DB

**Decision.** Claude Code's session DB is opaque to Hermes — we never read from it, never write to it, never inspect its schema. Hermes-recall keeps its own SQLite store at `~/.hermes/recall.db` (profile-scoped via `get_hermes_home()`). The bridge is one-way: the `Stop` hook (and a `PostToolUse` hook for incremental indexing on long sessions) captures the transcript state Claude Code has accumulated and writes it to recall.db. The transcript snapshot is read from the hook's stdin payload, which Claude Code provides per Stop / PostToolUse contract — not from Claude Code's session file.

**Compact rewrites.** When the user invokes `/compact`, Claude Code rewrites the session's in-memory transcript. The next `Stop` hook fires *after* compact — recall.db gets the post-compact transcript. The pre-compact full transcript was already captured by earlier `Stop` / `PostToolUse` firings (one per turn boundary), so recall.db has both: the full pre-compact turns *and* the post-compact summary. We treat recall.db as the archival store of record; Claude Code's session DB is treated as the live working set that can be re-compacted at any time.

**Schema.** `recall.db` has tables: `sessions(session_id, platform, chat_id, started_at, ended_at)`, `turns(session_id, turn_idx, role, content_md, content_json, ts)`, `turns_fts(content_md)` (FTS5 virtual table), `tool_calls(session_id, turn_idx, tool_name, args_json, result_json, latency_ms, ts)`. Indexes on `(platform, chat_id)` and `(ts)`.

**Cross-reference.** This determines the schema for `mcp/recall/server.py` (§2.1) and the `Stop` + `PostToolUse` hook contracts (§2.2). Updates the §3 data-flow lines that mention "Stop hook indexes session transcript for FTS5 recall."

### Q4 (resolved) — Settings direction and scope

**Decision.** `~/.hermes/config.yaml` is the single source of truth. **Hermes generates Claude Code settings on every session start; the reverse direction is unsupported and manual edits to the generated settings file are clobbered.**

**Mechanism.** The `bootstrap.py` SessionStart hook reads `config.yaml`, materializes the equivalent Claude Code settings JSON to a *profile-scoped* path (so two Hermes profiles don't trample each other's Claude Code settings), and points Claude Code at it. Specifically:
- Hermes invokes Claude Code with `CLAUDE_HOME=$HERMES_HOME/.claude` in the spawn env (or whatever env var Claude Code reads for its settings root — to be pinned in P0 against the version we target).
- The bootstrap hook regenerates `$HERMES_HOME/.claude/settings.json` from `config.yaml` at every SessionStart, after `_apply_profile_override()` has resolved the active profile.
- The generated settings.json is owned by Hermes; it carries a comment header `# generated from ~/.hermes/config.yaml; edits will be overwritten` and an explicit `_hermes_generated_at` timestamp field for diagnostic clarity.
- A `hermes doctor` check verifies the generated file matches what `config.yaml` would produce; any divergence is flagged.

**What is NOT generated.** Claude Code's own state (session history, auth tokens, skill cache) lives in `$HERMES_HOME/.claude/` and is preserved across sessions. Only `settings.json` is regenerated.

**Profile isolation.** Profile-scoped already works for Hermes (`get_hermes_home()` returns `~/.hermes/profiles/<name>` for profiles). Setting `CLAUDE_HOME` to the same root extends profile isolation to Claude Code state automatically. No new profile mechanism is needed.

**Cross-reference.** This determines the `bootstrap.py` SessionStart hook implementation (§2.2) and the P6 settings.json generator (§6). Updates §11's "Profile system (...)" stays-unchanged entry.

### Q5 (resolved) — Subagent depth

**Decision.** Hermes' `delegation.max_spawn_depth` (default 2) is enforced via a `PreToolUse` hook on the `Task` tool. Claude Code's built-in subagent depth limit is set to `>= delegation.max_spawn_depth` via the generated settings.json (so Claude Code's limit is the outer envelope; Hermes' limit is the inner enforcement). The Hermes hook is the authoritative cap.

**Mechanism.**
- Every Hermes session and subagent carries `HERMES_SUBAGENT_DEPTH` in its env (root session: `0`).
- The `Task` `PreToolUse` hook (`subagent_depth.py`, added to the hooks list in §2.2) reads `HERMES_SUBAGENT_DEPTH` from the parent process env. If `HERMES_SUBAGENT_DEPTH + 1 > delegation.max_spawn_depth`, the hook denies.
- On allow, the hook sets the child env's `HERMES_SUBAGENT_DEPTH = parent + 1`. (Claude Code's Task tool supports passing env to subagents per its plugin contract — to be pinned in P0.)
- `delegation.orchestrator_enabled` is enforced by the same hook: if `false`, only role=`leaf` subagents are allowed regardless of depth.
- `delegation.max_concurrent_children` is enforced by a *separate* `PreToolUse` hook on `Task` (`subagent_concurrency.py`) that maintains a process-group concurrency counter in a lockfile at `$HERMES_HOME/run/subagent_concurrency.lock`. Concurrency is per-root-session, matching today's behavior.

**Cross-reference.** This adds two hooks to the §2.2 table (`subagent_depth.py`, `subagent_concurrency.py`). Updates the P2 deliverable to include subagent enforcement hooks. Removes the implied need for `agents/orchestrator.md` to encode depth limits (the hook is the gate).

### Q7 (resolved) — Background process notification flow

**Decision.** `hermes-terminal` MCP keeps the background process registry. When a process completes, the MCP server writes a completion event to a **gateway notify socket** (Unix domain socket on POSIX; named pipe on Windows). The gateway runner reads the notify event, synthesizes a user-shaped message, and spawns a new `claude` subprocess with that synthesized message + the originating chat's `session_id`. This preserves "new turn on background completion" for gateway users.

**Interactive mode degrades gracefully.** In interactive (terminal) mode there is no long-lived gateway watching the socket — Claude Code is the foreground process and exits between turns. Background completions accumulate in the hermes-terminal MCP's registry; the next user message naturally causes a new session-resume, and the SessionStart hook reads pending completions and injects them as system-message context ("3 background processes completed since last turn: ..."). The auto-notify-mid-conversation feature is gateway-only; the behavior degradation is documented in user-facing docs.

**Mechanism (gateway path).**
- `hermes-terminal` MCP's `exec(background=True)` registers the process in `$HERMES_HOME/run/background_procs/<proc_id>.json` and forks the watcher.
- The watcher, on process exit, writes a completion event to the notify socket at `$HERMES_HOME/run/gateway_notify.sock` (path passed in via env var `HERMES_GATEWAY_NOTIFY_SOCK`, set by `gateway/claude_session_manager.py` when it spawns the subprocess).
- Gateway runner has a notify-socket listener (`gateway/notify_listener.py`, new file) that reads completion events. For each event, it builds a synthesized message like `[Background process <proc_id> completed: exit_code=<n>, stdout_tail=<...>]` and dispatches it through the normal per-chat session spawn path (`claude_session_manager.spawn(...)` with the originating `session_id` and platform context).
- The synthesized message is delivered with a special platform-event tag (`source=background_watcher`) so the gateway adapter can format it distinctly (e.g., a system-styled prefix on Telegram) instead of showing it as a user message echo.

**Mechanism (interactive path).**
- No notify socket. `hermes-terminal` MCP still writes completion events to `$HERMES_HOME/run/background_procs/<proc_id>.completion.json`.
- `bootstrap.py` SessionStart hook reads any `*.completion.json` files newer than the last session's `Stop` timestamp and injects a summary into the prompt as additional system context (or via Claude Code's `--append-system-prompt` flag — pinned in P0).
- The completion files are deleted by the hook after consumption.

**Cross-reference.** This adds `gateway/notify_listener.py` to the gateway changes in §2.3, adds `bootstrap.py` behavior to §2.2, and adds a new ENV var (`HERMES_GATEWAY_NOTIFY_SOCK`) to the spawn env in §3.2. Adds tests `tests/gateway/test_notify_listener.py` and `tests/hooks/test_bootstrap_background_completion.py` to §5.1.

---

## §7a — Still-open questions

These remain genuinely undecided and need answers before the implementation plan locks them in.

1. **Plugin distribution channel.** Marketplace listing, vendored `.tgz`, or git submodule of the existing `hermes-agent` repo? Affects how users install Hermes and how Hermes ships updates.
2. **Multi-modal payload in MCP.** Hermes' `_multimodal: True` tool-result shape (base64 image embedded in JSON) — confirm Claude Code accepts this from MCP tools as inline content.
3. **Skill provenance during migration.** Existing skills under `~/.hermes/skills/` need migration paths to `~/.hermes/plugins/hermes/skills/`. Curator state (provenance, usage telemetry) — does it migrate or reset?
4. **Approval fifo on Windows.** Named pipes work but the path conventions differ. Native Windows already early-beta; confirm the fifo design has a Windows variant. (Applies to Q7's notify socket too — same Windows-portability gap.)
5. **MCP collision policy.** Claude Code exposes `Bash`; `hermes-terminal` exposes a different `mcp__hermes_terminal__exec`. Confirm the model's tool-selection prompt makes the difference clear, or hide `Bash` via permission gating when the terminal target is non-local.
6. **Plugin marketplace authentication.** If Hermes ships through a marketplace, what's the publisher identity story? (Not blocking P0–P5.)

---

## §8 — Non-goals

- **No retention of multi-provider support.** The strategic decision in §1 is final — non-Anthropic transports are deleted.
- **No re-implementation of Claude Code features.** If Claude Code does something natively (compaction, planning, web search, subagents, file ops), we use the native primitive — we don't shadow it.
- **No data migration tooling for transports.** Users on OpenAI / Bedrock / Gemini at the time of cutover migrate to Anthropic credentials; we don't bridge.
- **No standalone `hermes` agent runtime as a fallback path.** Once P5 ships, there's one path — Claude Code with the plugin.
- **No new in-tree memory providers.** Existing in-tree providers stay; new ones ship as standalone plugins (existing policy, unchanged).
- **No breaking changes to the cron / kanban / curator on-disk formats.** Existing data continues to work without migration.
- **No data migration for the SessionDB transcript columns** — they move to `recall.db` via the `Stop` hook on a per-session basis as sessions occur, not via a one-shot migration.

---

## §9 — Risks and mitigations

| Risk | Mitigation |
|---|---|
| Claude Code SDK / plugin surface evolves and breaks the plugin shape | Pin to the SDK / plugin API version in `plugin.json`; CI runs the plugin against the pinned version; an `update` job tracks upstream changes. |
| MCP overhead per tool call (every tool now goes through MCP) | Co-locate MCP servers in the same process via Claude Code's in-process MCP mode where possible; benchmark per-tool latency before P3 cutover. |
| Hook composition order is hard to reason about | `plugins/hermes/hooks/README.md` documents order; `tests/hooks/test_composition.py` enforces it; a `hermes doctor` check verifies order matches the doc. |
| Settings.json drift (config in two places) | `config.yaml` is the single source-of-truth; SessionStart hook regenerates `~/.claude/settings.json` from it at session start. Reverse direction never happens. |
| Subagent semantics drift (Claude Code subagent ≠ Hermes delegate) | P2 maps deliberately; explicit subagent_type → role table in `plugins/hermes/agents/README.md`. |
| Plugin packaging churn (Claude Code plugins API still evolving) | Standalone `hermes` launcher stays a thin shell; if plugin API breaks, the launcher can be updated without touching backend code. |
| Gateway platform regressions during P3 | Per-platform regression test pass before each platform's cutover; one-platform-at-a-time rollout via a config flag. |
| Loss of multi-provider as a community-facing identity for Nous Research | Out-of-scope for this spec — strategic decision belongs to the maintainers. The spec assumes the answer is "yes, drop multi-provider" per the goal statement. |
| Big-bang deletion in P5 hides regressions | P5 is gated on a full release-cycle dogfood; if any flagged regression maps to a deleted file, that file is salvaged and the deletion list is amended. |

---

## §10 — Acceptance criteria

- [ ] `claude --plugin hermes` works on a fresh install with no `hermes-agent` repo present (plugin self-contained).
- [ ] `hermes gateway start` runs the gateway against `claude` subprocesses; all 12+ platforms operate identically from the user perspective.
- [ ] Every safety invariant from the existing security specs (Tirith content scanning, approval hardline + dangerous patterns, OSV malware block, URL safety SSRF, skill content scan, env scrub) holds on the plugin path.
- [ ] Every Hermes-unique surface (memory providers, remote terminal backends, cross-session FTS5 search, Camofox browser, auxiliary side-LLM, cron, kanban, curator) is reachable from a vanilla `claude` session via the plugin.
- [ ] Skills, memory, session search, cron, kanban data on disk continue to work without migration.
- [ ] LOC reduction targets in §2.6 are met after P5.
- [ ] No `hermes-agent`-internal references to `openai`, `bedrock`, `gemini`, `vllm`, `openrouter` remain in the agent-loop / tool-dispatch code path (allowed inside `hermes-aux` MCP only if a future need arises — not in this version).
- [ ] Plugin installs cleanly via `claude plugin install hermes` against the chosen distribution channel (see §7 #1).

---

## §11 — What stays unchanged (forever)

These surfaces are explicitly orthogonal to the agent loop and unaffected by this port:

- All gateway platform adapters (`gateway/platforms/*`).
- Cron scheduler (`cron/`) — invariants intact (3-minute hard interrupt, catchup window, file lock).
- Kanban board (`tools/kanban_tools.py` backend code) — invariants intact (board isolation, tenant namespacing, spawn-fail auto-block).
- Skill curator (`agent/curator.py`) — invariants intact (only touches `created_by: "agent"` skills, pinned-exempt, archive-not-delete).
- Skill provenance / usage telemetry (`tools/skill_provenance.py`, `tools/skill_usage.py`).
- LSP integration (`agent/lsp/*`).
- Insights / analytics / account_usage / usage_pricing.
- i18n / display / onboarding.
- Memory provider plugin framework (`plugins/memory/` — backends preserved; orchestrator collapses into hermes-memory MCP).
- Terminal environment backends (`tools/environments/*`).
- MCP OAuth manager (`tools/mcp_oauth.py`, `tools/mcp_oauth_manager.py`).
- Tool result spillover (`tools/tool_result_storage.py`).
- Profile system (`hermes_constants.py::get_hermes_home`, `_apply_profile_override`).
- The Hermes brand and CLI invocation — `hermes` keeps working as a verb users type; it just now exec's into Claude Code under the hood.

---

## §12 — Design provenance

This spec is forward-looking and explicitly speculative. It depends on:

1. The reverse-engineered specs in `specs/` being accurate (49 of them, all `draft-reverse-engineered`).
2. The Claude Code plugin surface (plugin.json, .mcp.json, settings.json, hooks, commands, agents, skills) staying stable enough to pin against. Claude Code plugins API is currently in active development; this spec captures the design intent against the surface as understood on 2026-05-19.
3. The Nous Research maintainers accepting the strategic shape (multi-provider dropped). If that answer flips, the spec collapses back to the predecessor's "SDK as transport, multi-provider kept" shape.

The phasing is deliberately conservative: each phase ships a working system; if any phase reveals an unacceptable trade-off, the previous phase remains the steady state. P5 is the only phase that requires irrevocable deletions; everything before P5 is additive on top of the existing in-process loop.
