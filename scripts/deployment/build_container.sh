#!/bin/bash
# Script to build and run the Docker container for the Intel Agentbot project

set -e

# Configuration
IMAGE_NAME="intel-agentbot"
TAG="latest"
CONTAINER_NAME="intel-agentbot-container"
PROJECT_DIR="$(pwd)"
SDE_BINARY="${PROJECT_DIR}/bin/sde"
XED_BINARY="${PROJECT_DIR}/bin/xed"

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker and try again."
    exit 1
fi

# Verify SDE and xed binaries exist
if [[ ! -f "${SDE_BINARY}" ]]; then
    echo "Error: SDE binary not found at ${SDE_BINARY}"
    exit 1
fi
if [[ ! -f "${XED_BINARY}" ]]; then
    echo "Error: xed binary not found at ${XED_BINARY}"
    exit 1
fi

# Verify API credentials
if [[ -z "${CLIENT_ID}" ]] || [[ "${CLIENT_ID}" == "<your-client-id>" ]]; then
    echo "Error: CLIENT_ID not set. Please set CLIENT_ID environment variable."
    exit 1
fi
if [[ -z "${CLIENT_SECRET}" ]] || [[ "${CLIENT_SECRET}" == "<your-client-secret>" ]]; then
    echo "Error: CLIENT_SECRET not set. Please set CLIENT_SECRET environment variable."
    exit 1
fi

# Build Docker image
echo "Building Docker image ${IMAGE_NAME}:${TAG}..."

if [ "$RASP" == "yes" ]; then
	docker build --build-arg RASP=$RASP --build-arg https_proxy="http://proxy-dmz.intel.com:912" --build-arg http_proxy="http://proxy-dmz.intel.com:912" -t "${IMAGE_NAME}:${TAG}" .
    if [ $? != 0 ]; then
        echo "Error: could not build the intel-agentbot image. Exiting."
        exit 23
    fi
else
	docker build -t "${IMAGE_NAME}:${TAG}" .
    if [ $? != 0 ]; then
            echo "Error: could not build the intel-agentbot image. Exiting."
            exit 23
    fi
fi

sleep 3

# Run container to execute tests
echo "Running tests in container..."
docker run --rm \
    --name "${CONTAINER_NAME}" \
    -v "${PROJECT_DIR}/tests:/app/tests" \
    -v "${PROJECT_DIR}/src:/app/src" \
    -v "${PROJECT_DIR}/config:/app/config" \
    "${IMAGE_NAME}:${TAG}" \
    make test

sleep 3

# Run container to execute analyze workflow
echo "Running stress-ng workflow in container..."
docker run --rm \
    --name "${CONTAINER_NAME}" \
    -v "${PROJECT_DIR}/tests:/app/tests" \
    -v "${PROJECT_DIR}/src:/app/src" \
    -v "${PROJECT_DIR}/config:/app/config" \
    "${IMAGE_NAME}:${TAG}" \
    make analyze

sleep 3

# Run container to execute stress-ng workflow
echo "Running stress-ng workflow in container..."
docker run --rm \
    --name "${CONTAINER_NAME}" \
    -v "${PROJECT_DIR}/tests:/app/tests" \
    -v "${PROJECT_DIR}/src:/app/src" \
    -v "${PROJECT_DIR}/config:/app/config" \
    "${IMAGE_NAME}:${TAG}" \
    make stress-ng

sleep 3

# Run container to execute propose workflow
echo "Running stress-ng workflow in container..."
docker run --rm \
    --name "${CONTAINER_NAME}" \
    -v "${PROJECT_DIR}/tests:/app/tests" \
    -v "${PROJECT_DIR}/src:/app/src" \
    -v "${PROJECT_DIR}/config:/app/config" \
    -e CLIENT_ID="${CLIENT_ID}" \
    -e CLIENT_SECRET="${CLIENT_SECRET}" \
    -e AUTO_APPEND_YAML="n" \
    "${IMAGE_NAME}:${TAG}" \
    bash -c "unset no_proxy && make propose"

sleep 2

echo "Container build and execution completed successfully."