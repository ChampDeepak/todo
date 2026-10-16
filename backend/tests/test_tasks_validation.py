"""Input validation tests.

422 means the request never reached the database. Catching bad input at the
edge is what stops a malformed payload from becoming a corrupt row that
somebody has to clean up by hand six months later.
"""
import pytest


@pytest.mark.parametrize(
    "payload,reason",
    [
        ({}, "title is required"),
        ({"title": ""}, "title cannot be empty"),
        ({"title": "x" * 201}, "title exceeds 200 characters"),
        ({"title": "ok", "status": "finished"}, "status is not a valid enum member"),
        ({"title": "ok", "priority": "urgent"}, "priority is not a valid enum member"),
        ({"title": "ok", "due_date": "not-a-date"}, "due_date is not a date"),
    ],
)
def test_invalid_payload_is_rejected_with_422(client, payload, reason):
    assert client.post("/api/tasks", json=payload).status_code == 422, reason


def test_list_rejects_an_oversized_page_limit(client):
    """An unbounded limit is how a list endpoint becomes an outage."""
    assert client.get("/api/tasks?limit=100000").status_code == 422
