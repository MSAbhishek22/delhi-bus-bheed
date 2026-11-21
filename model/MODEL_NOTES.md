# Model notes — route x hour crowdedness (Problem 2)

Built by `build_model.py` from `../data/October-Delhi.csv` (October 2026 bus e-ticketing, IST).

## Counts

- Ticket rows read: 2,559,899
- Rows used: 2,559,899  |  skipped (bad route/hour/count): 0
- Total boardings (sum of passenger_count): 2,753,606
- Base routes (direction suffix UP/DOWN stripped): 1,249
- Output table: 29,976 rows (every base route x 24 hours; hours with no tickets = 0 boardings)

## Band rule (exact)

Bands are relative to each route's own day. For each base route, its 24 hourly boarding totals are ranked busiest-first (ties: earlier hour first). Ranks 1-8 = **bahut bheed**, ranks 9-16 = **khadi bheed**, ranks 17-24 = **aaram se seat milegi**. Every route therefore has exactly 8 hours in each band. A small route at its busiest hour is 'bahut bheed' *for that route* — the band answers 'how crowded is this route at this hour compared with its own day', which is what a commuter choosing a time cares about.

## Top 10 base routes by boardings

| Base route | Boardings (Oct 2026) |
|---|---|
| 717A | 55,546 |
| 729 | 37,748 |
| 511A | 35,633 |
| 623 | 33,343 |
| 578 | 32,010 |
| 717B | 31,284 |
| 764 | 30,715 |
| 522 | 29,295 |
| 534 | 28,681 |
| 433 | 28,434 |

## Top 30 start stops by boardings

| Start stop | Boardings (Oct 2026) |
|---|---|
| Hamdard Nagar / Sangam Vihar | 19,676 |
| Saket Metro Station | 14,830 |
| Said Ul Zeb Village | 13,911 |
| Badarpur Border(T) | 13,837 |
| Mahipal Pur Village | 13,469 |
| Mehrauli Terminal | 13,450 |
| Kapashera Border | 13,118 |
| Mahipal Pur | 12,724 |
| Dhaula Kuan | 12,205 |
| Ambedkar Nagar Depot | 12,031 |
| West Patel Nagar | 11,998 |
| Andrews Ganj | 11,609 |
| Rang Puri (Nh8) | 11,480 |
| Badarpur Border | 11,412 |
| Mother Dairy | 10,293 |
| Kapashera Village | 10,290 |
| Samalkha Village | 10,181 |
| Karol Bagh Metro Station | 9,871 |
| Pul Prehladpur ( Badarpur) | 9,511 |
| Mahipal Pur (Nh8) | 8,779 |
| Maharani Bagh | 8,745 |
| Punj Sons / Govind Puri Metro Station | 8,684 |
| Andheria Bagh More | 8,388 |
| Isbt Nityanand Marg | 7,863 |
| Maya Puri Depot | 7,576 |
| Aiims | 7,557 |
| Maidan Garhi Crossing (Sdm Court) | 7,528 |
| Defence Colony | 7,412 |
| Hamdard Nagar | 7,385 |
| Vayusenabad (Tigri) | 7,382 |

## Spot-check — peak vs off-peak (organisers' check)

For the 3 busiest base routes: hours 8-11 and 17-20 should land in the highest band, hours 12-15 should land lower.

### Route 717A (55,546 boardings in Oct)

| Hours | Bands |
|---|---|
| 8, 9, 10, 11, 17, 18, 19, 20 | bahut bheed, bahut bheed, bahut bheed, khadi bheed, bahut bheed, bahut bheed, bahut bheed, bahut bheed |
| 12, 13, 14, 15 | khadi bheed, khadi bheed, khadi bheed, khadi bheed |

Peak hours in highest band: 7/8 · midday hours in highest band: 0/4 · check: PASS

### Route 729 (37,748 boardings in Oct)

| Hours | Bands |
|---|---|
| 8, 9, 10, 11, 17, 18, 19, 20 | bahut bheed, bahut bheed, bahut bheed, khadi bheed, bahut bheed, bahut bheed, bahut bheed, bahut bheed |
| 12, 13, 14, 15 | khadi bheed, khadi bheed, khadi bheed, khadi bheed |

Peak hours in highest band: 7/8 · midday hours in highest band: 0/4 · check: PASS

### Route 511A (35,633 boardings in Oct)

| Hours | Bands |
|---|---|
| 8, 9, 10, 11, 17, 18, 19, 20 | bahut bheed, bahut bheed, bahut bheed, khadi bheed, bahut bheed, bahut bheed, bahut bheed, bahut bheed |
| 12, 13, 14, 15 | khadi bheed, khadi bheed, khadi bheed, khadi bheed |

Peak hours in highest band: 7/8 · midday hours in highest band: 0/4 · check: PASS

**Overall spot-check: PASS** (pass = at least 6 of 8 peak hours in the highest band and no midday hour in the highest band, for each of the 3 busiest routes).

## Honest limits

- E-ticketing is only a 3-4% sample of all bus tickets, so boardings here are sample counts, not full ridership. Bands are relative within a route, which is safer than comparing raw counts across routes.
- Boardings are counted at the start stop of each ticket; crowdedness on later segments of a route can differ.
- Hours with zero e-tickets (e.g. late night on small routes) fall in the lowest band by construction.
