"""CRUD tests for /api/tasks.

Each test starts from an empty database, because conftest rolls back the
transaction after every one of them.
"""


def test_create_task_returns_201_and_persists(client):
    response = client.post(
        "/api/tasks",
        json={
            "title": "Write the Helm chart",
            "description": "Backend and frontend templates",
            "priority": "high",
            "due_date": "2026-11-01",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["title"] == "Write the Helm chart"
    assert body["status"] == "todo"      # default applied
    assert body["priority"] == "high"
    assert body["created_at"] is not None

    # Persisted, not just echoed back.
    assert client.get(f"/api/tasks/{body['id']}").json()["title"] == "Write the Helm chart"


def test_list_is_empty_on_a_fresh_database(client):
    """Proves test isolation works. This fails the moment rollback breaks."""
    assert client.get("/api/tasks").json() == []


def test_get_unknown_task_returns_404(client):
    response = client.get("/api/tasks/999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_changes_only_the_fields_sent(client, sample_task):
    """PUT uses exclude_unset, so omitted fields must keep their old values."""
    response = client.put(f"/api/tasks/{sample_task['id']}", json={"status": "in_progress"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["title"] == sample_task["title"]      # untouched
    assert body["priority"] == sample_task["priority"]  # untouched


def test_complete_endpoint_marks_task_done(client, sample_task):
    response = client.patch(f"/api/tasks/{sample_task['id']}/complete")
    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_delete_returns_204_and_task_is_gone(client, sample_task):
    assert client.delete(f"/api/tasks/{sample_task['id']}").status_code == 204
    assert client.get(f"/api/tasks/{sample_task['id']}").status_code == 404


def test_delete_unknown_task_returns_404(client):
    assert client.delete("/api/tasks/424242").status_code == 404
