from dataclasses import dataclass


@dataclass
class RoadSafetyYearStats:
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
