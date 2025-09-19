"""
Health check API routes.

Provides endpoints for monitoring API health and status.
"""

from fastapi import APIRouter
from datetime import datetime

from routing_service import routing_service
from storage_service import storage_service

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    routing_stats = routing_service.get_cache_stats()
    storage_stats = storage_service.get_storage_stats()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        **routing_stats,
        **storage_stats
    }