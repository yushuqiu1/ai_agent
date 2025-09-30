# Python slim base
FROM python:3.11-slim

# System deps (optional but handy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Install deps first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY simple_mcp_server.py .

# App port (Smithery maps this automatically)
ENV PORT=8080

# Start uvicorn
CMD ["python", "simple_mcp_server.py"]
