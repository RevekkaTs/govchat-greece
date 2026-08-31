# Live fire data integration (KR2)

**Branch:** `feature/live-fire-data` (branched from `master` at `e4144d9`)
**Status:** Design — not yet implemented
**Goal (KR2):** "Programmatically consume and integrate external APIs using Python"

## Overview

`govchat/scripts/seed_fire_data.py` currently seeds the `fire_data` ChromaDB
collection from four hand-written summary paragraphs (2021-2024), hardcoded
in the script itself. This design replaces that hardcoded data with a live
fetch from data.gov.gr, so the Fires domain is backed by a real external API
integration end to end.

**Scope:** Fires domain only. Road safety and energy are intentionally left
as a separate, later exercise — the pattern learned here (CKAN metadata call
→ signed blob download → parse → aggregate → seed) is reusable, but repeating
it three times now would not teach anything new (YAGNI).

**No changes to:** `agent.py`, `rag.py`, and `tools.py` apart from one
docstring line (see below). `fires_tool(year)` reads from the `fire_data`
collection exactly as it does today — only the contents of that collection
change, not its shape (one document per year, English summary paragraph) or
how it's queried.

`fires_tool` doesn't filter by year directly — it builds a query string like
`"fires Greece 2022"` and `search_fires` (`rag.py`) runs an embedding
similarity search over `fire_data`. This only works because each stored
document is one year's paragraph with the year written into the text, so the
query embedding lands closest to the matching year's document. That's the
contract this design has to preserve: yearly English paragraphs, one per
year, year mentioned in the text — not, e.g., one document per prefecture or
per raw incident.

**One explicit exception:** `tools.py`'s `fires_tool` docstring currently
reads `"Search forest fire and wildfire statistics for Greece (2021-2024)."`
Since the live dataset goes back to at least 2014, this line is updated to
match the actual year range once that range is known from a real fetch (no
other line in `tools.py` changes).

## Data source

- **Metadata API:** `GET https://data.gov.gr/api/3/action/package_show?id=mcp_forest_fires`
  (CKAN `package_show` action). Confirmed live: returns JSON with a
  `result.resources` array.
- **Resource selection:** pick the first resource in that array whose
  `format` is `"CSV"`.
- **Data download:** `GET` that resource's `url`. This URL points to Azure
  Blob Storage and is **signed and short-lived** (confirmed via a live fetch —
  it carries an `se=` expiry query parameter that expires same-day). This is
  why step 1 (the metadata call) must run fresh on every seed invocation —
  the CSV URL cannot be hardcoded or cached across runs.
- **Format:** CSV, parsed with Python's stdlib `csv` module (no new
  dependency — the project does not use `pandas` anywhere else).

### Confirmed columns

```
start_time, end_time, fire_station, prefecture, forestry, municipality,
location, address, forest_area_burned, woodland_area_burned,
grove_area_burned, low_vegetation_area_burned, swamp_area_burned,
agricultural_area_burned, crop_residue_area_burned,
dumping_ground_area_burned, firefighters, wildland_crew, volunteers, army,
other_firefighters, fire_trucks, local_authorities_vehicles,
water_tank_trucks, machinery, helicopters, airplanes_cl415,
airplanes_cl215, airplanes_pzl, airplanes_gru
```

Confirmed via a live sample of 5 rows starting `2014-01-02`. The full year
range of the dataset (earliest/latest year present) is **not** confirmed
ahead of implementation — the aggregation step must derive years from
whatever rows actually come back, not assume a fixed range.

## Aggregation logic

Raw rows are aggregated **per year** (not seeded one document per row).
For each row:

1. Extract the year from `start_time`.
2. Sum the eight `*_area_burned` columns for that row into one
   "hectares burned in this incident" figure.

Per year, from the rows in that year:

1. Total incident count.
2. Total hectares burned (sum of the per-row sums above).
3. Top 2-3 `prefecture` values by incident count.

This produces one aggregate record per year, which is rendered into one
English-language summary paragraph per year — matching the language and
shape of the four paragraphs it replaces. Because the real dataset goes
back to at least 2014 (vs. the hand-written set's 2021-2024), this will
likely produce more than four documents.

### Pure aggregation function

The row → yearly-aggregate step (date parsing + area summing + prefecture
counting) is pulled into its own pure function, e.g.:

```python
def aggregate_by_year(rows: list[dict]) -> dict[int, YearAggregate]:
    ...
```

taking already-parsed CSV rows (list of dicts, as `csv.DictReader` yields)
and returning a mapping of year → aggregate data (count, total hectares, top
prefectures). This function has no I/O and is the unit-tested part of the
script (see Testing below). Rendering an aggregate into the final English
paragraph text is a separate, simpler step and does not need its own test.

## Seeding flow

1. Call the CKAN API, find the CSV resource, download it.
2. Parse CSV rows with `csv.DictReader`.
3. Run `aggregate_by_year` over all rows.
4. Render one summary paragraph per year from the aggregates.
5. Only after all of the above succeeds: delete the existing documents in
   the `fire_data` collection and add the new ones.

## Error handling

Any failure in steps 1-4 above (CKAN call fails, download fails, CSV is
missing an expected column, etc.) must fail loudly (raise / non-zero exit)
**before** touching the existing `fire_data` collection. The collection is
only ever mutated after a fully successful fetch + parse + aggregate — a
partial or failed refresh must never leave `fire_data` empty or partially
overwritten. This mirrors the existing script's current behavior of
skipping the seed entirely if the collection is already populated, except
now the "don't leave it broken" guarantee also has to survive a live
network call that can fail in more ways than the old hardcoded version
could.

## Testing

Consistent with the project's existing seed scripts (`seed_rag.py`,
`seed_road_safety.py`), which have zero test coverage as a matter of
pattern — these are maintenance scripts, not a live request path, so no
network-hitting tests are added.

The one exception is `aggregate_by_year`, which is pure, has real bug risk
(date parsing, numeric summing, off-by-one year boundaries), and needs no
mocking to test. Add `govchat/tests/test_seed_fire_data.py` with one test
that feeds a small hardcoded CSV string (a handful of rows spanning at
least two years) through `csv.DictReader` and `aggregate_by_year`, and
asserts the resulting per-year counts and hectare totals.

## Out of scope / explicitly deferred

- Road safety and energy domains switching to live data (separate future
  exercise, same pattern).
- Any caching or scheduling of the refresh (it remains a manually-run
  script, same as today).
- Any change to `fires_tool`, `agent.py`, or how the collection is queried.
