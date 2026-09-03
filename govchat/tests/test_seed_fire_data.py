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
