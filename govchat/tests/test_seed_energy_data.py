import pytest

from scripts.energy_data_aggregation import aggregate_year


def _row(date: str, fuel: str, energy_mwh: float) -> dict:
    return {"date": date, "fuel": fuel, "energy_mwh": energy_mwh}


def test_aggregate_year_sums_and_merges_fuel_labels():
    rows = [
        # Day 1: uses the older "ΑΙΟΛΙΚΑ"/"ΦΥΣΙΚΟ ΑΕΡΙΟ" labels.
        _row("2022-01-01 00:00:00", "ΦΥΣΙΚΟ ΑΕΡΙΟ", 100.0),
        _row("2022-01-01 00:00:00", "ΑΙΟΛΙΚΑ", 50.0),
        _row("2022-01-01 00:00:00", "ΛΙΓΝΙΤΗΣ", 30.0),
        _row("2022-01-01 00:00:00", "ΥΔΡΟΗΛΕΚΤΡΙΚΑ", 10.0),
        _row("2022-01-01 00:00:00", "ΚΑΘΑΡΕΣ ΕΙΣΑΓΩΓΕΣ (ΕΙΣΑΓΩΓΕΣ-ΕΞΑΓΩΓΕΣ)", 10.0),
        _row("2022-01-01 00:00:00", "ΣΥΝΟΛΟ", 200.0),
        # Day 2: uses the newer "ΑΠΕ"/"ΑΕΡΙΟ" labels for the same underlying quantities.
        _row("2022-01-02 00:00:00", "ΑΕΡΙΟ", 90.0),
        _row("2022-01-02 00:00:00", "ΑΠΕ", 60.0),
        _row("2022-01-02 00:00:00", "ΛΙΓΝΙΤΗΣ", 20.0),
        _row("2022-01-02 00:00:00", "ΥΔΡΟΗΛΕΚΤΡΙΚΑ", 15.0),
        _row("2022-01-02 00:00:00", "ΚΑΘΑΡΕΣ ΕΙΣΑΓΩΓΕΣ (ΕΙΣΑΓΩΓΕΣ-ΕΞΑΓΩΓΕΣ)", 5.0),
        _row("2022-01-02 00:00:00", "ΣΥΝΟΛΟ", 190.0),
        # A different year's row must be excluded entirely.
        _row("2023-01-01 00:00:00", "ΣΥΝΟΛΟ", 999.0),
    ]

    result = aggregate_year(2022, rows)

    assert result.year == 2022
    assert result.gas_mwh == 190.0  # 100 (ΦΥΣΙΚΟ ΑΕΡΙΟ) + 90 (ΑΕΡΙΟ)
    assert result.renewables_mwh == 110.0  # 50 (ΑΙΟΛΙΚΑ) + 60 (ΑΠΕ)
    assert result.lignite_mwh == 50.0
    assert result.hydro_mwh == 25.0
    assert result.net_imports_mwh == 15.0
    assert result.total_mwh == 390.0


def test_aggregate_year_raises_when_categories_dont_sum_to_total():
    rows = [
        _row("2022-01-01 00:00:00", "ΑΕΡΙΟ", 100.0),
        _row("2022-01-01 00:00:00", "ΑΠΕ", 50.0),
        _row("2022-01-01 00:00:00", "ΛΙΓΝΙΤΗΣ", 30.0),
        _row("2022-01-01 00:00:00", "ΥΔΡΟΗΛΕΚΤΡΙΚΑ", 10.0),
        _row("2022-01-01 00:00:00", "ΚΑΘΑΡΕΣ ΕΙΣΑΓΩΓΕΣ (ΕΙΣΑΓΩΓΕΣ-ΕΞΑΓΩΓΕΣ)", 10.0),
        # Total is reported far higher than the categories actually sum to (200).
        _row("2022-01-01 00:00:00", "ΣΥΝΟΛΟ", 500.0),
    ]

    with pytest.raises(ValueError):
        aggregate_year(2022, rows)
