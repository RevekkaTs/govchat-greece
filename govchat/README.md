# GovChat Greece

AI chatbot για ελληνικά ανοιχτά κυβερνητικά δεδομένα, που αναπτύχθηκε ως τελική εργασία για το μάθημα AI for Developers.

**Πλήρης τεκμηρίωση:** [`docs/documentation.md`](docs/documentation.md)

## Τι κάνει

Απαντά σε ερωτήσεις φυσικής γλώσσας για τρεις θεματικές περιοχές:
- **Τροχαία Ατυχήματα**: Στατιστικά ατυχημάτων από την Ελληνική Αστυνομία (2021–2025)
- **Δασικές Πυρκαγιές**: Στατιστικά πυρκαγιών από το Υπουργείο Κλιματικής Κρίσης (2021–2024)
- **Ενέργεια**: Ισοζύγιο ηλεκτρικής ενέργειας — μείγμα καυσίμων και εισαγωγές/εξαγωγές (δεδομένα ΑΔΜΗΕ, 2021–2024)

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

## Endpoints API

Όλα τα endpoints είναι versioned κάτω από `/v1` (εκτός από ένα `/v2` endpoint).

| Endpoint | Μέθοδος | Auth | Περιγραφή |
|----------|---------|------|-----------|
| `/v1/auth/register` | POST | Όχι | Δημιουργία λογαριασμού |
| `/v1/auth/login` | POST | Όχι | OAuth2 login, επιστρέφει JWT token |
| `/v1/auth/me` | GET | Ναι | Τρέχων χρήστης |
| `/v2/auth/me` | GET | Ναι | Τρέχων χρήστης (v2 response shape) |
| `/v1/chat/sessions` | POST | Ναι | Νέα συνεδρία συνομιλίας |
| `/v1/chat/sessions` | GET | Ναι | Λίστα συνεδριών χρήστη |
| `/v1/chat/sessions/{id}/messages` | POST | Ναι | Αποστολή μηνύματος (εκτελεί agent) |
| `/v1/chat/sessions/{id}/messages` | GET | Ναι | Ιστορικό συνεδρίας |
| `/v1/chat/sessions/{id}/export` | GET | Ναι | Εξαγωγή συνεδρίας (JSON) |
| `/v1/chat/sessions/import` | POST | Ναι | Εισαγωγή συνεδρίας από εξαγόμενο JSON |
| `/v1/query?q=...` | GET | Όχι | Γρήγορη ερώτηση χωρίς εγγραφή |
| `/docs` | GET | Όχι | Swagger UI (αυτόματη τεκμηρίωση) |

## GenAI Λογική

| Τεχνική | Υλοποίηση |
|---------|-----------|
| **Prompt Engineering** | System prompt με role assignment, behavioral constraints, δυναμική ανίχνευση γλώσσας (Ελληνικά/Αγγλικά) — `app/ai/agent.py` |
| **RAG** | Ερωτήματα χρήστη → `text-embedding-3-small` → ChromaDB similarity search → top-3 chunks ως context — `app/ai/rag.py` |
| **AI Agent** | Βρόχος δύο σταδίων: gpt-4o-mini επιλέγει εργαλείο (`tool_choice="required"`) → εκτελείται RAG → δεύτερη κλήση για τελική απάντηση — `app/ai/agent.py` |
| **Tool Calling** | 3 εργαλεία: `road_safety_tool`, `fires_tool`, `energy_tool` — `app/ai/tools.py` |

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
git clone https://github.com/RevekkaTs/govchat-greece.git
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
python scripts/seed_energy_data.py   # δεδομένα ενέργειας
python scripts/seed_road_safety.py   # δεδομένα τροχαίων
python scripts/seed_fire_data.py     # δεδομένα πυρκαγιών
```

### Εκκίνηση backend

```bash
uvicorn app.main:app --reload
```

Swagger UI: http://localhost:8000/docs

### Εκκίνηση frontend (νέο terminal)

```bash
streamlit run streamlit_app.py
```

UI: http://localhost:8501

## Χρήση

### 1. Εγγραφή και σύνδεση

```bash
# Εγγραφή
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypass"}'

# Σύνδεση (λήψη token)
curl -X POST http://localhost:8000/v1/auth/login \
  -d "username=myuser&password=mypass"
```

### 2. Δημιουργία συνεδρίας

```bash
curl -X POST http://localhost:8000/v1/chat/sessions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Πρώτη συνεδρία"}'
```

### 3. Υποβολή ερώτησης

```bash
curl -X POST http://localhost:8000/v1/chat/sessions/1/messages \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"content": "Πόσα θανατηφόρα τροχαία συνέβησαν το 2022;"}'
```

### 4. Γρήγορο demo (χωρίς εγγραφή)

```bash
curl "http://localhost:8000/v1/query?q=Ποιο+ήταν+το+ενεργειακό+ισοζύγιο+το+2023;"
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
- `Ποιο ήταν το ενεργειακό ισοζύγιο της Ελλάδας το 2023;`
- `Πόσο ήταν το μερίδιο των ΑΠΕ στην παραγωγή ρεύματος το 2022;`
- `Σύγκρινε το μείγμα καυσίμων του 2021 και του 2024.`

### Forest Fires (English)
- `How many hectares burned in Greece in 2023?`
- `Which year had the worst wildfires in Greece?`
- `Compare forest fires in Greece between 2021 and 2022.`

### Energy (English)
- `What was Greece's electricity balance in 2023?`
- `What share of Greece's electricity came from renewables in 2024?`
- `What is the role of natural gas in Greece's energy mix?`

## Εκτέλεση Tests

```bash
pytest tests/ -v
```

Όλα τα 22 tests πρέπει να περνάνε. Χρησιμοποιούν in-memory SQLite και mock OpenAI API.

## Screenshots

Screenshots στον φάκελο [`docs/screenshots/`](docs/screenshots/).

## Μελλοντικές Βελτιώσεις

- **Περισσότερα datasets**: Στατιστικά εγκληματικότητας, υγείας, οικονομικοί δείκτες από το data.gov.gr
- **Streaming απαντήσεις**: Ροή token-by-token για καλύτερη εμπειρία χρήστη
- **Ζωντανά δεδομένα ΑΠΕ και διασυνδέσεων**: Επέκταση του live fetch από ΑΔΜΗΕ πέρα από το ενεργειακό ισοζύγιο (ωριαία ΑΠΕ, διασυνδέσεις)
