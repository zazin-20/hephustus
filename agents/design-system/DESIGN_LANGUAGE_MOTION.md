---
title: Hephaestus Design Language - Motion
role: design-system
updated: 2026-07-09
owner: architect
---

# Design Language - Motion

Back to [DESIGN_LANGUAGE.md](DESIGN_LANGUAGE.md)

## Motion Principles

Motion should feel:

- mechanical
- stateful
- decisive
- sparse but meaningful

Use motion to communicate:

- graph activation
- state transitions
- inspector focus changes
- preflight updates
- artifact flow
- correction escalation

Avoid:

- floaty easing everywhere
- decorative motion with no information value
- playful bounce

Animation should support legibility first. If a transition makes evidence
harder to parse, the transition is wrong.

## Motion Primitives

Use a small, repeatable motion vocabulary:

- `snap-in`
- `trace-on`
- `signal-pulse`
- `hard-flash`
- `collapse-stack`
- `reroute-live`
- `freeze-shift`

## Motion System Decisions

Motion is family-driven first and component-driven second.

This means:

- components do not invent their own motion character by default
- each interaction maps into a motion family
- family rules define timing, easing, and behavior
- component-level exceptions must be deliberate and rare

### Core Motion Families

- `transit`: route, view, and mode changes
- `hover-preview`: low-commitment affordance preview
- `field-focus`: editable field activation and focused authoring state
- `lock-primary`: primary selection acquisition
- `lock-secondary`: related or subordinate focus acquisition
- `disclose-inline`: local detail reveal inside a stable surface
- `disclose-structural`: reveal that changes layout or hierarchy
- `pending-scan`: connecting, loading, and unresolved system waiting
- `pulse`: persistent runtime-significant status motion
- `trace-flow`: spatial graph flow and artifact travel
- `trace-stream`: temporal output accumulation and live stream activity
- `reroute`: structural movement, drag release, and geometry settle
- `commit-local`: small local completion or confirmation
- `commit-structural`: graph, runtime, or governance-changing completion
- `alarm-soft`: caution, degraded, or override-eligible emphasis
- `alarm-hard`: blocked, failed, incompatible, or hard-stop emphasis
- `dismiss-neutral`: close, retract, cancel, or non-destructive exit
- `dismiss-destructive`: removal or deletion of structure or content
- `revert`: explicit undo or rollback
- `focus-visible`: keyboard focus and non-pointer focus traversal

### Family Timing Bands

Each family has one default timing band. Exceptions are allowed only when
clearly justified by legibility or direct-manipulation needs.

- `hover-preview`: 70-110ms
- `field-focus`, `focus-visible`: 90-140ms
- `lock-primary`, `lock-secondary`, `dismiss-neutral`, `dismiss-destructive`: 90-140ms
- `commit-local`, `commit-structural`, `alarm-soft`, `alarm-hard`, `revert`: 140-180ms
- `transit`, `disclose-inline`, `disclose-structural`, `pending-scan`: 180-240ms
- `reroute`, `trace-flow`, `trace-stream`: 220-320ms when timed
- `pulse`: persistent loop, not a one-shot duration

### Family Easing Character

Each family has its own easing character.

- `hover-preview`: light fast-out, no lock-in feel
- `field-focus`: quick structural wake-up, stable while active, clean return on blur
- `focus-visible`: crisp structural outline acquisition, no celebratory feel
- `lock-primary`: hard-out, fast snap, no softness
- `lock-secondary`: lighter hard-out, clearly subordinate to primary focus
- `dismiss-neutral`: fast-out, low emotional weight
- `dismiss-destructive`: firmer retract or collapse with stronger subtraction
- `commit-local`: firm ease-out, minimal travel
- `commit-structural`: firmer settle with clearer completion lock-in
- `alarm-soft`: restrained sharp ease-out, one brief emphasis
- `alarm-hard`: sharper onset, stronger contrast hit, may hold while unresolved
- `transit`: controlled structural ease
- `disclose-inline`: tight mechanical reveal
- `disclose-structural`: slightly heavier spatial reveal
- `pending-scan`: infrastructural, procedural, unresolved
- `reroute`: input-coupled during gesture, short settle after release
- `trace-flow`: mostly linear and directional
- `trace-stream`: stepped or progressive, tied to accumulation and recency
- `pulse`: restrained loop curve, rhythmic not breathing-like
- `revert`: clear reversal, not deletion and not celebration

