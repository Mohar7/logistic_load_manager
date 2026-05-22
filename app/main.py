# app/main.py - updated to include new routes
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    bot_management,
    company_management,
    dispatcher_management,
    driver_management,
    load_management,
    load_parser,
    telegram_integration,
)
from app.config import get_settings
from init_app import setup_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Async startup/shutdown hooks. Runs once before the app accepts requests
    and once after it stops accepting them."""
    logger.info("Starting the application...")
    await setup_database()
    logger.info("Application startup complete")
    yield
    logger.info("Application shutdown")


# Create FastAPI app
app = FastAPI(
    title="Logistics System API",
    description="API for managing loads, drivers, and logistics operations",
    version="1.0.0",
    lifespan=lifespan,
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
app.include_router(driver_management.router)
app.include_router(company_management.router)
app.include_router(dispatcher_management.router)
app.include_router(bot_management.router)
app.include_router(telegram_integration.router)


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
