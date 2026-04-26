FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY pyproject.toml README.md ./
COPY partle_mcp ./partle_mcp

RUN pip install --no-cache-dir .

ENTRYPOINT ["python", "-m", "partle_mcp"]