## Motion Rules

### Hover Preview Rule

Hover is its own low-commitment motion layer. It must not borrow the weight of
selection, commit, or alarm behavior.

Hover may communicate:

- this surface is interactive
- this control can expand
- this row is selectable
- this graph object can be inspected

Hover must not imply:

- selection already happened
- confirmation already happened
- a state transition already occurred

Default hover behavior:

- light contrast or border wake-up
- minimal positional response, if any
- no heavy glow
- no strong frame acquisition
- no success or failure semantics

Runtime-significant hover may be slightly stronger than ordinary hover, but it
must remain clearly subordinate to `lock-secondary`.

### Field Focus Rule

Editable field activation is its own motion class. It is not hover, not
selection, and not commit.

This applies to:

- text inputs
- textareas
- selects
- editable contract fields
- structured authoring controls

Behavior:

- focus-in: quick structural wake-up through border, label, or inset emphasis
- active typing: no looping motion, only a stable focused state
- blur with no change: clean return to neutral
- blur after change: optional `commit-local` confirmation may occur elsewhere,
  but not inside the field itself

Field focus should feel tool-like, precise, and calm.

### Disabled And Unavailable State Rule

Disabled and unavailable states should be motionless by default after any
transition into that state has completed.

This applies to:

- disabled controls
- reserved fields
- unavailable providers or models
- inactive mode-only controls
- blocked-until-enabled actions

These states should communicate through:

- reduced contrast
- clear structural disablement
- explicit labeling
- cursor and affordance changes

They should not use ongoing attention-seeking animation.

Exception:

- if a surface becomes newly blocked because of a user action, a one-time
  `alarm-soft` or related explanatory transition may announce the change
- after that transition, the surface should settle into stillness

### One-Shot Motion vs Persistent Motion

Persistent motion is a separate layer from one-shot interaction motion.

One-shot motion communicates change:

- selection
- reveal
- save
- confirm
- reject
- delete
- reroute settle
- mode switch

Persistent motion communicates ongoing state:

- active node
- waiting human
- live streaming trace
- active artifact flow
- degraded provider when operationally meaningful
- current running step

Persistent motion is allowed only on runtime-significant state. It is banned
from general chrome and decorative surfaces such as:

- sidebar chrome
- static headers
- normal cards
- routine form fields
- decorative backgrounds
- passive inventory surfaces

### Direct Manipulation Rule

Direct manipulation is input-coupled, not duration-coupled.

During manipulation:

- dragging follows the pointer directly
- wire handles follow the pointer directly
- geometry updates in real time
- no easing should pull the object toward the cursor

After release:

- a short `reroute` settle may resolve geometry
- settle motion should clarify final structure, not add flourish

### Cross-Surface Choreography

Consequential actions may trigger restrained choreography across related
surfaces rather than animating only the clicked element.

This is allowed only when the action changes graph, runtime, or governance
state.

Rules:

- choreograph at most 2-3 directly related surfaces
- one surface leads and the others confirm
- choreography should be sequential, not simultaneous
- confirmation surfaces should follow in a short 30-80ms stagger
- use no more than 2 follow-up surfaces after the lead surface
- choreography must explain cause and effect
- choreography must not become theatrical or ambient

Examples:

- selecting a node:
  primary node `lock-primary` -> related edges `lock-secondary` -> inspector `disclose-structural`
- confirming an ask edge:
  edge `commit-structural` -> waiting state clears -> downstream runnable state appears
- hard-stop preflight failure:
  failing row `alarm-hard` -> related node or edge receives mapped blocker emphasis
- saving a correction:
  correction surface `commit-structural` -> learning marker appears -> rule history updates

