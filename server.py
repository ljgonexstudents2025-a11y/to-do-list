from flask import Flask, request, jsonify, render_template, g
import sqlite3
from pathlib import Path

DB_PATH = Path("todos.db")
app = Flask(__name__)

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
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        );
    """)
    db.commit()

# ---------- Page route (frontend) ----------
@app.route("/")
def home():
    # Renders templates/index.html
    return render_template("index.html", title="To-Do List")

# ---------- REST API ----------
@app.get("/api/todos")
def list_todos():
    rows = get_db().execute("SELECT id, text, done FROM todos ORDER BY id DESC").fetchall()
    return jsonify([{"id": r["id"], "text": r["text"], "done": bool(r["done"])} for r in rows])

@app.post("/api/todos")
def add_todo():
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "text required"}), 400
    cur = get_db().execute("INSERT INTO todos(text) VALUES (?)", (text,))
    get_db().commit()
    return jsonify({"id": cur.lastrowid, "text": text, "done": False}), 201

@app.patch("/api/todos/<int:todo_id>")
def update_todo(todo_id):
    data = request.get_json() or {}
    if "done" in data:
        get_db().execute("UPDATE todos SET done=? WHERE id=?", (1 if data["done"] else 0, todo_id))
    if "text" in data:
        new_text = data["text"].strip()
        if new_text:
            get_db().execute("UPDATE todos SET text=? WHERE id=?", (new_text, todo_id))
    get_db().commit()
    row = get_db().execute("SELECT id, text, done FROM todos WHERE id=?", (todo_id,)).fetchone()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify({"id": row["id"], "text": row["text"], "done": bool(row["done"])})

@app.delete("/api/todos/<int:todo_id>")
def delete_todo(todo_id):
    get_db().execute("DELETE FROM todos WHERE id=?", (todo_id,))
    get_db().commit()
    return "", 204

if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True, port=5001)
