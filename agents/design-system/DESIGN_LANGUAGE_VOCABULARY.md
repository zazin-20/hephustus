---
title: Hephaestus Design Language - Vocabulary
role: design-system
updated: 2026-07-09
owner: architect
---

# Design Language - Vocabulary

Back to [DESIGN_LANGUAGE.md](DESIGN_LANGUAGE.md)

## Purpose

This document defines the copy and naming layer for Hephaestus.

It exists to make the product sound:

- operational
- precise
- governed
- intelligently severe

It also defines how the secondary Hephaestus theme should appear in language
without turning the product into mythology theater.

## Priority Rule

The copy system follows this order:

1. clarity
2. operational accuracy
3. product consistency
4. subtle thematic flavor

If a thematic phrase is less clear than a plain operational phrase, the plain
operational phrase wins.

## Voice Characteristics

The product voice should feel:

- exact rather than conversational
- competent rather than promotional
- serious rather than dramatic
- technical rather than mystical
- direct rather than cute

The user should feel that the system:

- respects their intelligence
- shows its work
- names problems clearly
- does not pretend uncertainty is confidence

## Core Language Model

Hephaestus is best understood as a forge for governed AI work.

That metaphor should appear through:

- blueprint language for contracts and specs
- workshop language for node work and rework
- inspection language for validation and gates
- forging language for artifact production and correction

It should not appear through:

- deity references
- heroic mythology
- lore-heavy names
- fantasy storytelling

## Tone Rules

Prefer:

- short labels
- high-information nouns
- procedural verbs
- explicit cause and effect
- system-readable severity language

Avoid:

- playful filler
- hype language
- emotional reassurance as default
- vague AI magic phrasing
- slangy or meme-coded copy

## Domain Vocabulary

### Artifacts

Primary language:

- artifact
- output
- input
- spec
- provenance
- lineage
- produced
- bound
- version

Allowed secondary thematic language:

- forged output
- stamped
- batch
- serial
- grade
- piece

Use the thematic words sparingly and mainly in supporting labels, metadata, or
section names.

Do not replace the canonical word `artifact` with a purely thematic synonym.

### Contracts And Context

Primary language:

- contract
- spec
- context
- directives
- replayed context
- frozen rules
- allowed tools
- allowed paths

Allowed secondary thematic language:

- blueprint
- build sheet
- compiled payload
- shop rule

`contract` and `spec` remain the canonical nouns. `blueprint` is a useful
supporting metaphor, not the primary system noun.

### Validation And Gates

Primary language:

- preflight
- runnable
- blocked
- invalid
- unavailable
- incompatible
- gate
- passed
- failed
- override

Allowed secondary thematic language:

- inspection
- tolerance
- fitting
- stock missing
- failed inspection

Use thematic language mainly in helper copy, section names, or error detail,
not as the only wording for critical runtime state.

### Corrections And Learning

Primary language:

- correction
- candidate
- promoted
- frozen rule
- superseded
- disabled
- provenance
- scope

Allowed secondary thematic language:

- rework
- reforge
- shop memory
- flaw history

`correction` stays canonical. `reforge` is appropriate for secondary phrasing
around retries or improvement history.

### Runtime And Execution

Primary language:

- run
- active
- paused
- resumed
- waiting for human
- awaiting confirmation
- streaming
- trace
- transcript

Allowed secondary thematic language:

- in forge
- energized
- cooling
- work log
- tool marks

Use these sparingly and only where the user still immediately understands the
underlying system state.

## Naming Patterns

### Good Primary Labels

- `Node Contract`
- `Artifact Spec`
- `Produced Artifacts`
- `Run Transcript`
- `Trace`
- `Preflight`
- `Correction Candidate`
- `Frozen Rules`

### Good Secondary Labels

- `Blueprint View`
- `Inspection Summary`
- `Work Log`
- `Provenance Mark`
- `Rework History`
- `Artifact Batch`

### Avoid

- `Divine Output`
- `Forge Magic`
- `Sacred Rules`
- `Olympian Mode`
- `Volcanic Run`
- `Anvil Engine`

## Status Copy Guidance

Use plain operational status first.

Preferred:

- `Active`
- `Blocked`
- `Waiting for Human`
- `Awaiting Confirmation`
- `Passed`
- `Failed`
- `Unavailable`
- `Invalid`

Allowed thematic support copy:

- `Passed inspection`
- `Failed inspection`
- `Reforged after correction`
- `Blueprint incomplete`
- `Output not yet forged`

Do not replace critical status words with metaphor-only alternatives.

Bad replacements:

- `Tempered` instead of `Passed`
- `Cracked` instead of `Failed`
- `Heating` instead of `Running`

These can work as supporting copy in some surfaces, but not as primary status
labels.

## Copy Placement Rules

Thematic language is strongest in:

- empty states
- section subtitles
- helper copy
- metadata group labels
- artifact and provenance surfaces
- learning and correction history

Thematic language is weaker in:

- destructive confirmation dialogs
- hard-stop preflight errors
- critical gate actions
- primary run controls
- provider and model availability states

In those critical surfaces, plain operational wording should dominate.

## UI Microcopy Patterns

Prefer patterns like:

- `Missing required input artifact`
- `Provider unavailable for this run`
- `Artifact spec is invalid`
- `Awaiting human confirmation`
- `Correction promoted to frozen rule`

Allow restrained thematic variants like:

- `Blueprint incomplete: output spec is missing`
- `Inspection failed: incompatible artifact binding`
- `No artifacts forged yet`
- `Rework recorded for this node`

## Banned Language

Do not use:

- grand mythological storytelling
- faux-profound AI language
- consumer productivity cheerfulness
- decorative hacker jargon with no meaning
- random industrial wording not tied to product behavior

## Implementation Rule

When naming a new component, state, panel, or action:

1. choose the clearest operational noun
2. choose the most explicit state verb
3. add only a small amount of thematic flavor if it improves memorability
4. remove the thematic flavor if it reduces clarity
