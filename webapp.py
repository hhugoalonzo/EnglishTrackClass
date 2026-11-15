# webapp.py
import os
import sqlite3
from flask import Flask, request, redirect, render_template, url_for, flash, Response
import hmac
from config import DB_PATH

app = Flask(__name__)
app.secret_key =  os.environ.get("FLASK_SECRET")

# ---- Simple Basic Auth ----
WEB_USER = os.environ.get("WEB_USER", "admin")
WEB_PASS = os.environ.get("WEB_PASS")   # must be set in env; no default

if not WEB_PASS:
    raise RuntimeError("Set WEB_PASS environment variable before starting the app")


@app.before_request
def require_auth():
    auth = request.authorization
    ok = (
        auth is not None
        and hmac.compare_digest(auth.username or "", WEB_USER)
        and hmac.compare_digest(auth.password or "", WEB_PASS)
    )
    if not ok:
        return Response("Authentication required", 401,
                        {"WWW-Authenticate": 'Basic realm="English Tracker"'})

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_schema():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                class_number INTEGER NOT NULL,
                date_taken   TEXT NOT NULL,
                topic        TEXT,
                notes        TEXT,
                status       TEXT DEFAULT 'Pending'
            )
        """)
        conn.commit()

ensure_schema()

@app.get("/")
def index():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM classes ORDER BY class_number DESC"
        ).fetchall()
    return render_template("index.html", rows=rows)

@app.post("/add")
def add():
    try:
        cnum = int(request.form["class_number"])
    except (KeyError, ValueError):
        flash("Class number must be a number")
        return redirect(url_for("index"))

    dt = request.form.get("date_taken", "").strip()
    if not dt:
        flash("Date is required (YYYY-MM-DD)")
        return redirect(url_for("index"))

    with get_db() as conn:
        conn.execute(
            """INSERT INTO classes (class_number, date_taken, topic, notes, status)
               VALUES (?,?,?,?,?)""",
            (cnum, dt,
             request.form.get("topic", "").strip(),
             request.form.get("notes", "").strip(),
             request.form.get("status", "Pending")),
        )
        conn.commit()
    flash(f"Class #{cnum} added")
    return redirect(url_for("index"))

@app.post("/update/<int:cid>")
def update(cid):
    with get_db() as conn:
        conn.execute(
            """UPDATE classes SET topic=?, notes=?, status=? WHERE id=?""",
            (request.form.get("topic", "").strip(),
             request.form.get("notes", "").strip(),
             request.form.get("status", "Pending"),
             cid),
        )
        conn.commit()
    return redirect(url_for("index"))

@app.post("/delete/<int:cid>")
def delete(cid):
    with get_db() as conn:
        conn.execute("DELETE FROM classes WHERE id=?", (cid,))
        conn.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)