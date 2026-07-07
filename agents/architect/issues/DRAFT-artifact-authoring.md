# DRAFT — Artifact authoring: author an artifact definition and connect it to a node

> **OPENED as [#29](https://github.com/zazin-20/hephustus/issues/29)
> (2026-07-07).** The `## What to build` / `## Acceptance criteria` /
> `## Blocked by` sections below were used as the issue body verbatim. This file
> remains the local spec-of-record elaboration; the GitHub issue is now the
> definition of done for the Worker.

**Owner:** one dedicated Worker (see `issue-dag.md`)
**Routing:** PM framed (`product-manager/todo/artifact-spec-authoring.md`);
Architect grilled + spec'd; Worker implements; QA verifies.
**Relates to:** #28 (node authoring — this compounds directly on it); ADR-0003.

## What to build

Make the **artifact definition** authorable from the UI and bindable to a node,
so a workflow author can define a quality gate without hand-writing the predicate
DSL. Today (post-#28) a node's `outputs`/`inputs` can bind to an artifact-spec
**path**, but the spec markdown itself — required headings, best practices,
antipatterns, examples, required-field checks — must be hand-authored. This issue
closes that gap.

### Ground truth (verified in code, 2026-07-07)
- **The runtime already does both halves of the loop — do NOT rebuild it.**
  - `integration/context.py` (~line 187) already renders a node's `outputs`
    spec files into the producing node's system prompt under "Artifact specs" —
    i.e. the producer already *references the artifact when generating*.
  - `workflow_runtime.py` exit gate `WF-OUT-*` already runs
    `artifact_spec.check_artifact` on handoff — the *deterministic check on the
    way out* already exists.
  - So this issue adds **authoring + a thin index + id-resolution only.** No
    gatekeeper or context-assembly behavior change.
- **Artifact specs are markdown** parsed by `hephaestus/artifact_spec.py`:
  YAML frontmatter + a `## Predicates` section (`non_empty(...)`,
  `min_items(...)`, `has_section(...)`, `matches(...)`, `has_field(...)`) +
  named `##` heading sections + a `## Good Looks Like` section. Sections the
  parser does not recognize are ignored by the checker but still flow as context
  to the producing node — so **antipatterns/examples are free** (extra prose
  sections, no parser change).
- **No spec home or store exists today.** `okf_layout.py` has issues/handoffs/
  qa/workflows/identities/skills — **no artifacts dir**; spec files are loose,
  referenced by raw path in `node.outputs`. `store/` has no artifacts DAL.

### Scope, in three layers
1. **DAL + layout — `store/artifacts.py` (thin index) + a canonical home.**
   - Add `okf_layout.artifacts_dir()` → `<agents_root>/artifacts/` (add to
     `required_directories`).
   - `store/artifacts.py`: `create_artifact`, `get_artifact`, `list_artifacts`,
     `update_artifact`, `delete_artifact`. The DB row is a **thin index** —
     `{artifact_id, name, path, tags, created_at}` — NOT the content. On
     create/update the DAL **composes the markdown** (frontmatter + `## Predicates`
     from the required-heading flags + the heading sections + `## Good Looks Like`
     + `## Antipatterns` + `## Examples`) and writes it to
     `artifacts_dir/<artifact_id>.md`; the file is the source of truth, the row
     is the stable, rename-safe reference. Follows the typed-DAL invariant
     (`.hephaestus/state.db` written only through `store/`).
2. **id-resolution — bind by id, stay backward-compatible with #28.**
   - Where `node.outputs`/`inputs` entries are resolved to paths
     (`context.py::_resolve_declared_path`, `workflow_runtime.py::_resolve_path`),
     resolve an entry as an `artifact_id` via the index first; fall back to
     treating it as a literal path if it is not a known id. Existing #28
     path-based bindings keep working unchanged.
   - Bridge + `api.js`: `create_artifact`/`update_artifact`/`list_artifacts`/
     `delete_artifact`, full payloads, behind the `window.pywebview?.api?.…`
     guard.
3. **UI — a Create/Edit Artifact surface + bind-in-node.**
   - A first-class "Artifacts" catalog (parallel to Nodes) with a create/edit
     form: `name`, a required-headings list editor (each heading + a
     "required" toggle → emits `non_empty`/`has_section`), best practices,
     antipatterns, examples (text areas), and `min_items` per heading (optional).
   - The node form's `outputs`/`inputs` editors become **artifact pickers**
     (select from the catalog, bind by id) instead of raw path entry — while
     still accepting a literal path for backward compatibility.
   - Refresh catalogs after save so a new artifact is immediately bindable.

### Explicitly deferred (fast-follow, NOT this issue)
- Richer predicates in the form: `matches` (regex) and frontmatter `has_field`.
- Live preview (running `check_artifact` against a sample doc in the form).
- Any external spec sanity-checker module (e.g. sphinx-style) — files-in-tree
  keeps that door open for later.

## Acceptance criteria
- A user can **author an artifact** from the UI — name, required headings (each
  with a required toggle), best practices, antipatterns, examples — and it is
  persisted as a markdown file under `agents/artifacts/<id>.md` in the
  `artifact_spec.py` format, with a thin index row in the operational store.
- The required-heading toggles produce a valid `## Predicates` section
  (`non_empty`/`has_section`, plus `min_items` where set) that
  `artifact_spec.load_artifact_spec` parses without error.
- A user can **connect the artifact to a node** by selecting it from the catalog
  in the node form (bind by `artifact_id`); the node persists the binding.
- On a workflow run, a node bound to the artifact (a) has the artifact injected
  into its producing context (existing `context.py` path) and (b) is gated by
  the existing `WF-OUT-*` check — demonstrated by an integration test or QA
  trace. **No runtime code adds new gating behavior** — this criterion proves the
  binding resolves into the already-built machinery.
- Existing #28 literal-path `outputs`/`inputs` bindings keep working unchanged
  (id-resolution falls back to path).
- `update_artifact`/`delete_artifact` round-trip; renaming an artifact's `name`
  does not break a node binding (binding is by id, not name/path).
- Full backend suite green; `npm --prefix frontend run build` green. Product
  code touched only in: `store/artifacts.py` (new), `okf_layout.py`,
  `integration/context.py` + `workflow_runtime.py` (id-resolution seam only),
  `desktop.py`, `frontend/src/api.js`, and new frontend artifact-form/catalog
  component(s). No existing test weakened or deleted.

## Blocked by
- **Nothing.** Builds only on merged work: #28 (node authoring / outputs binding),
  the artifact-spec engine, `context.py` injection, and the `WF-OUT-*` gate — all
  on `main`. Independent of dynamic fan-out and context compression.
