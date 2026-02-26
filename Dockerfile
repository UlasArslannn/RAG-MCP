# Dockerfile for RAG-MCP Project
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first (better caching)
COPY pyproject.toml uv.lock requirements.txt ./

# Install dependencies with uv
RUN uv sync --frozen --no-dev

# Install langchain dependencies from requirements.txt
# (excluding selenium/webdriver-manager - not needed in container)
RUN uv pip install langchain langchain-ollama langchain-chroma pandas

# Copy application code
COPY scripts/ ./scripts/
COPY sql.py ./
COPY reviews.db* ./

# Expose ports
EXPOSE 8000 8001

# Default: run MCP server
CMD ["uv", "run", "python", "scripts/new_server.py", "--server_type=sse"]
