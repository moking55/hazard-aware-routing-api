"""
Map visualization service for generating interactive HTML maps.

This module handles the creation of Folium maps with routes,
hazard zones, and interactive markers.
"""

from typing import List
import folium

from models import Coordinate, HazardZone


class MapService:
    """Service class for map generation and visualization."""
    
    @staticmethod
    def create_route_map(
        original_graph, 
        route: List, 
        start_coord: Coordinate, 
        end_coord: Coordinate, 
        hazards: List[HazardZone]
    ) -> str:
        """Generate interactive HTML map with route and hazards."""
        m = folium.Map(location=[start_coord.lat, start_coord.lon], zoom_start=14)
        
        # Add route
        if route:
            route_coords = [
                (original_graph.nodes[node]['y'], original_graph.nodes[node]['x']) 
                for node in route
            ]
            folium.PolyLine(
                locations=route_coords,
                color='blue',
                weight=5,
                opacity=0.8,
                popup=f"Safe Route ({len(route)} waypoints)"
            ).add_to(m)
        
        # Add start marker
        folium.Marker(
            [start_coord.lat, start_coord.lon],
            popup="🟢 START",
            icon=folium.Icon(color='green', icon='play')
        ).add_to(m)
        
        # Add end marker
        folium.Marker(
            [end_coord.lat, end_coord.lon],
            popup="🔴 END",
            icon=folium.Icon(color='red', icon='stop')
        ).add_to(m)
        
        # Add hazard zones
        for hazard in hazards:
            color = MapService._get_hazard_color(hazard.level)
            
            # Add hazard circle
            folium.Circle(
                location=(hazard.lat, hazard.lon),
                radius=hazard.radius_m,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.4,
                popup=f"<b>{hazard.name}</b><br>Level: {hazard.level}<br>Radius: {hazard.radius_m}m"
            ).add_to(m)
            
            # Add hazard center marker
            folium.CircleMarker(
                location=(hazard.lat, hazard.lon),
                radius=6,
                color='black',
                fill=True,
                popup=hazard.name
            ).add_to(m)
        
        return m._repr_html_()
    
    @staticmethod
    def _get_hazard_color(level: int) -> str:
        """Determine hazard zone color based on danger level."""
        if level >= 5:
            return 'darkred'
        elif level >= 4:
            return 'red'
        elif level >= 3:
            return 'orange'
        else:
            return 'yellow'


# Global instance for backward compatibility
map_service = MapService()