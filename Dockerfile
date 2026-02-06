# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including ffmpeg and curl
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Deno (CRITICAL for YouTube downloads)
RUN curl -fsSL https://deno.land/install.sh | sh
ENV DENO_INSTALL="/root/.deno"
ENV PATH="$DENO_INSTALL/bin:$PATH"

# Verify Deno installation
RUN deno --version

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Update yt-dlp to latest version (critical for YouTube bypass)
RUN pip install --no-cache-dir --upgrade --force-reinstall yt-dlp

# Copy application code (rebuild triggered: 2026-02-06-v2)
ARG CACHEBUST=1
COPY . .

# Expose port (Railway will set PORT env var)
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]
