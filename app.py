import sqlite3
import functools
from pathlib import Path
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, g
)
from markdown import markdown

app = Flask(__name__)
app.secret_key = "your-secret-key-change-in-production"
DATABASE = Path(__file__).parent / "blog.db"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("""CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    if not db.execute("SELECT 1 FROM settings WHERE key='password'").fetchone():
        db.execute("INSERT INTO settings (key, value) VALUES ('password', 'admin123')")
    db.commit()
    db.close()


def login_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def render_md(text):
    return markdown(text, extensions=["fenced_code", "codehilite"])


@app.route("/articles")
def articles():
    db = get_db()
    posts = db.execute("SELECT id, title, created_at FROM posts ORDER BY created_at DESC").fetchall()
    count = db.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    return render_template("articles.html", posts=posts, count=count)


@app.route("/message", methods=["GET", "POST"])
def message():
    db = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        content = request.form.get("content", "").strip()
        if not name or not content:
            flash("姓名和内容不能为空")
        else:
            db.execute(
                "INSERT INTO messages (name, content, created_at) VALUES (?, ?, ?)",
                (name, content, datetime.now().strftime("%Y-%m-%d %H:%M")),
            )
            db.commit()
            flash("留言成功")
            return redirect(url_for("message"))
    messages = db.execute("SELECT * FROM messages ORDER BY created_at DESC").fetchall()
    return render_template("message.html", messages=messages)


@app.route("/projects")
def projects():
    return render_template("projects.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/")
def index():
    db = get_db()
    posts = db.execute("SELECT id, title, created_at FROM posts ORDER BY created_at DESC").fetchall()
    return render_template("index.html", posts=posts)


@app.route("/post/<int:post_id>")
def post(post_id):
    db = get_db()
    p = db.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
    if not p:
        flash("文章不存在")
        return redirect(url_for("index"))
    return render_template("post.html", post=p, content_html=render_md(p["content"]))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db()
        pw = db.execute("SELECT value FROM settings WHERE key='password'").fetchone()["value"]
        if request.form["password"] == pw:
            session["logged_in"] = True
            return redirect(url_for("admin"))
        flash("密码错误")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("index"))


@app.route("/admin")
@login_required
def admin():
    db = get_db()
    posts = db.execute("SELECT id, title, created_at FROM posts ORDER BY created_at DESC").fetchall()
    return render_template("admin.html", posts=posts)


@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        title = request.form["title"].strip()
        content = request.form["content"].strip()
        if not title or not content:
            flash("标题和内容不能为空")
            return render_template("create.html")
        db = get_db()
        db.execute(
            "INSERT INTO posts (title, content, created_at) VALUES (?, ?, ?)",
            (title, content, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        db.commit()
        flash("文章发布成功")
        return redirect(url_for("admin"))
    return render_template("create.html")


@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit(post_id):
    db = get_db()
    p = db.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
    if not p:
        flash("文章不存在")
        return redirect(url_for("admin"))
    if request.method == "POST":
        title = request.form["title"].strip()
        content = request.form["content"].strip()
        if not title or not content:
            flash("标题和内容不能为空")
            return render_template("edit.html", post=p)
        db.execute("UPDATE posts SET title=?, content=? WHERE id=?", (title, content, post_id))
        db.commit()
        flash("文章更新成功")
        return redirect(url_for("admin"))
    return render_template("edit.html", post=p)


@app.route("/delete/<int:post_id>", methods=["POST"])
@login_required
def delete(post_id):
    db = get_db()
    db.execute("DELETE FROM posts WHERE id=?", (post_id,))
    db.commit()
    flash("文章已删除")
    return redirect(url_for("admin"))


@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old = request.form["old_password"]
        new = request.form["new_password"].strip()
        if not new:
            flash("新密码不能为空")
            return render_template("change_password.html")
        db = get_db()
        pw = db.execute("SELECT value FROM settings WHERE key='password'").fetchone()["value"]
        if old != pw:
            flash("旧密码错误")
            return render_template("change_password.html")
        db.execute("UPDATE settings SET value=? WHERE key='password'", (new,))
        db.commit()
        flash("密码修改成功")
        return redirect(url_for("admin"))
    return render_template("change_password.html")


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000, use_reloader=False)
