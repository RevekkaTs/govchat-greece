# Live fire data integration (KR2)

**Branch:** `feature/live-fire-data` (branched from `master` at `e4144d9`)
**Status:** Design — not yet implemented
**Goal (KR2):** "Programmatically consume and integrate external APIs using Python"

**Revision note:** This spec was rewritten after the original data-source
assumptions turned out to be wrong once verified against the live API and
real downloaded files (wrong CKAN dataset, wrong file format, wrong column
names, and undocumented layout drift across years). Every fact below was
confirmed against real responses/files, not assumed.

## Overview

`govchat/scripts/seed_fire_data.py` currently seeds the `fire_data` ChromaDB
collection from four hand-written summary paragraphs (2021-2024), hardcoded
in the script itself. This design replaces that hardcoded data with a live
fetch from data.gov.gr, so the Fires domain is backed by a real external API
integration end to end.

**Scope:** Fires domain only, years **2021-2024** (see "Why 2021-2024" below).
Road safety and energy are intentionally left as a separate, later exercise.

**No changes to:** `agent.py`, `rag.py`, and `tools.py` apart from one
docstring line. `fires_tool(year)` reads from the `fire_data` collection
exactly as it does today — only the contents of that collection change, not
its shape (one document per year, English summary paragraph) or how it's
queried.

`fires_tool` doesn't filter by year directly — it builds a query string like
`"fires Greece 2022"` and `search_fires` (`rag.py`) runs an embedding
similarity search over `fire_data`. This only works because each stored
document is one year's paragraph with the year written into the text, so the
query embedding lands closest to the matching year's document. That's the
contract this design has to preserve: yearly English paragraphs, one per
year, year mentioned in the text.

**One explicit exception:** `tools.py`'s `fires_tool` docstring currently
reads `"Search forest fire and wildfire statistics for Greece (2021-2024)."`
This stays accurate as-is, since the confirmed year range (below) is exactly
2021-2024 — no docstring change is needed after all.

## Data source (corrected)

- **Wrong in the original spec:** `package_show?id=mcp_forest_fires`. That
  package is real and does return a CSV, but it's a different, unrelated
  dataset covering only 2014-2018 — not the one the current hardcoded docs
  came from.
- **Correct package:** `archeio-agrotodasikon-symvanton`
  ("ΑΡΧΕΙΟ ΑΓΡΟΤΟΔΑΣΙΚΩΝ ΣΥΜΒΑΝΤΩΝ" — Rural/Forest Incidents Archive),
  package id `55d3451c-94cb-4577-8cb6-34d3e89a4299` — this matches the
  dataset ID already recorded in the current `seed_fire_data.py`'s comment.
  Confirmed live:
  `GET https://data.gov.gr/api/3/action/package_show?id=archeio-agrotodasikon-symvanton`
  returns one **XLS** resource per year, 2019-2025, each named
  `"ΑΓΡΟΤΟΔΑΣΙΚΕΣ ΠΥΡΚΑΓΙΕΣ <year>"`.
- **Resource selection:** for each target year (2021-2024), find the
  resource with `format == "XLS"` whose `name` contains that year as a
  token (e.g. `"ΑΓΡΟΤΟΔΑΣΙΚΕΣ ΠΥΡΚΑΓΙΕΣ 2022"`). Exactly one match is
  expected; zero or more than one is a fetch failure (fail loudly).
- **Download:** `GET` that resource's `url`. Confirmed live: this URL is a
  **stable data.gov.gr proxy link** (not itself the signed blob URL — that
  was also wrong in the original spec). It returns an HTTP 302 to a
  freshly-signed, same-day-expiring Azure Blob URL on every request.
  `requests.get(...)` follows redirects by default, so no special handling
  is needed — a plain `requests.get(resource["url"])` transparently gets a
  fresh signed URL every time this runs, which is why the metadata call
  must still happen fresh on every seed invocation (same reasoning as
  before, corrected mechanism).
- **Format:** legacy binary `.xls` (confirmed via magic bytes:
  `D0 CF 11 E0 A1 B1 1A E1`, the OLE2/BIFF signature), not CSV. This is a
  **new dependency**: `xlrd` (the only maintained library that still reads
  this legacy format — `openpyxl` only reads `.xlsx`/`.xlsm`). Add `xlrd`
  to `govchat/requirements.txt`.

## Why 2021-2024 (and not 2019, 2020, or 2025)

The original spec assumed a uniform schema. Downloading and inspecting all
seven available years (2019-2025) directly showed real layout drift:

| Year | Columns | Header row | Notes |
|---|---|---|---|
| 2019 | 32 | row 1 | No leading ID columns, no "leased aircraft" columns |
| 2020 | 36 | row 1 | +4 leading ID columns vs 2019, still no "leased" columns |
| **2021** | **38** | **row 1** | **+2 trailing "leased" columns vs 2020 — same column count and positions as 2022-2024, but see note below** |
| **2022** | **38** | **row 1** | Same shape as 2021 |
| **2023** | **38** | **row 1** | Same shape as 2021 |
| **2024** | **38** | **row 1** | Same shape as 2021 |
| 2025 | 39 | **row 3** (not row 1) | Extra title row shifts everything down; adds a "Κατηγορία Συμβάντος" column; dates stored as `"DD/MM/YYYY"` text instead of Excel serial numbers; drops the "Α/Φ GRU." column present in every other year |

