from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import random
import string
from datetime import datetime, timedelta

app = Flask(__name__)

DATABASE_URL = "postgresql://bot_database_2lmf_user:JS732kEmaD8szWfLbfcX6C1xVj7bxcC9@dpg-d4v5o2umcj7s73dg52u0-a.oregon-postgres.render.com/bot_database_2lmf"

def db():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def create_table():
    conn = db()
    cur = conn.cursor()
    # Adjust table to match your existing structure if needed
    cur.execute("""
    CREATE TABLE IF NOT EXISTS keys (
        key TEXT UNIQUE NOT NULL,
        expires TIMESTAMP NOT NULL,
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    cur.execute("DELETE FROM keys WHERE expires < NOW()")
    conn.commit()
    cur.close()
    conn.close()

def get_friendly_expiration(expires):
    delta = expires - datetime.now()
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
            "INSERT INTO keys (key, expires) VALUES (%s, %s)",
            (key, expires)
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("dashboard"))

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT key, expires, created FROM keys ORDER BY created DESC")
    keys = cur.fetchall()
    cur.close()
    conn.close()

    # Add index for display and format expiration
    keys = [(i+1, k[0], k[1], get_friendly_expiration(k[1])) for i, k in enumerate(keys)]

    return render_template("dashboard.html", keys=keys)

# ================= DELETE KEY =================
@app.route("/delete/<key>")
def delete_key(key):
    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM keys WHERE key=%s", (key,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
