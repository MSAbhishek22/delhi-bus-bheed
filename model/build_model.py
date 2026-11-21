#!/usr/bin/env python3
"""
Delhi Transport Stack — Problem 2 (Crowdedness-aware journey planner)
Crowdedness model: boardings per base route per hour -> 3-level band.

Data: ../data/October-Delhi.csv  (2,559,899 e-ticket rows, 1-31 Oct 2026, IST)

WHAT IT DOES
  1. Streams the CSV once (plain csv module, low memory) and sums
     `passenger_count` (boardings) per (base route, hour-of-day).
     Hour is taken from `created_at` ("YYYY-MM-DD HH:MM:SS.ffffff+05:30",
     hour = characters 11:13). All timestamps are IST (+05:30).
  2. Base route = `route` value with ONE trailing direction suffix removed:
     a trailing "DOWN" is stripped first, else a trailing "UP"
     (e.g. "8ADOWN" -> "8A", "433UP" -> "433", "8UP" -> "8").
  3. Also totals boardings per base route and per `start_stop_name`.
  4. Converts every (route, hour) into a crowdedness band (rule below).
  5. Writes route_hour_crowdedness.csv (one row per route x 24 hours,
     hours with no tickets count as 0 boardings) and MODEL_NOTES.md
     (counts, the band rule, top routes/stops, and the peak spot-check).

BAND RULE (exact)
  Bands are RELATIVE to each route's own day — a small route at its busiest
  hour is "bahut bheed" for that route, even if a big route carries more
  people at its quietest hour. For each base route:
    - Take its 24 hourly boarding totals (missing hours = 0).
    - Rank the 24 hours by boardings, busiest first; ties are broken by
      earlier hour first (deterministic).
    - Ranks 1-8   (busiest third)  -> "bahut bheed"
      Ranks 9-16  (middle third)  -> "khadi bheed"
      Ranks 17-24 (quietest third)-> "aaram se seat milegi"
  So every route has exactly 8 hours in each band.

SPOT-CHECK (organisers' peak/off-peak test)
  For the 3 busiest base routes, the notes list the band of hours
  8,9,10,11 and 17,18,19,20 (expected: mostly "bahut bheed") and of
  hours 12,13,14,15 (expected: lower bands).

Run:  python3 build_model.py
"""

import csv
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_CSV = os.path.join(HERE, "..", "data", "October-Delhi.csv")
OUT_CSV = os.path.join(HERE, "route_hour_crowdedness.csv")
OUT_NOTES = os.path.join(HERE, "MODEL_NOTES.md")

BAND_HIGH = "bahut bheed"
BAND_MID = "khadi bheed"
BAND_LOW = "aaram se seat milegi"


def base_route(route: str) -> str:
    r = route.strip()
    if r.endswith("DOWN"):
        return r[:-4]
    if r.endswith("UP"):
        return r[:-2]
    return r


