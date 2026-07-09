---
title: Design Tokens & Component Guidance
role: design-system
updated: 2026-07-09
owner: architect
---

# Design - Tokens & Component Guidance

Implementation companion for the Hephaestus UI language. Workers implement
against this for tokens and component guidance; changes here precede changes in
`frontend/src/`.

The canonical design-direction system begins at
[DESIGN_LANGUAGE.md](DESIGN_LANGUAGE.md). This file remains the compact token and
component-usage entry point.

Authority order for this folder:

1. `DESIGN_LANGUAGE.md` and its linked language documents
2. `DESIGN.md`
3. preview files such as `component-gallery.html`

Design-language deep dives:

- [DESIGN_LANGUAGE_PRODUCT.md](DESIGN_LANGUAGE_PRODUCT.md)
- [DESIGN_LANGUAGE_VISUAL.md](DESIGN_LANGUAGE_VISUAL.md)
- [DESIGN_LANGUAGE_VOCABULARY.md](DESIGN_LANGUAGE_VOCABULARY.md)
- [DESIGN_LANGUAGE_INTERACTIONS.md](DESIGN_LANGUAGE_INTERACTIONS.md)
- [DESIGN_LANGUAGE_MOTION.md](DESIGN_LANGUAGE_MOTION.md)
- [DESIGN_LANGUAGE_STATUS.md](DESIGN_LANGUAGE_STATUS.md)

## Language

- **Framework:** React + Tailwind v4
- **Mode:** dark-first
- **Aesthetic direction:** cyber-brutalism for AI operations
- Preserve existing tabs and layout unless an issue explicitly requires change.
- In browser-preview mode without `window.pywebview`, fall back to mock data.

## Tokens

Define and stabilize tokens in alignment with
[DESIGN_LANGUAGE.md](DESIGN_LANGUAGE.md) and
[DESIGN_LANGUAGE_VISUAL.md](DESIGN_LANGUAGE_VISUAL.md):

- color and signal roles
- typography pairings
- spacing rhythm
- border and radius discipline
- motion primitives
- copy and naming conventions

## Cyber-Brutalism Token Foundation

This is the current intended token posture for Hephaestus.

### Color Roles

Neutral field:

