"""
Core routing service for hazard-aware path calculation.

This module handles OSM graph loading, hazard zone processing,
and safe route calculation using A* algorithm.
"""

from typing import List, Tuple, Dict, Any
import osmnx as ox
import networkx as nx
from geopy.distance import geodesic
from fastapi import HTTPException
import logging

from models import Coordinate, HazardZone

logger = logging.getLogger(__name__)


class RoutingService:
    """Service class for handling routing operations."""
    
    def __init__(self):
        self.graph_cache: Dict[str, Any] = {}
    
    def load_osm_graph(self, location: str, network_type: str = "drive"):
        """Load and cache OSM graph data."""
        cache_key = f"{location}_{network_type}"
        
        if cache_key in self.graph_cache:
            logger.info(f"Using cached graph for {cache_key}")
            return self.graph_cache[cache_key]
        
        logger.info(f"Loading OSM data for {location} ({network_type})")
        try:
            graph = ox.graph_from_place(location, network_type=network_type)
            self.graph_cache[cache_key] = graph
            return graph
        except Exception as e:
            logger.error(f"Failed to load OSM data: {e}")
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to load map data for {location}"
            )
    
    def identify_dangerous_edges(
        self, 
        graph, 
        hazards: List[HazardZone], 
        danger_threshold: int
    ) -> Tuple[List[Tuple], Dict[Tuple, int], Dict[str, int]]:
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
    
    def create_safe_graph(self, graph, dangerous_edges: List[Tuple]) -> Tuple[Any, int]:
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
    
    def calculate_safe_route(
        self, 
        graph, 
        start_coord: Coordinate, 
        end_coord: Coordinate
    ) -> Tuple[List, float]:
        """Calculate route using A* algorithm."""
        try:
            start_node = ox.distance.nearest_nodes(
                graph, X=start_coord.lon, Y=start_coord.lat
            )
            end_node = ox.distance.nearest_nodes(
                graph, X=end_coord.lon, Y=end_coord.lat
            )
        except:
            start_node = ox.get_nearest_node(graph, (start_coord.lat, start_coord.lon))
            end_node = ox.get_nearest_node(graph, (end_coord.lat, end_coord.lon))
        
        if start_node not in graph.nodes or end_node not in graph.nodes:
            raise HTTPException(
                status_code=400, 
                detail="Start or end point is in a blocked area"
            )
        
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
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get statistics about cached graphs."""
        return {"cached_graphs": len(self.graph_cache)}


# Global instance for backward compatibility
routing_service = RoutingService()