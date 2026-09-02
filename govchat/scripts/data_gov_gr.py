import requests


def fetch_package_resources(package_id: str) -> list[dict]:
    """Fetch the resources list for a data.gov.gr CKAN package."""
    url = f"https://data.gov.gr/api/3/action/package_show?id={package_id}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success"):
        error = payload.get("error") or {}
        raise RuntimeError(
            f"CKAN request for package {package_id!r} failed: "
            f"{error.get('message') or error or 'unknown error'}"
        )
    return payload["result"]["resources"]


def find_resource_for_year(
    resources: list[dict], year: int, *, format: str | None = None
) -> dict:
    """Find the one resource whose name contains `year` as a whitespace-
    separated token. Pass `format` to also require an exact CKAN `format`
    match; leave it as None when a dataset's format metadata is unreliable
    (e.g. the road safety dataset mixes "xl"/"xlx"/blank across years) —
    the "exactly one match" check below still guards against an accidental
    match against an unrelated resource (like a "download all" ZIP) even
    without a format filter.
    """
    matches = [
        r
        for r in resources
        if str(year) in (r.get("name") or "").split()
        and (format is None or r.get("format") == format)
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one resource for {year}"
            + (f" with format {format!r}" if format else "")
            + f", found {len(matches)}"
        )
    return matches[0]


def replace_collection_documents(collection, documents: list[dict], embed_fn) -> None:
    """Embed every document first; only after all embeddings succeed,
    delete the collection's existing documents and add the new ones — so
    a failed embedding call never leaves the collection with some old
    documents deleted and only some new ones added.
    """
    print("Embedding new documents...")
    embedded = [(doc["id"], doc["text"], embed_fn(doc["text"])) for doc in documents]

    existing_ids = collection.get()["ids"]
    if existing_ids:
        collection.delete(ids=existing_ids)
        print(f"Removed {len(existing_ids)} existing documents.")

    for doc_id, text, embedding in embedded:
        collection.add(ids=[doc_id], embeddings=[embedding], documents=[text])
        print(f"  Added: {doc_id}")

    print(f"Done! Collection now has {collection.count()} documents.")
