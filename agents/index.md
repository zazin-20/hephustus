---
title: Agents — Pipeline & Role Registry
role: index
updated: 2026-07-04
owner: architect
---

# Agents — Pipeline & Role Registry

This is the index for the `agents/` OKF tree: the roles that build Hephaestus and
the pipeline they run. Each role has a directive file that defines its behavior;
the Orchestrator routes work to the role that owns it (static map in
`hephaestus/integration/routing.py`).

## Role registry

| Role | Directive | Spawned by |
|---|---|---|
| Orchestrator | [orchestrator/claude.md](orchestrator/claude.md) | Human |
| Product Manager | [product-manager/claude.md](product-manager/claude.md) | Orchestrator |
| Architect | [architect/architect.md](architect/architect.md) | Orchestrator |
| Worker | [worker/claude.md](worker/claude.md) | Orchestrator |
| QA | [qa/claude.md](qa/claude.md) | Orchestrator |
| Design System | [design-system/claude.md](design-system/claude.md) | Orchestrator |
| DevOps | [devops/index.md](devops/index.md) | Orchestrator |

## Pipeline

```
User Request
    → Orchestrator        (intake, decomposition, role routing)
    → Product Manager     (scope, journeys, PRD)
    → Architect           (system design, issue specs)
    → Worker              (implementation, one issue at a time)
    → Architect           (handoff review)
    → QA                  (verification, evidence)
    → Log Entry           (completion record)
```

The pipeline is one authored workflow the roles follow by convention — the
Orchestrator dispatches and tracks; each role owns its slice and does not do
another role's work.

## Tree

| Path | Holds |
|---|---|
| `orchestrator/` | Intake + routing; dispatch records under `tasks/`; spawn/environment reference |
| `product-manager/` | Scope, user journeys, PRDs |
| `architect/` | System design ([architect/architecture.md](architect/architecture.md)), issue specs, handoffs, PRD storage, dependency DAG |
| `worker/` | Implementation directive (Codex) + TDD playbook |
| `qa/` | Verification: tests, evidence, bug reports, the test-case catalog |
| `design-system/` | Design tokens + UI guidance |
| `devops/` | Infra / deployment |
| `log.md` | System-level change history (human rollup) |

## Governance model

Governance is user-authored: artifact-spec predicates plus the run-time
governance rules (`G-001`/`G-002`/`G-003`). See
[../docs/design/governance-engine.md](../docs/design/governance-engine.md).
The former hardcoded `S-001..S-006` structural library was removed 2026-06-23.
