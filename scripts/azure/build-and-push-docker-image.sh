#!/bin/bash
set -euo pipefail

APP_ACR_NAME="llmopsappacr"
IMAGE_NAME="llmops-app"
BUILD_TAG="${1:-latest}"

echo "🐳 Building Docker image locally (using optimized Dockerfile)..."

# Login to ACR
az acr login --name $APP_ACR_NAME

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Building from: $PROJECT_ROOT"

# Build image using Dockerfile.optimized for faster builds
docker build \
    --platform linux/amd64 \
    -t ${APP_ACR_NAME}.azurecr.io/${IMAGE_NAME}:${BUILD_TAG} \
    -t ${APP_ACR_NAME}.azurecr.io/${IMAGE_NAME}:latest \
    -f "$PROJECT_ROOT/Dockerfile.optimized" \
    "$PROJECT_ROOT"

# Push both tags
echo "📤 Pushing to ACR..."
docker push ${APP_ACR_NAME}.azurecr.io/${IMAGE_NAME}:${BUILD_TAG}
docker push ${APP_ACR_NAME}.azurecr.io/${IMAGE_NAME}:latest

echo "✅ Build and push complete!"
echo "Now run your Jenkins pipeline to deploy."