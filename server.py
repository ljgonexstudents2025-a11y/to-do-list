from flask import Flask, request, jsonify, render_template, g, Response
import sqlite3
from pathlib import Path
import time

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

DB_PATH = Path("todos.db")
app = Flask(__name__)

# ---------- Prometheus Metrics ----------

REQUEST_COUNT = Counter(
    "todo_app_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "http_status"],
)

REQUEST_LATENCY = Histogram(
    "todo_app_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
)

ERROR_COUNT = Counter(
    "todo_app_http_errors_total",
    "Total HTTP 5xx errors",
    ["endpoint"],
)

# ---------- Metrics hooks ----------

@app.before_request
def start_timer():
    # store start time on flask.g so we can compute latency later
    g.start_time = time.perf_counter()


@app.after_request
def record_metrics(response):
    # compute latency
    try:
        latency = time.perf_counter() - g.start_time
    except Exception:
        latency = None

    endpoint = request.endpoint or "unknown"

    # increment request count
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        http_status=response.status_code,
    ).inc()

    # observe latency
    if latency is not None:
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(latency)

    # count 5xx errors
    if response.status_code >= 500:
        ERROR_COUNT.labels(endpoint=endpoint).inc()

    return response

# ---------- Health check ----------

@app.route("/health")
def health():
    """
    Basic health endpoint for monitoring.
    Returns 200 and simple JSON if the app + DB are ok.
    """
    status = {"status": "ok"}

    try:
        db = get_db()
        # simple test query
        db.execute("SELECT 1")
        status["database"] = "ok"
    except Exception as exc:
        status["database"] = "error"
        status["error"] = str(exc)

    http_status = 200 if status.get("database") == "ok" else 500
    return jsonify(status), http_status

# ---------- Metrics endpoint ----------

@app.route("/metrics")
def metrics():
    """
    Expose Prometheus metrics.
    """
    data = generate_latest()
    return Response(data, mimetype=CONTENT_TYPE_LATEST)


# ---------- Database helpers ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db:
        db.close()

def init_db(): #changed the db to include due_date and category
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            text      TEXT NOT NULL,
            done      INTEGER NOT NULL DEFAULT 0,
            due_date  TEXT,
            category  TEXT
        );
    """)
    db.commit()

# ---------- Page route (frontend) ----------
@app.route("/")
def home():
    # Renders templates/index.html
    return render_template("index.html", title="To-Do List")

# ---------- REST API ----------
@app.get("/api/todos") #changed to include due_date and category
def list_todos():
    rows = get_db().execute(
        "SELECT id, text, done, due_date, category FROM todos ORDER BY id DESC"
    ).fetchall()
    return jsonify([
        {
            "id": r["id"],
            "text": r["text"],
            "done": bool(r["done"]),
            "due_date": r["due_date"],
            "category": r["category"],
        }
        for r in rows
    ])

@app.post("/api/todos") #changed to include due_date and category
def add_todo():
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "text required"}), 400

    due_date = data.get("due_date")   # expect "YYYY-MM-DD" or None
    category = data.get("category")   # e.g. "school", "work", "personal"

    db = get_db()
    cur = db.execute(
        "INSERT INTO todos(text, due_date, category) VALUES (?, ?, ?)",
        (text, due_date, category),
    )
    db.commit()
    return jsonify({
        "id": cur.lastrowid,
        "text": text,
        "done": False,
        "due_date": due_date,
        "category": category,
    }), 201

@app.patch("/api/todos/<int:todo_id>")
def update_todo(todo_id):
    data = request.get_json() or {}

    if "done" in data:
        get_db().execute(
            "UPDATE todos SET done=? WHERE id=?",
            (1 if data["done"] else 0, todo_id),
        )

    if "text" in data:
        new_text = data["text"].strip()
        if new_text:
            get_db().execute(
                "UPDATE todos SET text=? WHERE id=?",
                (new_text, todo_id),
            )

    if "due_date" in data:
        get_db().execute(
            "UPDATE todos SET due_date=? WHERE id=?",
            (data["due_date"], todo_id),
        )

    if "category" in data:
        get_db().execute(
            "UPDATE todos SET category=? WHERE id=?",
            (data["category"], todo_id),
        )

    get_db().commit()
    row = get_db().execute(
        "SELECT id, text, done, due_date, category FROM todos WHERE id=?",
        (todo_id,),
    ).fetchone()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify({
        "id": row["id"],
        "text": row["text"],
        "done": bool(row["done"]),
        "due_date": row["due_date"],
        "category": row["category"],
    })

@app.delete("/api/todos/<int:todo_id>")
def delete_todo(todo_id):
    get_db().execute("DELETE FROM todos WHERE id=?", (todo_id,))
    get_db().commit()
    return "", 204

import os

if __name__ == "__main__":
    with app.app_context():
        init_db()
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=False, host="0.0.0.0", port=port)
