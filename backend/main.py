import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from database import engine, Base
import models  # noqa: F401 — registers models with Base
from routers import auth, audit, reports, competitor, gsc, tools
from limiter import limiter
from logger import get_logger

log = get_logger("seo_agent.main")

# ── Validate that required secrets are set ────────────────────────────────────

_SECRET_KEY = os.getenv("SECRET_KEY", "")
if not _SECRET_KEY or _SECRET_KEY == "change-this-to-a-strong-random-secret-key":
    log.warning(
        "SECRET_KEY is not set or is still the default value. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

if not os.getenv("ANTHROPIC_API_KEY", "").startswith("sk-ant"):
    log.warning(
        "ANTHROPIC_API_KEY is not set or invalid. "
        "AI recommendations will be disabled. Get a key at https://console.anthropic.com/"
    )

# ── Database + filesystem setup ───────────────────────────────────────────────

Base.metadata.create_all(bind=engine)
os.makedirs(os.path.join(os.path.dirname(__file__), "reports"), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "reports", "gsc"), exist_ok=True)

# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="SEO AI Agent API",
    description="Full-stack SEO audit agent — crawl, analyze, AI recommendations, Word reports",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Rate limiter ──────────────────────────────────────────────────────────────

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3003",
    "https://eric-moon.onrender.com",
    "https://eric-moon-api.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Security headers middleware ───────────────────────────────────────────────

@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    # Only send HSTS in production (when behind HTTPS)
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response

# ── Request logging middleware ────────────────────────────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next) -> Response:
    response = await call_next(request)
    # Skip logging health checks to reduce noise
    if request.url.path not in ("/health", "/"):
        log.info(
            "%s %s %s",
            request.method,
            request.url.path,
            response.status_code,
        )
    return response

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(audit.router)
app.include_router(reports.router)
app.include_router(competitor.router)
app.include_router(gsc.router)
app.include_router(tools.router)

# ── Root endpoints ────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "SEO AI Agent API is running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


# ── Startup log ───────────────────────────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    log.info("SEO AI Agent API started — docs at /docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
