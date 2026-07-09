---
title: Hephaestus Design Language - Visual
role: design-system
updated: 2026-07-09
owner: architect
---

# Design Language - Visual

Back to [DESIGN_LANGUAGE.md](DESIGN_LANGUAGE.md)

## Design Direction

The chosen direction is:

**Cyber-brutalism for AI operations**

This means we borrow from brutalist web principles, then adapt them for a
graph-native AI control plane rather than copying raw retro-web defaults.

The brutalist reference is useful because it emphasizes:

- raw structure
- visible grids
- high contrast
- minimal ornament
- hard functional honesty
- strong differentiation from generic polished SaaS interfaces

Our version is more precise:

- brutalist in structure
- cybernetic in atmosphere
- editorial in hierarchy
- operational in tone

## What Cyber-Brutalism Means Here

For Hephaestus, cyber-brutalism is not retro-web cosplay and it is not neon for
its own sake.

It means:

- architecture is visible
- state is visible
- consequences are visible
- machine intent is visible

The "brutalism" part gives us:

- rigid structure
- unapologetic hierarchy
- obvious framing
- minimal softness

The "cyber" part gives us:

- signal color semantics
- scanline, grid, and systems-room atmosphere
- live-state energy
- an interface that feels computational rather than administrative

The result should feel like a hardened graph operating environment, not like a
design trend board.

## Core Principles

### Structural Honesty

The interface should reveal system structure rather than hide it.

Visible divisions, explicit boundaries, labeled surfaces, obvious state
transitions, and graph-first runtime semantics are part of the language.

### Hard Geometry

Use hard edges, visible borders, framed blocks, measured spacing, and explicit
containers. Avoid soft blobs, overly rounded surfaces, and inflated "friendly"
components.

### High-Contrast Restraint

Most of the system should live in black, charcoal, steel, frost, and signal
tones. Accent colors are intense and sparse. They are for meaning, not mood.

### Mechanical Interaction

State changes should feel abrupt, decisive, and intentional. Hover, selection,
confirm, reject, blocked, and passed states should feel like machine-state
changes, not playful micro-interactions.

### Typography As System Voice

Typography should feel direct, sharp, and technical. It should communicate that
the product is an operating system for governed AI work, not a marketing site
or consumer app.

### Content Before Decoration

The point of the product is to expose graph structure, runtime state,
artifacts, and evidence. Visual style should amplify legibility and seriousness,
not cover the system in cosmetic effects.

## Typography

High-level rules:

- Use a strong sans for primary reading and operational hierarchy
- Use a monospace face for ids, paths, contracts, traces, and run metadata
- Prefer crisp, visible hierarchy over subtle weight ladders
- Headings should feel assertive, not elegant
- Labels should be small, uppercase, and explicit

Typography roles:

- display or hero titles: severe, compact, and high-contrast
- section titles: strong sans, visibly separated from body copy
- labels: uppercase, narrow tracking, operational not decorative
- evidence and metadata: monospace by default
- helper copy: compact and subordinate

## Color

Base palette:

- black
- near-black blue
- steel gray
- cold white

Signal palette (updated 2026-07-09 — live re-keyed cyan → ember → charged
magenta #D412E9; ember was rejected same-day for reading as Claude-brand
orange):

- charged magenta for active/system/live
- acid mint for positive/flow/confirmed
- gold for caution/waiting human
- red-pink for blocked/failure
- violet for stale/version/secondary system markers

Signal semantics:

- magenta: selected, active, live, energized
- mint: confirmed, healthy, flowing, passed
- gold: caution, waiting, human intervention, degraded
- rose-red: blocked, failed, incompatible, violation
- violet: stale, pinned, versioned, deferred, secondary system state

Note: CSS snippets elsewhere in these documents that show cyan rgba values
predate this change — read them as `signal-live`. The red/cyan fringe inside
`glitch-strike` is optical chromatic aberration, not semantic color, and
stays. Do not add further purple-family signals: magenta (live) and violet
(stale) already share a neighborhood.

Rules:

- Keep the neutral field dominant
- Use bright accents sparingly
- Avoid soft gradients as the main mood system
- Prefer color blocks, glows, borders, and signal lines over decorative washes

## Shape

Use:

- hard corners or tight radii
- explicit dividers
- framed sections
- visible edge capsules
- dense but controlled cards

Preferred geometry:

