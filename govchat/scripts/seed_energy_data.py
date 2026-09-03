"""One-off script: downloads Greece's live daily energy-balance data from data.gov.gr (2021-2024) and refreshes the energy_data ChromaDB collection with per-year summaries."""

import csv
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
from dotenv import load_dotenv

load_dotenv(override=True)

from app.ai.rag import embed_text, get_energy_collection
from scripts.data_gov_gr import fetch_package_resources, replace_collection_documents
from scripts.energy_data_aggregation import aggregate_year

# Data pulled live from data.gov.gr (Ενεργειακό Ισοζύγιο / Energy Balance), published by ΑΔΜΗΕ.
PACKAGE_ID = "admie_dailyenergybalanceanalysis"  # id a3f194cc-723a-4e63-b97a-06960dea6a7f
TARGET_YEARS = [2021, 2022, 2023, 2024]  # the only complete calendar years in the dataset


def find_csv_resource(resources: list[dict]) -> dict:
    """Find the one CSV-format resource in the package (this dataset has a single CSV covering every year, not one resource per year)."""
    matches = [r for r in resources if r.get("format") == "CSV"]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one CSV resource, found {len(matches)}")
    return matches[0]


def fetch_all_rows(resource: dict) -> list[dict]:
    """Download and parse the full energy-balance CSV into row dicts."""
    response = requests.get(resource["url"], timeout=60)
    response.raise_for_status()

    reader = csv.DictReader(io.StringIO(response.content.decode("utf-8")))
    rows = []
    for row in reader:
        rows.append(
            {
                "date": row["date"],
                "fuel": row["fuel"],
                "energy_mwh": float(row["energy_mwh"]),
            }
        )
    return rows


def render_year_summary(aggregate) -> str:
    """Turn one year's aggregate into the English paragraph stored in ChromaDB."""

    def pct(part: float) -> float:
        return (part / aggregate.total_mwh) * 100 if aggregate.total_mwh else 0.0

    return (
        f"Greece's electricity balance in {aggregate.year}: total demand of "
        f"approximately {aggregate.total_mwh:,.0f} MWh. Natural gas supplied "
        f"{pct(aggregate.gas_mwh):.1f}% ({aggregate.gas_mwh:,.0f} MWh), renewables "
        f"{pct(aggregate.renewables_mwh):.1f}% ({aggregate.renewables_mwh:,.0f} MWh), "
        f"lignite {pct(aggregate.lignite_mwh):.1f}% ({aggregate.lignite_mwh:,.0f} MWh), "
        f"and hydro {pct(aggregate.hydro_mwh):.1f}% ({aggregate.hydro_mwh:,.0f} MWh). "
        f"Net imports were {aggregate.net_imports_mwh:,.0f} MWh "
        f"({pct(aggregate.net_imports_mwh):.1f}% of demand)."
    )


def fetch_all_aggregates() -> list:
    """Fetch and aggregate energy balance data for every year in TARGET_YEARS, printing progress as it goes."""
    print("Fetching energy balance dataset metadata from data.gov.gr...")
    resources = fetch_package_resources(PACKAGE_ID)
    resource = find_csv_resource(resources)

    print("Downloading energy balance data...")
    rows = fetch_all_rows(resource)

    aggregates = []
    for year in TARGET_YEARS:
        aggregate = aggregate_year(year, rows)
        print(
            f"  {year}: {aggregate.total_mwh:,.0f} MWh total, "
            f"{aggregate.renewables_mwh:,.0f} MWh renewables"
        )
        aggregates.append(aggregate)

    return aggregates


def seed():
    """Fetch, aggregate, and re-embed all years of energy balance data, replacing whatever was in the energy_data collection before."""
    aggregates = fetch_all_aggregates()

    documents = [
        {"id": f"energy_balance_{aggregate.year}", "text": render_year_summary(aggregate)}
        for aggregate in aggregates
    ]

    collection = get_energy_collection()
    replace_collection_documents(collection, documents, embed_text)


if __name__ == "__main__":
    seed()
