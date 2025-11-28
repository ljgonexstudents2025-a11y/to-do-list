from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    g,
    Response,
    redirect,
    url_for,
    session,
)
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path
import time
from functools import wraps
import os

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

DB_PATH = Path("todos.db")

app = Flask(__name__)
app.secret_key = "change-me-to-something-random"  # change for production


# ---------- Auth helper ----------

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


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


def init_db():
    """
    Create tables if they don't exist (users + todos).
    This runs once at startup.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # users table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
        """
    )

    # todos table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS todos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            text      TEXT NOT NULL,
            done      INTEGER NOT NULL DEFAULT 0,
            due_date  TEXT,
            category  TEXT
        );
        """
    )

    conn.commit()
    conn.close()


# ---------- Landing + Auth routes ----------

@app.route("/")
def landing():
    """Starter page: Login or Sign Up."""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Welcome</title>
    </head>
    <body>
        <h1 style="color:black; margin:2rem;">Welcome to your To-Do List</h1>
        <div style="margin:2rem;">
            <a href="{url_for('login')}">
                <button style="padding:0.5rem 1rem; margin-right:1rem;">Login</button>
            </a>
            <a href="{url_for('signup')}">
                <button style="padding:0.5rem 1rem;">Sign Up</button>
            </a>
        </div>
    </body>
    </html>
    """


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            error_html = "<p style='color:red;'>Please fill in all fields.</p>"
        else:
            db = get_db()

            existing = db.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,),
            ).fetchone()

            if existing:
                error_html = "<p style='color:red;'>Username already taken.</p>"
            else:
                password_hash = generate_password_hash(password)
                db.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, password_hash),
                )
                db.commit()

                user = db.execute(
                    "SELECT id, username FROM users WHERE username = ?",
                    (username,),
                ).fetchone()

                session["user_id"] = user["id"]
                session["username"] = user["username"]

                # AFTER SIGNUP → go to main todo page
                return redirect(url_for("index"))
    else:
        error_html = ""

    # GET or POST with error -> show form inline
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Sign Up</title>
    </head>
    <body>
        <h1 style="color:black; margin:2rem;">SIGNUP PAGE</h1>
        {error_html}
        <form method="post" style="margin:2rem; color:black;">
            <label>
                Username:
                <input type="text" name="username" required>
            </label>
            <br><br>
            <label>
                Password:
                <input type="password" name="password" required>
            </label>
            <br><br>
            <button type="submit">Sign Up</button>
        </form>
        <p style="margin:2rem; color:black;">
            Already have an account?
            <a href="{url_for('login')}">Log in</a>
        </p>
        <p style="margin:2rem;">
            <a href="{url_for('landing')}">Back to start</a>
        </p>
    </body>
    </html>
    """


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            error_html = "<p style='color:red;'>Invalid username or password.</p>"
        else:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            # AFTER LOGIN → go to main todo page
            return redirect(url_for("index"))
    else:
        error_html = ""

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Login</title>
    </head>
    <body>
        <h1 style="color:black; margin:2rem;">LOGIN PAGE</h1>
        {error_html}
        <form method="post" style="margin:2rem; color:black;">
            <label>
                Username:
                <input type="text" name="username" required>
            </label>
            <br><br>
            <label>
                Password:
                <input type="password" name="password" required>
            </label>
            <br><br>
            <button type="submit">Login</button>
        </form>
        <p style="margin:2rem; color:black;">
            Don't have an account?
            <a href="{url_for('signup')}">Sign up</a>
        </p>
        <p style="margin:2rem;">
            <a href="{url_for('landing')}">Back to start</a>
        </p>
    </body>
    </html>
    """


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))  # back to start page


# ---------- Main To-Do page (index) ----------

@app.route("/index")
@login_required
def index():
    # Renders templates/index.html – only for logged-in users
    return render_template("index.html", title="To-Do List")

@app.route("/account")
@login_required
def account():
    # For now, just redirect to the main to-do page
    return redirect(url_for("index"))


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


# ---------- REST API (unchanged) ----------

@app.get("/api/todos")
def list_todos():
    rows = get_db().execute(
        "SELECT id, text, done, due_date, category FROM todos ORDER BY id DESC"
    ).fetchall()
    return jsonify(
        [
            {
                "id": r["id"],
                "text": r["text"],
                "done": bool(r["done"]),
                "due_date": r["due_date"],
                "category": r["category"],
            }
            for r in rows
        ]
    )


@app.post("/api/todos")
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
    return (
        jsonify(
            {
                "id": cur.lastrowid,
                "text": text,
                "done": False,
                "due_date": due_date,
                "category": category,
            }
        ),
        201,
    )


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
    return jsonify(
        {
            "id": row["id"],
            "text": row["text"],
            "done": bool(row["done"]),
            "due_date": row["due_date"],
            "category": row["category"],
        }
    )


@app.delete("/api/todos/<int:todo_id>")
def delete_todo(todo_id):
    get_db().execute("DELETE FROM todos WHERE id=?", (todo_id,))
    get_db().commit()
    return "", 204


# ---------- Main ----------

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)

