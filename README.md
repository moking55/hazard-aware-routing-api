# Hazard-Aware Routing API

A FastAPI-based REST API for calculating safe routes that avoid hazardous areas.

## 🏗️ Project Structure

```
route_optimization/
├── main.py              # FastAPI app initialization and startup
├── config.py            # Configuration and constants
├── models.py            # Pydantic data models
├── routing_service.py   # Core routing logic and OSM integration
├── map_service.py       # Map visualization with Folium
├── storage_service.py   # In-memory data storage (replace with DB in prod)
├── requirements.txt     # Python dependencies
├── routes/              # API endpoint modules
│   ├── __init__.py
│   ├── health.py        # Health check endpoints
│   ├── hazards.py       # Hazard zone CRUD operations
│   └── routing.py       # Route calculation and maps
└── __pycache__/         # Python cache files
```

## 🚀 Features

- **Safe Route Calculation**: Uses A* algorithm to find optimal paths avoiding hazards
- **Hazard Zone Management**: CRUD operations for dangerous areas
- **Interactive Maps**: Folium-based visualization with routes and hazard zones
- **Multiple Transport Modes**: Support for driving, walking, and cycling
- **Caching**: Intelligent caching of OSM graphs and route results
- **RESTful API**: Clean, documented endpoints with FastAPI

## 📦 Installation & Deployment

### Local Development

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the development server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment

#### Quick Start with Docker Compose

```bash
# Clone and navigate to project
cd route_optimization

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Manual Docker Build

```bash
# Build development image
docker build -t hazard-routing-api .

# Build production image
docker build -t hazard-routing-api:prod -f Dockerfile.prod .

# Run container
docker run -p 8000:8000 hazard-routing-api
```

#### Windows Build Script

```cmd
# Build with default settings
build.bat

# Build with custom tag
build.bat v1.0.0

# Build production image
build.bat prod Dockerfile.prod
```

#### Linux/Mac Build Script

```bash
# Make script executable
chmod +x build.sh

# Build with default settings
./build.sh

# Build with custom tag
./build.sh v1.0.0

# Build production image
./build.sh prod Dockerfile.prod
```

3. Access the API:
- **API Documentation**: http://localhost:8000/docs
- **API Interface**: http://localhost:8000/
- **Health Check**: http://localhost:8000/health

## 🛠️ API Endpoints

### Route Calculation
- **POST /route** - Calculate safe route between two points
- **GET /map/{route_id}** - Get interactive HTML map
- **GET /route/{route_id}/stats** - Get route statistics

### Hazard Management
- **GET /hazards** - List all hazard zones
- **POST /hazards** - Add new hazard zone
- **DELETE /hazards/{hazard_id}** - Remove hazard zone

### System
- **GET /health** - API health check
- **GET /** - API documentation page

## 🔧 Configuration

Key settings in `config.py`:
- **Default location**: Chiang Mai, Thailand
- **Transport speeds**: Drive (50 km/h), Walk (5 km/h), Bike (15 km/h)
- **Hazard levels**: 1-10 scale
- **Default danger threshold**: 3 (blocks hazards level 4+)

## 📊 Code Architecture

### Services Layer
- **RoutingService**: OSM graph management and pathfinding
- **MapService**: Folium map generation and styling
- **StorageService**: Data persistence and caching

### API Layer
- Modular route handlers grouped by functionality
- Consistent error handling and response models
- Automatic API documentation with Pydantic

### Data Models
- Type-safe Pydantic models for all API inputs/outputs
- Validation for coordinates, hazard levels, and route parameters

## 🔍 Example Usage

### Calculate Route
```bash
curl -X POST "http://localhost:8000/route" \
  -H "Content-Type: application/json" \
  -d '{
    "start": {"lat": 18.7876, "lon": 98.9917},
    "end": {"lat": 18.7913, "lon": 99.0014},
    "danger_threshold": 3
  }'
```

### Add Hazard Zone
```bash
curl -X POST "http://localhost:8000/hazards" \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 18.787,
    "lon": 98.9905,
    "level": 5,
    "name": "Construction Zone",
    "radius_m": 150
  }'
```

## 🚧 Production Considerations

1. **Database**: Replace `StorageService` with PostgreSQL/MongoDB
2. **Authentication**: Add API key or OAuth2 authentication
3. **Rate Limiting**: Implement request throttling
4. **Monitoring**: Add logging, metrics, and health checks
5. **Deployment**: Use production WSGI server with multiple workers

## 🐳 Docker Configuration

### Available Dockerfiles

- **`Dockerfile`**: Multi-stage development build with all tools
- **`Dockerfile.prod`**: Optimized production build with minimal layers

### Docker Compose Services

- **route-api**: Main FastAPI application
- **redis**: Optional caching layer (commented)
- **postgres**: Optional database backend (commented)

### Environment Variables

- `PYTHONPATH`: Set to `/app`
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)
- `WORKERS`: Number of Uvicorn workers (production)
- `MAX_WORKERS`: Maximum worker limit

### Health Checks

The Docker containers include health checks that:
- Test the `/health` endpoint every 30 seconds
- Allow 40 seconds for startup
- Retry 3 times before marking unhealthy
- Timeout after 10 seconds per check