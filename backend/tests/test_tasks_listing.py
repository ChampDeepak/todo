"""Tests for listing, filtering and the stats aggregate."""
import pytest


@pytest.fixture()
def three_tasks(client):
    for title, task_status, priority in [
        ("Write Dockerfile", "todo", "high"),
        ("Set up GitHub Actions", "in_progress", "medium"),
        ("Run Trivy scan", "done", "low"),
    ]:
        assert client.post(
            "/api/tasks",
            json={"title": title, "status": task_status, "priority": priority},
        ).status_code == 201


def test_list_tasks_is_empty_on_a_fresh_database(client):
    """Proves the per-test database really is isolated."""
    response = client.get("/api/tasks")

    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_returns_every_task(client, three_tasks):
    response = client.get("/api/tasks")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_list_tasks_filters_by_status(client, three_tasks):
    response = client.get("/api/tasks", params={"status": "done"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Run Trivy scan"


def test_list_tasks_rejects_an_oversized_limit(client):
    """The page size is bounded, so one client cannot ask for every row."""
    assert client.get("/api/tasks", params={"limit": 10000}).status_code == 422


def test_stats_counts_tasks_by_status(client, three_tasks):
    response = client.get("/api/tasks/stats")

    assert response.status_code == 200
    stats = response.json()
    assert stats["total"] == 3
    assert stats["todo"] == 1
    assert stats["in_progress"] == 1
    assert stats["done"] == 1
    assert stats["completion_rate"] == pytest.approx(33.3)


def test_stats_route_is_not_shadowed_by_the_task_id_route(client):
    """/api/tasks/stats must not be parsed as /api/tasks/{task_id}."""
    assert client.get("/api/tasks/stats").status_code == 200
