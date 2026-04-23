"""FastAPI application entrypoint for AICES."""

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import models
from backend.database import Base, engine
from backend.routes.chat import router as chat_router
from backend.routes.history import router as history_router
from backend.routes.progress import router as progress_router
from backend.routes.quiz import router as quiz_router
from backend.routes.recommendations import router as recommendations_router
from backend.routes.user import router as user_router


def _get_allowed_origins() -> list[str]:
    """Read CORS origins from env, with safe local defaults for demos."""
    raw_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return origins or ["http://localhost:5173", "http://127.0.0.1:5173"]


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Create database tables when the application starts."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AICES Backend",
    version="4.0.0",
    description="Adaptive Intelligence-Based Concept Explanation System backend.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(quiz_router)
app.include_router(progress_router)
app.include_router(history_router)
app.include_router(user_router)
app.include_router(recommendations_router)


@app.get("/health")
def health_check():
    """Simple health endpoint for local checks."""
    return {
        "status": "ok",
        "service": "aices-backend",
        "version": app.version,
    }
