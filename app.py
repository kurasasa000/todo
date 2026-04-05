import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

# Vercel のサーバーレス環境では /tmp のみ書き込み可能
DB_PATH = '/tmp/todos.db' if os.environ.get('VERCEL') else os.path.join(os.path.dirname(__file__), 'todos.db')

# モジュールロード時にDB初期化（Vercel対応）
def _ensure_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            text      TEXT    NOT NULL,
            done      INTEGER NOT NULL DEFAULT 0,
            created_at TEXT   NOT NULL
        )
    """)
    conn.commit()
    conn.close()

_ensure_db()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            text      TEXT    NOT NULL,
            done      INTEGER NOT NULL DEFAULT 0,
            created_at TEXT   NOT NULL
        )
    """)
    conn.commit()
    conn.close()


@app.route('/')
def index():
    filter_mode = request.args.get('filter', 'all')
    conn = get_db()
    if filter_mode == 'active':
        rows = conn.execute("SELECT * FROM todos WHERE done=0 ORDER BY id DESC").fetchall()
    elif filter_mode == 'done':
        rows = conn.execute("SELECT * FROM todos WHERE done=1 ORDER BY id DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM todos ORDER BY id DESC").fetchall()
    total     = conn.execute("SELECT COUNT(*) FROM todos").fetchone()[0]
    remaining = conn.execute("SELECT COUNT(*) FROM todos WHERE done=0").fetchone()[0]
    conn.close()
    return render_template('index.html',
                           todos=rows,
                           filter_mode=filter_mode,
                           total=total,
                           remaining=remaining)


@app.route('/add', methods=['POST'])
def add():
    text = request.form.get('text', '').strip()
    if text:
        conn = get_db()
        conn.execute("INSERT INTO todos (text, created_at) VALUES (?, ?)",
                     (text, datetime.now().strftime('%Y-%m-%d %H:%M')))
        conn.commit()
        conn.close()
    return redirect(url_for('index', filter=request.form.get('filter', 'all')))


@app.route('/toggle/<int:todo_id>', methods=['POST'])
def toggle(todo_id):
    conn = get_db()
    conn.execute("UPDATE todos SET done = 1 - done WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index', filter=request.form.get('filter', 'all')))


@app.route('/delete/<int:todo_id>', methods=['POST'])
def delete(todo_id):
    conn = get_db()
    conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index', filter=request.form.get('filter', 'all')))


@app.route('/clear_done', methods=['POST'])
def clear_done():
    conn = get_db()
    conn.execute("DELETE FROM todos WHERE done=1")
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)
