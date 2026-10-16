"""Health endpoint tests.

These matter more than they look: in M8 Kubernetes uses these exact endpoints
to decide whether to restart a pod or route traffic to it. A regression here
causes a restart loop in production, not a red test in a nice CI log.
"""


def test_liveness_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_reports_database_reachable(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["database"] == "ok"


def test_metrics_endpoint_exposes_prometheus_format(client):
    """Guards the M9 contract. Prometheus parses this text format strictly."""
    client.get("/health")  # generate at least one sample
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert response.headers["content-type"].startswith("text/plain")
