# Architecture Audit — Deepening Opportunities (2026-06-23)

**Method:** `/improve-codebase-architecture`, informed by `governance-engine.md` (the target
architecture) and ADR-0001. Vocabulary: *module / interface / implementation / depth / seam /
adapter / leverage / locality*, and the **deletion test** (delete the module — does complexity
*concentrate* (deep, keep) or just *move* (pass-through)).

**Priority lens:** provider modularity — `gemini_cli` is coming and likely direct provider APIs,
so the Hephaestus↔engine seam must let a new provider (CLI *or* API) be added cleanly.

---

## 1. `Provider` as a deep module behind a registry — *priority; enables Gemini/APIs*

**Files:** `integration/runners.py`, `integration/routing.py`, `catalog.py`, `integration/adapters.py`, `integration/service.py`

**Problem:** `AgentRunner` is a genuinely **deep** seam — one `run(contract, ctx) -> AsyncIterator[AgentEvent]`; CLI-subprocess (`codex exec`), SDK (`claude-agent-sdk`), *and* a future HTTP-API runner all fit. But everything else a provider needs is **shallow and smeared** across six sites keyed by a closed `Tool` enum: `routing.Tool` + `ROLE_TOOL`; `catalog.provider_for_model`; `catalog.discover_claude`/`discover_codex`; `adapters.claude_flags`/`codex_flags`; `runners._claude_event`/`_codex_event`; `service.default_runners`. **Deletion test:** a `Provider` object bundling all of that would *concentrate* the complexity that's currently scattered → strong keep signal. Adding `gemini_cli` today means editing ~6 places with no single seam.

**Solution:** one `Provider` interface — `{runner, normalize_event, flags(contract), discover_models(), owns_model(model)}` — and a **registry**. Routing, catalog, and `service.default_runners` read the registry; the closed `Tool` enum becomes registry keys; per-provider raw→turn mapping moves **onto** its Provider.

**Benefits:** **locality** (all Claude/Codex/Gemini knowledge in one module each); **leverage** (the registry is *the* seam — Gemini = "write `GeminiProvider`, register it"; an API provider = same interface, HTTP runner); **test surface** (the `Provider` interface — "GeminiProvider maps a thinking chunk → `thinking` turn", "owns_model('gemini-2.5')"). Two adapters (Claude, Codex) already prove the seam is real; the registry makes the third trivial.

---

## 2. `ExecutionContract` — a 16-field data-bag that wants to be a *derived* Run record

**Files:** `contract.py`, `integration/service.py` (construction), `integration/adapters.py`, `integration/runners.py`

**Problem:** post-#13, `ExecutionContract` is one wide frozen struct conflating **authored config** (`model, effort, scope, tools, allowed_paths`), **per-run input** (`prompt, cwd, resume, issue_id`), **identity** (`actor, role, tool`), and **result** (`actual_model`), constructed ad-hoc field-by-field in `service`. It's **shallow** — interface ≈ implementation (a bag of 16 fields). `governance-engine.md` §7.1 says these are distinct: a **Node** (authored) resolves into a **Run/ExecutionContract** (derived).

**Solution:** put the depth in a **Node→ExecutionContract resolution** module — one place that resolves `(Node + input artifacts + constitution)` into the governed run spec — and treat the contract as the derived, immutable record (a `resolve(...)` interface, not 16 kwargs).

**Benefits:** **locality** (run-resolution in one place vs. scattered field-setting in `service`); a real **interface** on the contract; **test surface** = "resolving node X with inputs Y yields contract Z scoped to these paths." *Caveat: overlaps the planned §7 node-model build — may be "build the new model" rather than a standalone refactor.*

---

## 3. Per-provider event mapping lives as free functions, not on the provider

**Files:** `integration/runners.py` (`_claude_event`, `_codex_event`), `integration/turns.py`

**Problem:** `turns.py` (#11) deepened the *downstream* taxonomy (kind → descriptor), but the *upstream* per-provider translation (raw message → kind + tool-call/thinking/text extraction) is module-level free functions — the highest-bug-density code in the system (every agent-stream bug this session lived there) sitting *outside* any provider seam.

**Solution:** fold `normalize_event` into the `Provider` interface from #1 — each provider owns its raw→turn mapping next to its runner.

**Benefits:** friction concentrates per-provider (**locality**); the **interface is the test surface** — one mapping test per provider against one contract. *(A facet of #1; called out for its bug density.)*

---

## 4. No `CONTEXT.md` — the domain vocabulary isn't a glossary

**Files:** (new) `CONTEXT.md`

**Problem:** the settled domain language (Provider/Engine, **Node**, **ArtifactSpec**, **Workflow**, gate, edge, **constitution**, **scope-address**, **marker**, **distillation**) lives only as prose in `governance-engine.md`. No glossary keys future reviews or AI navigation → naming drifts ("FooBarHandler") as the new model is built.

**Solution:** lift the §2/§7 vocabulary into `CONTEXT.md`.

**Benefits:** **AI-navigability** and naming **locality** — every future node/spec/gate change speaks one vocabulary; makes #1–#3 land with consistent names.

---

## Recommendation

**Do #1** — existing, shallow, and directly unblocks `gemini_cli` and API providers; it absorbs #3.
**#2** is real but entangled with the upcoming node-model build. **#4** is a cheap enabler.
