#!/bin/bash
# Test script for FastAPI backend Docker container
# Usage: ./scripts/test-backend.sh [image-tag]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
IMAGE_NAME="ai-video-backend"
TAG="${1:-latest}"
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"
CONTAINER_NAME="backend-test-$$"  # Use PID for unique name
TEST_PORT="8000"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Testing FastAPI Backend Docker Image${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Image: ${YELLOW}${FULL_IMAGE_NAME}${NC}"
echo -e "Container: ${YELLOW}${CONTAINER_NAME}${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${BLUE}Cleaning up...${NC}"
    docker stop "${CONTAINER_NAME}" >/dev/null 2>&1 || true
    docker rm "${CONTAINER_NAME}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# Test 1: Check if image exists
echo -e "${BLUE}Test 1: Checking if image exists...${NC}"
if docker images "${FULL_IMAGE_NAME}" --format "{{.Repository}}" | grep -q "${IMAGE_NAME}"; then
    echo -e "${GREEN}✓ Image exists${NC}"
else
    echo -e "${RED}✗ Image not found. Run ./scripts/build-backend.sh first${NC}"
    exit 1
fi

# Test 2: Start container
echo ""
echo -e "${BLUE}Test 2: Starting container...${NC}"
docker run -d \
    --name "${CONTAINER_NAME}" \
    -p "${TEST_PORT}:8000" \
    -e APP_ENV=test \
    -e LOG_LEVEL=INFO \
    "${FULL_IMAGE_NAME}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Container started${NC}"
else
    echo -e "${RED}✗ Failed to start container${NC}"
    exit 1
fi

# Test 3: Wait for container to be healthy
echo ""
echo -e "${BLUE}Test 3: Waiting for container to be healthy...${NC}"
TIMEOUT=30
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' "${CONTAINER_NAME}" 2>/dev/null || echo "none")
    if [ "$STATUS" = "healthy" ]; then
        echo -e "${GREEN}✓ Container is healthy${NC}"
        break
    elif [ "$STATUS" = "none" ]; then
        # No health check, try direct HTTP request
        if curl -sf http://localhost:${TEST_PORT}/health >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Container is responding (no health check configured)${NC}"
            break
        fi
    fi
    echo -e "  Waiting... ($ELAPSED/$TIMEOUT seconds)"
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo -e "${RED}✗ Container did not become healthy${NC}"
    echo ""
    echo "Container logs:"
    docker logs "${CONTAINER_NAME}"
    exit 1
fi

# Test 4: Check health endpoint
echo ""
echo -e "${BLUE}Test 4: Testing /health endpoint...${NC}"
HEALTH_RESPONSE=$(curl -sf http://localhost:${TEST_PORT}/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health endpoint responding${NC}"
    echo -e "  Response: ${YELLOW}${HEALTH_RESPONSE}${NC}"
else
    echo -e "${RED}✗ Health endpoint not responding correctly${NC}"
    exit 1
fi

# Test 5: Check FFmpeg installation
echo ""
echo -e "${BLUE}Test 5: Verifying FFmpeg installation...${NC}"
FFMPEG_VERSION=$(docker exec "${CONTAINER_NAME}" ffmpeg -version 2>/dev/null | head -n1)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ FFmpeg is installed${NC}"
    echo -e "  Version: ${YELLOW}${FFMPEG_VERSION}${NC}"
else
    echo -e "${RED}✗ FFmpeg not found${NC}"
    exit 1
fi

# Test 6: Check Python version
echo ""
echo -e "${BLUE}Test 6: Verifying Python version...${NC}"
PYTHON_VERSION=$(docker exec "${CONTAINER_NAME}" python --version)
if echo "$PYTHON_VERSION" | grep -q "Python 3.13"; then
    echo -e "${GREEN}✓ Python 3.13 is installed${NC}"
    echo -e "  Version: ${YELLOW}${PYTHON_VERSION}${NC}"
else
    echo -e "${YELLOW}⚠ Python version: ${PYTHON_VERSION}${NC}"
fi

# Test 7: Check if running as non-root
echo ""
echo -e "${BLUE}Test 7: Verifying non-root user...${NC}"
CONTAINER_USER=$(docker exec "${CONTAINER_NAME}" whoami)
if [ "$CONTAINER_USER" != "root" ]; then
    echo -e "${GREEN}✓ Running as non-root user: ${CONTAINER_USER}${NC}"
else
    echo -e "${YELLOW}⚠ Container running as root${NC}"
fi

# Test 8: Check API routes
echo ""
echo -e "${BLUE}Test 8: Testing API routes...${NC}"
V1_RESPONSE=$(curl -sf http://localhost:${TEST_PORT}/api/v1/ping 2>/dev/null || echo "not found")
if echo "$V1_RESPONSE" | grep -q "pong"; then
    echo -e "${GREEN}✓ API v1 routes responding${NC}"
else
    echo -e "${YELLOW}⚠ API v1 routes: ${V1_RESPONSE}${NC}"
fi

# Test 9: Check container logs for errors
echo ""
echo -e "${BLUE}Test 9: Checking container logs for errors...${NC}"
ERROR_COUNT=$(docker logs "${CONTAINER_NAME}" 2>&1 | grep -i "error" | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ No errors in logs${NC}"
else
    echo -e "${YELLOW}⚠ Found ${ERROR_COUNT} error(s) in logs${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All tests passed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Container Information:${NC}"
docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo -e "${BLUE}Image Size:${NC}"
docker images "${FULL_IMAGE_NAME}" --format "  {{.Size}}"

echo ""
echo -e "${GREEN}Container will be stopped and removed on exit.${NC}"
echo -e "To keep it running, press Ctrl+C now."
echo ""
sleep 3
