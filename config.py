"""
Configuration settings for the Hazard-Aware Routing API.

This module contains application configuration, constants,
and settings that can be customized for different environments.
"""

import logging
from typing import Dict


class Config:
    """Application configuration class."""
    
    # API Configuration
    TITLE = "Hazard-Aware Routing API"
    DESCRIPTION = "REST API for calculating safe routes that avoid hazardous areas"
    VERSION = "1.0.0"
    
    # Server Configuration
    HOST = "0.0.0.0"
    PORT = 8000
    RELOAD = True
    
    # Routing Configuration
    DEFAULT_LOCATION = "Chiang Mai, Thailand"
    DEFAULT_NETWORK_TYPE = "drive"
    DEFAULT_DANGER_THRESHOLD = 3
    
    # Speed estimates for duration calculation (km/h)
    SPEED_ESTIMATES: Dict[str, float] = {
        "drive": 50.0,
        "walk": 5.0,
        "bike": 15.0
    }
    
    # Map Configuration
    DEFAULT_ZOOM_LEVEL = 14
    
    # Hazard Zone Configuration
    DEFAULT_HAZARD_RADIUS = 50  # meters
    MIN_HAZARD_RADIUS = 1
    MAX_HAZARD_RADIUS = 1000
    MIN_HAZARD_LEVEL = 1
    MAX_HAZARD_LEVEL = 10
    
    # Logging Configuration
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=Config.LOG_LEVEL,
        format=Config.LOG_FORMAT
    )


# API Documentation HTML Template
API_DOCS_HTML = """
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