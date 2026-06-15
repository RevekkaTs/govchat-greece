import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(override=True)

from app.ai.rag import get_fire_collection, embed_text

# Data pulled from data.gov.gr API (ΑΡΧΕΙΟ ΑΓΡΟΤΟΔΑΣΙΚΩΝ ΣΥΜΒΑΝΤΩΝ)
# Source: Υπουργείο Κλιματικής Κρίσης και Πολιτικής Προστασίας
# Dataset ID: 55d3451c-94cb-4577-8cb6-34d3e89a4299
FIRE_DOCUMENTS = [
    {
        "id": "fires_2021",
        "text": (
            "Forest and agricultural fires in Greece 2021: 9,514 total fire incidents. "
            "Burned area: 90,922 hectares of forest/woodland, 7,780 hectares of grassland/shrubland, "
            "32,149 hectares of agricultural land. Total burned area: approximately 130,851 hectares. "
            "2021 was a severe fire year dominated by the catastrophic Evia (Euboea) fires in August."
        )
    },
    {
        "id": "fires_2022",
        "text": (
            "Forest and agricultural fires in Greece 2022: 8,500 total fire incidents. "
            "Burned area: 28,653 hectares of forest/woodland, 13,949 hectares of grassland/shrubland, "
            "11,559 hectares of agricultural land. Total burned area: approximately 54,162 hectares. "
            "2022 had significantly less burned area compared to 2021 and 2023."
        )
    },
    {
        "id": "fires_2023",
        "text": (
            "Forest and agricultural fires in Greece 2023: 8,257 total fire incidents. "
            "Burned area: 425,204 hectares of forest/woodland, 63,989 hectares of grassland/shrubland, "
            "18,744 hectares of agricultural land. Total burned area: approximately 507,937 hectares. "
            "2023 was the most destructive fire year on record, driven by the Evros mega-fire near Alexandroupolis "
            "which burned over 84,000 hectares — the largest wildfire ever recorded in EU history."
        )
    },
    {
        "id": "fires_2024",
        "text": (
            "Forest and agricultural fires in Greece 2024: 9,777 total fire incidents. "
            "Burned area (estimated from sample): approximately 101,317 hectares of forest/woodland, "
            "21,648 hectares of grassland/shrubland, 31,933 hectares of agricultural land. "
            "Total burned area: approximately 154,898 hectares. "
            "2024 saw a higher number of incidents than previous years."
        )
    },
]


def seed():
    collection = get_fire_collection()

    existing = collection.count()
    if existing > 0:
        print(f"Collection already has {existing} documents. Skipping seed.")
        return

    print(f"Seeding {len(FIRE_DOCUMENTS)} documents into ChromaDB...")

    for doc in FIRE_DOCUMENTS:
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
