"""Data shape for one year's road-safety stats, plus a sanity check that the accident/casualty breakdowns add up to the reported totals."""

from dataclasses import dataclass


@dataclass
class RoadSafetyYearStats:
    """One year's road-safety totals: accidents broken down by severity, and casualties broken down by severity."""

    year: int
    fatal_accidents: int
    serious_accidents: int
    minor_accidents: int
    total_accidents: int
    deaths: int
    serious_injuries: int
    light_injuries: int
    total_casualties: int


def validate_year_stats(stats: RoadSafetyYearStats) -> None:
    """Raise ValueError if the accident or casualty breakdowns don't sum to the reported totals for that year."""
    accident_sum = (
        stats.fatal_accidents + stats.serious_accidents + stats.minor_accidents
    )
    if accident_sum != stats.total_accidents:
        raise ValueError(
            f"{stats.year}: fatal+serious+minor accidents ({accident_sum}) "
            f"!= reported total ({stats.total_accidents})"
        )

    casualty_sum = stats.deaths + stats.serious_injuries + stats.light_injuries
    if casualty_sum != stats.total_casualties:
        raise ValueError(
            f"{stats.year}: deaths+serious+light injuries ({casualty_sum}) "
            f"!= reported total casualties ({stats.total_casualties})"
        )