### Scrolling Rule

Scrolling should stay mostly native and motion-light.

Allow only:

- sticky header settle
- local reveal-on-entry where structural orientation benefits from it
- subtle progress emphasis in long evidence stacks, if truly useful

Do not use:

- ornamental parallax
- scroll storytelling
- decorative linked-motion backgrounds

### Reduced Motion Rule

Reduced-motion support must be family-aware, not just `animation: none`.

Keep:

- semantic state changes
- structural visibility changes
- critical selection and focus information

Reduce or remove:

- pulse loops
- long trace motion
- nonessential choreography
- heavy reveal travel

### System-Initiated Update Rule

System-initiated updates should not look identical to user-initiated commits.

Use:

- `commit-*` for user-caused actions
- `trace-stream`, `pending-scan`, or `alarm-*` for system-driven state changes,
  depending on meaning

### Live Data Append Rule

Incoming live data should append progressively instead of reanimating an entire
container.

Only new rows, chunks, or evidence additions should animate.
Existing transcript, trace, and evidence blocks should remain stable.

### Motion Conflict Priority Rule

When multiple motion classes compete on the same surface, this priority order
wins:

1. `alarm-hard`
2. `alarm-soft`
3. `lock-primary`
4. `commit-structural`
5. `disclose-structural`
6. `trace-flow` / `trace-stream`
7. `hover-preview`

Higher-priority motion suppresses lower-priority motion on the same surface.

### Repeated Alert Rule

Repeated alerts should degrade in intensity if the same unresolved state
persists.

The first hit gets emphasis. Ongoing unresolved state should settle into a held
visual condition instead of repeatedly shouting.

### Ambient Motion Rule

Background ambient motion is effectively banned except for rare
runtime-significant contexts.

Do not use:

- drifting decorative backgrounds
- idle glows in general chrome
- ambient loop activity in passive surfaces

### Staggered Entrance Rule

Staggered entrance motion is reserved for:

- first mount
- shell boot
- major structural reveal

It should not be used for ordinary updates.

### Mobile And Touch Rule

Mobile and touch should use the same motion families with:

- reduced amplitude
- reduced choreography depth
- shorter distances
- fewer linked surfaces per action

### Spatial Origin Rule

Selection-to-inspector transitions should preserve spatial origin where
possible.

When a node or edge opens related inspection, the inspection surface should feel
causally linked to the selected source rather than appearing arbitrarily.

### Calm Resolution Rule

Empty states and all-clear states should stay mostly still.

No celebratory motion is needed for "nothing is wrong." Calm, resolved, static
presentation is preferred.

### Hard Motion Ban

The design language explicitly bans:

- bounce
- elastic overshoot
- breathing animations

These are not optional style preferences. They are incompatible with the motion
character of Hephaestus.

> Color note (2026-07-09): `signal-live` is now molten ember (forge heat), not
> cyan. Cyan rgba values in the example snippets below predate this change and
> should be read as `signal-live`.

## Distortion Motion Additions

Approved 2026-07-09 alongside the Signal Distortion Layer in
`DESIGN_LANGUAGE_VISUAL.md`. These extend, and obey, the existing family rules.

One-shot (fire once on cause, then hold or settle):

- `glitch-strike` (~180ms, stepped): alarm-hard companion for hard failure —
  a controlled RGB-split interruption, then the held blocked state
- `frame-tear` (~220ms, stepped): stale/outdated reveal — one tear, then whole
- `crt-power-on` (~520ms): first-mount shell boot only; replaces nothing else
- character scramble on annunciator lines (~180ms settle)

Persistent (bound to unresolved, degraded, held, or live state only):

- `interference`: radio bands on `pending-scan` surfaces
- `sig-flicker`: dropout flicker on degraded readiness markers
- `carrier-wave`: thin wave across a holding human-gate stripe
- `stream-hold`: horizontal-hold shimmer while output genuinely streams
- `static-crawl`: dithered static on boot/connecting surfaces

Rules:

- distortion loops follow the same ban as all persistent motion: never on
  chrome, passive lists, or resolved states
