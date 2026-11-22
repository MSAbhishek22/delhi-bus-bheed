# Kitni Bheed Hai? — a crowdedness check for Delhi buses

**Live app: https://delhi-bus-bheed.netlify.app**

Pick a Delhi bus route and the hour you want to travel, and the app tells you how crowded that route usually is at that hour — a crowdedness band worked out from real October 2026 e-ticket data (1,249 routes × 24 hours).

**Team ABHI X AAYUSHI** — M S Abhishek (data model + app build) and Aayushi Goel (testing + review)
**Delhi Transport Stack Hackathon — Problem 2: Crowdedness-aware journey planner**

## Problem

When we wait at a bus stop, we cannot tell what is coming. The next bus may have seats free, or it may be too full to stand in. We find out only when it pulls up. A little warning would help: leave ten minutes early, wait for the next one, or take a different route.

## What we built

We built a small web app. We pick a bus route and the hour we want to travel. The app answers in one of three plain bands: **bahut bheed** (very crowded for this route), **khadi bheed** (fairly crowded, standing likely), or **aaram se seat milegi** (quiet for this route, a seat is likely). It also shows the route's full day as a 24-hour strip, so we can see crowded and quiet hours at a glance. And it suggests the nearest quieter hour within three hours — or says honestly that nearby hours are just as crowded.

## The data

We used Delhi bus e-ticket records for one full month, October 2026: 2,559,899 tickets. Each ticket lists a passenger count. We counted boardings by adding those counts up, not by counting rows — 2,753,606 in total. Route names carry direction tags like UP and DOWN; merging those left 1,249 base routes.

## Method

1. We read every ticket and noted its route and the hour it was issued.
2. We added up boardings for each route, hour by hour.
3. We merged the UP and DOWN versions of each route name.
4. For each route, we ranked its own 24 hours from busiest to quietest. The 8 busiest hours became "bahut bheed", the next 8 "khadi bheed", and the 8 quietest "aaram se seat milegi".
5. We saved it as one table — 1,249 routes × 24 hours — for the app to read.

## What the checks showed

We tested the three busiest routes: 717A, 729 and 511A. On all three, the morning and evening peak hours landed in the top band, and the midday hours (12–3) landed lower, in the middle band. One honest detail: the 11 am hour sits in the middle band on all three routes. The real morning rush is 7 to 10, and it eases before 11. The numbers told us that; we did not force them.

## Honest limits

- These are October patterns only — how that month usually looked, not what today looks like.
- E-tickets are only about 3–4% of all bus tickets, so our counts are a sample, not the full picture.
- We have no live bus positions. A cancelled bus, rain, or a festival day will not show up here.
- The bands are relative to each route's own day. "Bahut bheed" means busy for that route, not a fixed number of people.
- We count boardings where a trip starts. How full the bus feels halfway along the route can differ.

## What comes next

Next we want a stop-level view, so the answer is about your stop, not just your route. Then more months of data, so festivals and seasons show up. And if the organisers open a live feed of bus positions, we would add it on top: the pattern says what is usual, the live feed would say what is true right now.
