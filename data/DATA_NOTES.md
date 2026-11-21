# Data notes — October 2026 bus e-ticketing (Problem 2)

Downloaded 20 Nov 2026 from the Transport Stack Hackathon page (Problem 2 download link):
https://pub-091bd9e794bb4877b10b29e6df80f065.r2.dev/2026-10/October-Delhi.csv.zip
Direct download worked; no proxy needed.

## Files in this folder

| File | Size |
|---|---|
| October-Delhi.csv.zip | 66,145,093 bytes (~63 MB) |
| October-Delhi.csv | 290,014,457 bytes (~290 MB) |

(The zip also carried a macOS `__MACOSX` metadata folder; removed as junk.)

## CSV structure

Columns (9, in file order):

`passenger_count`, `amount`, `vehicle_number`, `ticket_type_id`, `end_stop_name`, `route`, `start_stop_name`, `created_at`, `is_ac`

First 3 rows, as they appear in the file:

```csv
1,"22",NULL,1,"Mahamaya Flyover West","8UP","Ali Village","2026-10-28 10:19:18.780611+05:30",True
1,"9","DL1PD6826",1,"Crown Plaza","8ADOWN","Kalindi Kunj Bdr","2026-10-28 10:19:29.989461+05:30",True
1,"13.5","DL51EV9760",1,"Clal Chowk","433UP","Andrews Ganj","2026-10-28 10:19:46.297108+05:30",True
```

No passenger-identifying columns exist (no names, phone numbers or card IDs). `vehicle_number` is the bus fleet registration; it is `NULL` on some rows.

## Headline numbers

- **Total rows:** 2,559,899 tickets
- **Distinct routes:** 2,259 — note the `route` value carries a direction suffix (e.g. `8UP`, `8ADOWN`, `433UP`), so the base-route count will be lower once suffixes are stripped.
- **Timestamp range (`created_at`, IST +05:30):** 2026-10-01 00:00:01 → 2026-10-31 23:58:22 — the full month of October 2026, as the brief states.

## Things to know before modelling

- Rows are **not sorted by time** — the file opens with 28 Oct rows. Sort or index by `created_at` first.
- `passenger_count` is per ticket row (mostly 1, sometimes 2+), so boardings = sum of `passenger_count`, not row count.
- `amount` is the fare in ₹ (values like 9, 13.5, 22, 27 seen).

Model not built yet — this is data prep only, per the prototype plan timeline (21 Nov: explore, agree the route/hour table shape).
