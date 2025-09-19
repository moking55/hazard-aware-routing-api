"""
FastAPI REST API for Hazard-Aware Routing

Endpoints:
- POST /route - Calculate safe route avoiding hazards
- GET /hazards - Get current hazard zones
- POST /hazards - Add/update hazard zones
- GET /health - Health check
- GET /map/{route_id} - Get interactive map HTML

Usage:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import logging

from config import Config, setup_logging, API_DOCS_HTML
from storage_service import storage_service
from routes import health, hazards, routing

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=Config.TITLE,
    description=Config.DESCRIPTION,
    version=Config.VERSION
)

# Include routers
app.include_router(health.router)
app.include_router(hazards.router)
app.include_router(routing.router)


@app.get("/", response_class=HTMLResponse)
async def root():
    """API documentation and test interface."""
    return HTMLResponse(content=API_DOCS_HTML)


@app.on_event("startup")
async def startup_event():
    """Initialize API with default hazard zones."""
    storage_service.initialize_default_hazards()
    hazard_count = len(storage_service.get_all_hazards())
    logger.info(f"Initialized with {hazard_count} default hazard zones")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host=Config.HOST, 
        port=Config.PORT, 
        reload=Config.RELOAD
    )