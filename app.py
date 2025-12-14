from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import random
import string
from datetime import datetime, timedelta

app = Flask(__name__)

DATABASE_URL = "postgresql://bot_database_2lmf_user:JS732kEmaD8szWfLbfcX6C1xVj7bxcC9@dpg-d4v5o2umcj7s73dg52u0-a.oregon-postgres.render.com/bot_database_2lmf"

def db():
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    return conn

def create_table():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS keys (
        id SERIAL PRIMARY KEY,
        key TEXT UNIQUE NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def generate_key():
    return "KEY-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))

def delete_expired_keys():
    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM keys WHERE expires_at < NOW()")
    conn.commit()
    cur.close()
    conn.close()

def get_friendly_expiration(expires_at):
    delta = expires_at - datetime.now()
    days = delta.days
    if days < 0:
        return "Expired"
    elif days == 0:
        return "Today"
    else:
        return f"{days} day(s) left"

# ================= DASHBOARD =================
@app.route("/", methods=["GET", "POST"])
def dashboard():
    create_table()
    delete_expired_keys()

    if request.method == "POST":
        try:
            days = int(request.form["days"])
        except ValueError:
            days = 1  # default 1 day if invalid
        key = generate_key()
        expires = datetime.now() + timedelta(days=days)

        conn = db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO keys (key, expires_at) VALUES (%s, %s)",
            (key, expires)
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("dashboard"))

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT id, key, expires_at FROM keys ORDER BY created_at DESC")
    keys = cur.fetchall()
    cur.close()
    conn.close()

    # Format expiration
    keys = [(k[0], k[1], k[2], get_friendly_expiration(k[2])) for k in keys]

    return render_template("dashboard.html", keys=keys)

# ================= DELETE KEY =================
@app.route("/delete/<int:key_id>")
def delete_key(key_id):
    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM keys WHERE id=%s", (key_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)