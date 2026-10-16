"""Filtering, search and statistics.

These exercise real SQL -- Postgres enum comparison, ILIKE, and a GROUP BY
aggregate. SQLite would accept some of this and behave differently, which is
why the suite runs against the same engine production uses.
"""
from datetime import date, timedelta


def _seed(client):
    rows = [
        {"title": "Provision EKS", "status": "todo", "priority": "high"},
        {"title": "Scan images with Trivy", "status": "in_progress", "priority": "high"},
        {"title": "Publish Helm chart", "status": "done", "priority": "medium"},
        {"title": "Write README", "status": "done", "priority": "low"},
    ]
    return [client.post("/api/tasks", json=r).json() for r in rows]


def test_filter_by_status_returns_only_matching_tasks(client):
    _seed(client)
    done = client.get("/api/tasks?status=done").json()
    assert len(done) == 2
    assert {t["status"] for t in done} == {"done"}


def test_filter_by_priority_returns_only_matching_tasks(client):
    _seed(client)
    high = client.get("/api/tasks?priority=high").json()
    assert len(high) == 2
    assert {t["priority"] for t in high} == {"high"}


def test_search_is_case_insensitive_substring_match(client):
    _seed(client)
    found = client.get("/api/tasks?search=trivy").json()
    assert len(found) == 1
    assert found[0]["title"] == "Scan images with Trivy"


def test_filters_combine_with_and_not_or(client):
    _seed(client)
    result = client.get("/api/tasks?status=done&priority=low").json()
    assert len(result) == 1
    assert result[0]["title"] == "Write README"


def test_pagination_limit_and_offset(client):
    _seed(client)
    first_page = client.get("/api/tasks?limit=2&offset=0").json()
    second_page = client.get("/api/tasks?limit=2&offset=2").json()
    assert len(first_page) == 2
    assert len(second_page) == 2
    # No overlap -- an ordering bug would show up here as a repeated id.
    assert {t["id"] for t in first_page}.isdisjoint({t["id"] for t in second_page})


def test_stats_counts_each_status_and_computes_completion_rate(client):
    _seed(client)
    stats = client.get("/api/tasks/stats").json()
    assert stats == {
        "total": 4,
        "todo": 1,
        "in_progress": 1,
        "done": 2,
        "overdue": 0,
        "completion_rate": 50.0,
    }


def test_stats_counts_a_past_due_unfinished_task_as_overdue(client):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    client.post("/api/tasks", json={"title": "Late", "due_date": yesterday})
    # A completed task with a past due date is finished, not overdue.
    client.post(
        "/api/tasks",
        json={"title": "Late but done", "due_date": yesterday, "status": "done"},
    )
    stats = client.get("/api/tasks/stats").json()
    assert stats["overdue"] == 1
    assert stats["total"] == 2


def test_stats_on_an_empty_database_does_not_divide_by_zero(client):
    """total=0 would be a ZeroDivisionError without the guard in the route."""
    stats = client.get("/api/tasks/stats").json()
    assert stats["total"] == 0
    assert stats["completion_rate"] == 0.0


def test_stats_route_is_not_shadowed_by_the_id_route(client):
    """/tasks/stats must not be parsed as /tasks/{task_id}. Route order bug."""
    assert client.get("/api/tasks/stats").status_code == 200
