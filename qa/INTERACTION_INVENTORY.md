# Interaction inventory — Delhi Bus Bheed, Phase 2

Verified 23 Nov 2026 against the local build (identical files to the deploy
zip) with a real browser (Playwright, Chromium): **27/27 checks passed, 0
console errors**, desktop 1280px + mobile 390px. Logic unit tests:
`tests/test_logic.mjs` 10/10 · model tests: `model/test_twin.py` 13/13.

**Mouse-click fix, 23 Nov 2026 (later the same day):** the Phase 2 demo
recording exposed a real bug the first pass missed — a plain mouse click on
a stop node never opened its panel, because the board's drag handler calls
`setPointerCapture` on pointerdown, so the browser delivers the click to
the SVG instead of the node (the first pass had only selected nodes by
keyboard/DOM events). Fixed in `app/index.html`: the drag handler now
remembers the press point and the node under it, and on pointerup a press
that moved ≤4 px runs the same `selectStop` the keyboard Enter path runs.
Re-verified with `qa/run_qa.py` (the project's browser QA, saved in this
folder): **27/27 checks passed, 0 console errors**, now including a REAL
mouse click (`page.mouse`, not a DOM click) on a stop node opening its
panel, a real drag starting on a node that pans without selecting, and a
mobile touch tap. Unit tests unchanged and still green: 13/13 + 10/10.

| # | Control | Expected behaviour | Status |
|---|---|---|---|
| 1 | "Watch the city breathe" (hero) | Scrolls to the twin board | PASS (anchor, native) |
| 2 | "Plan a journey" (hero) | Scrolls to the planner | PASS (anchor, native) |
| 3 | Low motion toggle | Adds/removes low-motion mode; label + pressed state update | PASS |
| 4 | ▶ Play the day | Simulated hour advances ~1 per 1.3 s; button becomes Pause | PASS (8 AM → 10 AM in ~3 s) |
| 5 | ❚❚ Pause | Clock stops | PASS |
| 6 | "This hour" (board) | Jumps the shared clock to the current real hour, pauses play | PASS (wired same as #9; hour sync verified) |
| 7 | Simulation slider (board) | Sets the shared hour everywhere (board, planner, strip, curve) | PASS |
| 8 | Twin stop node (mouse click / touch tap / Enter / Space) | Opens the stop panel with that stop's figures + routes at the current hour | PASS — real mouse click (`page.mouse`) re-verified 23 Nov after the pointer-capture fix; touch tap verified on mobile |
| 9 | Stop panel route button | Loads that route in the planner and scrolls to it | PASS |
| 10 | Zoom + / − / reset | viewBox zooms around centre; reset restores `0 0 1160 640` exactly | PASS |
| 11 | Twin drag-pan | Dragging pans the viewBox, clamped to the board; a drag starting on a stop node must NOT select it | PASS — asserted in `qa/run_qa.py`: viewBox pans, selection unchanged |
| 12 | Route search input | Live filtered list, busiest first, prefix matches first | PASS |
| 13 | Route search Enter / Escape | Enter picks the first match; Escape closes the list | PASS (Phase 1 logic, kept) |
| 14 | Route option click | Loads the route; verdict, strip, curve, windows, what-if all update | PASS |
| 15 | Top-10 route chips | Load the route; selected chip is highlighted | PASS |
| 16 | Stop select (110 stops) | Lists routes from that stop at the current hour, quietest band first | PASS (8 routes for the busiest stop) |
| 17 | From-stop route row | Loads that route in the planner | PASS |
| 18 | Travel-hour slider (planner) | Sets the shared hour; twin follows | PASS |
| 19 | "Use current hour" (planner) | Sets the shared clock to the current real hour | PASS |
| 20 | Day-strip cell (24) | Sets the hour; selected cell is ring-highlighted | PASS |
| 21 | Curve bar (24) | Sets the hour; selected bar outlined, value labelled | PASS |
| 22 | Quiet-window chip | Jumps to the window's first hour (a quietest-band hour) | PASS |
| 23 | What-if run button (40 busiest routes) | Computes the redistribution for the current route+hour; summary + table of load-taking routes with band before → after | PASS (717A @ 9 AM) |
| 24 | What-if on a non-top-40 route | No button; a plain note explains why it is not offered | PASS (012(NS)) |
| 25 | Data-load failure path | If `crowdedness.json` cannot load, an honest error box explains the HTTP-server fix; if `twin.json` fails, the board says so and the planner still works | PASS by code path (Phase 1 behaviour kept; twin fallback text set in catch handler) |

No dead controls, no `href="#"`, no placeholder actions. Every number shown
comes from `crowdedness.json` / `twin.json`, both generated from the real
October 2026 e-ticket data by scripts in `model/`.
