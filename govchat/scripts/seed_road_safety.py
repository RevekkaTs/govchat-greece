import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(override=True)

from app.ai.rag import get_road_safety_collection, embed_text

ROAD_SAFETY_DOCUMENTS = [
    {
        "id": "road_accidents_2021",
        "text": "Road accidents in Greece 2021: 574 fatal accidents, 505 serious accidents, 9,887 minor accidents, 10,966 total accidents. Casualties: 611 deaths, 582 seriously injured, 12,358 lightly injured, 13,551 total casualties."
    },
    {
        "id": "road_accidents_2022",
        "text": "Road accidents in Greece 2022: 601 fatal accidents, 564 serious accidents, 9,837 minor accidents, 11,002 total accidents. Casualties: 637 deaths, 639 seriously injured, 12,597 lightly injured, 13,873 total casualties."
    },
    {
        "id": "road_accidents_2023",
        "text": "Road accidents in Greece 2023: 579 fatal accidents, 576 serious accidents, 9,714 minor accidents, 10,869 total accidents. Casualties: 614 deaths, 661 seriously injured, 12,587 lightly injured, 13,862 total casualties."
    },
    {
        "id": "road_accidents_2024",
        "text": "Road accidents in Greece 2024: 623 fatal accidents, 466 serious accidents, 10,061 minor accidents, 11,150 total accidents. Casualties: 662 deaths, 553 seriously injured, 12,990 lightly injured, 14,205 total casualties."
    },
    {
        "id": "road_accidents_2025",
        "text": "Road accidents in Greece 2025: 489 fatal accidents, 444 serious accidents, 10,276 minor accidents, 11,209 total accidents. Casualties: 522 deaths, 523 seriously injured, 13,184 lightly injured, 14,229 total casualties."
    },
]


def seed():
    collection = get_road_safety_collection()

    existing = collection.count()
    if existing > 0:
        print(f"Collection already has {existing} documents. Skipping seed.")
        return

    print(f"Seeding {len(ROAD_SAFETY_DOCUMENTS)} documents into ChromaDB...")

    for doc in ROAD_SAFETY_DOCUMENTS:
        embedding = embed_text(doc["text"])
        collection.add(
            ids=[doc["id"]],
            embeddings=[embedding],
            documents=[doc["text"]]
        )
        print(f"  Added: {doc['id']}")

    print(f"Done! Collection now has {collection.count()} documents.")


if __name__ == "__main__":
    seed()
