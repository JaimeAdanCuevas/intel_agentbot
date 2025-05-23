# Use Ubuntu 22.04 as base image
FROM ubuntu:22.04

LABEL key="Jaime Cuevas <jaime.cuevas.ramirez@intel.com>" \
      version="1.0" \
      description="A Python-based coverage analysis tool"

ARG RASP
ARG https_proxy
ARG http_proxy

ENV RASP=${RASP}
ENV https_proxy=${https_proxy}
ENV http_proxy=${http_proxy}
ENV no_proxy="127.0.0.1,localhost,intel.com"

RUN if [ "$RASP" = "yes" ]; then \
    echo "export RASP=yes" >> /root/.bashrc && \
    echo 'export https_proxy="http://proxy-dmz.intel.com:912"' >> /root/.bashrc && \
    echo 'export http_proxy="http://proxy-dmz.intel.com:912"' >> /root/.bashrc && \
    echo 'export no_proxy="127.0.0.1,localhost,intel.com"' >> /root/.bashrc && \
    echo 'Acquire::http::Proxy "http://proxy-dmz.intel.com:912";' >> /etc/apt/apt.conf.d/99proxy && \
    echo 'Acquire::https::Proxy "http://proxy-dmz.intel.com:912";' >> /etc/apt/apt.conf.d/99proxy; \
fi

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-venv \
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
#RUN python3 -m venv .venv
#ENV PATH="/app/.venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PYTHONPATH=/app/src
ENV SDE_PATH=/app/bin/sde
ENV XED_PATH=/app/bin/xed

# Default command to run tests
CMD ["make", "test"]