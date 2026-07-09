---
title: Design System Log
role: design-system
updated: 2026-07-09
owner: architect
---

# Design System Log

## 2026-07-09 — Neon live-text rule + small-type floor raised

- Live-state text is no longer set in raw magenta: it now renders as a white
  core with a magenta halo (`text-primary` + new `--glow-text-live`
  text-shadow token). Applied to sig-live markers, active segmented buttons,
  active nav index, spec-strip token names, annunciator EVENT tag,
  click-to-fire cues, and code-view identifier highlights. Magenta remains on
  every non-text carrier: state dots, borders, underline bars, frames, glows,
  grid ground, pulses, and edge strokes; commit buttons keep dark text on the
  magenta fill.
- Raised the small-type floor by 2px across the whole library (9→11, 10→12,
  10.5→12.5, 11→13, 11.5→13.5), including the graph-canvas SVG edge labels
  (plate widened to fit). Recorded the new floor in DESIGN.md: nothing below
  11px.
- Verified via jsdom: all 42 units mount and toggle clean.

## 2026-07-09 — signal-live re-keyed again: ember → charged magenta #D412E9

- The molten-ember live color read as Claude-brand orange in practice; user
  replaced it same-day with charged magenta #D412E9 across `signal-live` and
  all `--live-*` alphas (selection frames, pulses, nav rail, focus, commit
  buttons, HUD brackets, grid ground, pending-scan, interference, phosphor
  bloom). Hover tint for commit buttons is now #e14ff2.
- `signal-warn` stays gold #ffd94d. Recorded a guardrail in DESIGN.md and
  DESIGN_LANGUAGE_VISUAL.md: magenta (live) and violet (stale) are neighbors —
  no further purple-family signals.
- Forge-heat wording removed from library copy and docs; the Hephaestus theme
  continues through structure, vocabulary, and motion rather than the live
  color.
- Verified via jsdom: all 42 units mount clean; token resolves to #D412E9.
- Deferred (user decision): integrating the React Bits `<ASCIIText />`
  component (React + three.js, wavy ASCII-rendered text). Open questions when
  resumed: target placement (hero `.type-display` titles vs sidebar brand vs
  live-signal elements) and integration approach (vanilla canvas port inside
  the self-contained library vs three.js CDN vs frontend/src-only React
  component). The original paste was truncated mid-source; request the full
  component when picking this up.

## 2026-07-09 — signal-live re-keyed from cyan to molten ember (forge heat)

