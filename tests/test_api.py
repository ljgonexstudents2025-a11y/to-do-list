import json
import sys
from pathlib import Path

import pytest

# --- Make sure Python can find server.py (in the project root) ---
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import server
from server import app, init_db, get_db


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """
    Use a temporary database file for each test run,
    so we don't mess with your real todos.db.
    """
    test_db_path = tmp_path / "test_todos.db"

    # Point the app's DB_PATH to our temp file
    monkeypatch.setattr(server, "DB_PATH", test_db_path)

    # Re-init the DB with the new path
    with app.app_context():
        init_db()

    yield

    # Clean up: close any db connection if needed
    with app.app_context():
        db = get_db()
        db.close()


def test_home_page_loads():
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"To-Do List" in resp.data


def test_list_todos_initially_empty():
    client = app.test_client()
    resp = client.get("/api/todos")
    assert resp.status_code == 200
    todos = resp.get_json()
    assert todos == []


def test_add_and_list_todo():
    client = app.test_client()

    # Add a todo via the API
    resp = client.post(
        "/api/todos",
        data=json.dumps(
            {
                "text": "Test task",
                "due_date": "2025-01-01",
                "category": "school",
            }
        ),
        content_type="application/json",
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["text"] == "Test task"
    assert data["done"] is False
    assert data["due_date"] == "2025-01-01"
    assert data["category"] == "school"

    # Now list todos and check it's there
    resp2 = client.get("/api/todos")
    assert resp2.status_code == 200
    todos = resp2.get_json()
    assert len(todos) == 1
    assert todos[0]["text"] == "Test task"


def test_add_todo_without_text_returns_400():
    client = app.test_client()

    resp = client.post(
        "/api/todos",
        data=json.dumps({"text": "   "}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data


def test_update_text_and_due_date_and_category():
    client = app.test_client()

    # Create todo
    resp = client.post(
        "/api/todos",
        data=json.dumps({"text": "Original", "due_date": None, "category": None}),
        content_type="application/json",
    )
    todo = resp.get_json()
    todo_id = todo["id"]

    # Update text, due_date, and category
    resp2 = client.patch(
        f"/api/todos/{todo_id}",
        data=json.dumps(
            {
                "text": "Updated text",
                "due_date": "2030-12-31",
                "category": "work",
            }
        ),
        content_type="application/json",
    )
    assert resp2.status_code == 200
    updated = resp2.get_json()
    assert updated["text"] == "Updated text"
    assert updated["due_date"] == "2030-12-31"
    assert updated["category"] == "work"


def test_mark_todo_done_and_delete():
    client = app.test_client()

    # Create todo
    resp = client.post(
        "/api/todos",
        data=json.dumps({"text": "Another task"}),
        content_type="application/json",
    )
    todo = resp.get_json()
    todo_id = todo["id"]

    # Mark it done
    resp2 = client.patch(
        f"/api/todos/{todo_id}",
        data=json.dumps({"done": True}),
        content_type="application/json",
    )
    assert resp2.status_code == 200
    updated = resp2.get_json()
    assert updated["done"] is True

    # Delete it
    resp3 = client.delete(f"/api/todos/{todo_id}")
    assert resp3.status_code == 204

    # Check it's gone
    resp4 = client.get("/api/todos")
    todos = resp4.get_json()
    assert len(todos) == 0


def test_update_nonexistent_todo_returns_404():
    client = app.test_client()

    # Choose an ID that doesn't exist
    resp = client.patch(
        "/api/todos/9999",
        data=json.dumps({"text": "Doesn't matter"}),
        content_type="application/json",
    )
    # Your code fetches after update; if row doesn't exist, returns 404
    assert resp.status_code == 404
    data = resp.get_json()
    assert "error" in data

