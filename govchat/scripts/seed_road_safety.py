"""One-off script: downloads live road-accident spreadsheets from data.gov.gr (2018-2025) and refreshes the road_safety_data ChromaDB collection with per-year summaries."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
import xlrd
from dotenv import load_dotenv

load_dotenv(override=True)

from app.ai.rag import embed_text, get_road_safety_collection
from scripts.data_gov_gr import (
    fetch_package_resources,
    find_resource_for_year,
    replace_collection_documents,
)
from scripts.road_safety_validation import RoadSafetyYearStats, validate_year_stats

# Data pulled live from data.gov.gr (Τροχαία ατυχήματα)
# Source: Υπουργείο Προστασίας του Πολίτη
PACKAGE_ID = "troxaia-atyxhmata"  # id 2778acd9-7e84-4712-a7a1-42419359a2ab
TARGET_YEARS = list(range(2018, 2026))  # 2018-2025 inclusive

LABEL_COLUMN = 1
VALUE_COLUMN = 2
ACCIDENTS_HEADER_ROW = 7
CASUALTIES_HEADER_ROW = 13
FATAL_ROW = 8
SERIOUS_ROW = 9
MINOR_ROW = 10
TOTAL_ACCIDENTS_ROW = 11
DEATHS_ROW = 14
SERIOUS_INJURY_ROW = 15
LIGHT_INJURY_ROW = 16
TOTAL_CASUALTIES_ROW = 17

ACCIDENTS_HEADER_LABEL = "ΑΤΥΧΗΜΑΤΑ"
CASUALTIES_HEADER_LABEL = "ΠΑΘΟΝΤΕΣ"


def _read_whole_number(sheet, row: int, col: int) -> int:
    """Read a cell expected to hold a whole number, raising if it's actually a fractional float (guards against silently truncating data)."""
    value = sheet.cell_value(row, col)
    if isinstance(value, float) and not value.is_integer():
        raise RuntimeError(
            f"Expected a whole number at row {row}, column {col}, got {value!r}"
        )
    return int(value)


def fetch_year_stats(resource: dict, year: int) -> RoadSafetyYearStats:
    """Download one year's road-safety XLS, validate its header labels, and return the year's accident/casualty stats."""
    response = requests.get(resource["url"], timeout=60)
    response.raise_for_status()

    workbook = xlrd.open_workbook(file_contents=response.content)
    sheet = workbook.sheet_by_index(0)

    accidents_label = str(sheet.cell_value(ACCIDENTS_HEADER_ROW, LABEL_COLUMN))
    accidents_year = _read_whole_number(sheet, ACCIDENTS_HEADER_ROW, VALUE_COLUMN)
    casualties_label = str(sheet.cell_value(CASUALTIES_HEADER_ROW, LABEL_COLUMN))
    casualties_year = _read_whole_number(sheet, CASUALTIES_HEADER_ROW, VALUE_COLUMN)

    if accidents_label != ACCIDENTS_HEADER_LABEL or accidents_year != year:
        raise RuntimeError(
            f"Road safety XLS for {year}: accidents header is "
            f"{accidents_label!r}/{accidents_year!r}, expected "
            f"{ACCIDENTS_HEADER_LABEL!r}/{year}"
        )
    if casualties_label != CASUALTIES_HEADER_LABEL or casualties_year != year:
        raise RuntimeError(
            f"Road safety XLS for {year}: casualties header is "
            f"{casualties_label!r}/{casualties_year!r}, expected "
            f"{CASUALTIES_HEADER_LABEL!r}/{year}"
        )

    stats = RoadSafetyYearStats(
        year=year,
        fatal_accidents=_read_whole_number(sheet, FATAL_ROW, VALUE_COLUMN),
        serious_accidents=_read_whole_number(sheet, SERIOUS_ROW, VALUE_COLUMN),
        minor_accidents=_read_whole_number(sheet, MINOR_ROW, VALUE_COLUMN),
        total_accidents=_read_whole_number(sheet, TOTAL_ACCIDENTS_ROW, VALUE_COLUMN),
        deaths=_read_whole_number(sheet, DEATHS_ROW, VALUE_COLUMN),
        serious_injuries=_read_whole_number(sheet, SERIOUS_INJURY_ROW, VALUE_COLUMN),
        light_injuries=_read_whole_number(sheet, LIGHT_INJURY_ROW, VALUE_COLUMN),
        total_casualties=_read_whole_number(sheet, TOTAL_CASUALTIES_ROW, VALUE_COLUMN),
    )
    validate_year_stats(stats)
    return stats


def fetch_all_stats() -> list:
    """Fetch and validate road safety stats for every year in TARGET_YEARS, printing progress as it goes."""
    print("Fetching road safety dataset metadata from data.gov.gr...")
    resources = fetch_package_resources(PACKAGE_ID)

    all_stats = []
    for year in TARGET_YEARS:
        # CKAN's format metadata is unreliable for this dataset ("xl",
        # "xlx", or blank depending on the year) — match by year token in
        # the resource name only. find_resource_for_year's "exactly one
        # match" check still guards against an accidental match against
        # the "download all" ZIP resource even without a format filter.
        resource = find_resource_for_year(resources, year)
        print(f"Downloading {year} data...")
        stats = fetch_year_stats(resource, year)
        print(
            f"  {year}: {stats.total_accidents} accidents, "
            f"{stats.total_casualties} casualties"
        )
        all_stats.append(stats)

    return all_stats


def render_year_summary(stats: RoadSafetyYearStats) -> str:
    """Turn one year's stats into the English paragraph stored in ChromaDB."""
    return (
        f"Road accidents in Greece {stats.year}: "
        f"{stats.fatal_accidents} fatal accidents, "
        f"{stats.serious_accidents} serious accidents, "
        f"{stats.minor_accidents} minor accidents, "
        f"{stats.total_accidents} total accidents. "
        f"Casualties: {stats.deaths} deaths, "
        f"{stats.serious_injuries} seriously injured, "
        f"{stats.light_injuries} lightly injured, "
        f"{stats.total_casualties} total casualties."
    )


def seed():
    """Fetch and validate all years of road safety data, replacing whatever was in the road_safety_data collection before."""
    all_stats = fetch_all_stats()

    documents = [
        {"id": f"road_accidents_{stats.year}", "text": render_year_summary(stats)}
        for stats in all_stats
    ]

    collection = get_road_safety_collection()
    replace_collection_documents(collection, documents, embed_text)


if __name__ == "__main__":
    seed()
