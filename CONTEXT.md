# Context

- `Engine` (Section 2, Section 7.1) - a `{provider, model, effort}` config a node runs on; the node's executor names one, it is stateless from Hephaestus's view, and it is swappable under a node.
- `Provider` (Section 2, Section 7.1) - a pluggable adapter behind the registry that an engine resolves to, bundling `runner`, raw->turn `normalize_event`, `flags(contract)`, model discovery, and `owns_model`.
- `Node` (Section 2, Section 7.1) - the unit you run: an executor plus governance that declares input/output artifact specs, scope, required skills, attached rules, context policy, and tags; reusable standalone or placed in a graph.
- `Executor` (Section 7.2) - `executor: {kind, ...}` on a node, where `kind: "engine"` names `{provider, model, effort}` and `kind: "builtin"` names a builtin such as `condition` or `notify`.
- `Artifact` (Section 2) - a produced document, and the only thing that crosses an edge.
- `ArtifactSpec` / `Artifact-spec` (Section 2, Section 7.1) - a user-authored document contract defining an artifact type through frontmatter scalars, named sections, composed predicates, and "good looks like" exemplars; it is both the deterministic gate checklist and the directives injected into the generating agent.
- `Workflow` (Section 7.1) - a graph of placements (a node at a position) plus edges (output->input routing) and per-edge guards.
- `Edge` (Section 2, Section 7.3) - an allowed transition between nodes that carries an artifact, never a transcript; in the resolved architecture it is routing only.
- `Guard` (Section 7.3) - an optional per-edge deterministic predicate or `condition` builtin used for branching.
- `Gate` (Section 2, Section 7.3, Section 7.4) - the check at a node boundary, derived from the node's declared I/O specs: entry gate requires valid inputs and correctly scoped context, and exit gate requires required outputs plus passing predicates and enforced skill obligations.
- `Constitution` (Section 7.1) - authored directive text per scope.
- `Constitutional Directives` / constitution layers (Section 2, Section 3.5, Section 7.7) - directives always present in node context, layered by scope; runs collect matching directive and frozen-rule rows from the address chain with narrowest-wins.
- `Scope address` / scope-addressed state (Section 7.1, Section 7.7) - the "instance" is an address, not an entity; run state is matched along `global -> machine -> workflow -> tag -> node(instance)`.
- `Marker` / marker protocol (Section 3.7, Section 7.5, Section 7.6) - a reserved line-anchored sentinel plus strict JSON typed signal that Hephaestus scans from assistant text and tool-call commands to capture handoffs, skill completion, distillation candidates, and related signals.
- `Distillation` (Section 2, Section 3.7) - turning a successful trace into a frozen rule through the alignment/learning loop.
- `Frozen rule` (Section 2, Section 3.7, Section 7.8) - a learned directive or deterministic constraint injected into the constitution at a chosen scope, stored with provenance and superseded by `(topic-key, scope)`.
- `Run` / `ExecutionContract` (Section 7.1, Section 7.8) - a run is one node execution, and its resolved immutable `ExecutionContract` is the derived governed run spec containing engine, scope, allowed paths, resolved context, actual input artifacts, `actual_model`, trace, produced artifacts, gate verdicts, and status.
- `Tags` (Section 7.1, Section 7.7) - free-form many-to-many grouping on a node that replaces `role`; rules can be scoped to a tag.
