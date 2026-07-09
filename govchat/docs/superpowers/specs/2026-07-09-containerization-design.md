# Containerization Design

**Date:** 2026-07-09
**Branch:** `feature/containerization`

---

## Context

GovChat runs as two separate processes (FastAPI + Streamlit) started manually. This work packages both into Docker containers so the entire app starts with a single `docker compose up` command. Learning goal: understand Dockerfiles, docker-compose, Docker networking, volumes, and environment variable management.

---

## Approach

Single `Dockerfile` shared by both services. `docker-compose.yml` defines two services (`api`, `frontend`) that build from the same image but use different startup commands.

---

## `.dockerignore` (`govchat/.dockerignore`)

Required to prevent `.venv/`, `__pycache__`, `.db` files, and `data/chroma_db/` from being copied into the image:

```
.venv/
__pycache__/
*.pyc
*.db
data/chroma_db/
.env
.git/
```

---

## Dockerfile (`govchat/Dockerfile`)

```
FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
```

Uses `python:3.12` (not `slim`) to avoid missing system libraries required by ChromaDB's ONNX runtime dependencies. No `CMD` — each service in docker-compose provides its own command.

---

## docker-compose.yml (`govchat/docker-compose.yml`)

```yaml
services:
  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - sqlite_data:/app/govchat.db
      - ./data/chroma_db:/app/data/chroma_db

  frontend:
    build: .
    command: streamlit run streamlit_app.py --server.port 8501
    ports:
      - "8501:8501"
    env_file: .env
    depends_on:
      - api
    environment:
      - API_URL=http://api:8000
```

---

## Streamlit URL Fix (`streamlit_app.py`)

Change line 4 from:
```python
API_URL = "http://localhost:8000"
```
To:
```python
import os
API_URL = os.getenv("API_URL", "http://localhost:8000")
```

Fallback to `localhost` preserves local non-Docker usage.

---

## ChromaDB Seeding

Volumes persist data across restarts — seeding is a one-time manual step after first startup:

```bash
docker compose exec api python scripts/seed_rag.py
docker compose exec api python scripts/seed_road_safety.py
docker compose exec api python scripts/seed_fire_data.py
```

---

A named volume `sqlite_data` is used for SQLite instead of a bind mount — if `govchat.db` doesn't exist as a file on the host, Docker would create a directory at that path, breaking SQLite. Named volumes are managed by Docker and are always file-safe.

---

## Files Changed

| File | Change |
|---|---|
| `.dockerignore` | New — excludes `.venv/`, `__pycache__`, `.db`, `data/chroma_db/`, `.env`, `.git/` |
| `Dockerfile` | New — `python:3.12` base, installs deps, copies code |
| `docker-compose.yml` | New — two services, named volume for SQLite, bind mount for ChromaDB |
| `streamlit_app.py` | Line 4 — read `API_URL` from env with `localhost` fallback |

---

## Verification

1. `docker compose up --build` — confirm both containers start
2. Open `http://localhost:8000/docs` — confirm FastAPI is reachable
3. Open `http://localhost:8501` — confirm Streamlit loads
4. Run seed scripts via `docker compose exec`
5. Send a message in Streamlit — confirm end-to-end flow works through Docker network
