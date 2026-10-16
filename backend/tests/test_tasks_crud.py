"""CRUD tests for /api/tasks.

Both the happy path and the error path. The error path is the half that
manual clicking never covers, so it is the half worth automating.
"""


def test_create_task_returns_201_and_the_created_row(client):
    response = client.post(
        "/api/tasks",
        json={
            "title": "Provision the EKS cluster",
            "description": "VPC with two public subnets first",
            "priority": "high",
            "due_date": "2026-12-01",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["title"] == "Provision the EKS cluster"
    assert body["priority"] == "high"
    assert body["status"] == "todo"  # server-side default applied
    assert body["created_at"] and body["updated_at"]


def test_create_task_rejects_an_empty_title_with_422(client):
    """Validation happens at the edge, before anything reaches the database."""
    response = client.post("/api/tasks", json={"title": ""})

    assert response.status_code == 422
    assert client.get("/api/tasks").json() == []  # nothing was written


def test_get_task_returns_the_task_it_was_asked_for(client, sample_task):
    response = client.get(f"/api/tasks/{sample_task['id']}")

    assert response.status_code == 200
    assert response.json()["title"] == "Write the Helm chart"


def test_get_task_returns_404_for_an_id_that_does_not_exist(client):
    response = client.get("/api/tasks/999999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_task_changes_only_the_fields_that_were_sent(client, sample_task):
    """A partial update must not null out the fields it omitted."""
    response = client.put(
        f"/api/tasks/{sample_task['id']}", json={"status": "in_progress"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["title"] == sample_task["title"]      # untouched
    assert body["priority"] == sample_task["priority"]  # untouched


def test_complete_task_marks_it_done(client, sample_task):
    response = client.patch(f"/api/tasks/{sample_task['id']}/complete")

    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_delete_task_returns_204_and_the_task_is_then_gone(client, sample_task):
    delete_response = client.delete(f"/api/tasks/{sample_task['id']}")
    assert delete_response.status_code == 204
    assert delete_response.content == b""  # 204 means no body, by definition

    assert client.get(f"/api/tasks/{sample_task['id']}").status_code == 404


def test_delete_task_returns_404_when_the_task_does_not_exist(client):
    assert client.delete("/api/tasks/999999").status_code == 404
