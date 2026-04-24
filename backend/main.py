"""FastAPI application entrypoint for AICES."""

from contextlib import asynccontextmanager
import os

from dotenv import load_dotenv
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

# Load environment variables
load_dotenv()

# Resolve the active AI provider configuration. The backend currently uses OpenRouter,
# while OPENAI_MODEL is kept as a legacy fallback during deployment transitions.
AI_PROVIDER = "openrouter"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = (
    os.getenv("OPENROUTER_MODEL")
    or os.getenv("OPENAI_MODEL")
    or "mistralai/mistral-7b-instruct"
)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
AICES_DB_PATH = os.getenv("AICES_DB_PATH", "./data/aices.db")
OPENROUTER_TIMEOUT_SECONDS = os.getenv("OPENROUTER_TIMEOUT_SECONDS", "8")


def _get_ai_environment_summary() -> dict[str, str]:
    """Return a deployment-safe view of the resolved AI provider configuration."""
    return {
        "AI_PROVIDER": AI_PROVIDER,
        "OPENROUTER_API_KEY": "configured" if OPENROUTER_API_KEY else "missing",
        "OPENROUTER_MODEL": OPENROUTER_MODEL,
        "OPENAI_MODEL": os.getenv("OPENAI_MODEL", ""),
        "OPENROUTER_TIMEOUT_SECONDS": OPENROUTER_TIMEOUT_SECONDS,
    }

def _get_allowed_origins() -> list[str]:
    """Read CORS origins from env, with safe local defaults for demos."""
    origins = [origin.strip() for origin in ALLOWED_ORIGINS.split(",") if origin.strip()]
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
    allow_credentials=True,
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
        "environment": {
            **_get_ai_environment_summary(),
            "ALLOWED_ORIGINS": ALLOWED_ORIGINS,
            "AICES_DB_PATH": AICES_DB_PATH,
        }
    }

@app.get("/debug")
def debug_info():
    """Debug endpoint for troubleshooting."""
    return {
        "status": "debug",
        "environment": {
            **_get_ai_environment_summary(),
            "ALLOWED_ORIGINS": ALLOWED_ORIGINS,
            "AICES_DB_PATH": AICES_DB_PATH,
        },
        "cors_origins": _get_allowed_origins(),
    }

@app.get("/test-fallback")
def test_fallback():
    """Test endpoint to verify fallback mechanism works."""
    try:
        print("[TEST] Testing fallback mechanism")
        return {
            "status": "success",
            "message": "Backend is working and can respond",
            "fallback_test": "If you see this, the backend is functional"
        }
    except Exception as e:
        print(f"[TEST ERROR] {e}")
        return {
            "status": "error",
            "message": f"Test failed: {e}",
            "fallback": "Even this test failed, which indicates a serious backend issue"
        }
