# PRD: Hephaestus Coordinator Interface

**Version:** 1.0  
**Date:** 2026-06-21  
**Status:** Ready for implementation

---

## Problem Statement

The user is building multi-agent software pipelines using Claude and Codex, but has no unified interface to manage them as a coordinated system. The current Agent tab is a single-run, fire-and-forget panel: one agent at a time, no persistent conversation history, no visibility into tool calls the agent made, and no mechanism to chain agents through a structured pipeline. When one agent finishes, the user must manually re-configure the next agent from scratch.

The compliance system runs in the background but surfaces its output in a separate tab, disconnected from the agent workflow. There is no path from a compliance violation to a corrective action. There is no agent identity — it is impossible to know which agent wrote which file, across which sessions, or in service of which issue.

The result is a system where the user is the coordinator: manually context-switching between agents, copy-pasting task descriptions, and losing conversation history between sessions.

---

## Solution

Replace the Agent tab with a **Coordinator interface** — a two-panel workspace where the user manages named **agent profiles**, holds persistent conversations with each agent, and drives a structured multi-agent pipeline through an **Orchestrator** agent.

The Orchestrator is the user's primary conversation partner. When it decides the next stage of work should begin, it emits a structured handoff marker. Hephaestus detects the marker, runs the outgoing agent's per-profile exit compliance check, and presents a contextual **Spawn** button pre-filled with the task. The user confirms; the next agent starts.

Every agent action across the codebase is recorded in a **trace log** keyed to the agent's identity card. Every conversation turn is stored for replay. Compliance violations surface as **push notifications** with a one-click path to the **Correction Box**, replacing the dedicated compliance tab.

---

## User Stories

1. As a user, I want to create a named agent profile with a role, working directory, and rule set, so that I can reuse it across sessions without re-configuring from scratch.
2. As a user, I want each agent profile to have a unique identity card, so that I can audit exactly which agent made which changes across the codebase.
3. As a user, I want to see all my agent profiles in a sidebar with live status indicators, so that I can tell at a glance which agents are running, idle, or done.
4. As a user, I want to click a profile and see the full conversation history from previous sessions, so that I can pick up where I left off without losing context.
5. As a user, I want to send a message to the active agent directly from the conversation panel, so that I can have a continuous back-and-forth rather than re-launching one-shot runs.
6. As a user, I want to see tool calls (file reads, file writes, bash commands) shown inline in the conversation thread, so that I can follow exactly what the agent is doing without reading raw logs.
7. As a user, I want to talk to the Orchestrator to describe a feature, so that it can plan the work and decide which agent role should handle it.
8. As a user, I want the Orchestrator to signal when it is ready to hand off work to the next agent, so that I do not have to manually judge when to proceed.
9. As a user, I want a Spawn button to appear when the Orchestrator is ready, pre-filled with the task and role it specified, so that I do not have to copy-paste the task myself.
10. As a user, I want the Spawn button to show a compliance check result before I confirm, so that I know whether the outgoing agent has met all its exit responsibilities.
11. As a user, I want to see which per-profile exit rules failed when the spawn is blocked, so that I can direct the agent to fix the gap before proceeding.
12. As a user, I want compliance violations to appear as push notifications rather than in a separate tab, so that they surface in context without interrupting my workflow.
13. As a user, I want to click "Correct" on a compliance notification and immediately open a Correction Box, so that I can capture my feedback while the context is fresh.
14. As a user, I want the Correction Box to be pre-filled with the violation, agent, and issue details, so that I only need to type the corrective note.
15. As a user, I want corrections to be persisted to a structured log, so that I can review them later and promote them to directives or rules.
16. As a user, I want every file the agent touches — in the OKF tree or anywhere in the codebase — to be recorded in a trace log keyed to the agent's identity, so that I have a full audit trail per session.
17. As a user, I want to assign different rule sets to different profiles of the same role, so that an Architect on one project can have stricter exit criteria than one on another.
18. As a user, I want to add a new exit rule to a profile without touching the engine code, so that I can evolve compliance expectations as the project matures.
19. As a user, I want the conversation history to persist across app restarts, so that I can close and reopen the app without losing agent context.
20. As a user, I want the Worker agent to be spawned from the Orchestrator's handoff decision, not by me manually switching tabs and re-entering a task, so that the pipeline flows without me being the glue.
21. As a user, I want to inspect any agent's conversation thread without interrupting it, so that I can monitor work in progress without stopping it.
22. As a user, I want to see which issue an agent is working on next to its profile card, so that the coordinator sidebar is informative at a glance.
23. As a user, I want the Orchestrator to know the current state of the OKF (open issues, violations) when I start a conversation, so that its planning is grounded in reality.
24. As a user, I want each agent profile to show a timeline of sessions with dates, so that I can navigate to a past session and review what happened.
25. As a user, I want the Code tab to remain accessible alongside the Coordinator, so that I can browse the codebase while managing agents.

