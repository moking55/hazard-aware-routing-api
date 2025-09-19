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

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import osmnx as ox
import networkx as nx
import numpy as np
from geopy.distance import geodesic
import folium
import uuid
import json
import asyncio
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hazard-Aware Routing API",
    description="REST API for calculating safe routes that avoid hazardous areas",
    version="1.0.0"
)

# Global storage (in production, use a database)
graph_cache = {}
hazard_zones = []
route_cache = {}

# Pydantic Models
class Coordinate(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")

class HazardZone(BaseModel):
    id: Optional[str] = Field(None, description="Unique hazard ID")
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")
    level: int = Field(..., ge=1, le=10, description="Hazard level (1-10)")
    name: Optional[str] = Field("Hazard Zone", description="Hazard name")
    radius_m: float = Field(50, ge=1, le=1000, description="Radius in meters")
    created_at: Optional[datetime] = None

class RouteRequest(BaseModel):
    start: Coordinate
    end: Coordinate
    location: str = Field("Chiang Mai, Thailand", description="Location/city name")
    network_type: str = Field("drive", pattern="^(drive|walk|bike)$")
    danger_threshold: int = Field(3, ge=1, le=10, description="Block hazards above this level")
    hazards: Optional[List[HazardZone]] = Field(None, description="Custom hazards for this request")

class RouteResponse(BaseModel):
    route_id: str
    status: str
    distance_km: Optional[float] = None
    duration_estimate_min: Optional[float] = None
    waypoints: Optional[List[Coordinate]] = None
    hazards_avoided: Optional[List[str]] = None
    map_url: Optional[str] = None
    error: Optional[str] = None

class RouteStats(BaseModel):
    total_edges: int
    dangerous_edges_removed: int
    hazard_zones_processed: int
    computation_time_sec: float

# Core Routing Functions
def load_osm_graph(location: str, network_type: str = "drive"):
    """Load and cache OSM graph data."""
    cache_key = f"{location}_{network_type}"
    
    if cache_key in graph_cache:
        logger.info(f"Using cached graph for {cache_key}")
        return graph_cache[cache_key]
    
    logger.info(f"Loading OSM data for {location} ({network_type})")
    try:
        graph = ox.graph_from_place(location, network_type=network_type)
        graph_cache[cache_key] = graph
        return graph
    except Exception as e:
        logger.error(f"Failed to load OSM data: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to load map data for {location}")

def identify_dangerous_edges(graph, hazards: List[HazardZone], danger_threshold: int):
    """Identify edges that fall within dangerous hazard zones."""
    if not graph.is_directed():
        graph = graph.to_directed()
    
    dangerous_edges = []
    edge_hazard_levels = {}
    stats = {"edges_checked": 0, "hazards_processed": 0}
    
    for hazard in hazards:
        if hazard.level <= danger_threshold:
            continue
            
        stats["hazards_processed"] += 1
        hazard_point = (hazard.lat, hazard.lon)
        
        for u, v, key, data in graph.edges(keys=True, data=True):
            stats["edges_checked"] += 1
            edge_id = (u, v, key)
            
            # Get edge coordinates
            u_lat, u_lon = graph.nodes[u]['y'], graph.nodes[u]['x']
            v_lat, v_lon = graph.nodes[v]['y'], graph.nodes[v]['x']
            
            # Check distance to hazard
            dist_to_u = geodesic(hazard_point, (u_lat, u_lon)).meters
            dist_to_v = geodesic(hazard_point, (v_lat, v_lon)).meters
            
            mid_lat = (u_lat + v_lat) / 2
            mid_lon = (u_lon + v_lon) / 2
            dist_to_mid = geodesic(hazard_point, (mid_lat, mid_lon)).meters
            
            min_distance = min(dist_to_u, dist_to_v, dist_to_mid)
            
            if min_distance <= hazard.radius_m:
                current_level = edge_hazard_levels.get(edge_id, 0)
                edge_hazard_levels[edge_id] = max(current_level, hazard.level)
                
                if hazard.level > danger_threshold and edge_id not in dangerous_edges:
                    dangerous_edges.append(edge_id)
    
    return dangerous_edges, edge_hazard_levels, stats

def create_safe_graph(graph, dangerous_edges):
    """Create graph with dangerous edges removed."""
    safe_graph = graph.copy()
    
    removed_count = 0
    for u, v, key in dangerous_edges:
        if safe_graph.has_edge(u, v, key):
            safe_graph.remove_edge(u, v, key)
            removed_count += 1
    
    # Remove isolated nodes
    isolated_nodes = list(nx.isolates(safe_graph))
    safe_graph.remove_nodes_from(isolated_nodes)
    
    return safe_graph, removed_count

def calculate_safe_route(graph, start_coord: Coordinate, end_coord: Coordinate):
    """Calculate route using A* algorithm."""
    try:
        start_node = ox.distance.nearest_nodes(graph, X=start_coord.lon, Y=start_coord.lat)
        end_node = ox.distance.nearest_nodes(graph, X=end_coord.lon, Y=end_coord.lat)
    except:
        start_node = ox.get_nearest_node(graph, (start_coord.lat, start_coord.lon))
        end_node = ox.get_nearest_node(graph, (end_coord.lat, end_coord.lon))
    
    if start_node not in graph.nodes or end_node not in graph.nodes:
        raise HTTPException(status_code=400, detail="Start or end point is in a blocked area")
    
    def heuristic(u, v):
        u_lat, u_lon = graph.nodes[u]['y'], graph.nodes[u]['x']
        v_lat, v_lon = graph.nodes[v]['y'], graph.nodes[v]['x']
        return geodesic((u_lat, u_lon), (v_lat, v_lon)).km
    
    try:
        route = nx.astar_path(
            graph, start_node, end_node,
            heuristic=heuristic, weight='length'
        )
        
        # Calculate route statistics
        total_distance = 0
        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            if graph.has_edge(u, v):
                edge_data = graph[u][v][0]
                total_distance += edge_data.get('length', 0)
        
        return route, total_distance
    
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail="No safe route exists")

