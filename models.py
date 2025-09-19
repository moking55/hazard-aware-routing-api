"""
Pydantic models for the Hazard-Aware Routing API.

This module contains all data models used for request/response validation
and data serialization throughout the application.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Coordinate(BaseModel):
    """Geographic coordinate (latitude, longitude) model."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")


class HazardZone(BaseModel):
    """Hazard zone model representing dangerous areas to avoid."""
    id: Optional[str] = Field(None, description="Unique hazard ID")
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")
    level: int = Field(..., ge=1, le=10, description="Hazard level (1-10)")
    name: Optional[str] = Field("Hazard Zone", description="Hazard name")
    radius_m: float = Field(50, ge=1, le=1000, description="Radius in meters")
    created_at: Optional[datetime] = None


class RouteRequest(BaseModel):
    """Request model for route calculation."""
    start: Coordinate
    end: Coordinate
    location: str = Field("Chiang Mai, Thailand", description="Location/city name")
    network_type: str = Field("drive", pattern="^(drive|walk|bike)$")
    danger_threshold: int = Field(3, ge=1, le=10, description="Block hazards above this level")
    hazards: Optional[List[HazardZone]] = Field(None, description="Custom hazards for this request")


class RouteResponse(BaseModel):
    """Response model for route calculation results."""
    route_id: str
    status: str
    distance_km: Optional[float] = None
    duration_estimate_min: Optional[float] = None
    waypoints: Optional[List[Coordinate]] = None
    hazards_avoided: Optional[List[str]] = None
    map_url: Optional[str] = None
    error: Optional[str] = None


class RouteStats(BaseModel):
    """Detailed statistics for route calculation."""
    total_edges: int
    dangerous_edges_removed: int
    hazard_zones_processed: int
    computation_time_sec: float