---

## Implementation Decisions

### Navigation restructure
The three-tab layout (Compliance, Code, Agent) collapses to two tabs: **Coordinator** and **Code**. The Compliance tab is removed as a standalone view. Compliance output is surfaced exclusively through push notifications (toasts) triggered by the existing watchdog pipeline. The compliance delta push mechanism (`window.__hephaestus_push__`) is extended to fire toast events when violations are detected, in addition to updating the (now background-only) snapshot.

### Agent profile store (`profiles.py`)
A new deep module manages agent profiles backed by a `profiles.toml` file at the OKF root. It provides CRUD operations with a simple interface:
- `create(name, role, working_dir, rules, model?, okf_root?) -> Profile`
- `list() -> list[Profile]`
- `get(agent_id) -> Profile`
- `delete(agent_id)`

Required fields at creation: `name`, `role`, `working_dir`, `rules`. Auto-generated on creation: `agent_id` (short UUID, role-prefixed e.g. `arch-001`), `created_at`. Optional: `model`, `okf_root` (defaults to working_dir if absent).

The profile store is the single source of truth for profile configuration. It does not store session state — that lives in history and trace files.

### Agent identity card (`identity.py`)
Each profile has an A2A-compatible identity card written to `agents/identities/{agent_id}.json` when the profile is created. Schema:

```json
{
  "agent_id": "arch-001",
  "name": "Architect - Hephaestus",
  "role": "architect",
  "created_at": "2026-06-21T14:00:00Z",
  "capabilities": ["write_spec", "write_handoff"],
  "sessions": []
}
```

The `sessions` list is appended each time a new session starts. The card is the provenance anchor — every OKF file written by this agent carries `authored_by: arch-001` in its frontmatter. The identity module provides `load(agent_id)`, `append_session(agent_id, session_id)`.

### Conversation history (`history.py`)
Conversation turns are appended to `agents/history/{agent_id}/{session_id}.jsonl` — one JSONL line per turn. Three turn types:

```json
{"ts": "...", "role": "user",      "text": "Review the handoff"}
{"ts": "...", "role": "assistant", "text": "Here is my review...", "kind": "text"}
{"ts": "...", "role": "tool",      "text": "read_file(handoffs/003.md)", "kind": "tool"}
```

The module provides `append(agent_id, session_id, turn)` and `load(agent_id, session_id) -> list[Turn]`. On profile open in the UI, the latest session's history is loaded and replayed into the conversation panel. History is persisted before and after each `AgentService.run()` call — user messages are written before the run starts, agent events are written as they stream.

### Trace log (`tracer.py`)
Every tool event from the agent stream is parsed and appended to `agents/trace/{agent_id}/{session_id}.jsonl`. The tracer intercepts `AgentEvent` where `kind == "tool"`, extracts the action type and target file path, and writes:

```json
{"ts": "...", "agent_id": "arch-001", "session_id": "sess_abc", "issue_id": "issue-004", "action": "write_file", "target": "hephaestus/graphview.py", "role": "architect"}
```

The tracer is a stateless writer — `append(entry: TraceEntry)`. It is called from the streaming path in `AgentService`, not from the Bridge, so it runs for all agent sessions regardless of UI state.

### Handoff marker parser (`handoff_parser.py`)
A pure module that scans agent event text for the structured handoff signal the Orchestrator is instructed to emit:

```json
{"handoff": {"role": "architect", "task": "Write the spec for issue-004", "issue_id": "issue-004"}}
```

Interface: `parse(text: str) -> HandoffMarker | None`. Called in the streaming path for Orchestrator sessions only. When a marker is detected, the event is emitted to the UI as a special `handoff` kind so the frontend can render the Spawn button.

### Per-profile exit rules (`rules/exit.py`)
A new rule layer separate from the then-existing structural rules (`S-001..S-006`, since removed 2026-06-23 — see the note at the end of this section). Exit rules are named Python functions with a standard signature:

```python
def has_issue_spec(ctx: OKFContext, issue_id: str) -> RuleFailure | None: ...
def has_handoff_doc(ctx: OKFContext, issue_id: str) -> RuleFailure | None: ...
```

A TOML config (`rules/exit_rules.toml`) maps profile rule names to their implementations. The evaluator `check_exit_rules(profile, issue_id) -> list[RuleFailure]` builds the OKF context and runs only the rules declared in the profile's `rules` list. Adding a rule = one TOML entry + one small Python function.

Exit rules are the per-profile, per-handoff gate layer.

> **Superseded (2026-06-23):** this section assumed the hardcoded `S-001..S-006`
> structural library ran as a background compliance layer. That library was
> removed; governance is now user-authored artifact-spec predicates plus the
> run-time governance rules (`G-001`/`G-002`/`G-003`), run by the generic
> `hephaestus/rules/registry.py`. See `docs/design/governance-engine.md`.

### Correction Box (`corrections.py`)
Corrections are appended to `agents/hephaestus/corrections.jsonl`:

```json
{"ts": "...", "violation": "G-001", "agent_id": "arch-001", "issue_id": "issue-004", "note": "Agent wrote outside its allowed paths."}
```

Interface: `append(correction: Correction)`. No promotion logic at this stage — the file is the raw feedback queue for manual review. Promotion to directives or rules is Phase 3.

### Bridge extensions (`desktop.py`)
The Bridge gains new methods exposed to JS via `js_api`:

- `list_profiles() -> list[dict]` — all profiles with current status
- `create_profile(name, role, working_dir, rules, model?, okf_root?) -> dict`
- `delete_profile(agent_id)`
- `get_history(agent_id, session_id?) -> list[dict]` — latest session if session_id omitted
- `send_task(agent_id, prompt, issue_id?) -> dict` — wraps existing start_agent with profile resolution
- `check_exit_rules(agent_id, issue_id) -> list[dict]` — runs exit rule check, returns failures
- `save_correction(violation, agent_id, issue_id, note) -> None`
- `get_trace(agent_id, session_id) -> list[dict]`

### AgentService streaming extension
The existing `_stream_agent` coroutine in `DesktopApp` is extended to:
1. Write user turn to history before starting
2. Write each `AgentEvent` to history as it streams (assistant or tool turn)
3. Call tracer for every tool event
4. Parse handoff markers for Orchestrator sessions and emit a `handoff` kind event to the UI
5. Append session_id to the identity card on first result event

### Frontend: Coordinator layout
The Coordinator is a two-panel layout:
- **Left panel (roster):** profile cards showing name, role, status badge (idle/running/done/error), active issue. "Add profile" button at the bottom.
- **Right panel (conversation):** chat-style thread showing user, assistant, and tool turns. Input field at the bottom. When a handoff marker is detected, a Spawn card appears inline in the thread showing the target role, task, and exit rule check result.

The Spawn button is green when all exit rules pass. When rules fail, the button is amber and expands to list which rules failed with fix hints. The user can still force-spawn (override) but the failures are visible.

### Toast notification system
A `ToastProvider` wraps the app root. The compliance push channel (`window.__hephaestus_push__`) is extended to carry a `notifications` array alongside the snapshot. Each notification has: `id`, `severity`, `rule_id`, `issue_id`, `agent_id`, `message`. Toasts auto-dismiss after 8 seconds unless the user interacts. "Correct →" opens the Correction Box pre-filled. "Dismiss" removes the toast and marks the notification acknowledged in the session (not persisted — violations re-fire if still present on next watchdog cycle).

