# Kitni Bheed Hai? — Delhi Bus Crowdedness Check

A prototype web app for the **Delhi Transport Stack Hackathon, Problem 2**
(crowdedness-aware journey planner), built by Team ABHI X AAYUSHI.
Prototype submission due 24 Nov 2026.

## What it does

Pick a Delhi bus route and the hour you want to travel. The app tells you how
crowded that route usually is at that hour, in three plain bands:

- **Bahut bheed** — very crowded for this route
- **Khadi bheed** — fairly crowded, standing likely
- **Aaram se seat milegi** — quiet for this route, seat likely

It also shows the route's full 24-hour pattern as a tappable strip, and
suggests the nearest quieter hour within ±3 hours — or says honestly when
nearby hours are just as crowded.

## How to run it

Static site, no build step. The page loads `crowdedness.json` at runtime, so
serve the folder over HTTP (opening `index.html` by double-clicking will make
the browser block the data file; the page explains this if it happens):

```
cd app
python3 -m http.server
# open http://localhost:8000
```

## Phase 2 — the twin (added 23 Nov 2026, for the Phase 2 sprint)

The page is now a small landing site around the planner:

- **Hero → problem → what we built → the twin → the planner → outcome →
  method and limits**, as distinct sections.
- **The twin:** a schematic board of the 110 busiest boarding stops and the
  170 strongest real passenger flows between them, with a simulation clock
  that replays a typical October day hour by hour. It is labelled on screen
  as what it is — a **pattern simulation from Oct 2026 e-ticket data, not
  live information**. Stop positions are computed from passenger flows by a
  force layout; the data has no coordinates, so the board is a schematic,
  never a map.
- **The planner, deepened:** the Phase 1 verdict and day strip are unchanged,
  and now sit next to the route's crowding curve (real boardings per hour,
  tap a bar to jump), its quiet windows, a leave-now-or-later comparison with
  real boarding counts, and a "start from a stop" view (routes from each of
  the 110 busiest stops, quietest first at the chosen hour). One clock runs
  the whole page.
- **The what-if:** for the 40 busiest routes, stop the route for one
  simulated hour and see where its load goes — shared to the other routes
  starting at the same stops, in proportion to their boardings there. The
  model is stated on the page and in `../model/TWIN_NOTES.md`, including
  what it leaves out.

## Files

- `index.html` — the whole app (HTML + CSS + JS in one file)
- `crowdedness.json` — the Phase 1 model output (bands per route)
- `twin.json` — the Phase 2 model output (city pulse, stops, flows, route
  hours, what-if base data), built by `../model/build_twin.py`

## Data source

Delhi bus e-ticketing data for one full month — **October 2026**:
2,559,899 tickets, 2,753,606 boardings, 1,249 base routes
(direction suffixes UP/DOWN merged). Boardings were counted per route per
hour, then each route's 24 hours were ranked against that route's own day:
its 8 busiest hours = "bahut bheed", next 8 = "khadi bheed", 8 quietest =
"aaram se seat milegi". See `../model/MODEL_NOTES.md` and
`../model/build_model.py` for the full method and the peak/off-peak
spot-check (passes on the three busiest routes).

## Honest limits

- **October patterns only.** The bands describe how October 2026 usually
  looked. They say nothing about today specifically.
- **No live bus positions.** This is not real-time information. A cancelled
  bus, rain, or a festival day will not show up here.
- **Bands are relative to each route's own day.** "Bahut bheed" means busy
  *for that route*, not a fixed number of people. A small route at its
  busiest hour and a trunk route at its busiest hour both show "bahut
  bheed", even though the trunk route carries far more people.
- **E-tickets are a sample.** Only about 3–4% of Delhi bus tickets are
  e-tickets, so boardings here are sample counts, not full ridership.
- Boardings are counted at the start stop of each ticket; how full the bus
  feels part-way along the route can differ.
- Hours with no e-tickets at all (late night on small routes) fall in the
  quietest band by construction.
