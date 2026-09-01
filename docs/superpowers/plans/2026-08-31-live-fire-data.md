# Live Fire Data Integration Implementation Plan

> **For the implementer:** this plan is written for you to execute yourself, task by task — write the code, run the commands, and check in for review between tasks (same workflow as KR7's containerization work). Steps use checkbox (`- [ ]`) syntax so you can track progress.

**Goal:** Replace the hardcoded 2021-2024 fire summary paragraphs in `govchat/scripts/seed_fire_data.py` with paragraphs generated from live data fetched from data.gov.gr, so the Fires domain is backed by a real external API integration (KR2).

**Architecture:** `seed_fire_data.py` calls the CKAN `package_show` API to find each year's XLS resource, downloads it, extracts prefecture + burned-area figures per incident via `xlrd`, and hands normalized rows to a small pure aggregation function. The rendered paragraphs replace the `fire_data` ChromaDB collection's contents atomically (embed everything first, only then delete + re-add). No other file in the app changes.

**Tech Stack:** Python stdlib, `requests` (already a dependency), `xlrd` (new dependency — reads legacy `.xls` binary format), existing `app.ai.rag` helpers (`get_fire_collection`, `embed_text`).

**Spec:** `docs/superpowers/specs/2026-08-31-live-fire-data-design.md`

## Global Constraints

- Scope is exactly years 2021, 2022, 2023, 2024 — no other years.
- The CKAN package id is `archeio-agrotodasikon-symvanton` (id `55d3451c-94cb-4577-8cb6-34d3e89a4299`) — NOT `mcp_forest_fires`.
- Data format is legacy binary `.xls`, read via `xlrd`. Do not use `pandas`, `openpyxl`, or the stdlib `csv` module for this.
- Burned-area figures stay in στρέμματα (stremmata) — no conversion to hectares. This is a deliberate choice: Greek readers intuitively understand stremmata, and it's the unit the source data already uses.
- The expected header row (row index 1, 38 columns) must be validated before parsing a year's data; any mismatch is a hard failure, not a warning.
- `fire_data` collection contents are only ever mutated after every new document has been successfully embedded — never delete-then-embed.
- No changes to `agent.py`, `rag.py`, or `tools.py` (the confirmed 2021-2024 range means `tools.py`'s existing docstring is already accurate, so this file does not need to be touched at all).
- No network-hitting tests — consistent with `seed_rag.py` and `seed_road_safety.py`, which have zero test coverage. Only the pure aggregation function gets a unit test.

---

### Task 1: Pure yearly aggregation function

**Files:**
- Create: `govchat/scripts/fire_data_aggregation.py`
- Test: `govchat/tests/test_seed_fire_data.py`

**Interfaces:**
- Produces: `YearAggregate` (dataclass: `year: int`, `incident_count: int`, `total_stremmata_burned: float`, `top_prefectures: list[tuple[str, int]]`) and `aggregate_year(year: int, rows: list[dict]) -> YearAggregate`, where each `row` dict has keys `"prefecture": str` and `"stremmata_burned": float`. Task 2 depends on both this exact signature and the dict shape it consumes.

- [ ] **Step 1: Write the failing test**

Create `govchat/tests/test_seed_fire_data.py`:

```python
from scripts.fire_data_aggregation import aggregate_year


def test_aggregate_year_counts_stremmata_and_top_prefectures():
    rows = [
        {"prefecture": "ΑΤΤΙΚΗΣ", "stremmata_burned": 10.0},
        {"prefecture": "ΑΤΤΙΚΗΣ", "stremmata_burned": 5.0},
        {"prefecture": "ΗΛΕΙΑΣ", "stremmata_burned": 2.5},
        {"prefecture": "ΗΛΕΙΑΣ", "stremmata_burned": 0.0},
        {"prefecture": "ΛΑΡΙΣΑΣ", "stremmata_burned": 1.0},
    ]

    result = aggregate_year(2022, rows)

    assert result.year == 2022
    assert result.incident_count == 5
    assert result.total_stremmata_burned == 18.5
    assert result.top_prefectures == [
        ("ΑΤΤΙΚΗΣ", 2),
        ("ΗΛΕΙΑΣ", 2),
        ("ΛΑΡΙΣΑΣ", 1),
    ]
```

(`ΑΤΤΙΚΗΣ` and `ΗΛΕΙΑΣ` tie at 2 incidents each — the expected order relies on `Counter.most_common()` being a stable sort that preserves first-seen order on ties, which is standard library behavior, not something this test is gambling on.)

- [ ] **Step 2: Run the test and confirm it fails**

From `govchat/` with the venv active:

```bash
pytest tests/test_seed_fire_data.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.fire_data_aggregation'`.

- [ ] **Step 3: Implement the pure function**

Create `govchat/scripts/fire_data_aggregation.py`:

```python
from collections import Counter
from dataclasses import dataclass


@dataclass
class YearAggregate:
    year: int
    incident_count: int
    total_stremmata_burned: float
    top_prefectures: list[tuple[str, int]]


def aggregate_year(year: int, rows: list[dict]) -> YearAggregate:
    total_stremmata = 0.0
    prefecture_counts: Counter = Counter()

    for row in rows:
        total_stremmata += row["stremmata_burned"]
        prefecture = row["prefecture"].strip()
        if prefecture:
            prefecture_counts[prefecture] += 1

    return YearAggregate(
        year=year,
        incident_count=len(rows),
        total_stremmata_burned=total_stremmata,
        top_prefectures=prefecture_counts.most_common(3),
    )
```

- [ ] **Step 4: Run the test and confirm it passes**

```bash
pytest tests/test_seed_fire_data.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add govchat/scripts/fire_data_aggregation.py govchat/tests/test_seed_fire_data.py
git commit -m "feat: add pure yearly fire-incident aggregation function"
```

---

### Task 2: Live fetch + parse + safe reseed

**Files:**
- Modify: `govchat/requirements.txt`
- Modify (full rewrite): `govchat/scripts/seed_fire_data.py`

**Interfaces:**
- Consumes: `aggregate_year(year: int, rows: list[dict]) -> YearAggregate` and `YearAggregate` from Task 1 (`scripts.fire_data_aggregation`); `get_fire_collection()` and `embed_text(text: str) -> list[float]` from `app.ai.rag` (already exist, unchanged).

- [ ] **Step 1: Add the new dependency**

Append `xlrd` as a new line at the end of `govchat/requirements.txt`, then install it into the active venv:

```bash
pip install xlrd
```

Verify it's importable:

```bash
python -c "import xlrd; print(xlrd.__version__)"
```

Expected: prints a version string (e.g. `2.0.1`), no error.

- [ ] **Step 2: Rewrite `seed_fire_data.py`**

Replace the entire contents of `govchat/scripts/seed_fire_data.py` with:

```python
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
import xlrd
from dotenv import load_dotenv

load_dotenv(override=True)

from app.ai.rag import get_fire_collection, embed_text
from scripts.fire_data_aggregation import aggregate_year

# Data pulled live from data.gov.gr (ΑΡΧΕΙΟ ΑΓΡΟΤΟΔΑΣΙΚΩΝ ΣΥΜΒΑΝΤΩΝ)
# Source: Υπουργείο Κλιματικής Κρίσης και Πολιτικής Προστασίας
# Package: archeio-agrotodasikon-symvanton (id 55d3451c-94cb-4577-8cb6-34d3e89a4299)
CKAN_PACKAGE_URL = (
    "https://data.gov.gr/api/3/action/package_show"
    "?id=archeio-agrotodasikon-symvanton"
)
TARGET_YEARS = [2021, 2022, 2023, 2024]

PREFECTURE_COLUMN = 5
AREA_COLUMNS = list(range(14, 22))  # 8 burned-area columns, in stremmata
FIRST_DATA_ROW = 2

# Confirmed header row (row index 1) — identical across all four target years.
# Only columns 5 and 14-21 are actually used; the rest are here so a layout
# change in the source file is caught instead of silently misparsed.
EXPECTED_HEADERS = [
    "Α/Α ΕΓΓΡΑΦΗΣ", "Α/Α ENGAGE", "X-ENGAGE", "Y-ENGAGE", "Υπηρεσία",
    "Νομός", "Ημερ/νία Έναρξης", "Ώρα Έναρξης", "Ημερ/νία Κατασβεσης",
    "Ώρα Κατάσβεσης", "Δασαρχείο", "Δήμος", "Περιοχή", "Διεύθυνση",
    "Δάση", "Δασική Έκταση", "Άλση", "Χορτ/κές Εκτάσεις",
    "Καλάμια - Βάλτοι", "Γεωργικές Εκτάσεις", "Υπολλείματα Καλλιεργειών",
    "Σκουπι-δότοποι", "ΠΥΡΟΣ. ΣΩΜΑ", "ΠΕΖΟΠΟΡΑ ΤΜΗΜΑΤΑ", "ΕΘΕΛΟ-ΝΤΕΣ",
    "ΣΤΡΑΤΟΣ", "ΑΛΛΕΣ ΔΥΝΑΜΕΙΣ", "ΠΥΡΟΣ. ΟΧΗΜ.", "ΟΧΗΜ. ΥΠΗΡΕΣΙΑΚΑ",
    "ΒΥΤΙΟ- ΦΟΡΑ", "ΜΗΧΑΝΗ-ΜΑΤΑ", "ΕΛΙΚΟ- ΠΤΕΡΑ", "Α/Φ CL415",
    "Α/Φ CL215", "Α/Φ PZL", "Α/Φ GRU.", "ΜΙΣΘ. ΕΛΙΚΟΠΤ.", "ΜΙΣΘ. ΑΕΡΟΣΚ.",
]


def find_resource_for_year(resources: list[dict], year: int) -> dict:
    matches = [
        r for r in resources
        if r.get("format") == "XLS" and str(year) in (r.get("name") or "").split()
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one XLS resource for {year} in the "
            f"archeio-agrotodasikon-symvanton package, found {len(matches)}"
        )
    return matches[0]


def fetch_year_rows(resource: dict, year: int) -> list[dict]:
    response = requests.get(resource["url"], timeout=60)
    response.raise_for_status()

    workbook = xlrd.open_workbook(file_contents=response.content)
    sheet = workbook.sheet_by_index(0)

    actual_headers = [str(sheet.cell_value(1, c)) for c in range(sheet.ncols)]
    if actual_headers != EXPECTED_HEADERS:
        raise RuntimeError(
            f"Fire data XLS for {year} has an unexpected column layout "
            f"(expected {len(EXPECTED_HEADERS)} columns matching the "
            f"2021-2024 schema). Got: {actual_headers}"
        )

    rows = []
    for r in range(FIRST_DATA_ROW, sheet.nrows):
        prefecture = str(sheet.cell_value(r, PREFECTURE_COLUMN)).strip()
        stremmata = 0.0
        for c in AREA_COLUMNS:
            value = sheet.cell_value(r, c)
            if isinstance(value, (int, float)):
                stremmata += value
            elif isinstance(value, str) and value.strip():
                stremmata += float(value.strip())
        rows.append({"prefecture": prefecture, "stremmata_burned": stremmata})

    return rows


def fetch_all_aggregates() -> list:
    print("Fetching fire dataset metadata from data.gov.gr...")
    response = requests.get(CKAN_PACKAGE_URL, timeout=30)
    response.raise_for_status()
    resources = response.json()["result"]["resources"]

    aggregates = []
    for year in TARGET_YEARS:
        resource = find_resource_for_year(resources, year)
        print(f"Downloading {year} data...")
        rows = fetch_year_rows(resource, year)
        aggregate = aggregate_year(year, rows)
        print(
            f"  {year}: {aggregate.incident_count} incidents, "
            f"{aggregate.total_stremmata_burned:,.0f} stremmata"
        )
        aggregates.append(aggregate)

    return aggregates


def render_year_summary(aggregate) -> str:
    prefecture_text = ", ".join(
        f"{name} ({count} incidents)" for name, count in aggregate.top_prefectures
    )
    return (
        f"Forest and agricultural fires in Greece {aggregate.year}: "
        f"{aggregate.incident_count} total fire incidents. "
        f"Total burned area: approximately "
        f"{aggregate.total_stremmata_burned:,.0f} stremmata. "
        f"Most affected prefectures: {prefecture_text}."
    )


def seed():
    aggregates = fetch_all_aggregates()

    documents = [
        {"id": f"fires_{aggregate.year}", "text": render_year_summary(aggregate)}
        for aggregate in aggregates
    ]

    print("Embedding new documents...")
    embedded = [
        (doc["id"], doc["text"], embed_text(doc["text"])) for doc in documents
    ]

    collection = get_fire_collection()
    existing_ids = collection.get()["ids"]
    if existing_ids:
        collection.delete(ids=existing_ids)
        print(f"Removed {len(existing_ids)} existing documents.")

    for doc_id, text, embedding in embedded:
        collection.add(ids=[doc_id], embeddings=[embedding], documents=[text])
        print(f"  Added: {doc_id}")

    print(f"Done! Collection now has {collection.count()} documents.")


if __name__ == "__main__":
    seed()
```

Note this drops the old "skip if collection already has documents" early return — every run now always re-fetches live and replaces the collection's contents. That's intentional: the whole point is a live-refreshable dataset, not a one-time seed.

- [ ] **Step 3: Run it for real**

From `govchat/` with the venv active and `OPENAI_API_KEY` set in `.env`:

```bash
python scripts/seed_fire_data.py
```

Expected output: four `Downloading <year> data...` lines followed by incident/stremmata figures, then `Embedding new documents...`, then `Removed 4 existing documents.` (or `0` on a fresh DB), then four `Added: fires_<year>` lines, ending `Done! Collection now has 4 documents.`

The printed incident counts and stremmata totals should be close to these (verified during spec-writing):

| Year | Incidents | Stremmata burned |
|---|---|---|
| 2021 | 9,514 | ~1,332,140 |
| 2022 | 9,856 | ~285,650 |
| 2023 | 8,257 | ~1,769,660 |
| 2024 | 9,777 | ~483,070 |

If a year's numbers are wildly different from this table, or the script raises an error, stop and treat it as a bug to investigate before moving on — don't rerun repeatedly hoping it resolves itself.

- [ ] **Step 4: Spot-check via `fires_tool`**

From `govchat/` with the venv active:

```bash
python -c "from app.ai.tools import fires_tool; print(fires_tool(2022))"
```

Expected: prints the new 2022 paragraph (mentions 2022, an incident count, stremmata, prefectures) — not the old hardcoded text.

- [ ] **Step 5: Run the full test suite**

```bash
pytest tests/ -v
```

Expected: all tests pass, including `test_aggregate_year_counts_stremmata_and_top_prefectures` from Task 1.

- [ ] **Step 6: Commit**

```bash
git add govchat/requirements.txt govchat/scripts/seed_fire_data.py
git commit -m "feat: seed fire_data collection from live data.gov.gr XLS data"
```
