# app/main.py - updated to include new routes
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import (
    load_parser,
    load_management,
    driver_management,
    company_management,
)
from app.config import get_settings
import logging
import asyncio
from init_app import setup_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Logistics System API",
    description="API for managing loads, drivers, and logistics operations",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(load_parser.router)
app.include_router(load_management.router)
app.include_router(driver_management.router)  # Add driver management router
app.include_router(company_management.router)  # Add company management router


@app.on_event("startup")
async def startup_event():
    """Run when the application starts."""
    logger.info("Starting the application...")
    # Initialize the database
    await setup_database()
    logger.info("Application startup complete")


@app.get("/")
async def root():
    """
    Root endpoint returning API information.
    """
    return {
        "message": "Welcome to the Logistics System API",
        "version": "1.0.0",
        "docs_url": "/docs",
    }


@app.get("/health")
async def health():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
