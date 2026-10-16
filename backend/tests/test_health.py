"""Health endpoint tests.

These matter more than they look. Kubernetes restarts a container whose
liveness probe fails, so a bug here turns into a crash loop in M8.
"""


def test_liveness_returns_ok_without_touching_the_database(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "service" in body and "environment" in body


def test_readiness_reports_the_database_as_reachable(client):
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}


def test_metrics_endpoint_returns_prometheus_text_format(client):
    """M9 depends on this endpoint existing and being scrapeable."""
    client.get("/health")  # generate at least one measured request

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "# HELP" in response.text
    assert "# TYPE" in response.text
