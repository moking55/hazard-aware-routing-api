#!/bin/bash
# Build script for Hazard-Aware Routing API Docker image

set -e

# Configuration
IMAGE_NAME="hazard-routing-api"
TAG=${1:-latest}
DOCKERFILE=${2:-Dockerfile}

echo "🐳 Building Docker image: ${IMAGE_NAME}:${TAG}"
echo "📁 Using Dockerfile: ${DOCKERFILE}"

# Build the image
docker build -t "${IMAGE_NAME}:${TAG}" -f "${DOCKERFILE}" .

echo "✅ Build completed successfully!"
echo "📋 Image details:"
docker images "${IMAGE_NAME}:${TAG}"

echo ""
echo "🚀 To run the container:"
echo "docker run -p 8000:8000 ${IMAGE_NAME}:${TAG}"
echo ""
echo "🔧 To run with docker-compose:"
echo "docker-compose up -d"