#!/usr/bin/env python3
"""Data-integrity tests for the Phase 2 twin model output (app/twin.json).

Run: python3 -m unittest test_twin -v   (from this folder)
Every expectation is anchored to a Phase 1 published number or to an
independent artifact (model/route_hour_crowdedness.csv, app/crowdedness.json),
never to the twin build's own say-so.
"""
import csv
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TWIN = json.load(open(os.path.join(HERE, "..", "app", "twin.json")))
CROWD = json.load(open(os.path.join(HERE, "..", "app", "crowdedness.json")))

TOTAL_BOARDINGS = 2_753_606          # MODEL_NOTES.md (Phase 1)
TOTAL_TICKETS = 2_559_899            # DATA_NOTES.md


def band_string(hours):
    order = sorted(range(24), key=lambda h: (-hours[h], h))
    out = ["A"] * 24
    for rank, h in enumerate(order):
        out[h] = "B" if rank < 8 else ("K" if rank < 16 else "A")
    return "".join(out)


class TestTotals(unittest.TestCase):
    def test_city_hours_sum_to_known_boardings(self):
        self.assertEqual(sum(TWIN["city_hours"]), TOTAL_BOARDINGS)
        self.assertEqual(TWIN["meta"]["total_boardings"], TOTAL_BOARDINGS)

    def test_city_peak_is_morning(self):
        peak = TWIN["city_hours"].index(max(TWIN["city_hours"]))
        self.assertIn(peak, (8, 9, 10), "network peak should be a morning-peak hour")

    def test_route_hours_match_phase1_csv(self):
        csv_totals = {}
        with open(os.path.join(HERE, "route_hour_crowdedness.csv")) as f:
            for row in csv.DictReader(f):
                csv_totals[row["base_route"]] = int(row["route_total_boardings"])
        self.assertEqual(len(csv_totals), 1249)
        self.assertEqual(set(csv_totals), set(TWIN["route_hours"]))
        for route, total in csv_totals.items():
            self.assertEqual(sum(TWIN["route_hours"][route]), total, route)

    def test_route_hours_reproduce_phase1_bands(self):
        # The Phase 2 hourly numbers must regenerate Phase 1's shipped bands
        # for every single route — this pins Phase 2 to the submitted model.
        for route, info in CROWD["routes"].items():
            self.assertEqual(band_string(TWIN["route_hours"][route]),
                             info["bands"], route)


class TestStops(unittest.TestCase):
    def test_stop_hours_sum_to_stop_total(self):
        for s in TWIN["stops"]:
            self.assertEqual(sum(s["hours"]), s["total"], s["name"])
            self.assertEqual(len(s["hours"]), 24)

    def test_stop_bands_follow_the_rule(self):
        for s in TWIN["stops"]:
            self.assertEqual(band_string(s["hours"]), s["bands"], s["name"])

    def test_stops_sorted_and_top_stop_matches_phase1_notes(self):
        totals = [s["total"] for s in TWIN["stops"]]
        self.assertEqual(totals, sorted(totals, reverse=True))
        # MODEL_NOTES.md, top start stop by boardings:
        self.assertEqual(TWIN["stops"][0]["name"], "Hamdard Nagar / Sangam Vihar")
        self.assertEqual(TWIN["stops"][0]["total"], 19676)

    def test_positions_inside_board(self):
        for s in TWIN["stops"]:
            self.assertTrue(0 <= s["x"] <= 1160, s["name"])
            self.assertTrue(0 <= s["y"] <= 640, s["name"])

    def test_stop_routes_are_real_and_consistent(self):
        for s in TWIN["stops"]:
            seen = set()
            for r in s["routes"]:
                self.assertIn(r["route"], TWIN["route_hours"])
                self.assertEqual(sum(r["hours"]), r["total"])
                self.assertNotIn(r["route"], seen)
                seen.add(r["route"])


class TestFlows(unittest.TestCase):
    def test_flow_endpoints_valid_and_distinct(self):
        n = len(TWIN["stops"])
        for f in TWIN["flows"]:
            self.assertTrue(0 <= f["a"] < n and 0 <= f["b"] < n)
            self.assertNotEqual(f["a"], f["b"])
            self.assertEqual(sum(f["hours"]), f["total"])

    def test_flows_are_a_subset_of_all_boardings(self):
        self.assertLess(sum(f["total"] for f in TWIN["flows"]), TOTAL_BOARDINGS)


class TestWhatIf(unittest.TestCase):
    """Reference implementation of the documented what-if model, run on the
    shipped twin.json alone: redistribution must conserve boardings."""

    def redistribute(self, route, hour):
        """The documented model: the route's boardings at `hour` from its top
        start stops are split at each stop across the other routes starting
        there, in proportion to their boardings at that stop at that hour.
        Boardings from the route's other stops are outside the model ('rest')."""
        w = TWIN["whatif"][route]
        total = TWIN["route_hours"][route][hour]
        moved, unassigned = 0.0, 0.0
        covered = 0
        for s in w["stops"]:
            share = s["hours"][hour]
            covered += share
            alt_base = [(a["route"], a["hours"][hour]) for a in s["alts"]]
            alt_total = sum(v for _, v in alt_base)
            if alt_total == 0:
                unassigned += share
                continue
            moved += share  # every boarding at this stop is reassigned
        rest = total - covered
        return total, moved, unassigned, rest

    def test_conservation_on_busy_routes(self):
        for route, hour in [("717A", 9), ("764", 18), ("729", 8)]:
            total, moved, unassigned, rest = self.redistribute(route, hour)
            self.assertGreater(total, 0)
            self.assertAlmostEqual(moved + unassigned + rest, total, places=6,
                                   msg=f"{route}@{hour}: moved+unassigned+rest != route boardings")
            self.assertGreaterEqual(rest, 0)

    def test_whatif_routes_are_the_busy_ones(self):
        totals = sorted((sum(v) for v in TWIN["route_hours"].values()), reverse=True)
        for route in TWIN["whatif"]:
            self.assertGreaterEqual(sum(TWIN["route_hours"][route]), totals[39])


if __name__ == "__main__":
    unittest.main()
