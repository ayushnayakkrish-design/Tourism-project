import logging
import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.database import Base, engine
from app.api.crowd import router as crowd_router
from app.api.places import router as places_router
from app.api.planner import router as planner_router
from app.api.routes import router as routes_router
from app.api.season import router as season_router

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("tourism")

if settings.AUTO_CREATE_DB:
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-oriented tourism intelligence backend with Google Maps routing, crowd intelligence, seasonal scoring, and optional AI explanations.",
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
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
