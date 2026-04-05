# Use Debian Bookworm (latest stable release)
FROM debian:bookworm

# Set working directory
WORKDIR /app

# Install dependencies (use apt instead of apk)
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv python3-dev redis-server bash build-essential \
    ninja-build meson \
    libopenblas-dev liblapack-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment for Python dependencies
RUN python3 -m venv /app/venv

# Set the virtual environment as default
ENV PATH="/app/venv/bin:$PATH"

# Upgrade pip inside the virtual environment
RUN pip install --upgrade pip

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Ensure `run.sh` is executable
RUN chmod +x /app/run.sh

# Use ENTRYPOINT instead of CMD
ENTRYPOINT [ "/app/run.sh" ]
