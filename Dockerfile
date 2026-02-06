# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including ffmpeg, curl, and Node.js
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    unzip \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Deno (PRIMARY - for PO Token generation)
RUN curl -fsSL https://deno.land/install.sh | sh
ENV DENO_INSTALL="/root/.deno"
ENV PATH="$DENO_INSTALL/bin:$PATH"

# Force Python to not buffer output (critical for Railway logs)
ENV PYTHONUNBUFFERED=1

# Verify installations (Deno + Node.js for PO Token)
RUN deno --version && node --version

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (v3: removed oauth2 plugin)
RUN pip install --no-cache-dir -r requirements.txt

# Update yt-dlp to latest version (critical for YouTube bypass)
RUN pip install --no-cache-dir --upgrade --force-reinstall yt-dlp

# Copy application code (force rebuild: 2026-02-06 v5)
ARG CACHEBUST=5
COPY . .

# Expose port (Railway will set PORT env var)
EXPOSE 8080

# Run the application with auto-update yt-dlp on startup
# This ensures we always have the latest YouTube bypass methods
CMD pip install -q --upgrade yt-dlp && python app.py
