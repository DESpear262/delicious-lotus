#!/bin/bash
# Build script for FastAPI backend Docker image
# Usage: ./scripts/build-backend.sh [tag]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
IMAGE_NAME="ai-video-backend"
TAG="${1:-latest}"
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Building FastAPI Backend Docker Image${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Image: ${YELLOW}${FULL_IMAGE_NAME}${NC}"
echo ""

# Change to the fastapi directory
cd "$(dirname "$0")/../fastapi" || exit 1

# Build the Docker image
echo -e "${GREEN}Building Docker image...${NC}"
docker build -t "${FULL_IMAGE_NAME}" .

# Check if build was successful
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Build successful!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    # Display image info
    echo -e "${GREEN}Image information:${NC}"
    docker images "${IMAGE_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

    echo ""
    echo -e "${GREEN}Image size:${NC}"
    SIZE=$(docker images "${FULL_IMAGE_NAME}" --format "{{.Size}}")
    echo -e "  ${YELLOW}${SIZE}${NC}"

    # Check if image is within target size (<500MB)
    SIZE_MB=$(docker images "${FULL_IMAGE_NAME}" --format "{{.Size}}" | sed 's/MB//' | sed 's/GB/*1024/')
    echo ""
    echo -e "${GREEN}Target: <500MB${NC}"

    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo -e "  1. Run tests: ${YELLOW}./scripts/test-backend.sh${NC}"
    echo -e "  2. Run container: ${YELLOW}docker run -p 8000:8000 ${FULL_IMAGE_NAME}${NC}"
    echo -e "  3. Test health check: ${YELLOW}curl http://localhost:8000/health${NC}"

else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}Build failed!${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi
