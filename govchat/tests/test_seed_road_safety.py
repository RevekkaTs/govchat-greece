import pytest
from scripts.road_safety_validation import RoadSafetyYearStats, validate_year_stats


def test_validate_year_stats_accepts_consistent_totals():
    stats = RoadSafetyYearStats(
        year=2022,
        fatal_accidents=601,
        serious_accidents=564,
        minor_accidents=9837,
        total_accidents=11002,
        deaths=637,
        serious_injuries=639,
        light_injuries=12597,
        total_casualties=13873,
    )

    validate_year_stats(stats)  # should not raise


def test_validate_year_stats_rejects_accident_mismatch():
    stats = RoadSafetyYearStats(
        year=2022,
        fatal_accidents=601,
        serious_accidents=564,
        minor_accidents=9837,
        total_accidents=99999,  # deliberately wrong
        deaths=637,
        serious_injuries=639,
        light_injuries=12597,
        total_casualties=13873,
    )

    with pytest.raises(ValueError):
        validate_year_stats(stats)


def test_validate_year_stats_rejects_casualty_mismatch():
    stats = RoadSafetyYearStats(
        year=2022,
        fatal_accidents=601,
        serious_accidents=564,
        minor_accidents=9837,
        total_accidents=11002,
        deaths=637,
        serious_injuries=639,
        light_injuries=12597,
        total_casualties=99999,  # deliberately wrong
    )

    with pytest.raises(ValueError):
        validate_year_stats(stats)
