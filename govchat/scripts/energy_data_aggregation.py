"""Pure aggregation logic: turns a year's raw ADMIE energy-balance rows into one per-year summary (demand covered by gas, renewables, lignite, hydro, and net imports)."""

from dataclasses import dataclass

# The raw data relabels the same underlying quantity mid-history rather than
# on a clean year boundary (e.g. ΑΙΟΛΙΚΑ/wind-only and ΑΠΕ/all-renewables
# rows are interleaved across 2022-2023), so both labels are merged into one
# bucket here instead of being treated as different fuels.
FUEL_BUCKETS = {
    "ΑΕΡΙΟ": "gas",
    "ΦΥΣΙΚΟ ΑΕΡΙΟ": "gas",
    "ΑΙΟΛΙΚΑ": "renewables",
    "ΑΠΕ": "renewables",
    "ΛΙΓΝΙΤΗΣ": "lignite",
    "ΥΔΡΟΗΛΕΚΤΡΙΚΑ": "hydro",
    "ΚΑΘΑΡΕΣ ΕΙΣΑΓΩΓΕΣ (ΕΙΣΑΓΩΓΕΣ-ΕΞΑΓΩΓΕΣ)": "net_imports",
    "ΣΥΝΟΛΟ": "total",
}

# Category sums won't hit the reported total exactly (floating-point rounding
# in the source), so allow a small relative tolerance before treating a
# mismatch as a real problem (mislabeled/missing category).
TOTAL_TOLERANCE_RATIO = 0.01


@dataclass
class YearEnergyAggregate:
    """One year's electricity balance: total demand, and how much of it came from each source."""

    year: int
    total_mwh: float
    gas_mwh: float
    renewables_mwh: float
    lignite_mwh: float
    hydro_mwh: float
    net_imports_mwh: float


def aggregate_year(year: int, rows: list[dict]) -> YearEnergyAggregate:
    """Sum each fuel bucket's energy_mwh for one year's raw balance rows, merging relabeled fuel categories."""
    sums = {"gas": 0.0, "renewables": 0.0, "lignite": 0.0, "hydro": 0.0, "net_imports": 0.0, "total": 0.0}

    for row in rows:
        if not row["date"].startswith(str(year)):
            continue
        bucket = FUEL_BUCKETS.get(row["fuel"])
        if bucket is None:
            continue
        sums[bucket] += row["energy_mwh"]

    aggregate = YearEnergyAggregate(
        year=year,
        total_mwh=sums["total"],
        gas_mwh=sums["gas"],
        renewables_mwh=sums["renewables"],
        lignite_mwh=sums["lignite"],
        hydro_mwh=sums["hydro"],
        net_imports_mwh=sums["net_imports"],
    )

    category_sum = (
        aggregate.gas_mwh
        + aggregate.renewables_mwh
        + aggregate.lignite_mwh
        + aggregate.hydro_mwh
        + aggregate.net_imports_mwh
    )
    tolerance = abs(aggregate.total_mwh) * TOTAL_TOLERANCE_RATIO
    if abs(category_sum - aggregate.total_mwh) > tolerance:
        raise ValueError(
            f"{year}: gas+renewables+lignite+hydro+net_imports ({category_sum:,.0f}) "
            f"!= reported total ({aggregate.total_mwh:,.0f})"
        )

    return aggregate
