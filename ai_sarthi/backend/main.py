"""
AI Sarthi — FastAPI Main Application
"""
import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# --- App Startup/Shutdown ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    logger.info("=== AI Sarthi Backend Starting ===")

    # Initialize database
    try:
        from database.models import create_tables, get_session
        from etl.ingest import run_ingestion
        create_tables()
        logger.info("Database tables created")

        # Check if data already ingested
        with get_session() as sess:
            from database.models import District
            count = sess.query(District).count()
            if count < 36:
                logger.info("Running data ingestion...")
                run_ingestion()
            else:
                logger.info(f"Database already has {count} districts")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

    # Initialize RAG (lazy load)
    try:
        from rag.retrieval import get_rag_system
        rag = get_rag_system()
        logger.info(f"RAG system initialized: {rag.get_status()}")
    except Exception as e:
        logger.warning(f"RAG initialization warning: {e}")

    # Initialize SLM (lazy, GPU-dependent)
    try:
        from slm.inference import get_slm
        slm = get_slm()
        logger.info(f"SLM status: {slm.get_status()}")
    except Exception as e:
        logger.warning(f"SLM initialization warning: {e}")

    logger.info("=== AI Sarthi Backend Ready ===")
    yield
    logger.info("=== AI Sarthi Backend Shutting Down ===")


app = FastAPI(
    title="AI Sarthi API",
    description="SLM-Based Healthcare Budget Analysis for Maharashtra",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        os.environ.get("FRONTEND_URL", ""),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Import routers ----
from routers import districts, budgets, chat, analytics, allocations, reports, system

app.include_router(districts.router, prefix="/api/districts", tags=["Districts"])
app.include_router(budgets.router, prefix="/api/budgets", tags=["Budgets"])
app.include_router(chat.router, prefix="/api/chat", tags=["AI Chat"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(allocations.router, prefix="/api/allocations", tags=["Allocations"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(system.router, prefix="/api/system", tags=["System"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "AI Sarthi",
        "version": "1.0.0",
        "description": "SLM-Based Healthcare Budget Analysis for Maharashtra",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health", tags=["Root"])
async def health():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )
