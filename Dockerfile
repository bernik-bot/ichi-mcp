# ichi-mcp: an MCP stdio server for the free, public ICHI API (https://ichi.global). Read-only, no API key, no state.
# Build:  docker build -t ichi-mcp .
# Run:    docker run -i --rm ichi-mcp          (stdio: the MCP client talks to the container's stdin/stdout)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install . && useradd --create-home --uid 10001 ichi

# no secrets, no volumes, no ports: the server only makes outbound HTTPS GETs to ichi.global
USER ichi
ENTRYPOINT ["ichi-mcp"]
