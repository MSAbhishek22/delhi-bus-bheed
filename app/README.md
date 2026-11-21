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

## Files

- `index.html` — the whole app (HTML + CSS + JS in one file)
- `crowdedness.json` — the model output the app reads (copied from `../model/`)

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
