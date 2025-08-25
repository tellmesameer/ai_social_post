# backend\main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .api import app as api_router
from .storage import cleanup_tmp
from .logger_config import logger, log_call
from .models import create_db_and_tables

@asynccontextmanager

async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting AI Social Post Generator...")
    
    # Create database tables
    create_db_and_tables()
    logger.info("Database initialized")
    
    # Clean up old temporary files
    cleanup_tmp(max_age_hours=24)
    logger.info("Temporary file cleanup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Social Post Generator...")

# Create main FastAPI app
app = FastAPI(
    title="AI Social Post Generator",
    description="Generate LinkedIn-ready social posts from URLs using AI",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(api_router, prefix="/api/v1")

# Root endpoint
@app.get("/")

async def root():
    """Root endpoint."""
    return {
        "message": "AI Social Post Generator",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
