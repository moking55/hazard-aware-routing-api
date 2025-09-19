"""
Hazard zone management API routes.

Provides endpoints for CRUD operations on hazard zones.
"""

from fastapi import APIRouter, HTTPException
from typing import List
import logging

from models import HazardZone
from storage_service import storage_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/hazards", response_model=List[HazardZone])
async def get_hazards():
    """Get all current hazard zones."""
    return storage_service.get_all_hazards()


@router.post("/hazards", response_model=HazardZone)
async def add_hazard(hazard: HazardZone):
    """Add a new hazard zone."""
    result = storage_service.add_hazard(hazard)
    logger.info(f"Added hazard zone: {result.name} (Level {result.level})")
    return result


@router.delete("/hazards/{hazard_id}")
async def delete_hazard(hazard_id: str):
    """Delete a hazard zone."""
    if not storage_service.delete_hazard(hazard_id):
        raise HTTPException(status_code=404, detail="Hazard zone not found")
    
    return {"message": f"Hazard zone {hazard_id} deleted"}