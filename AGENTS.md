# AGENTS.md — Delhi Bus Bheed (Delhi Transport Stack, Problem 2)

Read this first, every session. Then read the ABHI_22 Unified Master Blueprint
(`~/workspace/abhi_22/ABHI_22_UNIFIED_MASTER_BLUEPRINT.md` — "READ THIS FIRST"
and Part V) — it is the single source of truth and outranks this file.

## What this project is

- Team **ABHI X AAYUSHI** (M S Abhishek + Aayushi Goel). Solo-facing work is
  Abhishek's; never invent a team member.
- Phase 1 (submitted 22 Nov 2026 on Where U Elevate): "Kitni Bheed Hai?" —
  crowdedness-aware journey planner from real Oct 2026 Delhi bus e-ticket data
  (2,559,899 tickets, 2,753,606 boardings, 1,249 base routes × 24 hours,
  3 bands relative to each route's own day).
- Phase 2 (build sprint from 25 Nov 2026; finale 11 Dec, IIIT Delhi): the
  THINKS upgrade — a living pattern-twin of the network. See
  `design/DESIGN_CONSTITUTION.md` and `model/TWIN_NOTES.md`.
- **Phase 1 filing is closed. Never touch, redo or "improve" the submission.**

## Hard rules for this project

1. **Truth over claims.** The data is a *pattern* from October 2026 e-tickets
   (a 3–4% sample of all tickets). Nothing in the app may claim or imply live
   bus positions or live crowding. The twin is a **pattern simulation** and is
   labelled that way on screen, always.
2. **No fabricated geography.** The dataset has stop names but no coordinates.
   The network view is a *schematic* layout computed from real boarding flows,
   labelled as schematic. Never place stops at invented map positions.
3. **Bands are relative to each route's (or stop's) own day** — 8 busiest hours
   = bahut bheed, next 8 = khadi bheed, 8 quietest = aaram se seat milegi.
   This is Phase 1's established product language; keep it, always with the
   English explanation beside it. All other copy is plain English, short
   sentences, no marketing words.
4. **Every visible control must work** — see `qa/INTERACTION_INVENTORY.md`.
   No dead buttons, no placeholder actions, no fake success states.
5. **Tests are never edited to pass.** Add tests for new logic; if a test
   fails, fix the code or report the failure honestly.
6. **Deploy route is fixed:** static folder → zip → Netlify Drop (the user's
   step) + source pushed to GitHub `MSAbhishek22/delhi-bus-bheed` via the
   connector. Do not invent credentials or other deploy routes.
7. Motion: transform + opacity only, `prefers-reduced-motion` respected,
   pause off-screen. No heavy libraries; the site must stay fast on a phone.

## Files

- `app/index.html` — the whole front end (single file, no build step)
- `app/crowdedness.json` — Phase 1 model output (bands per route) — do not regenerate casually
- `app/twin.json` — Phase 2 model output (city pulse, stops, flows, route hours, what-if base)
- `model/build_model.py` — Phase 1 model · `model/build_twin.py` — Phase 2 model
- `model/test_twin.py` — data-integrity tests · `tests/test_logic.mjs` — page-logic tests
- `design/DESIGN_CONSTITUTION.md` — Phase 2 design identity + references
- `qa/INTERACTION_INVENTORY.md` — every control, expected behaviour, status
