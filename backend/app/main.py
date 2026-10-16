"""FastAPI application factory and wiring."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.routes import health, tasks

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Task tracking API for the DevOps capstone.",
)

# The browser blocks cross-origin calls unless the server opts in. The frontend
# is served from a different origin (port 3000) than the API (port 8000).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(tasks.router)

# Exposes GET /metrics in Prometheus text format, with request count, latency
# histogram and in-progress gauge per endpoint. Consumed by M9.
Instrumentator().instrument(app).expose(app, include_in_schema=False)