2021-2024 is the one contiguous range with a **verified-matching column
count and layout** across all four files — confirmed by downloading and
diffing all four, not inferred. It also happens to exactly match the year
range of the hardcoded docs being replaced. 2019, 2020, and 2025 are
explicitly **out of scope**: including them would require either a second
column-position mapping (2019/2020) or a different header-row offset and
date-format branch (2025), none of which has been verified. A future pass
can extend coverage once those layouts are individually confirmed the same
way — this design does not attempt to auto-detect or best-effort them; an
unrecognized year is simply not fetched.

**Correction (found during implementation, not during spec-writing):** the
2021-2024 headers are not byte-identical after all — column 28 is labeled
`"ΟΧΗΜ. ΟΤΑ"` in 2021 but `"ΟΧΗΜ. ΥΠΗΡΕΣΙΑΚΑ"` in 2022-2024 (both mean
"local authority / service vehicles" — almost certainly the same concept,
relabeled at some point). This column isn't used by the aggregation at
all. Rather than hardcode both accepted labels for one irrelevant column,
the header validation only checks the column count and the labels of the
columns actually consumed (prefecture + the 8 area columns) — see
"Confirmed columns" below.

## Confirmed columns (2021-2024 layout)

Full header row as seen in 2022-2024 (0-indexed; 2021 is identical except
column 28, see the correction above):

```
0  Α/Α ΕΓΓΡΑΦΗΣ          10 Δασαρχείο              20 Υπολλείματα Καλλιεργειών   30 ΜΗΧΑΝΗ-ΜΑΤΑ
1  Α/Α ENGAGE            11 Δήμος                  21 Σκουπι-δότοποι             31 ΕΛΙΚΟ- ΠΤΕΡΑ
2  X-ENGAGE              12 Περιοχή                22 ΠΥΡΟΣ. ΣΩΜΑ                 32 Α/Φ CL415
3  Y-ENGAGE              13 Διεύθυνση              23 ΠΕΖΟΠΟΡΑ ΤΜΗΜΑΤΑ            33 Α/Φ CL215
4  Υπηρεσία              14 Δάση                   24 ΕΘΕΛΟ-ΝΤΕΣ                  34 Α/Φ PZL
5  Νομός                 15 Δασική Έκταση          25 ΣΤΡΑΤΟΣ                     35 Α/Φ GRU.
6  Ημερ/νία Έναρξης      16 Άλση                   26 ΑΛΛΕΣ ΔΥΝΑΜΕΙΣ              36 ΜΙΣΘ. ΕΛΙΚΟΠΤ.
7  Ώρα Έναρξης           17 Χορτ/κές Εκτάσεις       27 ΠΥΡΟΣ. ΟΧΗΜ.                37 ΜΙΣΘ. ΑΕΡΟΣΚ.
8  Ημερ/νία Κατασβεσης   18 Καλάμια - Βάλτοι        28 ΟΧΗΜ. ΥΠΗΡΕΣΙΑΚΑ (2021: ΟΧΗΜ. ΟΤΑ)
9  Ώρα Κατάσβεσης        19 Γεωργικές Εκτάσεις      29 ΒΥΤΙΟ- ΦΟΡΑ
```

Only two columns are actually used for aggregation:

- **Column 5** (`Νομός`, prefecture) — used for the top-prefectures count.
- **Columns 14-21**, the eight burned-area columns (forest, forest extent,
  groves, low vegetation, swamp, agricultural, crop residue, dumping
  ground) — summed per row into one stremmata-burned figure per incident.

Data rows start at sheet row index 2 (row 0 is a merged group-header row,
row 1 is the real header row). **Schema validation checks only what's
consumed** — total column count (38) plus the labels of column 5 and
columns 14-21 — not every column's exact text, since column 28's label
is known to vary between 2021 and 2022-2024 without affecting anything
this script reads.

**Units:** the group header reads `"ΚΑΜΜΕΝΗ ΕΚΤΑΣΗ (Σε Στρέμματα)"` — burned
area in **στρέμματα (stremmata)**. This design keeps the figures in
stremmata rather than converting to hectares (per user preference — Greek
readers intuitively understand stremmata, and the source data is already
in that unit; converting away from it adds a step without adding clarity).
The rendered paragraphs say "stremmata," not "hectares."

**No per-row date parsing is needed.** Each XLS resource already covers
exactly one calendar year (one file per year), so the year for a document
is simply the year the resource was fetched for — not derived from any
date column. This is a simplification versus the original spec, which
incorrectly assumed a single combined file needing per-row year extraction.

## Verified against real numbers

Downloading all four files and computing real totals (before writing this
spec) gives:

