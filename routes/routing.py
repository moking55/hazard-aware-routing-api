"""
Route calculation API routes.

Provides endpoints for route calculation, map generation, and route statistics.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from datetime import datetime
import uuid
import logging

from models import RouteRequest, RouteResponse, RouteStats, Coordinate
from routing_service import routing_service
from map_service import map_service
from storage_service import storage_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/route", response_model=RouteResponse)
async def calculate_route(request: RouteRequest):
    """Calculate a safe route between two points."""
    route_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    try:
        # Load graph
        graph = routing_service.load_osm_graph(request.location, request.network_type)
        
        # Use request hazards or global hazards
        hazards = request.hazards if request.hazards else storage_service.get_all_hazards()
        
        if not hazards:
            logger.warning("No hazards defined, calculating normal route")
        
        # Find dangerous edges
        dangerous_edges, edge_hazard_levels, stats = routing_service.identify_dangerous_edges(
            graph, hazards, request.danger_threshold
        )
        
        # Create safe graph
        safe_graph, removed_count = routing_service.create_safe_graph(graph, dangerous_edges)
        
        # Calculate route
        route, total_distance = routing_service.calculate_safe_route(
            safe_graph, request.start, request.end
        )
        
        # Create waypoints
        waypoints = [
            Coordinate(lat=graph.nodes[node]['y'], lon=graph.nodes[node]['x']) 
            for node in route
        ]
        
        # Estimate duration (assuming 50 km/h average for drive, 5 km/h for walk, 15 km/h for bike)
        speed_kmh = {"drive": 50, "walk": 5, "bike": 15}[request.network_type]
        duration_min = (total_distance / 1000) / speed_kmh * 60
        
        # Create map
        map_html = map_service.create_route_map(graph, route, request.start, request.end, hazards)
        
        # Cache results
        route_data = {
            "route": route,
            "waypoints": waypoints,
            "map_html": map_html,
            "hazards": hazards,
            "stats": RouteStats(
                total_edges=graph.number_of_edges(),
                dangerous_edges_removed=removed_count,
                hazard_zones_processed=len([h for h in hazards if h.level > request.danger_threshold]),
                computation_time_sec=(datetime.now() - start_time).total_seconds()
            )
        }
        storage_service.cache_route(route_id, route_data)
        
        hazards_avoided = [h.name for h in hazards if h.level > request.danger_threshold]
        
        response = RouteResponse(
            route_id=route_id,
            status="success",
            distance_km=round(total_distance / 1000, 2),
            duration_estimate_min=round(duration_min, 1),
            waypoints=waypoints,
            hazards_avoided=hazards_avoided,
            map_url=f"/map/{route_id}"
        )
        
        logger.info(f"Route calculated: {response.distance_km}km, avoided {len(hazards_avoided)} hazards")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Route calculation failed: {e}")
        return RouteResponse(
            route_id=route_id,
            status="error",
            error=str(e)
        )


@router.get("/map/{route_id}", response_class=HTMLResponse)
async def get_route_map(route_id: str):
    """Get interactive HTML map for a calculated route."""
    map_html = storage_service.get_route_map_html(route_id)
    if not map_html:
        raise HTTPException(status_code=404, detail="Route not found")
    
    return HTMLResponse(content=map_html)


@router.get("/route/{route_id}/stats", response_model=RouteStats)
async def get_route_stats(route_id: str):
    """Get detailed statistics for a calculated route."""
    stats = storage_service.get_route_stats(route_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Route not found")
    
    return stats