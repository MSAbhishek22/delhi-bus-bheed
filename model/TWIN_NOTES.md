# Twin model notes — Phase 2 (build_twin.py)

- Ticket rows read: 2,559,899
- Total boardings (sum of passenger_count): 2,753,606
- Distinct start stops in data: 7,148; twin shows top 110
- Distinct OD pairs (start != end): 257,437; twin shows top 170 with both ends in the node set
- Routes with hourly boardings shipped: 1,249
- What-if base data: 40 busiest routes x top 5 start stops x top 8 alternatives
- twin.json size: 368,789 bytes

## What-if model (exact)

For route R at hour h with boardings B = route_hours[R][h]:
1. Only R's boardings from its top start stops are modelled; boardings from R's other stops are counted and reported as outside the model.
2. At each modelled stop, R's boardings at hour h are split across the other routes starting at the same stop, in proportion to those routes' boardings at that stop at hour h.
3. Any share at a stop with no alternative route boarding at that hour is reported as 'no alternative from this stop at this hour' — it is not silently reassigned.
4. An alternative's new band is found by adding its extra boardings to its hour-h total and re-ranking its 24 hours with the Phase 1 rule.
This is a simple, stated model — real riders may wait, walk or switch to the Metro. The app says so next to the result.

## Layout

Fruchterman-Reingold force layout (seed 20261031, 500 iterations) over the shipped flow network, stops weighted by nothing but their flows. Positions are schematic only.
