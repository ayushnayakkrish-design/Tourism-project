# Tourism Intelligence Backend — Production-Ready MVP

A FastAPI backend for intelligent tourism planning using Google Places API (New), Google Routes API, crowd observations, seasonal scoring, and an optional OpenAI Responses API explanation layer.

## What was fixed

- Real Google route durations are used by the itinerary engine instead of hard-coded travel time.
- Planner builds an all-pairs route matrix so start → stop → stop → start legs are available.
- Opening-hours windows are respected; closed or infeasible places are reported as skipped.
- Multi-day planning resets from the start location each day.
- Duplicate destinations and invalid coordinates/times are rejected.
- Nearby/search responses use one normalized response shape.
- Google/AI upstream errors are sanitized and retried for transient failures.
- Route Matrix NDJSON responses are parsed into JSON objects.
- AI uses the current Responses API pattern with a strict JSON schema and safely parses raw REST output.
- AI is explanation-only and receives structured backend facts; it is not the source of tourism facts.
- Season recommendation now reports the requested month separately from the best available profile.
- Season profile writes are idempotent for `(place_id, month)`.
- Added database indexes and Alembic migrations.
- Added request IDs, structured error responses, health/readiness endpoints, CORS/host controls, and basic rate limiting.
- Added tests for planner routing, opening hours, validation, route-matrix parsing, AI parsing, crowd prediction, and seasonal scoring.

Google requires field masks for Places and Routes requests; the project intentionally requests only the fields it uses to reduce unnecessary data and billing exposure. See the official Google Maps Platform documentation.

## 1. Prerequisites

- Python 3.11+
- A Google Cloud project with billing configured
- Places API (New) enabled
- Routes API enabled
- A restricted Google Maps Platform API key
- Optional: an OpenAI API key and a model enabled for your API project

## 2. Setup on Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Edit `.env` and set your real Google API key. Keep `.env` private and never commit it.

## 3. Database migration

Production/staging uses Alembic rather than `create_all`:

```powershell
alembic upgrade head
```

For a disposable local demo only, you can set `AUTO_CREATE_DB=true`.

## 4. Run

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Development auto-reload:

```powershell
python -m uvicorn app.main:app --reload
```

Open:
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/health/ready`

## 5. Main APIs

### Places

```text
GET  /api/places/search?q=Konark
GET  /api/places/geocode?address=Puri%20Odisha
GET  /api/places/{place_id}
POST /api/places/nearby
```

### Routes

```text
POST /api/routes/route
POST /api/routes/matrix
```

### Crowd

```text
POST /api/crowd/observations
GET  /api/crowd/{place_id}
GET  /api/crowd/{place_id}/best-time
```

### Planner

```text
POST /api/planner/generate
POST /api/planner/explain
```

Planner input supports:
- start coordinates
- destination place IDs
- available hours
- number of days
- start time/date
- default visit duration
- return-to-start option
- preferences

The planner uses Google route-matrix durations for travel and opening-hour periods when those fields are available from Place Details.

### Seasonal intelligence

```text
POST /api/season/profiles
POST /api/season/recommend
```

The season engine uses a transparent weighted score:

- Weather: 35%
- Crowd: 30%
- Festival: 15%
- Accessibility: 20%

These are application-defined weights, not Google/OpenAI facts.

## 6. AI safety architecture

The backend first gathers structured facts from Google/DB/rules. The optional AI layer only explains those facts.

The OpenAI Responses API is used with strict structured output. The model is configured through `OPENAI_MODEL`; do not hard-code a model name that your API project cannot access. The current OpenAI documentation shows Responses API usage and structured output support; model availability can differ by account/project.

## 7. Testing

Run:

```powershell
python -m compileall -q app tests
pytest -q
```

Tests do not call live Google/OpenAI services.

## 8. Production deployment checklist

1. Use PostgreSQL (set `DATABASE_URL`) for multi-instance production.
2. Run `alembic upgrade head` during deployment.
3. Set `ENVIRONMENT=production`.
4. Set `CORS_ORIGINS` to the exact frontend origins.
5. Set `ALLOWED_HOSTS` to the API domain(s).
6. Restrict the Google API key by API and application/IP where appropriate.
7. Keep API keys in a secret manager/environment variables.
8. Put the API behind HTTPS and a reverse proxy/API gateway.
9. Use an external distributed rate limiter for multiple workers/instances; the built-in limiter is a lightweight single-process safeguard.
10. Add centralized logs/metrics/tracing in the hosting platform.
11. Back up PostgreSQL and test restore procedures.
12. Monitor Google/OpenAI usage and billing.

## 9. Architecture

```text
Frontend
   |
   v
FastAPI API
   |
   +--> Google Places API (structured place facts)
   +--> Google Routes API (travel times/distances)
   +--> SQL database (crowd + seasonal data)
   |
   +--> Deterministic planner / scoring engine
   |
   +--> Optional OpenAI explanation layer
```

The deterministic planner remains the source of truth for route feasibility, travel time, opening hours, and crowd/season scores.

## 10. Docker / PostgreSQL

For a production-like local stack:

```powershell
$env:GOOGLE_MAPS_API_KEY="your-key"
docker compose up --build
```

The compose stack uses PostgreSQL and runs Alembic migrations before starting two Uvicorn workers. Change the example database password before deploying anywhere shared.
