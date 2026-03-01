"""
Cerebro Chaos - FastAPI Application
Main entry point for the backend server.
"""
import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend dir is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from api.routes import router
from models.database import Base, engine

# Create FastAPI app
app = FastAPI(
    title="Cerebro Chaos",
    description="🧠 AI-Powered Reliability Engineering Platform - Predict, Simulate, and Fix system failures before they hit production.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "Cerebro Chaos",
        "version": "1.0.0",
        "description": "AI-Powered Reliability Engineering Platform",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