def main() -> None:
    route_hour = defaultdict(int)   # (base_route, hour) -> boardings
    route_total = defaultdict(int)  # base_route -> boardings
    stop_total = defaultdict(int)   # start_stop_name -> boardings
    rows_read = 0
    rows_used = 0
    rows_skipped = 0
    total_boardings = 0

    with open(DATA_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows_read += 1
            try:
                pax = int(row["passenger_count"])
                hour = int(row["created_at"][11:13])
                route_raw = (row["route"] or "").strip()
                if not route_raw or not (0 <= hour <= 23):
                    raise ValueError("bad route/hour")
            except (ValueError, TypeError, KeyError):
                rows_skipped += 1
                continue
            br = base_route(route_raw)
            route_hour[(br, hour)] += pax
            route_total[br] += pax
            stop = (row["start_stop_name"] or "").strip()
            if stop:
                stop_total[stop] += pax
            total_boardings += pax
            rows_used += 1

    base_routes = sorted(route_total)
    print(f"rows read={rows_read} used={rows_used} skipped={rows_skipped}")
    print(f"total boardings={total_boardings}  base routes={len(base_routes)}")

    # ---- bands: rank each route's 24 hours, thirds -------------------------
    bands = {}  # (base_route, hour) -> band label
    hourly = {}  # (base_route, hour) -> boardings (all 24 hours, 0-filled)
    for br in base_routes:
        vals = [(route_hour.get((br, h), 0), h) for h in range(24)]
        for v, h in vals:
            hourly[(br, h)] = v
        ranked = sorted(vals, key=lambda t: (-t[0], t[1]))  # busiest first
        for rank, (_v, h) in enumerate(ranked):
            if rank < 8:
                bands[(br, h)] = BAND_HIGH
            elif rank < 16:
                bands[(br, h)] = BAND_MID
            else:
                bands[(br, h)] = BAND_LOW

    # ---- write route_hour_crowdedness.csv ----------------------------------
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["base_route", "hour", "boardings", "band", "route_total_boardings"])
        for br in base_routes:
            for h in range(24):
                w.writerow([br, h, hourly[(br, h)], bands[(br, h)], route_total[br]])
    print(f"wrote {OUT_CSV} ({len(base_routes) * 24} data rows)")

    # ---- spot-check: 3 busiest routes --------------------------------------
    top_routes = sorted(route_total.items(), key=lambda kv: -kv[1])[:10]
    top_stops = sorted(stop_total.items(), key=lambda kv: -kv[1])[:30]

    def band_row(br, hours):
        return [bands[(br, h)] for h in hours]

    spot_lines = []
    spot_pass = True
    check_routes = [r for r, _ in top_routes[:3]]
    for br in check_routes:
        peak = band_row(br, [8, 9, 10, 11, 17, 18, 19, 20])
        mid = band_row(br, [12, 13, 14, 15])
        peak_high = sum(1 for b in peak if b == BAND_HIGH)
        mid_high = sum(1 for b in mid if b == BAND_HIGH)
        ok = peak_high >= 6 and mid_high == 0
        spot_pass = spot_pass and ok
        spot_lines.append((br, route_total[br], peak, mid, peak_high, mid_high, ok))

    # ---- MODEL_NOTES.md ------------------------------------------------------
    with open(OUT_NOTES, "w", encoding="utf-8") as f:
        f.write("# Model notes — route x hour crowdedness (Problem 2)\n\n")
        f.write("Built by `build_model.py` from `../data/October-Delhi.csv` "
                "(October 2026 bus e-ticketing, IST).\n\n")
        f.write("## Counts\n\n")
        f.write(f"- Ticket rows read: {rows_read:,}\n")
        f.write(f"- Rows used: {rows_used:,}  |  skipped (bad route/hour/count): {rows_skipped:,}\n")
        f.write(f"- Total boardings (sum of passenger_count): {total_boardings:,}\n")
        f.write(f"- Base routes (direction suffix UP/DOWN stripped): {len(base_routes):,}\n")
        f.write(f"- Output table: {len(base_routes) * 24:,} rows "
                f"(every base route x 24 hours; hours with no tickets = 0 boardings)\n\n")

        f.write("## Band rule (exact)\n\n")
        f.write("Bands are relative to each route's own day. For each base route, its 24 hourly "
                "boarding totals are ranked busiest-first (ties: earlier hour first). "
                "Ranks 1-8 = **bahut bheed**, ranks 9-16 = **khadi bheed**, "
                "ranks 17-24 = **aaram se seat milegi**. Every route therefore has exactly "
                "8 hours in each band. A small route at its busiest hour is 'bahut bheed' "
                "*for that route* — the band answers 'how crowded is this route at this hour "
                "compared with its own day', which is what a commuter choosing a time cares about.\n\n")

        f.write("## Top 10 base routes by boardings\n\n")
        f.write("| Base route | Boardings (Oct 2026) |\n|---|---|\n")
        for r, t in top_routes:
            f.write(f"| {r} | {t:,} |\n")
        f.write("\n")

        f.write("## Top 30 start stops by boardings\n\n")
        f.write("| Start stop | Boardings (Oct 2026) |\n|---|---|\n")
        for s, t in top_stops:
            f.write(f"| {s} | {t:,} |\n")
        f.write("\n")

        f.write("## Spot-check — peak vs off-peak (organisers' check)\n\n")
        f.write("For the 3 busiest base routes: hours 8-11 and 17-20 should land in the "
                "highest band, hours 12-15 should land lower.\n\n")
        for br, tot, peak, mid, peak_high, mid_high, ok in spot_lines:
            f.write(f"### Route {br} ({tot:,} boardings in Oct)\n\n")
            f.write("| Hours | Bands |\n|---|---|\n")
            f.write("| 8, 9, 10, 11, 17, 18, 19, 20 | " + ", ".join(peak) + " |\n")
            f.write("| 12, 13, 14, 15 | " + ", ".join(mid) + " |\n")
            f.write(f"\nPeak hours in highest band: {peak_high}/8 · "
                    f"midday hours in highest band: {mid_high}/4 · "
                    f"check: {'PASS' if ok else 'FAIL'}\n\n")
        f.write(f"**Overall spot-check: {'PASS' if spot_pass else 'FAIL'}** "
                "(pass = at least 6 of 8 peak hours in the highest band and no midday "
                "hour in the highest band, for each of the 3 busiest routes).\n\n")

        f.write("## Honest limits\n\n")
        f.write("- E-ticketing is only a 3-4% sample of all bus tickets, so boardings here "
                "are sample counts, not full ridership. Bands are relative within a route, "
                "which is safer than comparing raw counts across routes.\n")
        f.write("- Boardings are counted at the start stop of each ticket; crowdedness on "
                "later segments of a route can differ.\n")
        f.write("- Hours with zero e-tickets (e.g. late night on small routes) fall in the "
                "lowest band by construction.\n")

    print(f"wrote {OUT_NOTES}")
    for br, tot, peak, mid, peak_high, mid_high, ok in spot_lines:
        print(f"route {br}: peak_high={peak_high}/8 midday_high={mid_high}/4 -> "
              f"{'PASS' if ok else 'FAIL'}")
    print(f"SPOT-CHECK OVERALL: {'PASS' if spot_pass else 'FAIL'}")


if __name__ == "__main__":
    main()
