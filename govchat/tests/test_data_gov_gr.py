import pytest

from scripts.data_gov_gr import find_resource_for_year, replace_collection_documents


class _FakeCollection:
    """A minimal stand-in for a ChromaDB collection, just recording calls."""

    def __init__(self, existing_ids: list[str] | None = None):
        self._existing_ids = existing_ids or []
        self.deleted_ids: list[str] | None = None
        self.added: list[dict] = []

    def get(self):
        return {"ids": self._existing_ids}

    def delete(self, ids):
        self.deleted_ids = ids

    def add(self, ids, embeddings, documents, metadatas=None):
        self.added.append(
            {
                "ids": ids,
                "embeddings": embeddings,
                "documents": documents,
                "metadatas": metadatas,
            }
        )

    def count(self):
        return len(self.added)


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


def test_replace_collection_documents_passes_metadata_through_to_add():
    collection = _FakeCollection()
    documents = [
        {"id": "energy_balance_2022", "text": "...", "metadata": {"year": 2022}},
        {"id": "energy_balance_2023", "text": "...", "metadata": {"year": 2023}},
    ]

    replace_collection_documents(collection, documents, embed_fn=lambda text: [0.0])

    metadatas = [call["metadatas"] for call in collection.added]
    assert metadatas == [[{"year": 2022}], [{"year": 2023}]]


def test_replace_collection_documents_defaults_metadata_to_empty_dict():
    collection = _FakeCollection()
    documents = [{"id": "fires_2022", "text": "..."}]  # no "metadata" key at all

    replace_collection_documents(collection, documents, embed_fn=lambda text: [0.0])

    assert collection.added[0]["metadatas"] == [{}]

