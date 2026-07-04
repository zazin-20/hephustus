---
title: Orchestrator
role: orchestrator
updated: 2026-07-03
owner: architect
---

# Orchestrator

Navigation page for the Orchestrator role.

The Orchestrator is the **entrypoint and routing layer**. It takes a user request,
breaks it into work, and routes each piece to the role that owns it. It does not
design systems, write specs, implement, or verify — it dispatches and tracks.

## Contents

| Path | Holds |
|---|---|
| `claude.md` | The Orchestrator directive (behavior contract) |
| `spawn-environment.md` | Verified shell/CLI compatibility per subagent type; required reading before writing any dispatch prompt |
| `tasks/` | Routed tasks, one file per dispatched unit of work |
| `tasks/completed/` | Tasks that have been closed out |

## Where work goes next

Routing is static and role-based (see `hephaestus/integration/routing.py`):

| Kind of work | Routed to |
|---|---|
| Scope / journeys / backlog | Product Manager |
| System design / issue specs | Architect |
| Implementation | Worker (Codex) |
| Verification | QA |
| Design tokens / UI guidance | Design System |
| Infra / deployment | DevOps |

See [../index.md](../index.md) for the full pipeline and role registry.