- Replaced cyan (#58cfff) with molten ember (#ff8b3d) as `signal-live` across
  the component library: selection frames, active pulses, nav rail, focus
  outlines, commit buttons, HUD corner brackets, wireframe grid ground,
  pending-scan sweep, interference bands, and the CRT phosphor bloom.
- Rationale: cyan was the last generic-cyberpunk element with no tie to the
  product's identity; ember realizes the reserved `accent-heat-live` intent —
  active = energized = in the forge. Chosen over incandescent gold (collided
  with caution) and heated copper (too low-voltage for an active signal).
- Shifted `signal-warn` from amber #ffc452 to gold #ffd94d to preserve
  at-a-glance separation from ember.
- Kept the red/cyan fringe inside `glitch-strike`: it is optical chromatic
  aberration (CRT misconvergence), not semantic cyan.
- Updated DESIGN.md (signal roles, glow-live), DESIGN_LANGUAGE_VISUAL.md
  (signal palette + semantics + snippet supersession note), and
  DESIGN_LANGUAGE_MOTION.md (color note) to match.
- Verified via jsdom: zero stale color references, all 42 units mount clean,
  tokens resolve to #ff8b3d / #ffd94d.

## 2026-07-09 — Wide form layouts, true-black ground, signal distortion layer

- Reworked the three longest library units onto wide grid layouts to cut
  vertical length: node drill-in inspector (9 sections in a 3-column grid,
  960px), node contract form (identity/model/scope rows 3-across, six list
  editors in a 3×2 grid, 940px), artifact definition form (paired name/tags,
  guidance textareas 3-across, actions in the header, 940px). Added a
  `.form-grid` helper to the library CSS.
- Changed `ground-0` to true black (#000000) and re-tuned the surface ladder
  beneath it; DESIGN.md color roles updated to match.
- Added the Signal Distortion Layer (user-approved placement list):
  - Tier 1, state-tied: `fx-glitch` RGB-split strike paired with alarm-hard
    (hard stops, violations, blocked nodes, incompatible edges), `fx-tear` for
    stale/outdated reveals, `interference` bands on all pending-scan surfaces,
    `sig-flicker` on degraded readiness, `carrier` wave on holding human
    gates, `stream-hold` shimmer while streaming, `dither`/`static-field` as
    dead-channel material (empty states, disabled fields, boot splash), and a
    character-scramble settle on annunciator event lines.
  - Tier 2, ambient: `crt-layer` (aperture grille + vignette + phosphor bloom)
    on the stage ground and a one-time `crt-power-on` shell boot reveal.
  - Reduced motion kills every distortion loop and collapses one-shots.
- Added a new Foundations unit, "Signal distortion layer" (library is now 42
  units), demonstrating every effect with its binding rule.
- Amended the language docs to govern the layer: new "Signal Distortion
  Layer" section in DESIGN_LANGUAGE_VISUAL.md (tiers, placements, retained
  rejections, priority rule), "Distortion Motion Additions" in
  DESIGN_LANGUAGE_MOTION.md, and a "Signal Distortion Token Layer" section in
  DESIGN.md.
- Verified via jsdom: all 42 units mount clean, all bench toggles pass, and
  every distortion hook asserts present (glitch on hard stop, tear on stale,
  carrier on gate, flicker on degraded, dither on splash/empty, CRT layer and
  boot on the shell, annunciator scramble settles to correct text).

## 2026-07-09 — Canonical component library built

- Created `component-library.html`: the canonical, self-contained interactive
  component library rebuilt through the full design-language system. 41 units
  across ten groups: Foundations, Primitives, Shell, Workflow Canvas, Runtime,
  Library, Coordinator, Forms, Code + Run, Not mounted.
- Implemented the DESIGN.md token layer verbatim as CSS custom properties
  (surface ladder, structural lines, text roles, five signal colors, spacing
  rhythm, hard-radius discipline, depth/glow tokens).
- Implemented the motion system as working CSS: lock-primary,
  commit-structural, alarm-hard/soft, disclose-inline, transit, trace-stream,
  pending-scan, pulse, and trace-flow, using the documented timing bands,
  easing characters, and family-aware reduced-motion rules.
- Applied the approved motif set with restraint: HUD corner markers, scanline
  texture on canvas/stream grounds, wireframe ground plane, caution striping on
  human gates, blueprint/spec-sheet framing, and serial/provenance marks.
- Replaced the old gallery's soft-SaaS styling (rounded pills, gradient
  buttons, glassmorphism blur, drifting glow, rise-in bounce) with brutalist
  structure per the language; status copy now follows
  DESIGN_LANGUAGE_VOCABULARY.md (Active / Blocked / Waiting for Human /
  Passed / Failed, thematic flavor only in support copy).
- Added a per-component spec readout (tokens + motion families + copy rule)
  so downstream Workers can trace every pattern back to the language docs.
- Verified: JS syntax check plus a jsdom smoke test — all 41 units mount
  clean, all control-bench toggles work, and key flows (list editing,
  model-to-effort unlock, correction modal, trace disclosure, run-agent
  streaming) pass with zero window errors.
- Updated `claude.md` (folder map, authority order, references), `DESIGN.md`
  (components section), and `DESIGN_LANGUAGE_STATUS.md` (status + next steps)
  to index the library as canonical. `component-gallery.html` stays as an
  exploration sandbox only.
- Follow-ups: browser review pass for seam-level polish; extraction into
  React + Tailwind v4 primitives in `frontend/src/` is Worker scope, guided by
  this library.

## 2026-07-09

- Clarified folder authority to remove design-source ambiguity.
- Locked `DESIGN_LANGUAGE.md` as the cornerstone and canonical design-direction
  document.
- Positioned `DESIGN.md` as the implementation companion for tokens and
  component guidance.
- Marked `component-gallery.html` as a preview sandbox that follows, but does
  not define, the design language.
- Added a formal motion vocabulary and animation inventory to
  `DESIGN_LANGUAGE.md`.
- Captured the required animated surfaces and state changes for the workflow
  command center, runtime nodes, artifact edges, preflight dock, inspector,
  context preview, human gates, learning UI, library surfaces, forms, and
  interactive canvas editing.
- Expanded `DESIGN_LANGUAGE.md` with a clearer operational definition of
  cyber-brutalism, experience targets, material hierarchy, signature motifs,
  density rules, and explicit do/do-not guidance.
- Expanded `DESIGN.md` with a concrete token foundation for color, typography,
  spacing, radius, borders, depth, motion, and surface taxonomy.
- Intentionally deferred `component-gallery.html` changes until the design
  language is complete enough to guide implementation coherently.