### OKF tree additions
New directories created on first use:
- `agents/identities/` — agent identity cards
- `agents/history/` — per-agent, per-session conversation logs
- `agents/trace/` — per-agent, per-session action traces
- `agents/hephaestus/` — system-level files (corrections.jsonl)

All are within the `agents/` tree, covered by the existing watchdog and browsable in the Code Viewer.

---

## Testing Decisions

**What makes a good test:** test the external behaviour of a module through its public interface, not its implementation. A good test sets up a state, calls the interface, and asserts on the observable output — a returned value, a written file, an emitted event. Do not assert on internal data structures or private method calls.

**Prior art in this codebase:** `tests/test_monitor.py` (stateful rescan + diff via `ComplianceMonitor`), `tests/test_watch.py` (real filesystem end-to-end via watchdog), `tests/test_integration.py` (schema regression + session resume via `AgentService`), `tests/test_desktop_agent.py` (real background loop with `EchoRunner` + fake window).

**Modules to test:**

- `profiles.py` — create/read/list/delete cycle; assert agent_id is auto-generated and role-prefixed; assert required fields are enforced; assert optional fields default correctly.
- `identity.py` — card written to correct path on profile creation; `append_session` adds to sessions list; load returns correct card.
- `history.py` — append writes JSONL; load returns turns in order; latest-session lookup returns correct session when multiple exist.
- `tracer.py` — tool events are captured; non-tool events are ignored; target path extraction is correct for `write_file`, `read_file`, `bash` action types.
- `handoff_parser.py` — valid handoff JSON in text returns `HandoffMarker`; JSON embedded mid-text is found; malformed JSON returns `None`; non-handoff JSON returns `None`.
- `rules/exit.py` — each named rule passes on a clean fixture and fails on a fixture missing the expected artifact; `check_exit_rules` returns only failures for the declared rule set; unknown rule name raises a clear error.
- `corrections.py` — append writes JSONL; multiple corrections accumulate in order; file is created if absent.

**Not tested at unit level (covered by integration or manual verification):** Bridge methods (thin adapters), frontend components, PyWebView window lifecycle.

---

## Out of Scope

- **Automatic pipeline execution** — the Orchestrator signals readiness, the human confirms. No auto-spawning of agents without user confirmation.
- **Codebase graph view** — deferred. The trace log built here is the data foundation for the future graph overlay, but the graph rendering itself is out of scope.
- **Correction promotion** — capturing corrections to `corrections.jsonl` is in scope; automatically promoting them to directives or generating new rules from them is Phase 3.
- **Behavioral (LLM-judged) rules** — the exit rule layer uses Python functions only. LLM-evaluated rules (e.g. "did the worker follow the TDD playbook?") are Phase 3.
- **Multi-user or remote access** — single-user desktop only.
- **Agent-to-agent communication** — agents do not talk to each other directly. All coordination flows through the human via the Coordinator.
- **Packaging / distribution** — PyInstaller bundles are not part of this PRD.

---

## Further Notes

- The A2A identity card format is intentionally compatible with the Agent-to-Agent protocol spec (Google, 2025). Full A2A interoperability (remote card discovery, capability negotiation) is not implemented, but the card schema leaves the door open without requiring migration.
- The `authored_by` frontmatter field on OKF documents requires that agents producing OKF files include it. This is a directive concern, not an engine concern — the compliance rules can check for its presence but cannot enforce it on agent output. This should be documented in the role directives (e.g. `agents/architect/architect.md`) when those are authored.
- The handoff marker convention (`{"handoff": {...}}`) must be included in the Orchestrator's directive file. Without it, the Orchestrator will not emit parseable handoffs and the Spawn button will not appear.
- Session history and trace logs are append-only. No compaction, rotation, or deletion logic is included. At MVP scale this is negligible.
- The corrections file is the seed of the self-improving OKF loop — the most differentiated feature in the long-term vision. Keeping the schema clean now (structured JSONL, not prose) means Phase 3 promotion logic can be built without a migration.