- square or near-square corners
- visible 1px and 2px structural lines
- framed blocks inside framed blocks
- hard separators before soft grouping
- rectangular chips over bubbly pills when possible

Avoid:

- pillowy components
- generic glassmorphism
- oversized rounded SaaS cards
- whimsical illustration-led UI

## Layout

Use:

- visible grid logic
- strong rails and docking
- asymmetry where it helps hierarchy
- intentional panel stacking
- graph surfaces that feel spatial, not boxed into tab metaphors

Prefer:

- left and right rails over hidden drawers
- docked information over floating overlays
- stacked inspection over tab-churn
- persistent runtime context over page-to-page fragmentation

Dead space should be used sparingly. The system should feel dense with intent,
not cramped by accident.

## Materials And Surface Hierarchy

The interface should use a clear surface ladder:

1. Ground: near-black field with subtle structure
2. Shell: top bars, side rails, and global framing surfaces
3. Panels: major operational blocks such as canvas shell, inspector, preflight dock
4. Cards: nested evidence, summaries, contracts, and rows
5. Signals: chips, markers, labels, pills, traces, and warnings

Each step up the ladder should become:

- slightly brighter or more contrasted
- more bounded
- more explicit in purpose

No surface should look decorative by default. Every frame should look
functional.

## Signature Motifs

These should recur across the product:

- visible grid fields behind graph surfaces
- diagnostic corner markers and framed edges
- narrow uppercase labels above dense content
- signal bars, edge lines, and state markers
- stacked evidence cards with clear containment
- hard separators between authoring, runtime, and governance concerns

They should be repeated enough to form identity, but never so loudly that they
compete with runtime readability.

## Depth And Atmosphere

Atmosphere should come from:

- layered darkness rather than flat black
- structural lines rather than blurry fog
- selective glow on active states
- controlled screen-like texture or scanning cues

Avoid:

- dreamy blur-heavy depth
- decorative lens effects
- soft colorful ambiance disconnected from state
- novelty textures that hurt readability

## Density And Spacing

Spacing should be compact, deliberate, and system-like.

Prefer a rhythm based on:

- 4
- 8
- 12
- 16
- 24
- 32

Use density intentionally:

- hero runtime surfaces can be dense if structure is strong
- settings-like forms should be tightened into contract-editing blocks
- evidence lists should stack tightly with clear separators

Do not solve hierarchy only by adding more empty space. Solve it through
framing, labels, contrast, and ordering.

## Icons, Markers, And Labels

Icons should feel infrastructural, not playful.

Use markers to express:

- state
- type
- scope
- runtime ownership
- validation severity

Labels should be:

- explicit
- short
- uppercase where appropriate
- attached to the thing they describe

Avoid vague decorative icons that do not carry operational meaning.

## Operational Style Rules

When unsure, prefer the option that is:

- more explicit
- more structured
- more bounded
- more inspectable
- more semantically colored

When two versions are equally usable, prefer the one that feels more like a
control plane and less like a dashboard template.

## Do / Do Not

Do:

- show rails, borders, labels, and structure
- make active and blocked states unmistakable
- use color as semantics
- make evidence feel contained and auditable
- preserve a serious, authored tone

Do not:

- round everything into softness
- hide critical state behind hover-only interactions
- make runtime and authoring look interchangeable
- use neon as decoration without state meaning
- make panels feel like interchangeable SaaS widgets

## External Aesthetic References

External references are used as selective inputs, not as style packs to import.

References reviewed for this phase:

- [Cybercore Visual Elements - Shapes](https://shapes.inc/fandom/cybercore/visual-elements)
- [Vaporwave - Wikipedia](https://en.wikipedia.org/wiki/Vaporwave)

Important constraint:

- Cybercore contributes more cleanly to Hephaestus than Vaporwave does
- Vaporwave is only useful here in very reduced, structural ways
- anything that turns the product into nostalgia theater or decorative
  cyberpunk cosplay must be rejected

### Reference Fit: Cybercore

Cybercore aligns well with the existing cyber-brutalist direction because it
already emphasizes neon-on-dark signal systems, HUD overlays, hardware
exposure, scanline texture, and stressed-machine framing.

#### Keep

- neon signal colors on dark fields when they encode state
- HUD-like overlays and framed readout markers
- exposed hardware motifs such as PCB logic, ribbon-cable routing, microchip
  geometry, and heatsink-like repetition
- warning labels and industrial decals when attached to real runtime risk
- subtle CRT or scanline texture in the background of high-value graph surfaces
- wireframe geometry when it clarifies digital space rather than decorating it

#### Use Sparingly

- glitch cues only as singular interruption signals for hard failure or
  corrupted state
- data-saturated overlays only inside dense runtime evidence surfaces
- translucent shell references only when used as a secondary surface texture,
  not as the dominant material model
- ultraviolet and magenta only as secondary support tones behind the primary
  cyan, mint, amber, and rose runtime palette

#### Reject

- digital maximalism as a default surface strategy
- chromatic aberration everywhere
- heavy datamoshing or pixel sorting
- faux Neo-Tokyo styling with semantically empty kanji
- holographic or iridescent surfaces as a general component default
- clutter stacks that reduce inspectability

#### Motif Translation: HUD Corner Markers

Use Cybercore's overlay language in a stripped operational form.

```css
.surface-frame--hud {
  position: relative;
}

.surface-frame--hud::before,
.surface-frame--hud::after {
  content: "";
  position: absolute;
  width: 14px;
  height: 14px;
  border-top: 2px solid var(--color-signal-cyan);
}

.surface-frame--hud::before {
  top: 8px;
  left: 8px;
  border-left: 2px solid var(--color-signal-cyan);
}

.surface-frame--hud::after {
  top: 8px;
  right: 8px;
  border-right: 2px solid var(--color-signal-cyan);
}
```

Use on:

- node drill-in shell
- preflight dock
- context preview frame
- active graph command surfaces

#### Motif Translation: Subtle Scanline Texture

Scanline texture is allowed only as low-contrast structural atmosphere.

```css
.surface-texture--scanline {
  position: relative;
}

.surface-texture--scanline::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0.08;
  background-image: linear-gradient(
    to bottom,
    rgba(255, 255, 255, 0.05) 0,
    rgba(255, 255, 255, 0.05) 1px,
    transparent 1px,
    transparent 4px
  );
}
```

Use on:

- canvas ground
- live transcript and trace surfaces
- full-screen run-mode shell

Do not use on:

- ordinary buttons
- passive inventory lists
- small form controls

#### Motif Translation: Warning Tape / Industrial Markers

Warning decoration is valid only when it carries actual runtime caution.

```css
.marker--caution-stripe {
  background-image: repeating-linear-gradient(
    -45deg,
    rgba(255, 196, 82, 0.18) 0 8px,
    rgba(20, 20, 22, 0.18) 8px 16px
  );
  border: 1px solid rgba(255, 196, 82, 0.52);
}
```

Use on:

- waiting-human gate banners
- override-required notices
- degraded provider callouts

### Reference Fit: Vaporwave

Vaporwave is much less aligned with Hephaestus, but a few of its structural
ideas can still contribute if they are aggressively reduced.

#### Keep In Reduced Form

- early-web framing language where it reinforces exposed interface structure
- sparse wireframe grids or 3D-render cues when they help explain graph space
- slight retro-digital framing in background composition for large hero
  surfaces

#### Use Sparingly

- Memphis-like geometry only as a distant background accent
- 3D-rendered object language only when it strengthens spatial understanding
- nostalgic web chrome only when reduced into hard structural framing

#### Reject

- pastel-heavy palette shifts
- dreamy or ironic nostalgia
- Greco-Roman statues
- surreal anti-corporate collage
- decorative VHS decay across core UI
- meme-coded typography or fullwidth text gimmicks
- playful retro motifs that compete with runtime evidence

#### Motif Translation: Wireframe Ground Plane

The wireframe lesson is spatial, not nostalgic.

```css
.canvas-ground--wireframe {
  background-color: var(--color-ground-0);
  background-image:
    linear-gradient(rgba(88, 207, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(88, 207, 255, 0.08) 1px, transparent 1px);
  background-size: 24px 24px;
}
```

Use on:

- the main graph ground
- empty graph states
- spatial hero surfaces that explain graph topology

#### Motif Translation: Old-Web Frame Compression

Vaporwave's early-web lineage is only useful when converted into compressed,
hard framing.

```css
.panel-frame--compressed {
  border: 2px solid var(--color-border-strong);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.05),
    0 0 0 1px rgba(0, 0, 0, 0.35);
}
```

Use on:

- docked side panels
- command strips
- stacked evidence cards

### External Reference Left-Out List

The following source qualities are intentionally left out of Hephaestus.

From Cybercore:

- overload as the default composition rule
- image corruption as an always-on texture
- iridescent glam-tech materials
- visual chaos without state meaning
- decorative kanji, binary spam, or fake terminal noise

From Vaporwave:

- ironic nostalgia as a product mood
- statues, palms, sunsets, malls, and dreamscape collage
- pastel softness replacing signal contrast
- retro branding parody as a central interface voice
- VHS degradation as a permanent visual filter

## Signal Distortion Layer

Approved 2026-07-09. Glitch, dither, radio distortion, and CRT texture are part
of the visual system as a **governed signal-quality language**, refining the
earlier Cybercore boundaries. Distortion encodes the state of the signal, never
decoration. Reference implementation: `component-library.html`.

### Tier 1 — State-Tied Distortion

These fire only when the state they encode is real:

- **glitch-strike**: one-shot RGB-split interruption as the alarm-hard
  companion — hard-stop preflight failures, violations, blocked nodes,
  incompatible edges, failed gates. Never loops.
- **frame-tear**: a single tear for stale or outdated reveals — pinned
  inspector gone stale, outdated node markers.
- **interference**: drifting radio bands layered on every `pending-scan`
  surface — provider connecting, preflight recompute, run boot.
- **sig-flicker**: signal-strength dropout on degraded readiness markers.
- **carrier wave**: a thin wave riding the caution stripe while a human gate
  holds.
- **dither**: Bayer-style texture as the material of inactive, empty, or
  dead-channel matter — empty states, disabled and reserved fields, all-clear
  monitors, boot static.
- **stream-hold**: horizontal-hold shimmer on stream surfaces, only while
  genuinely streaming.
- **character scramble**: brief tuning-in settle on event annunciator lines.

### Tier 2 — Ambient CRT Layer

Threshold-intensity atmosphere, allowed only on stage/canvas grounds and the
shell:

- aperture-grille micro-mask plus vignette and faint phosphor bloom over the
  true-black ground (`crt-layer`), at low single-digit opacities
- a one-time CRT power-on reveal on first mount (`crt-power-on`)

### Still Rejected

- glitch on healthy or passing states
- constant chromatic aberration on text
- VHS wobble on form fields
- datamosh transitions between views
- any distortion strong enough to reduce evidence legibility

### Priority Rule

When distortion competes with legibility of runtime evidence, distortion loses.
Reduced-motion kills every distortion loop and collapses one-shots.

## Hephaestus-Themed Additions

The Hephaestus theme is an approved secondary layer inside the visual system.

It does not replace the cyber-brutalist direction. It only sharpens the
product's sense of fabrication, inspection, and governed production.

### Use Cases That Fit

These thematic cues are good additions when tied to real meaning:

- blueprint or spec-sheet framing for contracts, artifact specs, and context
  compilations
- maker-mark or forge-stamp details for artifact identity and provenance
- industrial caution treatment for validation, human gates, and override
  surfaces
- machine-housing corner brackets, rivet logic, and plate-like framing on hero
  surfaces
- subtle heated or energized accents on active runtime paths only
- workshop-style metadata formatting for artifact ids, versions, grades, and
  run provenance

### Safe Visual Motifs

These motifs are safe because they strengthen the product model without turning
the interface theatrical:

- blueprint headers and dense spec tables
- stamped labels and serial-number formatting
- inspection-card framing
- fabrication-table grids
- tool-mark textures in tiny doses
- restrained caution striping
- forged-material language in artifact cards and output summaries

### Use Sparingly

The following are allowed only in small doses and only on high-value surfaces:

- heat-inspired glow on active run states
- metallic plate framing
- hammered or tool-struck asymmetry in divider details
- workshop language in empty states and supporting copy

### Reject

Do not introduce:

- flames, lava, sparks, or smoke as ambient decoration
- literal anvils, hammers, or deity iconography across the UI
- bronze-age or fantasy styling that fights the computational setting
- rough forged textures that reduce readability
- mythology-heavy terminology in ordinary controls

### Placement Guidance

Best-fit surfaces:

- artifact edges and artifact previews
- node drill-in contract and provenance sections
- preflight dock and gate summaries
- correction history and learning promotion surfaces
- graph canvas ground and active runtime rails

Weak-fit surfaces:

- routine form fields
- passive library lists
- generic buttons
- low-level navigation chrome

### Priority Rule

When a Hephaestus-themed choice conflicts with a brutalist or operational
choice, the brutalist or operational choice wins.
