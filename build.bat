@echo off
REM Build script for Hazard-Aware Routing API Docker image (Windows)

set IMAGE_NAME=hazard-routing-api
set TAG=%1
if "%TAG%"=="" set TAG=latest
set DOCKERFILE=%2
if "%DOCKERFILE%"=="" set DOCKERFILE=Dockerfile

echo 🐳 Building Docker image: %IMAGE_NAME%:%TAG%
echo 📁 Using Dockerfile: %DOCKERFILE%

REM Build the image
docker build -t "%IMAGE_NAME%:%TAG%" -f "%DOCKERFILE%" .

if %ERRORLEVEL% neq 0 (
    echo ❌ Build failed!
    exit /b 1
)

echo ✅ Build completed successfully!
echo 📋 Image details:
docker images "%IMAGE_NAME%:%TAG%"

echo.
echo 🚀 To run the container:
echo docker run -p 8000:8000 %IMAGE_NAME%:%TAG%
echo.
echo 🔧 To run with docker-compose:
echo docker-compose up -d