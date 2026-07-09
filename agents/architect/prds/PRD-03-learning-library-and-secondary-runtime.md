---
title: PRD 03 - Learning, Library, and Secondary Runtime Surfaces
status: ready-for-agent
updated: 2026-07-08
owner: architect
integration_order: 3
---

## Problem Statement

Hephaestus needs stronger long-lived control-plane surfaces around learning,
inventory, and reuse. The correction box exists conceptually but lacks a serious
UI, the Library is useful but not yet a typed inventory, workflow templates and
versioned reusable nodes need structure, and the product still needs a clear
secondary path for quick single-node experimentation without reintroducing the old
Console mental model.

## Solution

Add a structured learning surface for correction candidates and frozen rules,
reshape Library into a typed control-plane inventory, and introduce reusable
workflow templates and node-update flows. Keep standalone node execution only as a
clearly secondary ad-hoc runner that inherits graph-runtime semantics instead of
becoming a parallel product.

## User Stories

1. As an operator, I want pending correction candidates to be visible, so that recurring failures can turn into reusable learning.
2. As an operator, I want correction candidates to show provenance from the run and trace that produced them, so that promotions remain evidence-backed.
3. As an operator, I want correction scope choices such as global, machine, workflow, tag, and node, so that rules can be applied at the narrowest valid level.
4. As an operator, I want the UI to default to the narrowest valid scope, so that learning does not overreach by accident.
5. As an operator, I want scope widening to require an escalation protocol, so that broader rules are deliberate.
6. As an operator, I want promoted frozen rules to be inspectable alongside pending candidates, so that active policy and candidate policy are not split across unrelated surfaces.
7. As an operator, I want disable and supersede history, so that rule evolution is visible instead of destructive.
8. As an operator, I want correction markers on the graph, so that learning opportunities are visible in place without reading a separate dashboard first.
9. As an operator, I want those learning markers to be subtler in Author Mode and stronger in Run Mode, so that design and operation each preserve the right focus.
10. As an administrator, I want the Library to hold typed sections for Nodes, Artifacts, Skills, Providers/Engines, Frozen Rules, and Workflow Templates, so that reusable control-plane inventory is structured.
11. As an administrator, I want Providers/Engines to foreground operational readiness rather than duplicate node editing, so that availability and health are easy to inspect.
12. As an author, I want reusable nodes in workflows to reference pinned versions, so that authored graphs do not drift silently.
13. As an author, I want workflow-level review of available node updates, so that upgrade work is centralized and understandable.
14. As an author, I want breaking node updates to stay pinned by default, so that I do not inherit breaking changes accidentally.
15. As an author, I want non-breaking updates reviewed through semantic impact rather than a raw changelog dump, so that upgrade decisions are legible.
16. As an author, I want outdated nodes marked subtly on the canvas, so that staleness is visible without turning every graph into a warning wall.
17. As a workflow author, I want templates to instantiate into editable drafts, so that reusable blueprints accelerate graph creation without locking me into rigid scaffolds.
18. As a workflow author, I want unresolved template placeholders to block run through red preflight, so that incomplete templates cannot execute by accident.
19. As a workflow author, I want templates treated as executable blueprints rather than static diagrams, so that reuse aligns with the real runtime.
20. As a user, I want a clearly secondary single-node runner for quick experiments, so that I can prototype or sanity-check a node without authoring a full workflow.
21. As a user, I want that ad-hoc runner to inherit the same runtime semantics as workflow runs, so that standalone testing does not drift from real execution behavior.
22. As a user, I want ad-hoc execution to remain visibly secondary to workflow execution, so that the product does not slide back into a console-first mental model.
23. As a user, I want provider and engine readiness surfaced before I run nodes, so that environment issues are visible in inventory as well as preflight.
24. As a team, we want inventory, learning, and templates to use the same graph/runtime vocabulary as the rest of the product, so that the control plane feels coherent.

## Implementation Decisions

- Correction promotion defaults to the narrowest valid scope.
- Scope escalation requires evidence-backed widening plus explicit confirmation.
- Excessive retry loops auto-surface correction candidates.
- Learning markers appear on-canvas in both modes, with stronger prominence in Run Mode.
- The Library is restructured into typed control-plane inventory sections: Nodes, Artifacts, Skills, Providers/Engines, Frozen Rules, and Workflow Templates.
- Providers/Engines emphasize readiness, availability, and operational status rather than becoming a second place to edit node contracts.
- Workflow templates are executable blueprints with placeholders.
- Instantiating a template creates an incomplete-but-editable draft. Unresolved placeholders are treated as red-preflight blockers.
- Placed workflow nodes reference pinned library-node versions.
- Update review is centralized at the workflow level, though individual updates may still be possible.
- Breaking updates stay pinned by default; upgrade-and-repair is explicit opt-in.
- Update review is semantic and impact-oriented, not changelog-oriented.
- Standalone execution remains in v1 only as a secondary ad-hoc runner.
- Recommended direction: present standalone execution as a temporary one-node graph using the same runtime semantics, so Console does not re-emerge as a peer mental model. This remains a recommended assumption pending a future explicit lock if product direction changes.

## Testing Decisions

- Good tests verify policy provenance, scope defaults, escalation requirements, and supersede/disable history from user-visible behavior.
- Test correction candidate generation from retry patterns and failure metadata rather than implementation-specific event plumbing.
- Test library inventory as typed data and capability surfaces, not as incidental list rendering.
- Test template instantiation by asserting placeholder propagation, editable draft creation, and red-preflight blocking until resolution.
- Test node-version pinning and update review through authored workflow behavior: stale markers, impact summaries, and explicit upgrade actions.
- Test standalone runner parity at the runtime-contract level so ad-hoc runs cannot drift from workflow semantics.
- Prior art should build on existing artifact/node storage tests and workflow runtime tests, with new coverage around inventory metadata and learning-state transitions.

## Out of Scope

- Template-to-instance provenance synchronization beyond basic instantiation.
- Auto-follow behavior.
- Shareable filter state across users or links.
- Full policy automation that promotes broad-scope rules without human confirmation.
- A return to role-based spawn cards as a primary runtime pattern.

## Further Notes

- This PRD deliberately lands last because it depends on the canvas-first runtime, artifact semantics, and preflight/context surfaces from the first two PRDs.
- If a future decision reverses the ad-hoc runner recommendation, that should be captured as a follow-up design note before implementation.
