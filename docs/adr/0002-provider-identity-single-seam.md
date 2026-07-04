# ADR-0002: Provider Identity — Single Resolution Seam, Registry-Only Keys

**Status:** Accepted
**Date:** 2026-07-04
**Owner:** architect

## Context

`governance-engine-revised.md` §7.1 and audit #1/#2 call for providers to be
**pluggable adapters behind one registry**, with the closed `Tool` enum
becoming registry keys so a new provider (the doc's own `gemini_cli` example)
is *one module, registered* — not an edit in several places. The
`ProviderRegistry` (`hephaestus/integration/providers.py`) already exists and
correctly bundles `{runner, normalize_event, flags, discover_models,
owns_model}` per provider; runner dispatch in `AgentService.run()` is already
string-keyed through `provider_key(...)` and `registry.runners()`.

A `/improve-codebase-architecture` pass (2026-07-04), grilled by the Architect,
found the migration is substantially done but two seams were never finished, and
§8 lists "Provider registry" as a decision that was never formally recorded.
This ADR records the decision and scopes the finish work. Two concerns, both
about *who owns provider identity*, at two altitudes:

### Concern 1 — the provider-resolution fallback chain is written out four times

The rule "given a model and fallbacks, which provider?" —
`registry.provider_for_model(model) or task.provider or node.provider` — is
inlined at four sites:

- `contract_resolution.resolve()` (the sole `ExecutionContract` constructor, audit #2)
- `AgentService.begin()` — which then *immediately* calls `resolve_contract(...)`,
  so the identical chain runs twice on the same inputs
- `AgentService.resolve()` — the CLI `--echo` preview path (no contract built)
- `AgentService._resolve_node()` — runs *before* any `Node` exists (uses the
  provider to create the node), a genuine before-contract case

Three of the four cannot be collapsed into "read `.provider` off the resolved
contract" because they legitimately need the provider before a contract exists.
The real defect is that the *rule itself* lives in four copies: a fifth
tiebreaker could be added to one and missed in the others, and
`begin()` recomputes what `resolve_contract` is about to compute anyway.

### Concern 2 — the closed `Tool` enum is a vestigial shim with one real limiter

`Tool` (`routing.py`, self-described "compatibility enum") no longer drives
dispatch — that goes through the registry by string key. It survives as
identity/display (`ClaudeRunner.tool`, `PreparedRun.tool: Tool | str`,
`_display_tool`) plus one genuinely functional limiter: the CLI
`choices=[tool.value for tool in Tool]` (`service.py`) would **reject** a
registered `gemini_cli` even though the registry and dispatch would handle it.
That single line is the actual gap between "closed enum" and §7.1's "one
module, registered." A lingering compat alias with no removal trigger is itself
an antipattern, so the enum is removed rather than kept.

## Decision

**Make provider identity a single seam owned by the registry, and delete the
`Tool` enum.**

1. **One provider-resolution rule.** Add
   `ProviderRegistry.resolve_provider(model, *fallbacks) -> str | None`:
   ```python
   def resolve_provider(self, model, *fallbacks):
       return self.provider_for_model(model) or next((f for f in fallbacks if f), None)
   ```
   It generalizes the existing `provider_for_model` (which is `resolve_provider(model)`
   with no fallbacks). All four sites call it instead of inlining the chain:
   - `resolve()` / `begin()` / `resolve()`-preview: `registry.resolve_provider(model, task.provider, node.provider)`
   - `_resolve_node()`: `registry.resolve_provider(task.model, task.provider)` (no node yet)

   It takes plain `str` provider keys (never the `AgentTask`/`Node` objects), so
   `providers.py` gains no dependency on `runners`/`nodes` — no import cycle.
   It returns `str | None` exactly like `provider_for_model`; each caller keeps
   its own None-handling (e.g. `_resolve_node`'s explicit `raise ValueError`).
   Behavior is unchanged — pure deduplication of the rule.

2. **Registry keys, no enum.** Remove `Tool`, `PROVIDER_TOOL`, and
   `tool_for_provider`. Replace enum members with the plain string keys already
   used everywhere (`"claude"`, `"codex"`). Retype `AgentRunner.tool`,
   `PreparedRun.tool`, and runner class attributes to `str`. Make the CLI
   `choices` read `sorted(registry.keys())` so a registered provider is
   accepted without touching routing. `EchoRunner`'s default becomes `"claude"`.

## Consequences

### Positive

- The provider-resolution rule exists in exactly one place; adding a tiebreaker
  is a one-line change, not a four-site lockstep edit. Removes the latent
  divergence risk between `begin()` and `resolve_contract()`.
- §7.1's migration becomes *true*: a new provider (`gemini_cli`, a direct API)
  is one registered module, addable without editing `routing.py` or CLI choices.
- No lingering compat shim to rot; the registry is unambiguously the single
  provider seam.

### Negative / risk

- Removing `Tool` from `hephaestus/integration/__init__.py`'s public exports is
  a package-API change. Acceptable: no consumer outside this repo is known, and
  the string keys it aliased are the stable public contract.
- ~6 mechanical call sites plus test updates. Low risk *because dispatch is
  already registry-driven* — the enum was not doing the routing work, so its
  removal cannot break routing.

### Neutral

- No behavior change for existing single-provider (`claude`/`codex`) flows;
  the full suite must stay green as the acceptance bar.

## Alternatives Considered

1. **Keep `Tool` as a deprecated alias for the two built-ins.** Rejected — a
   compat shim with no removal trigger is the "temporary that becomes
   permanent" antipattern; the enum's only value (type-safety on two literals)
   is already superseded by `str` + registry-key validation.
2. **Fold model resolution (`task.model or node.model`) into the same helper.**
   Rejected — model fallback and provider fallback are separate concerns each
   call site decides differently; merging them couples unrelated decisions.
3. **Defer until a real second provider lands.** Rejected — the work is small
   and mostly done; finishing now removes a standing contradiction with the
   design doc and the latent resolution-divergence bug, rather than carrying
   both until forced.

## Supersedes / relates to

- Formalizes the "Provider registry" decision listed as pending in
  `governance-engine-revised.md` §8 (audit #1).
- Completes the "ExecutionContract as a derived record" resolution seam (audit
  #2, issue #21) by making provider identity part of that single seam.
