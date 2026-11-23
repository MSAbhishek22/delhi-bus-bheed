# Design constitution — Delhi Bus Bheed, Phase 2

Written 23 Nov 2026, before the Phase 2 build, per the ABHI_22 Blueprint
Part V (design research → unique constitution → build).

## Identity: "The city as a departure board"

Phase 2 is a living twin, so the page should feel like the board at a big
terminus that happens to show the whole city: a deep ink-green board panel
carrying the network twin and the simulation clock, set into a warm paper
page. Numbers are set like departure-board figures — tabular, mono, large.
Everything else stays quiet so the board is the loudest thing on the page.

- **Layout:** wide (1180px) dashboard flow — hero → problem → solution →
  the twin (full-bleed dark board) → planner (split: controls left, curve
  and verdict right) → outcome strip → honest limits. Phase 1 was a single
  narrow column; Phase 2 is a console.
- **Typography:** system grotesque for text; a mono face (ui-monospace) for
  the clock, figures and hour ticks — the departure-board voice.
- **Colour:** warm paper `#f5f1e8`, ink `#14201a`, board panel `#0d1512`
  with phosphor-green `#57d992` accents. The three band colours stay the
  product language (red / amber / green) but the green band shifts to the
  phosphor tone on the board. No purple-blue gradients, no glass blobs.
- **Motion language:** the clock *ticks* — when the simulated hour changes,
  nodes pulse once (scale/opacity) and flows redraw; sections rise in on
  scroll (IntersectionObserver, transform/opacity). Nothing drifts or
  floats; motion is tied to time, like the product. Reduced-motion: the
  clock still changes hour (user's control) but pulses and reveals stop.
- **The spatial feature:** the network twin itself — a schematic,
  explorable map of the city's busiest stops and the real passenger flows
  between them, laid out by a force algorithm over real Oct 2026 flows.
  Labelled "schematic — stops placed by flow, not by geography" on screen.

## References inspected (patterns only — nothing copied)

Inspected 23 Nov 2026 from the user's standing reference set:

1. **dark.design** — dark UI gallery; took: restraint on dark surfaces,
   one accent colour doing all the work (our phosphor green on ink-green).
2. **minimal.gallery** — took: the hero discipline — one huge statement,
   one action, nothing else above the fold.
3. **land-book.com** — took: landing structure proof — problem and outcome
   as their own full sections, not footnotes under the tool.
4. **21st.dev** — took: component polish — segmented controls, tick-mark
   sliders, chips with clear selected states for the clock + planner.
5. **gsap.com** — took: scroll-reveal rhythm (elements rise once, in
   sequence, then rest) — implemented with IntersectionObserver + CSS,
   no library.
6. **threeui.com** — took: the idea of depth in a data scene — twin nodes
   carry a soft pulse ring and flows sit under nodes, giving the board a
   shallow 3D feel without a 3D library.

Not copied: no layouts, text, code or assets from any of these.

## How Phase 2 differs from the fleet's recent work

- **Verity** (dark glass "research instrument", amber/cyan, serif display):
  Bheed is paper-light with a single dark board, mono figures, no glass,
  no serif. Different metaphor (terminus board vs laboratory instrument).
- **Bheed Phase 1** (light Swiss + glassmorphism blobs, narrow column,
  form-then-answer): Phase 2 keeps the paper and the band colours but drops
  the glass and blobs, widens into a console, and leads with a living
  spatial view instead of a form.
- **Saans / Hostel Dost** (soft consumer cards): Bheed is a data console —
  denser, more tabular, built for scanning a whole day at a glance.

## Registry note

This file is the project's entry in the design registry for the fleet:
identity "departure board / city twin", recorded 23 Nov 2026. The next
project must differ from this in metaphor, layout and motion language,
not just in accent colour.
