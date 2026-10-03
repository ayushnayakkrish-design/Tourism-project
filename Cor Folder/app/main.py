import logging
import secrets
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.core.passwords import hash_password
from app.dev3_models import User, UserPreference
from app.api.crowd import router as crowd_router
from app.api.places import router as places_router
from app.api.planner import router as planner_router
from app.api.routes import router as routes_router
from app.api.season import router as season_router

# Developer 2 — Gamification routers
from app.gamification.api_visits import router as visits_router
from app.gamification.api_wallet import router as wallet_router
from app.gamification.api_rewards import router as rewards_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router, admin_router as user_admin_router
from app.api.community import router as community_router
from app.api.moderation import router as moderation_router
from app.api.localization import router as localization_router, translation_router
from app.api.voice import router as voice_router

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("tourism")

if settings.AUTO_CREATE_DB:
    Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(_application):
    if len(settings.AUTH_SECRET) < 32 or settings.AUTH_SECRET.startswith("replace-with-"):
        raise RuntimeError("Set AUTH_SECRET to a unique random value of at least 32 characters before starting the API")
    if bool(settings.BOOTSTRAP_ADMIN_EMAIL) != bool(settings.BOOTSTRAP_ADMIN_PASSWORD):
        raise RuntimeError("Set both BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD, or leave both empty")
    if settings.BOOTSTRAP_ADMIN_EMAIL:
        if len(settings.BOOTSTRAP_ADMIN_PASSWORD) < 10:
            raise RuntimeError("BOOTSTRAP_ADMIN_PASSWORD must be at least 10 characters")
        with SessionLocal() as db:
            email = settings.BOOTSTRAP_ADMIN_EMAIL.strip().lower()
            if db.query(User).filter_by(email=email).first() is None:
                admin = User(id=secrets.token_urlsafe(18), email=email, password_hash=hash_password(settings.BOOTSTRAP_ADMIN_PASSWORD), display_name="Administrator", role="SUPER_ADMIN")
                db.add(admin)
                db.flush()
                db.add(UserPreference(user_id=admin.id))
                db.commit()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-oriented tourism intelligence backend with Google Maps routing, crowd intelligence, seasonal scoring, and optional AI explanations.",
    lifespan=lifespan,
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)


class FixedWindowRateLimitMiddleware:
    def __init__(self, app, limit: int):
        self.app = app
        self.limit = limit
        self.requests = defaultdict(deque)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or self.limit <= 0 or scope.get("path") in {"/health", "/health/live", "/health/ready", "/docs", "/openapi.json", "/redoc"}:
            await self.app(scope, receive, send)
            return
        client = scope.get("client")
        key = client[0] if client else "unknown"
        now = time.monotonic()
        queue = self.requests[key]
        while queue and now - queue[0] >= 60:
            queue.popleft()
        if len(queue) >= self.limit:
            response = JSONResponse(status_code=429, content={"error": {"code": "RATE_LIMITED", "message": "Too many requests"}})
            await response(scope, receive, send)
            return
        queue.append(now)
        await self.app(scope, receive, send)


app.add_middleware(FixedWindowRateLimitMiddleware, limit=settings.RATE_LIMIT_PER_MINUTE)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled error request_id=%s path=%s", request_id, request.url.path)
        response = JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error", "request_id": request_id}})
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{time.perf_counter() - started:.4f}"
    return response


app.include_router(places_router, prefix="/api/places", tags=["Places"])
app.include_router(routes_router, prefix="/api/routes", tags=["Routes"])
app.include_router(crowd_router, prefix="/api/crowd", tags=["Crowd"])
app.include_router(planner_router, prefix="/api/planner", tags=["Planner"])
app.include_router(season_router, prefix="/api/season", tags=["Season"])

# Developer 2 — Gamification, Visit Verification & Rewards
app.include_router(visits_router, prefix="/api/visits", tags=["Visits"])
app.include_router(wallet_router, prefix="/api", tags=["Wallet"])
app.include_router(rewards_router, prefix="/api", tags=["Rewards"])

# Developer 3 identity/community/localization/query routes. The only Developer 2
# integration change is the auth_stub adapter, which preserves its CurrentUser API.
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(user_admin_router, prefix="/api", tags=["User Administration"])
app.include_router(community_router, prefix="/api", tags=["Community"])
app.include_router(moderation_router, prefix="/api/moderation", tags=["Moderation"])
app.include_router(localization_router, prefix="/api/places", tags=["Localized Content"])
app.include_router(translation_router, prefix="/api", tags=["Translation"])
app.include_router(voice_router, prefix="/api", tags=["Voice and Intent"])


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/health/live", tags=["Health"])
def live():
    return {"status": "alive"}


@app.get("/health/ready", tags=["Health"])
def ready():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:
        logger.exception("Readiness check failed")
        return JSONResponse(status_code=503, content={"status": "not_ready", "reason": "Database unavailable"})
