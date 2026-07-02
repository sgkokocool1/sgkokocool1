from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.routers import distribution, episodes, jobs, overview, sync

settings = get_settings()

app = FastAPI(title="Robot Data Dashboard API", version="0.1.0")

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prefix = settings.api_prefix
app.include_router(overview.router, prefix=prefix)
app.include_router(distribution.router, prefix=prefix)
app.include_router(jobs.router, prefix=prefix)
app.include_router(episodes.router, prefix=prefix)
app.include_router(sync.router, prefix=prefix)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
