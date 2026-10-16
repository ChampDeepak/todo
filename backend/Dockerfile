# syntax=docker/dockerfile:1

# Single-stage: Python needs its interpreter at runtime, so there is no build
# toolchain to discard the way the frontend has. slim (not alpine) because
# alpine uses musl libc, which forces source builds of wheels and produces
# slower, larger-to-build images for the scientific/C-extension stack.
FROM python:3.12-slim

# PYTHONDONTWRITEBYTECODE: no .pyc clutter in a read-only-ish container.
# PYTHONUNBUFFERED: logs reach stdout immediately instead of sitting in a
#   buffer -- without it, `kubectl logs` shows nothing until the app crashes.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# ---- Layer order is deliberate --------------------------------------------
# Dependencies change rarely; source changes on every commit. Copying
# requirements first means a one-character code edit reuses the cached
# pip-install layer instead of reinstalling the whole dependency tree.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Source, newest-changing last ------------------------------------------
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY docker-entrypoint.sh .

# ---- Non-root --------------------------------------------------------------
# root inside the container is uid 0 on the host kernel. A container escape
# from a root process lands on the host as root; from uid 1001 it lands as a
# nobody. Kubernetes can enforce runAsNonRoot cluster-wide, which refuses to
# start an image that declares root -- so this is also an M8 prerequisite.
RUN chmod +x docker-entrypoint.sh \
    && useradd --uid 1001 --no-create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Docker-level healthcheck. Compose and swarm read it; Kubernetes ignores it
# and uses its own probes, which is why app/routes/health.py exists separately.
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
