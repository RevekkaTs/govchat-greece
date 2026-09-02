import pytest

from scripts.data_gov_gr import find_resource_for_year


def test_find_resource_for_year_matches_year_token_in_name():
    resources = [
        {"name": "Στατιστικά 2021", "format": "XLS"},
        {"name": "Στατιστικά 2022", "format": "XLS"},
        {"name": "Όλα τα δεδομένα", "format": "ZIP"},
    ]

    result = find_resource_for_year(resources, 2022)

    assert result["name"] == "Στατιστικά 2022"


def test_find_resource_for_year_raises_when_no_match():
    resources = [{"name": "Στατιστικά 2021", "format": "XLS"}]

    with pytest.raises(RuntimeError):
        find_resource_for_year(resources, 2022)


def test_find_resource_for_year_format_filter_disambiguates():
    resources = [
        {"name": "Στατιστικά 2022 (παλιά έκδοση)", "format": "CSV"},
        {"name": "Στατιστικά 2022", "format": "XLS"},
    ]

    result = find_resource_for_year(resources, 2022, format="XLS")

    assert result["format"] == "XLS"


def test_find_resource_for_year_raises_on_ambiguous_match_without_format_filter():
    resources = [
        {"name": "Στατιστικά 2022 (παλιά έκδοση)", "format": "CSV"},
        {"name": "Στατιστικά 2022", "format": "XLS"},
    ]

    with pytest.raises(RuntimeError):
        find_resource_for_year(resources, 2022)
