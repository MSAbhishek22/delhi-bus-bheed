#!/usr/bin/env python3
"""
Phase 2 twin model: stop-level, flow-level and what-if aggregates from the
same October 2026 Delhi bus e-ticket data Phase 1 used.

Outputs ../app/twin.json with:
  - city_hours: network boardings per hour (the city's pulse)
  - stops: busiest start stops, each with hourly boardings, own-day bands,
    schematic layout position, and the routes that start there (with their
    boardings at that stop, per hour)
  - flows: busiest start->end stop pairs (real passenger flows from tickets),
    with hourly boardings
  - route_hours: boardings per hour for every base route (for the planner
    crowding curve)
  - whatif: for the 40 busiest routes, the base data for the disruption
    what-if (see TWIN_NOTES.md for the exact model)

Positions are a force-directed schematic layout over the flow network.
The data has NO stop coordinates; positions mean "placed by flow", never
geography. The app labels this on screen.

Method notes and counts are written to TWIN_NOTES.md.
"""
import json
import math
import os
import random
from collections import defaultdict

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "data", "October-Delhi.csv")
OUT_JSON = os.path.join(HERE, "..", "app", "twin.json")
OUT_NOTES = os.path.join(HERE, "TWIN_NOTES.md")

TOP_STOPS = 110          # nodes in the twin
TOP_FLOWS = 170          # OD pairs shipped
WHATIF_ROUTES = 40       # busiest routes get what-if base data
WHATIF_STOPS = 5         # top start stops per what-if route
WHATIF_ALTS = 8          # top alternative routes per stop
STOP_ROUTES = 8          # routes listed per stop in the twin


def base_route(route: str) -> str:
    """Phase 1 rule: strip ONE trailing DOWN, else one trailing UP."""
    r = route.strip()
    if r.endswith("DOWN"):
        r = r[:-4]
    elif r.endswith("UP"):
        r = r[:-2]
    return r


def band_string(hours):
    """Phase 1 rule on any 24-hour series: rank hours busiest-first
    (ties: earlier hour first); ranks 1-8 'B', 9-16 'K', 17-24 'A'."""
    order = sorted(range(24), key=lambda h: (-hours[h], h))
    out = ["A"] * 24
    for rank, h in enumerate(order):
        out[h] = "B" if rank < 8 else ("K" if rank < 16 else "A")
    return "".join(out)


def main():
    route_hour = defaultdict(lambda: [0] * 24)
    stop_hour = defaultdict(lambda: [0] * 24)
    od_hour = defaultdict(lambda: [0] * 24)
    route_stop_hour = defaultdict(lambda: [0] * 24)
    city_hours = [0] * 24
    total_boardings = 0
    rows = 0

    cols = ["passenger_count", "end_stop_name", "route", "start_stop_name", "created_at"]
    for chunk in pd.read_csv(SRC, usecols=cols, chunksize=400_000,
                             dtype={"end_stop_name": str, "route": str,
                                    "start_stop_name": str, "created_at": str}):
        rows += len(chunk)
        chunk["hour"] = chunk["created_at"].str.slice(11, 13).astype(int)
        chunk["base"] = chunk["route"].fillna("").map(base_route)
        chunk["start"] = chunk["start_stop_name"].fillna("").str.strip()
        chunk["end"] = chunk["end_stop_name"].fillna("").str.strip()
        pc = chunk["passenger_count"]

        for (r, h), v in chunk.groupby(["base", "hour"])["passenger_count"].sum().items():
            route_hour[r][h] += int(v)
        for (s, h), v in chunk.groupby(["start", "hour"])["passenger_count"].sum().items():
            if s:
                stop_hour[s][h] += int(v)
        m = (chunk["start"] != "") & (chunk["end"] != "") & (chunk["start"] != chunk["end"])
        for (a, b, h), v in chunk[m].groupby(["start", "end", "hour"])["passenger_count"].sum().items():
            od_hour[(a, b)][h] += int(v)
        for (r, s, h), v in chunk.groupby(["base", "start", "hour"])["passenger_count"].sum().items():
            if s:
                route_stop_hour[(r, s)][h] += int(v)
        for h, v in chunk.groupby("hour")["passenger_count"].sum().items():
            city_hours[h] += int(v)
        total_boardings += int(pc.sum())
        print(f"  chunk done: rows so far {rows:,}", flush=True)

    print(f"rows={rows:,} boardings={total_boardings:,}")

    # ---- stops: busiest by total boardings -------------------------------
    stop_total = {s: sum(v) for s, v in stop_hour.items()}
    top_stops = sorted(stop_total, key=lambda s: -stop_total[s])[:TOP_STOPS]
    stop_idx = {s: i for i, s in enumerate(top_stops)}

    # routes per stop (from route_stop_hour), totals + hourly at that stop
    stop_routes = defaultdict(list)   # stop -> [(route, total_at_stop, hours)]
    route_stops = defaultdict(list)   # route -> [(stop, total_on_route, hours)]
    for (r, s), hrs in route_stop_hour.items():
        t = sum(hrs)
        if t <= 0:
            continue
        stop_routes[s].append((r, t, hrs))
        route_stops[r].append((s, t, hrs))
    for s in stop_routes:
        stop_routes[s].sort(key=lambda x: -x[1])
    for r in route_stops:
        route_stops[r].sort(key=lambda x: -x[1])

    # ---- flows: busiest OD pairs with both ends in the node set ----------
    od_total = {k: sum(v) for k, v in od_hour.items()}
    flows = []
    for (a, b), hrs in sorted(od_hour.items(), key=lambda kv: -od_total[kv[0]]):
        if a in stop_idx and b in stop_idx:
            flows.append({"a": stop_idx[a], "b": stop_idx[b],
                          "total": od_total[(a, b)], "hours": hrs})
        if len(flows) >= TOP_FLOWS:
            break

    # ---- schematic layout: Fruchterman-Reingold over the flow network ----
    n = len(top_stops)
    rng = random.Random(20261031)
    pos = np.array([[rng.random(), rng.random()] for _ in range(n)], dtype=float)
    edges = [(f["a"], f["b"], math.sqrt(f["total"])) for f in flows]
    area, iters = 1.0, 500
    k = math.sqrt(area / n)
    temp = 0.12
    for it in range(iters):
        disp = np.zeros_like(pos)
        # repulsion
        delta = pos[:, None, :] - pos[None, :, :]
        dist = np.sqrt((delta ** 2).sum(-1)) + 1e-9
        np.fill_diagonal(dist, 1e9)
        force = (k * k) / dist
        disp += (delta / dist[:, :, None] * force[:, :, None]).sum(1)
        # attraction along flows, weighted
        for a, b, w in edges:
            d = pos[a] - pos[b]
            dd = math.sqrt(float(d @ d)) + 1e-9
            f = (dd * dd / k) * min(w / 40.0, 3.0)
            disp[a] -= d / dd * f
            disp[b] += d / dd * f
        # gravity to centre keeps the cloud together
        disp += (0.5 - pos) * 0.9
        step = np.sqrt((disp ** 2).sum(-1, keepdims=True)) + 1e-9
        pos += disp / step * np.minimum(step, temp)
        pos = np.clip(pos, 0.02, 0.98)
        temp *= 0.995
    W, H = 1160.0, 640.0
    xy = {}
    for i, s in enumerate(top_stops):
        xy[s] = [round(float(pos[i][0]) * W, 1), round(float(pos[i][1]) * H, 1)]

    stops_out = []
    for s in top_stops:
        hrs = stop_hour[s]
        stops_out.append({
            "name": s, "total": stop_total[s], "hours": hrs,
            "bands": band_string(hrs), "x": xy[s][0], "y": xy[s][1],
            "routes": [{"route": r, "total": t, "hours": hrs2}
                       for r, t, hrs2 in stop_routes[s][:STOP_ROUTES]],
        })

    # ---- what-if base data for the busiest routes ------------------------
    route_total = {r: sum(v) for r, v in route_hour.items()}
    whatif = {}
    for r in sorted(route_total, key=lambda r: -route_total[r])[:WHATIF_ROUTES]:
        stops_list = []
        for s, t, hrs in route_stops[r][:WHATIF_STOPS]:
            alts = [{"route": r2, "hours": h2}
                    for r2, t2, h2 in stop_routes[s] if r2 != r][:WHATIF_ALTS]
            stops_list.append({"stop": s, "hours": hrs, "alts": alts})
        whatif[r] = {"stops": stops_list}

    out = {
        "meta": {
            "source": "Delhi bus e-ticketing, October 2026 (same dataset as Phase 1)",
            "tickets_note": "Boardings counted at each ticket's start stop; e-tickets are a 3-4% sample of all tickets.",
            "layout_note": "Schematic layout: stop positions computed from passenger flows, not geography. The dataset has no stop coordinates.",
            "total_boardings": total_boardings,
            "stops_shown": len(stops_out),
            "flows_shown": len(flows),
        },
        "city_hours": city_hours,
        "stops": stops_out,
        "flows": flows,
        "route_hours": {r: route_hour[r] for r in sorted(route_hour)},
        "whatif": whatif,
    }
    with open(OUT_JSON, "w") as f:
        json.dump(out, f, separators=(",", ":"), ensure_ascii=False)
    size = os.path.getsize(OUT_JSON)

    with open(OUT_NOTES, "w") as f:
        f.write("# Twin model notes — Phase 2 (build_twin.py)\n\n")
        f.write(f"- Ticket rows read: {rows:,}\n")
        f.write(f"- Total boardings (sum of passenger_count): {total_boardings:,}\n")
        f.write(f"- Distinct start stops in data: {len(stop_hour):,}; twin shows top {len(stops_out)}\n")
        f.write(f"- Distinct OD pairs (start != end): {len(od_hour):,}; twin shows top {len(flows)} with both ends in the node set\n")
        f.write(f"- Routes with hourly boardings shipped: {len(route_hour):,}\n")
        f.write(f"- What-if base data: {len(whatif)} busiest routes x top {WHATIF_STOPS} start stops x top {WHATIF_ALTS} alternatives\n")
        f.write(f"- twin.json size: {size:,} bytes\n\n")
        f.write("## What-if model (exact)\n\n")
        f.write("For route R at hour h with boardings B = route_hours[R][h]:\n")
        f.write("1. Only R's boardings from its top start stops are modelled; boardings "
                "from R's other stops are counted and reported as outside the model.\n")
        f.write("2. At each modelled stop, R's boardings at hour h are split across the "
                "other routes starting at the same stop, in proportion to those routes' "
                "boardings at that stop at hour h.\n")
        f.write("3. Any share at a stop with no alternative route boarding at that hour "
                "is reported as 'no alternative from this stop at this hour' — it is "
                "not silently reassigned.\n")
        f.write("4. An alternative's new band is found by adding its extra boardings to "
                "its hour-h total and re-ranking its 24 hours with the Phase 1 rule.\n")
        f.write("This is a simple, stated model — real riders may wait, walk or switch "
                "to the Metro. The app says so next to the result.\n\n")
        f.write("## Layout\n\n")
        f.write("Fruchterman-Reingold force layout (seed 20261031, 500 iterations) over "
                "the shipped flow network, stops weighted by nothing but their flows. "
                "Positions are schematic only.\n")
    print(f"wrote {OUT_JSON} ({size:,} bytes) and {OUT_NOTES}")


if __name__ == "__main__":
    main()