- `ground-0`: true black base (#000000)
- `ground-1`: blue-black elevated base
- `ground-2`: steel-dark raised surface
- `ground-3`: frost-dark inner card

Structural lines:

- `line-subtle`: low-contrast frame and dividers
- `line-strong`: active frame, selected block, emphasized boundaries
- `line-critical`: blocked or failing emphasis

Text:

- `text-primary`: cold white for important content
- `text-secondary`: steel-frost for readable supporting content
- `text-muted`: dim operational metadata
- `text-inverse`: dark text for bright signal fills only

Signals (live re-keyed 2026-07-09, twice: cyan → ember → charged magenta):

- `signal-live`: charged magenta (#D412E9) — active, selected, energized
- `signal-pass`: mint
- `signal-warn`: gold (#ffd94d)
- `signal-stop`: rose-red
- `signal-stale`: violet

The ember experiment read as Claude-brand orange and was replaced same-day
with charged magenta. Older references to "cyan" or "ember" for live state
are superseded. Watch the magenta/violet (`signal-stale`) adjacency when
composing dense status rows — the stale marker is soft lavender and stays
distinguishable, but do not introduce further purple-family signals.

Live text rendering rule (neon treatment, 2026-07-09): text carrying live
state is never set in raw magenta. It renders as a white core with a magenta
halo — `color: text-primary` + `text-shadow: glow-text-live`. Magenta itself
appears only in non-text carriers: state dots, borders, underline bars,
frames, glows, grid lines, and edge strokes. Filled commit buttons keep dark
inverse text on the magenta fill.

Minimum type sizes (raised 2026-07-09): the small-type floor moved up 2px
across the board — labels 12px, meta/mono 13px, signal markers 12px, chip
type-prefixes 11px. Nothing below 11px anywhere.

Usage rules:

- neutrals dominate the screen
- signal colors stay sparse and meaningful
- gradients are secondary accents, not the core mood system
- glows are only for active computational emphasis

### Typography Roles

- `font-sans`: primary operational sans
- `font-mono`: contracts, ids, traces, paths, evidence, and metadata
- `type-display`: hero surface title
- `type-title`: section and panel titles
- `type-label`: compact uppercase label
- `type-body`: dense readable system copy
- `type-meta`: low-prominence supporting metadata

Rules:

- titles are sharp, not elegant
- labels are explicit and tightly tracked
- metadata defaults to mono when it refers to machine-owned values

### Spacing Rhythm

Primary scale:

- `space-1`: 4
- `space-2`: 8
- `space-3`: 12
- `space-4`: 16
- `space-5`: 24
- `space-6`: 32

Rules:

- prefer compact density with strong framing
- use spacing to support structure, not to create softness
- nested cards should tighten rhythm instead of ballooning outward

### Radius And Corners

- `radius-0`: 0
- `radius-1`: 6
- `radius-2`: 10
- `radius-3`: 14

Rules:

- default to hard or tight corners
- reserve larger rounding for secondary chips only when it improves scanning
- avoid soft oversized card radii

### Border And Framing

- `border-default`: 1px structural line
- `border-strong`: 2px emphasis line
- `frame-inset`: inner containment line for dense operational panels

Rules:

- borders are part of hierarchy, not just decoration
- selected and active states should escalate framing before adding more glow
- nested surfaces should feel intentionally contained

### Shadows And Glow

- `shadow-panel`: deep but tight operational lift
- `shadow-card`: restrained nested depth
- `glow-live`: magenta active-state glow
- `glow-pass`: mint confirmation glow
- `glow-stop`: red failure glow

Rules:

- depth should stay directional and controlled
- avoid soft fuzzy shadows that make the UI feel atmospheric instead of operational
- glow should highlight computation, not replace hierarchy

### Motion Tokens

- `motion-snap-in`
- `motion-trace-on`
- `motion-signal-pulse`
- `motion-hard-flash`
- `motion-collapse-stack`
- `motion-reroute-live`
- `motion-freeze-shift`

Rules:

- short durations
- decisive entry and exit
- no playful bounce
- looping motion only for active runtime meaning

## Signal Distortion Token Layer

Implements the Signal Distortion Layer defined in
[DESIGN_LANGUAGE_VISUAL.md](DESIGN_LANGUAGE_VISUAL.md). Live reference:
`component-library.html`.

State-tied effect classes:

- `fx-glitch`: one-shot RGB-split strike, paired with `fx-alarm-hard`
- `fx-tear`: one-shot frame tear for stale/outdated reveals
- `interference` (via `pending-scan::before`): radio bands on pending surfaces
- `sig-flicker`: dropout flicker for degraded readiness markers
- `carrier` : carrier wave riding a held human-gate stripe
- `stream-hold`: horizontal-hold shimmer, applied only while streaming
- `dither` / `static-field`: dead-channel material for empty, disabled, and
  booting surfaces (also baked into `.input:disabled`)

Ambient CRT (stage-level only):

- `crt-layer`: aperture-grille micro-mask + vignette + faint phosphor bloom
- `crt-boot`: one-time power-on reveal on first mount

Rules:

- distortion encodes signal quality; it is never decoration
- loops bind to unresolved / degraded / held / live state only
- reduced motion removes all distortion loops and collapses one-shots
- if a distortion cue reduces evidence legibility, remove the cue

## Hephaestus Theme Token Layer

This layer is optional and secondary.

Use it to support the approved Hephaestus metaphor without weakening the
cyber-brutalist backbone.

### Surface Accent Tokens

- `surface-blueprint`: spec-sheet or blueprint treatment for contract-heavy panels
- `surface-inspection`: validation and gate framing surface
- `surface-workbench`: drill-in and artifact provenance surface

Rules:

- use only on hero or high-information panels
- do not spread across generic chrome
- the base structure must still read as brutalist first

### Structural Detail Tokens

- `line-inspection`: caution or validation-emphasis framing line
- `line-stamp`: serial or provenance separator line
- `frame-plate`: machine-housing style panel edge treatment
- `frame-bracket`: restrained corner-bracket detail for important surfaces

Rules:

- use as local detail, not universal defaults
- framing escalates hierarchy only when the surface is truly important

### Texture Tokens

- `texture-fabrication-grid`: dense measured ground or panel grid
- `texture-toolmark`: extremely subtle wear or strike-inspired surface detail
- `texture-spec-sheet`: compact ruled-line or compiled-sheet treatment

Rules:

- textures must stay low-contrast
- never reduce readability of content
- never apply decorative roughness to small controls

### Identity Tokens

- `marker-serial`: artifact serial formatting treatment
- `marker-batch`: output batch or lineage grouping treatment
- `marker-forge-stamp`: restrained maker-mark style metadata accent
- `marker-inspection-grade`: validation or artifact quality marker

Rules:

- use on artifact, provenance, and validation surfaces first
- avoid applying identity markers to generic navigation or buttons

### Heat And Energy Tokens

- `accent-heat-live`: restrained energized-state accent for active runtime
- `accent-quench-resolved`: settled completion accent for cooled or resolved states
- `accent-strike-warn`: caution emphasis used with inspection or override surfaces

Rules:

- heat cues are runtime-only
- no ambient fire-like treatment
- energy accents should read as machine activity, not fantasy atmosphere

## Copy Guidance

Naming and microcopy decisions must follow
[DESIGN_LANGUAGE_VOCABULARY.md](DESIGN_LANGUAGE_VOCABULARY.md).

Implementation shorthand:

- primary nouns stay operational
- state labels stay explicit
- Hephaestus flavor belongs in support copy, metadata, and section framing
- metaphor must never replace critical status clarity

## Surface Taxonomy

Apply tokens by surface class:

- `shell`: app frame, sidebar, topbar, global rails
- `hero`: canvas shell, node drill-in, preflight dock
- `panel`: major bounded blocks inside hero surfaces
- `card`: evidence and nested summaries
- `signal`: chips, pills, warnings, inline state markers
- `field`: contract-editing inputs and selectors

Each deeper layer should become more specific, not more decorative.

## Components

[component-library.html](component-library.html) is the canonical reference
implementation of this token layer: 41 interactive units covering foundations,
primitives, shell, workflow canvas, runtime hero surfaces, library, coordinator,
forms, code/run, and unmounted views. Workers should copy its CSS custom
properties, class patterns, and motion classes when implementing in
`frontend/src/`.

The older [component-gallery.html](component-gallery.html) is a placeholder
exploration surface only and must not be used as an implementation reference.

Component expectations (embodied in the library):

- canvas surfaces should feel spatial and load-bearing
- inspector surfaces should feel stacked and evidentiary
- preflight surfaces should read like system analysis
- forms should feel like contract authoring, not preferences UI
- chips, pills, and badges should communicate type or state, not generic style