| Year | Incidents (computed) | Incidents (current hardcoded doc) | Stremmata burned (computed) |
|---|---|---|---|
| 2021 | 9,514 | 9,514 | ~1,332,140 |
| 2022 | 9,856 | 8,500 | ~285,650 |
| 2023 | 8,257 | 8,257 | ~1,769,660 |
| 2024 | 9,777 | 9,777 | ~483,070 |

Incident counts match exactly for three of the four years, confirming the
row/column mapping is correct. The current hardcoded docs report burned
area in hectares (e.g. "~130,851 hectares" for 2021) rather than
stremmata, so the area figures aren't directly comparable in this table —
even converted to the same unit, this dataset's totals are the same order
of magnitude as the hardcoded docs' but don't match precisely, sometimes
by up to ~3x (notably 2023, the year of the Evros mega-fire). This
dataset is an operational incident-response log — it most likely reflects
real-time area estimates logged during firefighting rather than a final,
official post-season survey, which is a plausible and known kind of
discrepancy between Greek wildfire data sources. This is expected, not a
bug: the new documents will report different (real, live-sourced, and
now differently-united) numbers than the hand-written ones they replace.
Worth calling out explicitly so it doesn't read as breakage.

## Aggregation logic

For each target year (2021, 2022, 2023, 2024), independently:

1. Fetch and open that year's XLS resource, sheet index 0.
2. Validate the header row (row 1) against the confirmed 38-column list
   above — fail loudly on any mismatch (see Error handling).
3. For each data row (row 2 onward):
   - Read the prefecture (column 5).
   - Sum columns 14-21 to get total stremmata burned in that incident.
4. Aggregate across all rows for that year: incident count, total
   stremmata burned, and the top 3 prefectures by incident count.

This produces one aggregate record per year → one English-language summary
paragraph per year, matching the shape of the four paragraphs it replaces.

### Pure aggregation function

The per-row summing and per-year aggregation is pulled into a pure
function that has no dependency on `xlrd` or file I/O:

```python
def aggregate_year(year: int, rows: list[dict]) -> YearAggregate:
    ...
```

`rows` is a list of already-normalized dicts — `{"prefecture": str,
"stremmata_burned": float}` — one per incident, produced by the
XLS-reading layer (which owns the column-position mapping and the header
validation). `aggregate_year` itself only does
counting, summing, and top-3 counting — this is the part with real bug
risk (off-by-one, float summing, tie-breaking) and no I/O, so it's the
part that gets a unit test (see Testing). Rendering an aggregate into the
final paragraph text is a separate, simpler step and does not need one.

## Seeding flow

1. Call the CKAN API for `archeio-agrotodasikon-symvanton`.
2. For each of 2021, 2022, 2023, 2024: find its XLS resource, download it,
   validate its header, extract normalized rows, run `aggregate_year`.
3. Render one summary paragraph per year from the four aggregates.
4. Embed all four new documents.
5. Only after every embedding succeeds: replace the collection's contents
   — delete existing documents, then add the four new ones.

Step 5 deliberately embeds everything *before* touching the collection.
This is stricter than the original spec's ordering (which deleted first,
then embedded and added in the same loop) — if an embedding call failed
partway through that loop, the collection would be left with the old
documents already deleted and only some new ones added. Precomputing every
embedding first means a failure there is caught before the collection is
touched at all, preserving the "never leave it partially refreshed"
guarantee for this failure mode too, not just for fetch/parse failures.

## Error handling

Any failure — the CKAN call, finding a year's resource, downloading it,
the header not matching the confirmed layout, or an embedding call failing
— must fail loudly (raise / non-zero exit) **before** touching the
existing `fire_data` collection. A partial or failed refresh must never
leave `fire_data` empty or partially overwritten.

This also means: if any one of 2021-2024 fails to fetch or parse, the
*entire* seed run fails — this is the "(b) verify and scope to stable
years" choice applied consistently. It is not a best-effort/partial-update
design; the four years in scope are expected to always succeed together,
and a failure on any of them is worth surfacing loudly rather than quietly
publishing three years instead of four.

## Testing

Consistent with the project's existing seed scripts (`seed_rag.py`,
`seed_road_safety.py`), which have zero test coverage as a matter of
pattern — these are maintenance scripts, not a live request path, so no
network-hitting tests are added, and the `xlrd`-based file-reading code is
not unit tested either.

The one exception is `aggregate_year`, which is pure, has real bug risk,
and needs no mocking to test. Add `govchat/tests/test_seed_fire_data.py`
with a test that feeds a small hardcoded list of normalized row dicts
(a handful of `{"prefecture": ..., "stremmata_burned": ...}` entries
across a few different prefectures) through `aggregate_year`, and asserts
the resulting incident count, total stremmata burned, and top-3
prefecture ordering.

## Out of scope / explicitly deferred

- 2019, 2020, and 2025 for the Fires domain (see "Why 2021-2024" above) —
  a future pass can add them once each layout is individually verified.
- Road safety and energy domains switching to live data (separate future
  exercise).
- Any caching or scheduling of the refresh (it remains a manually-run
  script, same as today).
- Any change to `fires_tool`, `agent.py`, or how the collection is queried.