- Added a full interaction inventory to `DESIGN_LANGUAGE.md`, covering global
  navigation, mode switching, selection, expand/collapse behavior, filtering,
  authoring, graph composition, runtime control, validation, human gates,
  evidence inspection, learning actions, inventory management, and destructive
  or dismissive actions.
- Added interaction behavior rules so future component work can distinguish
  direct manipulation, primary actions, visible cause-and-effect, persistent
  inspection state, and runtime-vs-authoring posture.
- Recorded the motion-system decisions in `DESIGN_LANGUAGE.md`, including
  family-driven motion, timing bands, easing character, one-shot vs persistent
  motion separation, runtime-only persistent motion, input-coupled direct
  manipulation, and restrained cross-surface choreography rules.
- Clarified that cross-surface choreography must be staggered and causal rather
  than simultaneous, with one lead surface and at most two short-offset
  confirmation surfaces.
- Added `hover-preview` as a separate low-commitment motion family with its own
  timing, easing, and behavior rules so hover never masquerades as selection,
  commit, or alarm.
- Added the rule that disabled and unavailable states are motionless after any
  transition into that state, with only one-time explanatory emphasis allowed
  when a user action newly causes the block.
- Added `field-focus` as a separate motion family for editable inputs and
  authoring controls so focused typing states remain distinct from hover,
  selection, and commit behavior.
- Replaced the monolithic `DESIGN_LANGUAGE.md` with a linked design-language
  system:
  `DESIGN_LANGUAGE.md`,
  `DESIGN_LANGUAGE_PRODUCT.md`,
  `DESIGN_LANGUAGE_VISUAL.md`,
  `DESIGN_LANGUAGE_INTERACTIONS.md`,
  `DESIGN_LANGUAGE_MOTION.md`,
  and `DESIGN_LANGUAGE_STATUS.md`.
- Folded the approved late-stage motion decisions into the new motion document,
  including scrolling rules, reduced-motion behavior, pending/loading motion,
  system-vs-user updates, keyboard focus, revert behavior, motion conflict
  priority, alert intensity decay, ambient-motion bans, mobile touch scaling,
  spatial-origin transitions, calm all-clear states, and hard bans on bounce,
  elastic overshoot, and breathing animations.
- Added an external-reference appendix to `DESIGN_LANGUAGE_MOTION.md` mapping
  the useful parts of `eloyb.design` to Hephaestus motion families, with
  detailed adaptation notes, example code snippets, and an explicit list of
  reference behaviors intentionally left out.
- Added external-reference sections to `DESIGN_LANGUAGE_VISUAL.md` and
  `DESIGN_LANGUAGE_MOTION.md` translating selective Cybercore and Vaporwave
  traits into Hephaestus-safe visual and motion motifs.
- Recorded that Cybercore contributes more strongly than Vaporwave to the
  product direction, especially for HUD framing, scanline texture, hardware
  motifs, warning markers, scan motion, trace motion, and restrained signal
  pulse behavior.
- Recorded that Vaporwave is only admissible in reduced structural forms such
  as wireframe ground planes, compressed old-web framing, and subtle spatial
  continuity during large graph-surface transitions.
- Explicitly documented the left-out qualities from both references so future
  component work does not drift into pastel nostalgia, decorative glitch
  culture, iridescent glam-tech, or state-free atmospheric motion.
- Added the Hephaestus theme as a restrained secondary layer in the design
  language, explicitly subordinate to the cyber-brutalist backbone.
- Recorded the best-fit thematic seams for Hephaestus: artifacts, validation,
  node drill-in, and mechanical motion character rather than mythology-forward
  ornament.
- Added a visual guidance section listing safe Hephaestus-themed motifs,
  sparing-use motifs, rejected motifs, and the product surfaces where the
  theme is strongest versus weakest.
- Added `DESIGN_LANGUAGE_VOCABULARY.md` as a new linked design-language
  document covering product voice, naming rules, status copy posture, and the
  allowed boundaries for Hephaestus-themed language.
- Extended `DESIGN.md` with a secondary Hephaestus token layer so forge-style
  framing, blueprint surfaces, inspection details, serial markers, and runtime
  energy accents can be implemented consistently instead of improvised.
- Updated the design-system role directive and folder index so vocabulary is
  now treated as a first-class owned part of the design system alongside
  tokens, component guidance, and canonical design direction.
- Expanded `claude.md` from a narrow role directive into a combined directive
  and folder index so it now acts as the fast-entry navigation file for the
  entire design-system bundle.
- Added folder map, authority order, reading sequence, current design
  hierarchy, and explicit scope boundaries to `claude.md` so the current stack
  can be understood from one file.
