import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
import xlrd
from dotenv import load_dotenv

load_dotenv(override=True)

from app.ai.rag import embed_text, get_fire_collection
from scripts.data_gov_gr import (
    fetch_package_resources,
    find_resource_for_year,
    replace_collection_documents,
)
from scripts.fire_data_aggregation import aggregate_year

# Data pulled live from data.gov.gr (ΑΡΧΕΙΟ ΑΓΡΟΤΟΔΑΣΙΚΩΝ ΣΥΜΒΑΝΤΩΝ)
# Source: Υπουργείο Κλιματικής Κρίσης και Πολιτικής Προστασίας
PACKAGE_ID = "archeio-agrotodasikon-symvanton"  # id 55d3451c-94cb-4577-8cb6-34d3e89a4299
TARGET_YEARS = [2021, 2022, 2023, 2024]

PREFECTURE_COLUMN = 5
AREA_COLUMNS = list(range(14, 22))  # 8 burned-area columns, in stremmata
FIRST_DATA_ROW = 2

# Only columns 5 (prefecture) and 14-21 (burned-area) are actually used.
# Validated against the real 2021-2024 files: total column count is stable
# at 38, and these two labels are stable across all four years — but
# column 28 ("service vehicles" vs "local authority vehicles") is worded
# differently in 2021 vs 2022-2024, which is why the full header isn't
# checked verbatim.
EXPECTED_COLUMN_COUNT = 38
PREFECTURE_HEADER = "Νομός"
AREA_HEADERS = [
    "Δάση",
    "Δασική Έκταση",
    "Άλση",
    "Χορτ/κές Εκτάσεις",
    "Καλάμια - Βάλτοι",
    "Γεωργικές Εκτάσεις",
    "Υπολλείματα Καλλιεργειών",
    "Σκουπι-δότοποι",
]


def fetch_year_rows(resource: dict, year: int) -> list[dict]:
    response = requests.get(resource["url"], timeout=60)
    response.raise_for_status()

    workbook = xlrd.open_workbook(file_contents=response.content)
    sheet = workbook.sheet_by_index(0)

    if sheet.ncols != EXPECTED_COLUMN_COUNT:
        raise RuntimeError(
            f"Fire data XLS for {year} has {sheet.ncols} columns, "
            f"expected {EXPECTED_COLUMN_COUNT}"
        )

    actual_prefecture_header = str(sheet.cell_value(1, PREFECTURE_COLUMN)).strip()
    if actual_prefecture_header != PREFECTURE_HEADER:
        raise RuntimeError(
            f"Fire data XLS for {year}: column {PREFECTURE_COLUMN} is "
            f"{actual_prefecture_header!r}, expected {PREFECTURE_HEADER!r}"
        )

    actual_area_headers = [
        str(sheet.cell_value(1, c)).strip() for c in AREA_COLUMNS
    ]
    if actual_area_headers != AREA_HEADERS:
        raise RuntimeError(
            f"Fire data XLS for {year} has unexpected area columns: "
            f"{actual_area_headers}"
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
                try:
                    stremmata += float(value.strip())
                except ValueError as exc:
                    raise RuntimeError(
                        f"Fire data XLS for {year}: cell at row {r}, "
                        f"column {c} has non-numeric burned-area value "
                        f"{value!r}"
                    ) from exc
        rows.append({"prefecture": prefecture, "stremmata_burned": stremmata})

    return rows


def fetch_all_aggregates() -> list:
    print("Fetching fire dataset metadata from data.gov.gr...")
    resources = fetch_package_resources(PACKAGE_ID)

    aggregates = []
    for year in TARGET_YEARS:
        resource = find_resource_for_year(resources, year, format="XLS")
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

    collection = get_fire_collection()
    replace_collection_documents(collection, documents, embed_text)


if __name__ == "__main__":
    seed()
