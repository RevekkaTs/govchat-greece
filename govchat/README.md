# GovChat Greece

A conversational AI chatbot for Greek open government data, built as a final project for the AI for Developers course at AUEB.

## What it does

Ask questions in natural language about:
- **Road Safety**: Traffic accident statistics from data.gov.gr
- **Forest Fires**: Wildfire data from data.gov.gr
- **Energy**: Greek electricity production and consumption (ADMIE data via RAG)

## Architecture

```
User → FastAPI (auth + chat endpoints)
           ↓
      AI Agent (OpenAI function calling, gpt-4o-mini)
      ├── road_safety_tool → data.gov.gr API (live)
      ├── fires_tool       → data.gov.gr API (live)
      └── energy_tool      → ChromaDB RAG (pre-loaded ADMIE data)
           ↓
      SQLite (users, chat sessions, messages)
```

## Course Topics Demonstrated

| Topic | Where |
|-------|-------|
| FastAPI | All API endpoints, SQLModel, auth |
| Prompt Engineering | System prompt in agent.py, tool descriptions |
| RAG | ChromaDB + text-embedding-3-small for energy domain |
| AI Agents | Tool-calling loop in agent.py |

## Setup

### Prerequisites
- Python 3.11+
- OpenAI API key

### Installation

```bash
git clone <repo-url>
cd govchat
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

Edit `.env`:
```
OPENAI_API_KEY=sk-...
SECRET_KEY=your-random-secret-key
```

### Seed the RAG database

Run once before first use:
```bash
python scripts/seed_rag.py
```

### Run the server

```bash
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive API documentation.

## Usage

### 1. Register and login

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypass"}'

# Login (get token)
curl -X POST http://localhost:8000/auth/login \
  -d "username=myuser&password=mypass"
```

### 2. Start a chat session

```bash
curl -X POST http://localhost:8000/chat/sessions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "My first chat"}'
```

### 3. Ask questions

```bash
curl -X POST http://localhost:8000/chat/sessions/1/messages \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"content": "How many road accidents happened in 2023?"}'
```

### 4. Quick demo (no auth needed)

```bash
curl "http://localhost:8000/query?q=What+is+ADMIE?"
```

## Running Tests

```bash
pytest tests/ -v
```

All 7 tests should pass. Tests use an in-memory SQLite database and mock the OpenAI API.

## Screenshots

*(Add screenshots of Swagger UI and sample conversations here)*

## Future Improvements

- **More datasets**: Add crime statistics, health data, economic indicators from data.gov.gr
- **Conversation memory**: Include previous messages in agent context for follow-up questions
- **Streaming responses**: Stream AI responses token-by-token for better UX
- **Admin dashboard**: View all users and conversations via admin endpoints
- **Better RAG**: Load real ADMIE data from their published reports via PDF parsing
- **Caching**: Cache frequent API calls to data.gov.gr to reduce latency
- **Rate limiting**: Protect endpoints from abuse
- **Docker**: Add Dockerfile for easy deployment