def create_route_map(original_graph, route, start_coord: Coordinate, end_coord: Coordinate, hazards: List[HazardZone]):
    """Generate interactive HTML map."""
    m = folium.Map(location=[start_coord.lat, start_coord.lon], zoom_start=14)
    
    # Add route
    if route:
        route_coords = [(original_graph.nodes[node]['y'], original_graph.nodes[node]['x']) for node in route]
        folium.PolyLine(
            locations=route_coords,
            color='blue',
            weight=5,
            opacity=0.8,
            popup=f"Safe Route ({len(route)} waypoints)"
        ).add_to(m)
    
    # Add markers
    folium.Marker(
        [start_coord.lat, start_coord.lon],
        popup="🟢 START",
        icon=folium.Icon(color='green', icon='play')
    ).add_to(m)
    
    folium.Marker(
        [end_coord.lat, end_coord.lon],
        popup="🔴 END",
        icon=folium.Icon(color='red', icon='stop')
    ).add_to(m)
    
    # Add hazard zones
    for hazard in hazards:
        color = 'darkred' if hazard.level >= 5 else 'red' if hazard.level >= 4 else 'orange' if hazard.level >= 3 else 'yellow'
        
        folium.Circle(
            location=(hazard.lat, hazard.lon),
            radius=hazard.radius_m,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.4,
            popup=f"<b>{hazard.name}</b><br>Level: {hazard.level}<br>Radius: {hazard.radius_m}m"
        ).add_to(m)
        
        folium.CircleMarker(
            location=(hazard.lat, hazard.lon),
            radius=6,
            color='black',
            fill=True,
            popup=hazard.name
        ).add_to(m)
    
    return m._repr_html_()

# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def root():
    """API documentation and test interface."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hazard-Aware Routing API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { font-weight: bold; color: #2c5aa0; }
            code { background: #e8e8e8; padding: 2px 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>🛣️ Hazard-Aware Routing API</h1>
        <p>REST API for calculating safe routes that avoid hazardous areas</p>
        
        <div class="endpoint">
            <div class="method">POST /route</div>
            <p>Calculate a safe route between two points</p>
            <p>Body: <code>{"start": {"lat": 18.7876, "lon": 98.9917}, "end": {"lat": 18.7913, "lon": 99.0014}}</code></p>
        </div>
        
        <div class="endpoint">
            <div class="method">GET /hazards</div>
            <p>Get all current hazard zones</p>
        </div>
        
        <div class="endpoint">
            <div class="method">POST /hazards</div>
            <p>Add a new hazard zone</p>
            <p>Body: <code>{"lat": 18.787, "lon": 98.9905, "level": 5, "name": "Danger Zone", "radius_m": 150}</code></p>
        </div>
        
        <div class="endpoint">
            <div class="method">GET /map/{route_id}</div>
            <p>Get interactive HTML map for a calculated route</p>
        </div>
        
        <div class="endpoint">
            <div class="method">GET /health</div>
            <p>API health check</p>
        </div>
        
        <p><a href="/docs">📖 Interactive API Documentation</a></p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cached_graphs": len(graph_cache),
        "hazard_zones": len(hazard_zones),
        "cached_routes": len(route_cache)
    }

@app.get("/hazards", response_model=List[HazardZone])
async def get_hazards():
    """Get all current hazard zones."""
    return hazard_zones

@app.post("/hazards", response_model=HazardZone)
async def add_hazard(hazard: HazardZone):
    """Add a new hazard zone."""
    if not hazard.id:
        hazard.id = str(uuid.uuid4())
    hazard.created_at = datetime.now()
    
    # Remove existing hazard with same ID
    global hazard_zones
    hazard_zones = [h for h in hazard_zones if h.id != hazard.id]
    hazard_zones.append(hazard)
    
    logger.info(f"Added hazard zone: {hazard.name} (Level {hazard.level})")
    return hazard

@app.delete("/hazards/{hazard_id}")
async def delete_hazard(hazard_id: str):
    """Delete a hazard zone."""
    global hazard_zones
    original_count = len(hazard_zones)
    hazard_zones = [h for h in hazard_zones if h.id != hazard_id]
    
    if len(hazard_zones) == original_count:
        raise HTTPException(status_code=404, detail="Hazard zone not found")
    
    return {"message": f"Hazard zone {hazard_id} deleted"}

@app.post("/route", response_model=RouteResponse)
async def calculate_route(request: RouteRequest):
    """Calculate a safe route between two points."""
    route_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    try:
        # Load graph
        graph = load_osm_graph(request.location, request.network_type)
        
        # Use request hazards or global hazards
        hazards = request.hazards if request.hazards else hazard_zones
        
        if not hazards:
            logger.warning("No hazards defined, calculating normal route")
        
        # Find dangerous edges
        dangerous_edges, edge_hazard_levels, stats = identify_dangerous_edges(
            graph, hazards, request.danger_threshold
        )
        
        # Create safe graph
        safe_graph, removed_count = create_safe_graph(graph, dangerous_edges)
        
        # Calculate route
        route, total_distance = calculate_safe_route(safe_graph, request.start, request.end)
        
        # Create waypoints
        waypoints = [
            Coordinate(lat=graph.nodes[node]['y'], lon=graph.nodes[node]['x']) 
            for node in route
        ]
        
        # Estimate duration (assuming 50 km/h average for drive, 5 km/h for walk, 15 km/h for bike)
        speed_kmh = {"drive": 50, "walk": 5, "bike": 15}[request.network_type]
        duration_min = (total_distance / 1000) / speed_kmh * 60
        
        # Create map
        map_html = create_route_map(graph, route, request.start, request.end, hazards)
        
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
        route_cache[route_id] = route_data
        
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

@app.get("/map/{route_id}", response_class=HTMLResponse)
async def get_route_map(route_id: str):
    """Get interactive HTML map for a calculated route."""
    if route_id not in route_cache:
        raise HTTPException(status_code=404, detail="Route not found")
    
    return HTMLResponse(content=route_cache[route_id]["map_html"])

@app.get("/route/{route_id}/stats", response_model=RouteStats)
async def get_route_stats(route_id: str):
    """Get detailed statistics for a calculated route."""
    if route_id not in route_cache:
        raise HTTPException(status_code=404, detail="Route not found")
    
    return route_cache[route_id]["stats"]

# Initialize with default hazards
@app.on_event("startup")
async def startup_event():
    """Initialize API with default hazard zones."""
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
    
    global hazard_zones
    hazard_zones.extend(default_hazards)
    logger.info(f"Initialized with {len(default_hazards)} default hazard zones")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)