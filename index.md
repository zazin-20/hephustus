---
title: Hephaestus Agent System
version: 0.2.0
status: active
created: 2026-06-21
updated: 2026-06-21
owner: architect
---

# Hephaestus — Agent System Index

Hephaestus is the OKF system manager and agent compliance layer for multi-repo,
multi-tool AI-assisted development. It sits above the agent system and manages
the ground truth that all agents operate from.

## Purpose

Hephaestus does two things:

1. **OKF Management** — create, edit, and maintain the `agents/` knowledge tree
   that defines how every role-playing agent behaves
2. **Compliance Monitoring** — track whether agents are following their directives,
   flag violations, and surface corrections back into the OKF system

Hephaestus does NOT orchestrate agents directly. The Orchestrator agent (via
`codex-cc`) handles spawning. Hephaestus manages the knowledge system those
agents consume.

## System Map

```
hephaestus/
├── agents/               ← this OKF tree (you are here)
│   └── index.md
├── spec/
│   ├── architecture.md   ← full system design
│   └── rules/
│       └── structural.md ← built-in compliance rules
└── log.md                ← system-level change history
```

## Core Surfaces (MVP)

| Surface | Purpose |
|---|---|
| OKF Editor | Create / edit / view any file in the `agents/` tree |
| Pipeline Dashboard | Visual state of every work item across the full pipeline |
| Compliance Monitor | Active rule checks, violation flags, correction box |
| Code Viewer | Read-only browse of the multi-repo codebase |

## Agent Role Registry

These are the role-playing agents Hephaestus monitors. Each role has a directive
file that defines its behavior. Hephaestus tracks compliance against these files.

| Role | Directive File | Tool | Spawned By |
|---|---|---|---|
| Orchestrator | `agents/orchestrator/claude.md` | Claude Code | Human |
| Product Manager | `agents/product-manager/claude.md` | Claude Code | Orchestrator |
| Architect | `agents/architect/architect.md` | Claude Code | Orchestrator |
| Worker | `agents/worker/claude.md` | Codex (via codex-cc) | Orchestrator |
| QA | `agents/qa/claude.md` | Claude Code | Orchestrator |
| Designer | `agents/design-system/claude.md` | Claude Code | Orchestrator |
| DevOps | `agents/devops/index.md` | Claude Code | Orchestrator |

## Work Pipeline

The canonical flow that Hephaestus monitors for compliance:

```
User Request
    → Orchestrator (intake, task breakdown, role routing)
    → Product Manager (scope, journeys, PRD)
    → Architect (system design, issue spec creation)
    → Worker (implementation, one issue spec at a time, TDD)
    → Architect (handoff review)
    → QA (verification, evidence)
    → Log Entry (completion record)
```

Traceability artifacts at each stage:

| Stage | Artifact Location |
|---|---|
| Issue specs | `agents/architect/issues/` |
| Handoffs | `agents/architect/handoffs/` |
| PM decisions | `agents/product-manager/readme.md` |
| QA evidence | `agents/qa/evidence/` (per-issue records) |
| Completion log | `agents/log/` (per-issue records; `agents/log.md` is the human rollup) |

## Integration Points

| System | Integration Method |
|---|---|
| Claude Code | Claude Agent SDK (Python) — session + subagent management |
| Codex | MCP server (stdio / JSON-RPC 2.0) via codex-cc skill |
| OKF files | Direct filesystem read/write on `agents/` tree |
| Codebase repos | Read-only filesystem access for Code Viewer |

## Related Documents

- [spec/architecture.md](../spec/architecture.md) — full system design
- [structural.md](structural.md) — the governance model (user-authored artifact-spec predicates + the run-time governance G-rules; the hardcoded S-001..S-006 library was removed 2026-06-23)
- [log.md](../log.md) — change history
