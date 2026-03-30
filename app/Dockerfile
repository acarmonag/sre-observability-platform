FROM python:3.12-slim

# System dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Use /srv as working dir so we can place code at /srv/app/
WORKDIR /srv

# Install dependencies first (separate layer for cache efficiency)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code into /srv/app/ so that "from app.X import Y" resolves correctly
COPY --chown=appuser:appuser . ./app/

# Ensure all subdirectories are Python packages
RUN find ./app -type d -exec touch {}/__init__.py \; 2>/dev/null || true

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=5 \
    CMD curl -sf http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