- `glitch-strike` shares alarm-hard's position at the top of the motion
  conflict priority order
- reduced motion removes every distortion loop and collapses one-shots to
  effectively instant state changes

## External Motion References

External references are used as selective inspiration, not as behavior
templates to copy wholesale.

Reference reviewed for this phase:

- [eloyb.design](https://eloyb.design/)

Important constraint:

- the available reference evidence here is strongest in the site's coded,
  terminal-like copy, interaction framing, and project descriptions
- the fit analysis below is therefore partly inferential
- we are adapting motion character, not recreating portfolio theatrics

### Reference Fit: `trace-stream`

Why it fits:

- the reference homepage uses code-like framing such as `function()`,
  `randomfacts array`, coordinate readouts, and operational status language
- this supports a stepped, accumulating, terminal-like stream behavior
- that maps well to transcript, trace, tool output, and live thinking streams

Reference source:

- [eloyb.design homepage](https://eloyb.design/)

Hephaestus adaptation:

- stream output should append in discrete, recent-first readable steps
- new output should feel emitted, not faded in decoratively
- old output should remain stable while only new lines receive motion

Example adaptation:

```css
.trace-stream-line--new {
  animation: trace-stream-in 180ms steps(3, end) both;
}

@keyframes trace-stream-in {
  0% {
    opacity: 0;
    transform: translateY(4px);
    filter: blur(1px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
    filter: blur(0);
  }
}
```

Use on:

- live transcript rows
- tool output lines
- thinking/event stream rows

### Reference Fit: `pending-scan`

Why it fits:

- the reference homepage reads like a live coded status surface
- phrases such as current status, connect, availability, and direct state
  descriptors suggest unresolved procedural status rather than friendly loading

Reference source:

- [eloyb.design homepage](https://eloyb.design/)

Hephaestus adaptation:

- connecting, awaiting provider readiness, or loading run context should feel
  infrastructural and unresolved
- the motion should imply "system check in progress", not "brand animation"

Example adaptation:

```css
.pending-scan {
  position: relative;
  overflow: hidden;
}

.pending-scan::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(88, 207, 255, 0.18) 45%,
    transparent 100%
  );
  transform: translateX(-100%);
  animation: pending-scan-pass 1.1s linear infinite;
}

@keyframes pending-scan-pass {
  to {
    transform: translateX(100%);
  }
}
```

Use on:

- provider connecting state
- loading run snapshot
- unresolved preflight recomputation

### Reference Fit: `lock-primary` and `commit-structural`

Why it fits:

- the reference repeatedly uses direct imperative calls such as `CLICK TO
  CONNECT` and `TAP TO CONNECT`
- that supports a hard invitation followed by decisive commitment
- this is a good fit for primary selection and consequential runtime commits

Reference source:

- [eloyb.design homepage](https://eloyb.design/)

Hephaestus adaptation:

- selecting the primary node or edge should feel like acquiring control
- confirming an ask edge or placing a graph element should feel load-bearing
- no soft easing, no celebratory flourish

Example adaptation:

```css
.lock-primary-acquire {
  animation: lock-primary-hit 120ms cubic-bezier(.18, .84, .32, 1) both;
}

@keyframes lock-primary-hit {
  0% {
    transform: translateY(2px) scale(.985);
    box-shadow: inset 0 0 0 0 rgba(88, 207, 255, 0);
  }
  100% {
    transform: translateY(0) scale(1);
    box-shadow: inset 0 0 0 2px rgba(88, 207, 255, 0.52);
  }
}
```

```css
.commit-structural-done {
  animation: commit-structural-settle 170ms cubic-bezier(.16, .88, .24, 1) both;
}

@keyframes commit-structural-settle {
  0% {
    transform: scale(.985);
    border-color: rgba(123, 242, 192, 0.28);
  }
  100% {
    transform: scale(1);
    border-color: rgba(123, 242, 192, 0.58);
  }
}
```

Use on:

- primary node selection
- edge confirm
- save node / save artifact
- add graph edge

### Reference Fit: `disclose-inline`

Why it fits:

- the reference has a coded, ASCII-like, condensed presentation style
- that supports tight, local reveals rather than soft accordion behavior
- Hephaestus evidence surfaces benefit from contained disclosure rather than
  theatrical unfolding

Reference source:

- [eloyb.design homepage](https://eloyb.design/)

Hephaestus adaptation:

- inline reveals should feel like exposing additional evidence, not opening a
  consumer FAQ
- local structure should remain intact while detail density increases

Example adaptation:

```css
.disclose-inline-enter {
  animation: disclose-inline-open 190ms cubic-bezier(.2, .78, .28, 1) both;
  transform-origin: top;
}

@keyframes disclose-inline-open {
  0% {
    opacity: 0;
    transform: translateY(-4px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}
```

Use on:

- trace row expansion
- context subsection reveal
- rule detail reveal
- inline evidence expansion

### Reference Fit: `alarm-hard` in a Reduced Form

Why it fits:

- the reference project list explicitly contains glitch-art and experimental
  motion language
- the right lesson is not "glitch everything"
- the usable lesson is that true disruption can be sharp and singular

Reference source:

- [eloyb.design homepage](https://eloyb.design/)

Hephaestus adaptation:

- hard failure should feel like a controlled interruption
- use a single sharp disruption or frame-hit, then settle into a held blocked
  state
- never loop theatrical glitch behavior in normal operation

Example adaptation:

```css
.alarm-hard-hit {
  animation: alarm-hard-strike 150ms linear both;
}

@keyframes alarm-hard-strike {
  0% {
    transform: translateX(0);
    filter: none;
    border-color: rgba(255, 127, 149, 0.22);
  }
  30% {
    transform: translateX(-2px);
    filter: saturate(1.15);
    border-color: rgba(255, 127, 149, 0.85);
  }
  100% {
    transform: translateX(0);
    filter: none;
    border-color: rgba(255, 127, 149, 0.58);
  }
}
```

Use on:

- failed gate state
- missing required input
- incompatible artifact contract
- hard-stop preflight failure

### Reference Fit: `transit` and `disclose-structural` in a Reduced Form

Why it fits:

- the reference project descriptions mention GSAP-heavy creative transitions
- for Hephaestus, the useful lesson is staged structure, not portfolio drama
- larger structural changes should feel architectural and ordered

Reference source:

- [eloyb.design homepage](https://eloyb.design/)

Hephaestus adaptation:

- structural reveals should occur in clear stages
- mode and view changes should read as system reconfiguration
- do not use cinematic page wipes or expressive hero choreography

Example adaptation:

```css
.transit-structural {
  animation: transit-structural-swap 220ms cubic-bezier(.22, .74, .25, 1) both;
}

@keyframes transit-structural-swap {
  0% {
    opacity: 0;
    transform: translateY(8px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}
```

Use on:

- Author Mode to Run Mode
- inventory to template review
- inspector structural open
- docked panel replacement

## Reference Rejections From `eloyb.design`

The following qualities are intentionally left out of Hephaestus:

- decorative glitch loops
- ambient artistic motion
- landing-page hero theatrics
- expressive portfolio transitions for ordinary chrome
- decorative background drift
- motion whose job is mood rather than state explanation

Reason:

- Hephaestus is an operational control plane
- motion must explain state, causality, and runtime consequence
- expressive portfolio behavior is useful only when reduced into precise,
  system-readable motion grammar

## Supplementary Motion References

These references refine specific motion families but do not change the core
motion system.

References reviewed for this phase:

- [Cybercore Visual Elements - Shapes](https://shapes.inc/fandom/cybercore/visual-elements)
- [Vaporwave - Wikipedia](https://en.wikipedia.org/wiki/Vaporwave)

### Reference Fit: Cybercore for `pending-scan`, `trace-flow`, `pulse`, and `alarm-soft`

Why it fits:

- Cybercore strongly emphasizes neon-on-dark HUD overlays, scanlines, warning
  cues, and stressed-system framing
- that maps naturally to unresolved computation, active graph flow, and
  degraded-but-not-failed runtime states
- the usable lesson is infrastructural energy, not decorative overload

#### `pending-scan`

Cybercore strengthens the idea that waiting states should feel like active
system checks rather than passive brand loading.

```css
.pending-scan--hud::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(
      90deg,
      transparent 0%,
      rgba(88, 207, 255, 0.18) 42%,
      rgba(88, 207, 255, 0.28) 50%,
      rgba(88, 207, 255, 0.18) 58%,
      transparent 100%
    );
  transform: translateX(-100%);
  animation: pending-scan-hud 1s linear infinite;
}

@keyframes pending-scan-hud {
  to {
    transform: translateX(100%);
  }
}
```

Use on:

- provider connection checks
- run boot sequence
- preflight recomputation

#### `trace-flow`

Cybercore's circuitry language is useful when translated into directional edge
motion.

```css
.edge--trace-flow-active path {
  stroke-dasharray: 10 8;
  animation: trace-flow-circuit 900ms linear infinite;
}

@keyframes trace-flow-circuit {
  to {
    stroke-dashoffset: -18;
  }
}
```

Use on:

- live artifact movement
- active downstream execution path
- fan-out edges during live run

#### `pulse`

Pulse should feel like a held energized state, not a breathing organism.

```css
.node--active-runtime {
  animation: runtime-pulse-cyber 1.4s steps(2, end) infinite;
}

@keyframes runtime-pulse-cyber {
  0%, 100% {
    box-shadow: inset 0 0 0 2px rgba(88, 207, 255, 0.45);
  }
  50% {
    box-shadow: inset 0 0 0 2px rgba(88, 207, 255, 0.7);
  }
}
```

Use on:

- active node
- current streaming surface
- currently awaited human-gate edge

#### `alarm-soft`

Cybercore warning markers justify a firmer caution emphasis without escalating
to hard failure behavior.

```css
.alarm-soft--warning {
  animation: alarm-soft-caution 160ms cubic-bezier(.2, .8, .28, 1) both;
}

@keyframes alarm-soft-caution {
  0% {
    border-color: rgba(255, 196, 82, 0.28);
    background-color: rgba(255, 196, 82, 0);
  }
  100% {
    border-color: rgba(255, 196, 82, 0.72);
    background-color: rgba(255, 196, 82, 0.08);
  }
}
```

Use on:

- override-eligible preflight items
- degraded provider warning
- waiting-for-human transition

### Reference Fit: Vaporwave in a Reduced Spatial Form

Why it fits:

- Vaporwave contributes mild wireframe and retro-digital spatial cues
- those cues can help large canvas surfaces feel computational
- it does not define interaction weight, confirmation, or alert character

#### Reduced `transit`

Vaporwave only supports the idea that large graph surface changes can preserve
spatial atmosphere through subtle grid continuity.

```css
.canvas-transit--grid-shift::after {
  content: "";
  position: absolute;
  inset: 0;
  opacity: 0.12;
  transform: translateY(8px);
  animation: canvas-grid-settle 220ms cubic-bezier(.22, .74, .25, 1) both;
}

@keyframes canvas-grid-settle {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 0.12;
    transform: translateY(0);
  }
}
```

Use on:

- author-mode to run-mode shell swaps
- graph-load entry
- empty-state to active-graph entry

Rule:

- never let this become dreamy or atmospheric enough to distract from runtime
  state

### Supplementary Reference Left-Out List

These source qualities remain intentionally excluded from the motion language.

From Cybercore:

- constant glitch loops
- datamosh transitions
- chromatic aberration as animation
- overload motion on passive surfaces
- motion whose only goal is sensory intensity

From Vaporwave:

- dreamy drift
- nostalgia-first transitions
- slow surreal fades
- decorative VHS wobble
- mood-led motion detached from state change

## Animation Inventory

### 1. Global Shell

Required motion:

- app-load reveal for sidebar, topbar, and primary stage
- route or component-switch transition inside the gallery stage
- toast entry and exit for save, run, confirm, reject, and artifact actions
- hover and pressed states for navigation rows, pills, chips, and buttons
- sticky-topbar settle behavior while scrolling dense inspectors

### 2. Workflow Command Center

Required motion:

- default entry into Run Mode as the primary command surface
- Author Mode to Run Mode switch with clear shell-state change
- live snapshot to draft snapshot transition with freeze semantics
- legend open and collapse transitions
- filter activation that dims non-matching graph elements instead of hiding them instantly
- graph lock state when a live run starts

### 3. Runtime Nodes On The Canvas

Required motion:

- node selection lock-in
- active-node pulse
- blocked-node failure emphasis
- waiting-human hold state
- outdated-node stale marker reveal
- learning-candidate escalation marker
- retry-attempt count updates
- pause and resume transitions
- pinned-inspector vs live-follow state change

### 4. Artifact Edges And Wires

Required motion:

- edge trace-on when an artifact becomes active
- edge-state change between healthy, incompatible, missing input, and awaiting confirmation
- artifact fan-out reveal when one produced artifact feeds multiple downstream edges
- edge selection emphasis
- inline ask-edge confirmation and rejection state changes
- manual wire-edit handle reveal in Author Mode only
- live reroute during purely visual wire editing
- artifact capsule preview expansion when an edge is inspected

### 5. Preflight Dock

Required motion:

- dock entry when validation is first computed
- row insertion and removal as readiness changes
- severity changes between green, amber, and red
- hard-stop red failure reveal
- amber override eligibility reveal
- per-run override rationale capture confirmation
- runnable-node list refresh after graph edits

### 6. Node Drill-In Inspector

Required motion:

- inspector open from node selection
- pinned vs live-follow transition
- stale-vs-active hint when inspector focus no longer matches the active node
- section expansion and collapse for transcript, trace, gates, and corrections
- jump-to-related-edge or related-node transition
- produced-artifact preview reveal
- violation foregrounding and resolved-history reveal

### 7. Context Preview

Required motion:

- summary-first load state
- expand-all transition into full payload visibility
- per-section expansion for directives, skills, artifacts, specs, replayed context, and frozen rules
- diff or change emphasis when context changes between attempts
- frozen-rule injection reveal

### 8. Human Gates And Ask Edges

Required motion:

- awaiting-confirm pulse
- confirm completion state
- reject-to-pause transition
- mandatory-reason field activation on reject
- resume-after-revision transition
- attempt-lineage continuity after resume

### 9. Corrections And Learning

Required motion:

- candidate-learning surfacing after repeated failures
- recommendation emphasis on narrowest valid scope
- promotion from candidate to frozen rule
- supersede and disable history reveal
- provenance jump from rule to originating run or trace
- graph-visible learning marker activation

### 10. Library And Template Surfaces

Required motion:

- inventory view to templates-and-updates view transition
- readiness or degradation signal changes for providers and engines
- update-available markers on reusable nodes
- template-instantiation placeholder reveal
- unresolved-placeholder blocker emphasis
- explicit opt-in update review for pinned workflow assets

### 11. Authoring Forms And Contract Editors

Required motion:

- node-editor section switching without tab-like dead cuts
- artifact-binding add and remove transitions
- compatibility hint reveal when a binding is valid or invalid
- output-artifact ownership emphasis
- field-level validation reveal for contracts, allowed tools, paths, providers, and models
- save confirmation for node, artifact, and edge edits

### 12. Interactive Canvas Editing

Required motion:

- node drag start, drag hold, and drop settle
- live edge rerouting while nodes move
- visual wire-edit handle activation
- selected-port emphasis before a wire is placed
- edge-add confirmation
- mode-aware control reveal so authoring controls do not pollute Run Mode

## Immediate Motion Priorities

The first motion pass should focus on the surfaces that most strongly define the
product:

1. Workflow command center
2. Runtime nodes on the canvas
3. Artifact edges and ask edges
4. Preflight dock
5. Node drill-in inspector
6. Context preview
