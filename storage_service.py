"""
Storage service for managing in-memory data storage.

This module handles the management of hazard zones, route cache,
and other application state. In production, this should be replaced
with a proper database backend.
"""

from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from models import HazardZone, RouteStats


class StorageService:
    """Service class for data storage and cache management."""
    
    def __init__(self):
        self.hazard_zones: List[HazardZone] = []
        self.route_cache: Dict[str, Dict[str, Any]] = {}
    
    # Hazard Zone Management
    def get_all_hazards(self) -> List[HazardZone]:
        """Get all current hazard zones."""
        return self.hazard_zones
    
    def add_hazard(self, hazard: HazardZone) -> HazardZone:
        """Add a new hazard zone."""
        if not hazard.id:
            hazard.id = str(uuid.uuid4())
        hazard.created_at = datetime.now()
        
        # Remove existing hazard with same ID
        self.hazard_zones = [h for h in self.hazard_zones if h.id != hazard.id]
        self.hazard_zones.append(hazard)
        
        return hazard
    
    def delete_hazard(self, hazard_id: str) -> bool:
        """Delete a hazard zone by ID. Returns True if deleted, False if not found."""
        original_count = len(self.hazard_zones)
        self.hazard_zones = [h for h in self.hazard_zones if h.id != hazard_id]
        return len(self.hazard_zones) != original_count
    
    def initialize_default_hazards(self) -> None:
        """Initialize storage with default hazard zones."""
        default_hazards = [
            HazardZone(
                id="hazard-1",
                lat=18.787,
                lon=98.9905,
                level=5,
                name="Red Danger Zone",
                radius_m=150
            ),
            HazardZone(
                id="hazard-2", 
                lat=18.789594622931315,
                lon=98.9953468265745,
                level=5,
                name="Dark Red Zone",
                radius_m=120
            ),
            HazardZone(
                id="hazard-3",
                lat=18.7925,
                lon=99.0000,
                level=3,
                name="Orange Zone",
                radius_m=100
            )
        ]
        
        self.hazard_zones.extend(default_hazards)
    
    # Route Cache Management
    def cache_route(
        self, 
        route_id: str, 
        route_data: Dict[str, Any]
    ) -> None:
        """Cache route calculation results."""
        self.route_cache[route_id] = route_data
    
    def get_cached_route(self, route_id: str) -> Optional[Dict[str, Any]]:
        """Get cached route data by ID."""
        return self.route_cache.get(route_id)
    
    def get_route_map_html(self, route_id: str) -> Optional[str]:
        """Get cached route map HTML."""
        route_data = self.get_cached_route(route_id)
        return route_data["map_html"] if route_data else None
    
    def get_route_stats(self, route_id: str) -> Optional[RouteStats]:
        """Get cached route statistics."""
        route_data = self.get_cached_route(route_id)
        return route_data["stats"] if route_data else None
    
    # Statistics
    def get_storage_stats(self) -> Dict[str, int]:
        """Get storage statistics."""
        return {
            "hazard_zones": len(self.hazard_zones),
            "cached_routes": len(self.route_cache)
        }


# Global instance for the application
storage_service = StorageService()