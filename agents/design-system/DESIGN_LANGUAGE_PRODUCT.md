---
title: Hephaestus Design Language - Product
role: design-system
updated: 2026-07-09
owner: architect
---

# Design Language - Product

Back to [DESIGN_LANGUAGE.md](DESIGN_LANGUAGE.md)

## Purpose

This document defines the product-facing shape of the design language:

- what Hephaestus is
- what the hero surfaces are
- how the product should feel
- how major surface boundaries should read

## What Hephaestus Is

Hephaestus is a graph-centered AI control plane.

Its runtime is expressed through:

- nodes
- artifacts
- contracts
- gates
- traces
- corrections

The UI must reinforce that the system is:

- authored
- inspectable
- governed
- stateful

## Product Shape

The user should understand the application as:

1. A graph authoring surface
2. A graph runtime surface
3. A control-plane inventory
4. A governance and learning surface

Every major screen should reinforce that mental model.

## Hero Surfaces

These are the hero surfaces of the application. They should feel primary, not
interchangeable.

### 1. Workflow Canvas

This is the command center.

The canvas is where workflows are authored, run, paused, inspected, and
resumed. It must look authoritative, spatial, and load-bearing.

### 2. Node Drill-In Inspector

This is the serious inspection rail for selected graph elements.

It houses:

- node contract
- input artifacts
- output specs
- context preview
- transcript
- trace
- gates
- produced artifacts
- violations and corrections

It should feel like an operational instrument panel, not a settings drawer.

### 3. Artifact Edge Surface

Edges are not decorative connectors. They carry artifact meaning.

Artifact capsules, fan-out junctions, compatibility warnings, ask/allow state,
and produced artifact previews are hero-level elements.

### 4. Preflight Dock

Preflight is a trust surface.

It tells the user:

- what is runnable
- what is invalid
- what is risky
- what is a hard stop

It should feel like a rigorous systems check, not lightweight form validation.

### 5. Context Preview

Context preview expresses one of the product's deepest values: context control.

Users need to see what the system will send. This surface must feel compiled,
inspectable, and evidentiary.

### 6. Library

Library is the reusable inventory of the control plane:

- Nodes
- Artifacts
- Skills
- Providers / engines
- Frozen rules
- Workflow templates

It should feel like a hardened registry, not a casual gallery of cards.

### 7. Correction And Learning Surfaces

Hephaestus learns through corrections, retries, provenance, and rule
promotion. These surfaces should feel procedural and auditable, not like
"suggestions."

## Experience Targets

If the design language is working, the user should feel:

- oriented rather than impressed
- in control rather than assisted
- informed rather than reassured
- responsible rather than entertained

We are aiming for:

- high confidence
- visible system logic
- operational seriousness
- dense but readable control surfaces

We are not aiming for:

- cozy productivity software
- whimsical AI magic
- glossy enterprise neutrality
- visual softness as a default mode

## Surface Boundaries

Authoring, runtime, validation, and learning should feel related, but not
merged into one visually ambiguous soup.

The design should make it obvious when the user is:

- shaping a graph
- observing a live run
- diagnosing a blocker
- approving a handoff
- promoting a learning

This should be clear even before the user reads the text.

## Tone Summary

If the design language is working, Hephaestus should feel like:

- a machine room for governed AI systems
- an authored graph runtime
- a control plane with visible consequences
- a product that respects operator intelligence

It should feel raw, exact, and unapologetic without becoming unusable.

## Hephaestus Theme Layer

The product name is not an excuse for mythology-heavy decoration.

Hephaestus should enter the product as a secondary thematic layer that supports
the operational model already defined by the cyber-brutalist backbone.

Priority order:

1. brutalist structure
2. cybernetic signal language
3. Hephaestus-like forge metaphors and industrial craft details

This means the theme should be felt through:

- forged output language around artifacts and production
- workshop, blueprint, inspection, and rework metaphors
- industrial seriousness in validation and runtime control
- subtle fabrication cues in surfaces, labels, and motion character

It should not appear as:

- literal god imagery
- fantasy aesthetics
- ornamental fire everywhere
- myth references on every control
- a visual layer strong enough to compete with runtime clarity

## Best-Fit Thematic Areas

The Hephaestus layer fits best where the product already behaves like a forge.

### Artifact System

Artifacts are the strongest thematic seam.

They can be framed as:

- forged outputs
- stamped units
- inspected pieces
- versioned stock with provenance

This should show up in:

- artifact chips
- artifact metadata rows
- artifact preview cards
- artifact lineage and provenance surfaces

### Validation And Gates

Preflight, validation, and gate surfaces naturally support inspection-bench
language.

Examples:

- missing inputs as missing material or stock
- invalid specs as malformed blueprint or bad tolerances
- incompatible bindings as bad fittings
- failed gates as failed inspection
- corrected runs as rework or reforge events

### Node Drill-In

The inspector can borrow workbench logic without changing the core information
architecture.

Natural fits:

- contracts as blueprint sheets
- transcript as work log
- trace as tool marks
- violations as flaws
- corrections as rework history

### Motion Character

Motion can carry the theme through mechanical impact rather than mythology.

Good fits:

- confirmations that feel stamped or locked
- warnings that feel like controlled inspection strikes
- reveals that feel like shutters, plates, clamps, or docked panels
- active runtime states that feel energized, not magical

## Good-To-Add Elements

These are approved thematic additions when used with restraint:

- blueprint-sheet framing in contracts and specs
- serial or batch-style artifact metadata
- forge-stamp or maker-mark style identity cues
- inspection and tolerance language in validation
- workshop and rework metaphors in correction history
- fabricated-material framing for artifact movement across edges
- industrial caution markers for human gates and overrides
- subtle heat or energized-state cues only on active runtime surfaces

## Boundaries

The Hephaestus theme must remain subordinate to clarity.

Rules:

- use thematic language mainly on hero surfaces, not every component
- prefer metaphor that strengthens system understanding
- keep visual cues sparse and structural
- attach every thematic cue to a real product meaning
- if a thematic detail reduces legibility, remove it

When unsure, choose the more operational and less mythic version.
