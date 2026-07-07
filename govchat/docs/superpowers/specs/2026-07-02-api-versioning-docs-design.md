# API Versioning & Documentation Design

**Date:** 2026-07-02  
**Branch:** `feature/api-versioning-docs`

---

## Context

GovChat currently has no API versioning and minimal Swagger documentation (no response models, no tags, no endpoint descriptions). This work introduces URL path versioning (v1/v2) and proper documentation to address two work KRs. v2 also activates role-based auth (`get_current_admin`) that exists in `dependencies.py` but is currently unused.

---

## Versioning Structure

**Strategy:** URL path versioning — all routes prefixed with `/v1/` or `/v2/` in `main.py`.

**v1** — all existing endpoints, prefix added in `main.py`:
- `POST /v1/auth/register`
- `POST /v1/auth/login`
- `GET /v1/auth/me`
- `POST /v1/chat/sessions`, `GET /v1/chat/sessions`
- `POST /v1/chat/sessions/{id}/messages`, `GET /v1/chat/sessions/{id}/messages`
- `GET /v1/chat/sessions/{id}/export`
- `POST /v1/chat/sessions/import`
- `GET /v1/query`

**v2** — breaking change on auth + new admin endpoint, in new file `app/routers/auth_v2.py`:
- `GET /v2/auth/me` — returns `{id, username, is_admin}` (v1 returns only `{id, username}`)
- `GET /v2/admin/users` — admin-only, lists all users; uses existing `get_current_admin` from `app/dependencies.py`

---

## Documentation

**Response models** — new file `app/schemas.py`:
- `UserResponse` — `{id, username}`
- `UserDetailResponse` — `{id, username, is_admin}` (v2)
- `SessionResponse` — `{id, user_id, title, created_at}`
- `MessageResponse` — `{id, session_id, role, content, domain, created_at}`
- `TokenResponse` — `{access_token, token_type}`

**Per-router additions:**
- `tags=` on each `APIRouter()` call (`"auth"`, `"chat"`, `"query"`)
- `summary=` and `description=` on each endpoint decorator
- `response_model=` on each endpoint pointing to the appropriate schema

**App metadata** — update `main.py` FastAPI init:
```python
app = FastAPI(
    title="GovChat Greece API",
    description="AI-powered chatbot for Greek government open data.",
    version="1.0.0",
)
```

---

## Files Changed

| File | Change |
|---|---|
| `app/main.py` | Add `/v1` prefix to all router includes; add app metadata |
| `app/schemas.py` | New — all response Pydantic models |
| `app/routers/auth.py` | Add tags, summaries, response_model |
| `app/routers/chat.py` | Add tags, summaries, response_model |
| `app/routers/query.py` | Add tags, summaries, response_model |
| `app/routers/auth_v2.py` | New — v2 auth/me and admin/users endpoints |
| `streamlit_app.py` | Update all API URLs from `/auth/` to `/v1/auth/` etc. |
| `tests/test_api.py` | Update all route paths to `/v1/` prefix |

---

## Existing Code to Reuse

- `get_current_admin` in `app/dependencies.py` — wire directly to `GET /v2/admin/users`
- `User` model in `app/models.py` — source for `UserResponse` and `UserDetailResponse` fields

---

## Verification

1. Start the backend: `uvicorn app.main:app --reload`
2. Open `http://localhost:8000/docs` — confirm:
   - Endpoints grouped under Auth, Chat, Query tags
   - Each endpoint has a summary and response schema
   - v1 and v2 auth sections both visible
3. Login, get token, authorize in Swagger
4. Call `GET /v2/auth/me` — confirm `is_admin` field present
5. Call `GET /v2/admin/users` with non-admin token — expect 403
6. Run `pytest tests/ -v` — confirm all 7 tests pass with updated paths
7. Start Streamlit — confirm frontend still works end to end
