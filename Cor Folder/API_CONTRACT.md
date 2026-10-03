# API Contract — Developer 3 Identity and Community

Base URL: `http://127.0.0.1:8000`. OpenAPI/Swagger is served at `/docs`.

Ownership labels: **DEV 1** owns tourism place/map/route/crowd/planner/season APIs; **DEV 2** owns visits, wallets, points, and rewards; **DEV 3** owns the routes in this document; **SHARED** identifies integration seams.

## Authentication

All protected routes use `Authorization: Bearer <access_token>`. Public registration creates a `TOURIST`; roles and user IDs are never accepted from request bodies or identity headers.

| Method | Path | Access |
|---|---|---|
| POST | `/api/auth/register` | Public |
| POST | `/api/auth/login` | Public |
| GET | `/api/auth/me` | Signed in |
| GET, PATCH | `/api/users/me` | Signed in |
| GET, PATCH | `/api/users/me/preferences` | Signed in |
| PATCH | `/api/admin/users/{user_id}/role` | `SUPER_ADMIN` |

Password is stored as a salted scrypt hash. Access tokens are signed HS256 JWTs; the server reloads the account and role from the database on each request. Set `AUTH_SECRET` to a unique random value of at least 32 characters. Optional bootstrap admin credentials are read from `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` at startup.

## Community and moderation

| Method | Path | Access |
|---|---|---|
| POST | `/api/community/places` | Signed in |
| GET | `/api/community/places/mine` | Signed in; own items |
| GET | `/api/community/places` | Public; approved only |
| GET | `/api/community/places/{submission_id}` | Public; approved only |
| POST | `/api/community/reviews` | Signed in |
| GET | `/api/places/{place_id}/reviews` | Public; approved only |
| GET | `/api/moderation/queue` | Moderator, government admin, super admin |
| GET | `/api/moderation/submissions?status=PENDING` | Moderator, government admin, super admin |
| GET | `/api/moderation/history?target_type=submission&target_id={id}` | Moderator, government admin, super admin |
| GET | `/api/moderation/submissions/{id}` | Moderator, government admin, super admin |
| POST | `/api/moderation/submissions/{id}/approve` | Moderator, government admin, super admin |
| POST | `/api/moderation/submissions/{id}/reject` | Moderator, government admin, super admin |
| POST | `/api/moderation/reviews/{id}/approve` | Moderator, government admin, super admin |
| POST | `/api/moderation/reviews/{id}/reject` | Moderator, government admin, super admin |

New community submissions and reviews start `PENDING`. Only approved content appears in public lists. Each moderation decision records moderator ID, target, action, note, and timestamp. One review per user and canonical `place_id` is enforced by a database constraint. `place_id` remains an opaque Developer 1 identifier; Developer 3 does not create a second places table.

## Multilingual content and translation

Initial language codes are `en`, `hi`, and `or`; extend the supported language set in `app/dev3_schemas.py` when the product adds another language.

| Method | Path | Access |
|---|---|---|
| GET | `/api/places/{place_id}/content/{language}` | Public |
| PUT | `/api/places/{place_id}/content/{language}` | Moderator/admin; only government admin or super admin may label content `official` |
| POST | `/api/translate` | Signed in |

The translation provider receives `{ "text", "source_language", "target_language" }` as JSON and must return `{ "translation": "..." }`. Cache keys are deterministic hashes of source language, target language, and input text. If no provider is configured, a cache miss returns `503 TRANSLATION_NOT_CONFIGURED`.

## Voice and intent

| Method | Path | Access |
|---|---|---|
| POST | `/api/ai/intent` | Signed in |
| POST | `/api/voice/query` | Signed in; voice preference must be enabled |
| POST | `/api/voice/transcribe` | Signed in; voice preference must be enabled |
| POST | `/api/voice/search` | Signed in; voice preference must be enabled |
| GET | `/api/maps/query?place_name=...&region=...` | Public |

Intent responses contain `intent` and validated `parameters` (`category`, `location`, `open_now`, and original `query`). When `OPENAI_API_KEY` is configured, extraction uses strict structured output; otherwise or on provider/schema failure, it falls back to deterministic local parsing. Intent extraction supplies search parameters only; it is not a source of tourism facts.

Speech-to-text accepts base64 audio and `content_type` in JSON. The configured provider receives `{ "audio_base64", "content_type", "language" }` with bearer authentication and returns `{ "transcript": "..." }`. Configure `SPEECH_TO_TEXT_API_URL` and `SPEECH_TO_TEXT_API_KEY`. Audio is limited to 7 MB after decoding.

`/api/voice/search` converts a place-search intent into a query for **DEV 1** `PlacesService.search_text` and normalizes its result. The current Developer 1 search contract does not apply an `open_now` filter; that field is returned in intent and the response documents this limitation. Developer 1 owns any change to Places search filtering.

## Developer 1 and Developer 2 integration

- **DEV 1:** `place_id` is the opaque identifier returned by `/api/places/search` and related routes. Voice search delegates to the existing `PlacesService`; it does not reproduce the maps or tourism search logic.
- **DEV 2:** the existing `/api/visits`, `/api/wallet`, `/api/points/transactions`, `/api/rewards`, and `/api/redemptions` APIs remain in Developer 2 modules. `app/gamification/auth_stub.py` now adapts Developer 3's authenticated identity to Developer 2's existing `CurrentUser(user_id, role)` interface. Only `SUPER_ADMIN` maps to Developer 2's `admin`; client-supplied `X-User-ID` and `X-User-Role` are ignored.
- **Shared IDs:** the user primary key is the stable `user_id` consumed by Developer 2; the canonical place ID is stored as an opaque string in Developer 3 reviews/content.

No Developer 2 points, wallet, reward, visit-verification, or gamification business logic is implemented by Developer 3.

## Errors and persistence

Validation uses HTTP 422; missing/invalid bearer tokens use 401; role violations use 403; absent resources use 404; duplicate accounts/reviews or repeat moderation use 409; rate limiting uses 429; unconfigured or failed providers use 503/502. Error responses include a stable `detail.code` where the route defines one. FastAPI validation errors keep its standard response shape.

Developer 3 tables are introduced by Alembic revision `0003_developer3`. Run `alembic upgrade head` before serving a migrated database. Local demo mode may use `AUTO_CREATE_DB=true`.
