# GovChat Greece

AI chatbot για ελληνικά ανοιχτά κυβερνητικά δεδομένα, που αναπτύχθηκε ως τελική εργασία για το μάθημα AI for Developers.

## Τι κάνει

Απαντά σε ερωτήσεις φυσικής γλώσσας για τρεις θεματικές περιοχές:
- **Τροχαία Ατυχήματα**: Στατιστικά ατυχημάτων από την Ελληνική Αστυνομία (2021–2025)
- **Δασικές Πυρκαγιές**: Στατιστικά πυρκαγιών από το Υπουργείο Κλιματικής Κρίσης (2021–2024)
- **Ενέργεια**: Παραγωγή και κατανάλωση ηλεκτρικής ενέργειας (δεδομένα ΑΔΜΗΕ)

## Τρόπος Ανάκτησης Δεδομένων

Και οι τρεις θεματικές χρησιμοποιούν **RAG (Retrieval-Augmented Generation)** — δεν γίνεται καμία ζωντανή κλήση στο data.gov.gr κατά τη διάρκεια της συνομιλίας. Τα δεδομένα έχουν ληφθεί εκ των προτέρων, μετατραπεί σε embeddings και αποθηκευτεί στο ChromaDB.

| Θεματική | Μέθοδος | ChromaDB Collection | Πηγή |
|----------|---------|---------------------|------|
| Τροχαία Ατυχήματα | RAG | `road_safety_data` | Ελληνική Αστυνομία |
| Δασικές Πυρκαγιές | RAG | `fire_data` | Υπ. Κλιματικής Κρίσης |
| Ενέργεια | RAG | `energy_data` | ΑΔΜΗΕ |

Κάθε ερώτηση του χρήστη μετατρέπεται σε embedding (`text-embedding-3-small`) και αναζητείται σε σχετικά chunks στο ChromaDB. Τα chunks επιστρέφονται στο LLM ως context για τη διαμόρφωση της απάντησης.

## Αρχιτεκτονική

```
Χρήστης → FastAPI (auth + chat endpoints)
               ↓
          AI Agent (OpenAI function calling, gpt-4o-mini)
          ├── road_safety_tool → ChromaDB RAG (δεδομένα Αστυνομίας 2021–2025)
          ├── fires_tool       → ChromaDB RAG (δεδομένα Υπ. Κλιματικής Κρίσης 2021–2024)
          └── energy_tool      → ChromaDB RAG (δεδομένα ΑΔΜΗΕ)
               ↓
          SQLite (χρήστες, συνεδρίες, μηνύματα)
```

## Θέματα Μαθήματος

| Θέμα | Υλοποίηση |
|------|-----------|
| FastAPI | Όλα τα endpoints, SQLModel, authentication |
| Prompt Engineering | System prompt στο agent.py, περιγραφές εργαλείων |
| RAG | ChromaDB + text-embedding-3-small για τροχαία, πυρκαγιές και ενέργεια |
| AI Agents | Βρόχος function calling στο agent.py |

## Εγκατάσταση

### Προαπαιτούμενα
- Python 3.11+
- OpenAI API key

### Βήματα

```bash
git clone <repo-url>
cd govchat
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Ρύθμιση περιβάλλοντος

Αντιγράψτε το `.env.example` σε `.env` και συμπληρώστε τα κλειδιά:

```
OPENAI_API_KEY=sk-...
SECRET_KEY=your-random-secret-key
```

### Αρχικοποίηση βάσεων RAG

Εκτελέστε μία φορά πριν την πρώτη χρήση:

```bash
python scripts/seed_rag.py           # δεδομένα ενέργειας
python scripts/seed_road_safety.py   # δεδομένα τροχαίων
python scripts/seed_fire_data.py     # δεδομένα πυρκαγιών
```

### Εκκίνηση server

```bash
uvicorn app.main:app --reload
```

Ανοίξτε το http://localhost:8000/docs για διαδραστική τεκμηρίωση API.

## Χρήση

### 1. Εγγραφή και σύνδεση

```bash
# Εγγραφή
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypass"}'

# Σύνδεση (λήψη token)
curl -X POST http://localhost:8000/auth/login \
  -d "username=myuser&password=mypass"
```

### 2. Δημιουργία συνεδρίας

```bash
curl -X POST http://localhost:8000/chat/sessions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Πρώτη συνεδρία"}'
```

### 3. Υποβολή ερώτησης

```bash
curl -X POST http://localhost:8000/chat/sessions/1/messages \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"content": "Πόσα θανατηφόρα τροχαία συνέβησαν το 2022;"}'
```

### 4. Γρήγορο demo (χωρίς εγγραφή)

```bash
curl "http://localhost:8000/query?q=Τι+είναι+ο+ΑΔΜΗΕ;"
```

## Ενδεικτικές Ερωτήσεις

### Τροχαία Ατυχήματα
- `Πόσα θανατηφόρα τροχαία συνέβησαν στην Ελλάδα το 2022;`
- `Πόσοι άνθρωποι σκοτώθηκαν σε τροχαία το 2024;`
- `Σύγκρινε τα τροχαία ατυχήματα του 2021 και του 2023.`

### Δασικές Πυρκαγιές
- `Πόσα εκτάρια κάηκαν στην Ελλάδα το 2023;`
- `Ποια χρονιά είχε τις μεγαλύτερες πυρκαγιές;`
- `Σύγκρινε τις πυρκαγιές του 2021 και του 2022.`

### Ενέργεια (Ελληνικά)
- `Ποιοι είναι οι στόχοι για ανανεώσιμες πηγές ενέργειας στην Ελλάδα;`
- `Πόσο κόστιζε η ηλεκτρική ενέργεια χονδρικής το 2023;`
- `Ποια είναι η πρόοδος της απολιγνιτοποίησης στην Ελλάδα;`

### Forest Fires (English)
- `How many hectares burned in Greece in 2023?`
- `Which year had the worst wildfires in Greece?`
- `Compare forest fires in Greece between 2021 and 2022.`

### Energy (English)
- `How much electricity did Greece produce from solar energy in 2023?`
- `What countries is Greece electrically connected to?`
- `What is the role of natural gas in Greece's energy mix?`

## Εκτέλεση Tests

```bash
pytest tests/ -v
```

Όλα τα 7 tests πρέπει να περνάνε. Χρησιμοποιούν in-memory SQLite και mock OpenAI API.

## Screenshots

*(Προσθέστε screenshots από το Swagger UI και δείγματα συνομιλιών)*

## Μελλοντικές Βελτιώσεις

- **Περισσότερα datasets**: Στατιστικά εγκληματικότητας, υγείας, οικονομικοί δείκτες από το data.gov.gr
- **Μνήμη συνομιλίας**: Συμπερίληψη προηγούμενων μηνυμάτων στο context του agent
- **Streaming απαντήσεις**: Ροή token-by-token για καλύτερη εμπειρία χρήστη
- **Dashboard διαχειριστή**: Προβολή χρηστών και συνομιλιών μέσω admin endpoints
- **Βελτιωμένο RAG**: Φόρτωση πραγματικών δεδομένων ΑΔΜΗΕ από PDF αναφορές
- **Docker**: Dockerfile για εύκολη ανάπτυξη
