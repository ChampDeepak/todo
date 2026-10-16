#!/bin/sh
# Applies pending migrations, then hands control to the CMD (uvicorn).
#
# `exec "$@"` matters: it replaces this shell with uvicorn as PID 1, so Docker's
# SIGTERM reaches uvicorn directly. Without exec, the shell stays PID 1, ignores
# SIGTERM, and every deploy ends with a 10-second kill timeout and dropped
# in-flight requests.
#
# Production caveat worth knowing: running migrations in the app entrypoint
# means N replicas all run `alembic upgrade head` at once on rollout. Alembic
# takes a lock so they serialise rather than corrupt, but the correct pattern at
# scale is a separate migration Job that must finish before the Deployment rolls.
set -e

echo "[entrypoint] waiting for the database..."
python - <<'PY'
import os, time, sys
from sqlalchemy import create_engine, text
url = os.environ.get("DATABASE_URL", "postgresql+psycopg://taskr:taskr@db:5432/taskr")
for attempt in range(30):
    try:
        create_engine(url).connect().execute(text("SELECT 1"))
        print("[entrypoint] database is up")
        sys.exit(0)
    except Exception as exc:
        print(f"[entrypoint] attempt {attempt + 1}/30: {type(exc).__name__}")
        time.sleep(2)
print("[entrypoint] database never became reachable", file=sys.stderr)
sys.exit(1)
PY

echo "[entrypoint] applying migrations"
alembic upgrade head

echo "[entrypoint] starting: $*"
exec "$@"
