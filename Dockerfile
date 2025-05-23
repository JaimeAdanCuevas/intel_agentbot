# Use Ubuntu 22.04 as base image
FROM ubuntu:22.04

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3.9 \
    python3.9-venv \
    python3-pip \
    stress-ng \
    make \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install SDE (assumes sde-external-9.33.0-2024-02-02-lin.tar.bz2 is available locally or downloadable)
# For simplicity, copy from local ./bin/sde if available
COPY ./bin/sde /app/bin/sde
COPY ./bin/xed /app/bin/xed
RUN chmod +x /app/bin/sde /app/bin/xed

# Create and activate virtual environment
RUN python3.9 -m venv .venv
ENV PATH="/app/.venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PYTHONPATH=/app/src
ENV SDE_PATH=/app/bin/sde
ENV XED_PATH=/app/bin/xed

# Default command to run tests
CMD ["make", "test"]