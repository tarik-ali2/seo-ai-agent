from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import models  # noqa: F401 — registers models with Base
from routers import auth, audit, reports, competitor
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

Base.metadata.create_all(bind=engine)
os.makedirs(os.path.join(os.path.dirname(__file__), "reports"), exist_ok=True)

app = FastAPI(
    title="SEO AI Agent API",
    description="Free MVP SEO audit agent — crawl, analyze, generate Word reports",
    version="1.0.0",
)

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

app.include_router(auth.router)
app.include_router(audit.router)
app.include_router(reports.router)
app.include_router(competitor.router)


@app.get("/")
def root():
    return {"message": "SEO AI Agent API is running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
