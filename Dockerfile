FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install deps first for layer caching
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy source
COPY . .

# Expose default port for HTTP mode
EXPOSE 8080

# Default: run the unified server. (Smithery overrides env to MCP_TRANSPORT=http)
CMD ["python", "simple_mcp_server.py"]
