# ── Stage 1: Build virtualenv with all dependencies ───────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Build essentials for wheels that need compilation (e.g. some Plotly deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Minimal runtime image ────────────────────────────
FROM python:3.12-slim AS runtime

# curl is used for a basic HTTP healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only the virtualenv from builder (keeps image small)
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy the full frontend source
COPY . .

# ── Non-root security user (matches backend/Dockerfile pattern) ─
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -d /app -s /sbin/nologin appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8501

# Healthcheck targeting the Streamlit health endpoint
HEALTHCHECK --interval=30s --timeout=15s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "streamlit_app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
