---
title: PRD 02 - Artifact Flow, Preflight, and Context Surfaces
status: ready-for-agent
updated: 2026-07-08
owner: architect
integration_order: 2
---

## Problem Statement

The backend already thinks in artifacts, contracts, gates, and compiled context,
but the UI still leaves artifact flow and run readiness under-explained. Edges do
not clearly communicate artifact semantics, invalid bindings are too easy to miss,
preflight trust is too low, and users cannot inspect what context a node will
actually receive before execution.

## Solution

Make artifact movement explicit and legible on the graph, make preflight a
persistent trust-building surface, and expose compiled context as a read-first
inspectable artifact. Edges should communicate artifact identity and compatibility,
preflight should explain graph readiness before a run starts, and context preview
should show the exact inputs to a node without turning the UI into an unbounded
prompt editor.

## User Stories

1. As a workflow author, I want edges to represent artifact movement clearly, so that graph wiring reflects the real runtime model.
2. As a workflow author, I want edge labels to show artifact name and id, so that bindings are recognizable without path memorization.
3. As a workflow author, I want artifacts to stay represented as edges rather than default node types, so that the execution graph remains focused on compute nodes while still showing data flow.
4. As a workflow author, I want artifact flow to branch from an artifact capsule or junction, so that fan-out reads as one produced artifact feeding multiple consumers.
5. As a workflow author, I want multiple downstream edges from one artifact to remain visually separate, so that each consumer path has its own control state.
6. As a workflow author, I want separate visible input ports with real contract names, so that multi-input nodes are self-explanatory.
7. As a workflow author, I want those port labels to be editable, so that the graph reflects evolving contract language.
8. As a workflow author, I want semantic contract changes to invalidate bindings explicitly, so that broken assumptions are visible immediately.
9. As a workflow author, I want pure contract renames to preserve bindings, so that harmless edits do not cause repair churn.
10. As a workflow author, I want one primary output artifact per node in v1, so that authoring stays simpler while still supporting real flows.
11. As a workflow author, I want artifact specs owned by the producing node, so that contract authority is obvious.
12. As a workflow author, I want downstream compatibility fallout to surface immediately when a producer spec changes, so that I can repair the graph before running it.
13. As a workflow author, I want incompatible input/output bindings flagged before run, so that graph errors do not hide until execution.
14. As a workflow author, I want missing artifact inputs to be obvious on the graph, so that partial workflows are easy to diagnose.
15. As an operator, I want clicking an edge to open its own inspector, so that I can inspect the artifact contract and latest produced artifact in context.
16. As an author, I want a persistent preflight dock, so that validation lives beside the graph instead of appearing as a blocking modal.
17. As an author, I want preflight to tell me which nodes are runnable, so that I know what the system can execute immediately.
18. As an author, I want preflight to call out missing inputs, invalid artifact specs, unavailable providers/models, suspicious allowed paths/tools, unreachable nodes, and invalid routing, so that the graph feels trustworthy before I run it.
19. As an operator, I want severity-based preflight with green, amber, and red states, so that I can distinguish readiness, caution, and hard-stop failures.
20. As an operator, I want amber overrides to be per-run only, so that cautious exceptions do not silently become workflow defaults.
21. As an operator, I want red failures to be a hard stop in v1, so that obviously unsafe or invalid runs cannot be pushed through.
22. As a user, I want Run Draft to re-run preflight every time, so that validation always matches the snapshot being launched.
23. As a node author, I want a compiled context preview, so that I can inspect constitution, directives, skills, input artifacts, artifact specs, replayed prior context, and frozen rules before execution.
24. As a node author, I want context preview sections collapsed to summaries by default, so that the surface stays inspectable without becoming unreadable.
25. As a node author, I want to expand into full context text, so that I can audit the exact payload when needed.
26. As a team, we want context preview to be inspectable but not universally editable, so that context control does not turn into prompt sprawl.
27. As a workflow author, I want manual wire editing in Author Mode, so that I can clean up visually complex edges without changing workflow semantics.
28. As a workflow author, I want that manual wire editing to be presentation-only, so that visual cleanup does not mutate the authoritative graph.
29. As a workflow author, I want a reset presentation layout action, so that local wire tweaks can be discarded quickly.
30. As a workflow author, I want snap-to-grid by default, plus alignment/distribution tools for selected nodes, so that layouts stay legible without full auto-layout.

## Implementation Decisions

- Artifacts remain first-class edges, not default node types.
- Artifact identity is centered on named/id'd artifact contracts rather than raw path strings.
- Literal path fallback is removed entirely. Old path-wired workflows are not migrated; they are removed rather than tolerated.
- Schema breaks in this area are taken cleanly instead of soft-deprecated.
- V1 supports one primary output artifact per node and multiple labeled inputs per consumer node.
- Fan-out preserves one shared artifact identity with separate downstream edge instances and separate control states.
- Artifact junctions/capsules are the visual origin for fan-out branches.
- Edge objects are first-class selectable entities with their own inspector state.
- Producer nodes own output artifact specs; edges reference the produced artifact rather than duplicating the contract.
- Validation is split into immediate optimistic checks and slower authoritative checks.
- Preflight is docked and persistent, not modal.
- Amber overrides are per-run only; red failures are not overridable in v1.
- Context preview is a compiled, read-first surface with collapsed summaries and expandable full text.
- Manual wire editing exists only in Author Mode, is purely visual, and persists as personal/session presentation state.
- Node positions remain shared authored state. Wire presentation remains personal/session-local state.
- Artifact junction positions are derived from node layout rather than independently authored.
- Automatic full graph layout is out of scope; simple align/distribute tools and snap-to-grid are in scope.

## Testing Decisions

- Good tests verify binding validity, artifact identity propagation, and preflight severity outcomes from authored graph state.
- Test fan-out as shared artifact identity plus distinct edge states, not as duplicated artifact models.
- Test contract-edit invalidation behavior separately for rename-safe edits and semantic changes.
- Test preflight against representative graph fixtures that cover missing inputs, spec errors, unavailable providers/models, suspicious path/tool settings, and unreachable routing.
- Test context preview by asserting correct compiled-section presence and expansion behavior rather than exact whitespace or formatting details.
- Test manual wire editing as presentation-only state that never mutates workflow execution data.
- Prior art should build on current workflow model/runtime tests and current artifact authoring tests, extending them with graph-level authoring and validation coverage.

## Out of Scope

- Artifact-as-node visual model.
- Legacy workflow migration from path-based bindings.
- Full automatic node layout or auto-tidy graph rearrangement.
- Wire editing that changes runtime semantics.
- Universal context editing.

## Further Notes

- This PRD should land after the canvas command-center work because artifact semantics and preflight need the new graph-native operating surface to read clearly.
- The artifact vocabulary should stay aligned with the existing backend language: node contracts, artifact specs, gates, traces, and compiled context.
