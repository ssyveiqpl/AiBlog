import sqlite3
import functools
import os
import uuid
import secrets
import zipfile
import io
import re
from pathlib import Path
from datetime import datetime
from xml.sax.saxutils import escape as xml_escape

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, g, send_from_directory, Response, jsonify, send_file
)
from markdown import markdown
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 86400 * 7
app.config["TESTING"] = os.environ.get("FLASK_TESTING") == "1"

DATABASE = Path(__file__).parent / "blog.db"
UPLOAD_FOLDER = Path(__file__).parent / "static" / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}
POSTS_PER_PAGE = 10
MESSAGES_PER_PAGE = 50

# In-memory pageview buffer
_pageview_buffer = []


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
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
        tags TEXT DEFAULT '',
        category TEXT DEFAULT '',
        cover_image TEXT DEFAULT '',
        status TEXT DEFAULT 'published',
        series_id INTEGER DEFAULT NULL,
        created_at TEXT NOT NULL
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        content TEXT NOT NULL,
        approved INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (post_id) REFERENCES posts(id)
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
    db.execute("""CREATE TABLE IF NOT EXISTS friend_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        url TEXT NOT NULL,
        description TEXT DEFAULT ''
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS pageviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER DEFAULT 0,
        date TEXT NOT NULL,
        count INTEGER DEFAULT 1
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS series (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        created_at TEXT NOT NULL
    )""")
    # Migrations for new columns
    for col in ("category", "cover_image", "status", "series_id"):
        try:
            db.execute(f"ALTER TABLE posts ADD COLUMN {col} TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass
    try:
        db.execute("ALTER TABLE comments ADD COLUMN approved INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    # Indexes
    for idx_sql in [
        "CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status)",
        "CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_pageviews_post_date ON pageviews(post_id, date)",
    ]:
        try:
            db.execute(idx_sql)
        except sqlite3.OperationalError:
            pass
    # FTS5
    try:
        db.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS posts_fts USING fts5(
            title, content, tags, content=posts, content_rowid=id
        )""")
        db.execute("""INSERT OR IGNORE INTO posts_fts(rowid, title, content, tags)
            SELECT id, title, content, tags FROM posts""")
    except sqlite3.OperationalError:
        pass
    # Default password
    if not db.execute("SELECT 1 FROM settings WHERE key='password'").fetchone():
        db.execute("INSERT INTO settings (key, value) VALUES (?, ?)",
                   ("password", generate_password_hash("admin123")))
    db.commit()
    db.close()


def rebuild_fts():
    db = get_db()
    try:
        db.execute("INSERT INTO posts_fts(posts_fts) VALUES('rebuild')")
        db.commit()
    except sqlite3.OperationalError:
        pass


def login_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def csrf_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if request.method == "POST":
            token = request.form.get("csrf_token")
            if not token or token != session.get("csrf_token"):
                flash("安全验证失败，请重试")
                return redirect(request.referrer or url_for("index"))
        return f(*args, **kwargs)
    return wrapper


def render_md(text):
    return markdown(text, extensions=["fenced_code", "codehilite"])


def allowed_file(name):
    return "." in name and name.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_all_categories():
    db = get_db()
    rows = db.execute(
        "SELECT DISTINCT category FROM posts WHERE category != '' AND status='published' ORDER BY category"
    ).fetchall()
    return [r["category"] for r in rows]


def get_all_tags():
    db = get_db()
    rows = db.execute("SELECT DISTINCT tags FROM posts WHERE tags != '' AND status='published'").fetchall()
    tag_set = set()
    for row in rows:
        for t in row["tags"].split(","):
            t = t.strip()
            if t:
                tag_set.add(t)
    return sorted(tag_set)


def record_pageview(post_id=0):
    _pageview_buffer.append((post_id, datetime.now().strftime("%Y-%m-%d")))


def flush_pageviews():
    if not _pageview_buffer:
        return
    db = get_db()
    for post_id, date in _pageview_buffer:
        row = db.execute(
            "SELECT id FROM pageviews WHERE post_id=? AND date=?", (post_id, date)
        ).fetchone()
        if row:
            db.execute("UPDATE pageviews SET count=count+1 WHERE id=?", (row["id"],))
        else:
            db.execute("INSERT INTO pageviews (post_id, date, count) VALUES (?, ?, 1)", (post_id, date))
    db.commit()
    _pageview_buffer.clear()


@app.teardown_appcontext
def flush_pv(_e=None):
    if _pageview_buffer:
        try:
            flush_pageviews()
        except Exception:
            pass


def get_stats():
    db = get_db()
    row = db.execute("""SELECT
        (SELECT COUNT(*) FROM posts WHERE status='published') as posts,
        (SELECT COUNT(*) FROM posts WHERE status='draft') as drafts,
        (SELECT COUNT(*) FROM comments) as comments,
        (SELECT COUNT(*) FROM comments WHERE approved=0) as pending_comments,
        (SELECT COUNT(*) FROM messages) as messages,
        (SELECT COALESCE(SUM(count),0) FROM pageviews WHERE post_id!=0) as views
    """).fetchone()
    return dict(row)


def get_series_list():
    db = get_db()
    return db.execute("SELECT * FROM series ORDER BY name").fetchall()


# ─── CSRF token injection ───
@app.before_request
def inject_csrf():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)


# ─── Security headers ───
@app.after_request
def add_security_headers(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Content-Security-Policy",
        "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https:; font-src https://cdnjs.cloudflare.com;")
    return resp


# ─── Error handlers ───
@app.errorhandler(404)
def not_found(_e):
    return render_template("error.html", code=404, message="页面不存在"), 404


@app.errorhandler(500)
def server_error(_e):
    return render_template("error.html", code=500, message="服务器内部错误"), 500


# ─── Index ───
@app.route("/")
def index():
    db = get_db()
    posts = db.execute(
        "SELECT id, title, tags, category, cover_image, created_at FROM posts WHERE status='published' ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    return render_template("index.html", posts=posts)


# ─── Articles with search, tag filter, category filter & pagination ───
@app.route("/articles")
def articles():
    db = get_db()
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "").strip()
    tag = request.args.get("tag", "").strip()
    cat = request.args.get("cat", "").strip()

    where_clauses = ["status='published'"]
    params = []

    if q:
        like = f"%{q}%"
        where_clauses.append("(title LIKE ? OR content LIKE ?)")
        params.extend([like, like])
    if tag:
        where_clauses.append("tags LIKE ?")
        params.append(f"%{tag}%")
    if cat:
        where_clauses.append("category=?")
        params.append(cat)

    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    count = db.execute(f"SELECT COUNT(*) FROM posts{where_sql}", params).fetchone()[0]
    total_pages = max(1, (count + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE)
    page = min(page, total_pages)
    offset = (page - 1) * POSTS_PER_PAGE

    posts = db.execute(
        f"SELECT id, title, tags, category, cover_image, created_at FROM posts{where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params + [POSTS_PER_PAGE, offset],
    ).fetchall()

    tag_set = get_all_tags()
    categories = get_all_categories()

    return render_template(
        "articles.html", posts=posts, count=count,
        tags=tag_set, q=q, active_tag=tag,
        categories=categories, active_cat=cat,
        page=page, total_pages=total_pages,
    )


# ─── Search via FTS5 ───
@app.route("/search")
def search():
    db = get_db()
    q = request.args.get("q", "").strip()
    if not q:
        return redirect(url_for("articles"))
    try:
        rows = db.execute(
            "SELECT p.id, p.title, p.tags, p.category, p.cover_image, p.created_at "
            "FROM posts_fts f JOIN posts p ON f.rowid=p.id "
            "WHERE posts_fts MATCH ? AND p.status='published' ORDER BY rank LIMIT 50",
            (q,)
        ).fetchall()
    except sqlite3.OperationalError:
        like = f"%{q}%"
        rows = db.execute(
            "SELECT id, title, tags, category, cover_image, created_at FROM posts "
            "WHERE status='published' AND (title LIKE ? OR content LIKE ?) ORDER BY created_at DESC LIMIT 50",
            (like, like)
        ).fetchall()
    return render_template("articles.html", posts=rows, count=len(rows),
                           tags=get_all_tags(), categories=get_all_categories(),
                           q=q, active_tag="", active_cat="", page=1, total_pages=1)


# ─── Categories page ───
@app.route("/categories")
def categories():
    db = get_db()
    cats = db.execute(
        "SELECT category, COUNT(*) as cnt FROM posts WHERE category != '' AND status='published' GROUP BY category ORDER BY category"
    ).fetchall()
    # Single query for all posts grouped by category
    all_posts = db.execute(
        "SELECT id, title, category, created_at FROM posts WHERE category != '' AND status='published' ORDER BY created_at DESC"
    ).fetchall()
    posts_by_cat = {}
    for p in all_posts:
        posts_by_cat.setdefault(p["category"], []).append(p)
    return render_template("categories.html", categories=cats, posts_by_cat=posts_by_cat)


# ─── Archive ───
@app.route("/archive")
def archive():
    db = get_db()
    rows = db.execute(
        "SELECT id, title, created_at FROM posts WHERE status='published' ORDER BY created_at DESC"
    ).fetchall()
    archives = {}
    for r in rows:
        ym = r["created_at"][:7]
        archives.setdefault(ym, []).append(r)
    sorted_yms = sorted(archives.keys(), reverse=True)
    return render_template("archive.html", archives=archives, sorted_yms=sorted_yms)


# ─── Post detail with comments ───
@app.route("/post/<int:post_id>")
def post(post_id):
    record_pageview(post_id)
    db = get_db()
    p = db.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
    if not p:
        flash("文章不存在")
        return redirect(url_for("index"))
    if p["status"] == "draft" and not session.get("logged_in"):
        flash("文章不存在")
        return redirect(url_for("index"))
    comments = db.execute(
        "SELECT * FROM comments WHERE post_id=? AND approved=1 ORDER BY created_at ASC", (post_id,)
    ).fetchall()
    # related posts by same category or tags
    related = []
    if p["category"] or p["tags"]:
        rel_clauses = ["status='published' AND id != ?"]
        rel_params = [post_id]
        if p["category"]:
            rel_clauses.append("category=?")
            rel_params.append(p["category"])
        if p["tags"]:
            for t in p["tags"].split(","):
                t = t.strip()
                if t:
                    rel_clauses.append("tags LIKE ?")
                    rel_params.append(f"%{t}%")
        rel_sql = "SELECT id, title, created_at FROM posts WHERE " + " OR ".join(
            [f"({c})" for c in rel_clauses]
        ) + " ORDER BY created_at DESC LIMIT 5"
        try:
            related = db.execute(rel_sql, rel_params).fetchall()
        except Exception:
            related = []
    # series info
    series = None
    series_posts = []
    if p["series_id"]:
        series = db.execute("SELECT * FROM series WHERE id=?", (p["series_id"],)).fetchone()
        if series:
            series_posts = db.execute(
                "SELECT id, title, created_at FROM posts WHERE series_id=? AND status='published' ORDER BY created_at ASC",
                (p["series_id"],)
            ).fetchall()
    # reading time
    word_count = len(p["content"].split())
    reading_time = max(1, round(word_count / 200))
    return render_template(
        "post.html", post=p, content_html=render_md(p["content"]),
        comments=comments, related=related, series=series, series_posts=series_posts,
        reading_time=reading_time,
    )


# ─── Comment ───
@app.route("/post/<int:post_id>/comment", methods=["POST"])
@csrf_required
def add_comment(post_id):
    db = get_db()
    p = db.execute("SELECT 1 FROM posts WHERE id=?", (post_id,)).fetchone()
    if not p:
        flash("文章不存在")
        return redirect(url_for("index"))
    name = request.form.get("name", "").strip()
    content = request.form.get("content", "").strip()
    if not name or not content:
        flash("姓名和内容不能为空")
    else:
        db.execute(
            "INSERT INTO comments (post_id, name, content, approved, created_at) VALUES (?, ?, ?, 0, ?)",
            (post_id, name, content, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        db.commit()
        flash("评论成功，等待审核")
    return redirect(url_for("post", post_id=post_id))


# ─── RSS Feed ───
@app.route("/feed")
def rss_feed():
    db = get_db()
    posts = db.execute(
        "SELECT id, title, content, created_at FROM posts WHERE status='published' ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    site_url = request.url_root.rstrip("/")
    items = []
    for p in posts:
        items.append(f"""    <item>
      <title>{xml_escape(p['title'])}</title>
      <link>{site_url}/post/{p['id']}</link>
      <description><![CDATA[{render_md(p['content'])}]]></description>
      <pubDate>{xml_escape(p['created_at'])}</pubDate>
      <guid>{site_url}/post/{p['id']}</guid>
    </item>""")
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>AI探索笔记</title>
    <link>{site_url}</link>
    <description>记录人工智能、机器学习与前沿技术的思考、实践与发现</description>
    <language>zh-CN</language>
    {"\n".join(items)}
  </channel>
</rss>"""
    return Response(xml, mimetype="application/xml")


# ─── Sitemap ───
@app.route("/sitemap.xml")
def sitemap():
    db = get_db()
    posts = db.execute(
        "SELECT id, created_at FROM posts WHERE status='published' ORDER BY created_at DESC"
    ).fetchall()
    site_url = request.url_root.rstrip("/")
    urls = [f"""  <url>
    <loc>{xml_escape(site_url)}/</loc>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{xml_escape(site_url)}/articles</loc>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{xml_escape(site_url)}/archive</loc>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>{xml_escape(site_url)}/categories</loc>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>{xml_escape(site_url)}/projects</loc>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>{xml_escape(site_url)}/message</loc>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>{xml_escape(site_url)}/about</loc>
    <priority>0.6</priority>
  </url>"""]
    for p in posts:
        urls.append(f"""  <url>
    <loc>{xml_escape(site_url)}/post/{p['id']}</loc>
    <lastmod>{xml_escape(p['created_at'])}</lastmod>
    <priority>0.8</priority>
  </url>""")
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{"\n".join(urls)}
</urlset>"""
    return Response(xml, mimetype="application/xml")


# ─── Message ───
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
    page = request.args.get("page", 1, type=int)
    count = db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    total_pages = max(1, (count + MESSAGES_PER_PAGE - 1) // MESSAGES_PER_PAGE)
    page = min(page, total_pages)
    offset = (page - 1) * MESSAGES_PER_PAGE
    messages = db.execute(
        "SELECT * FROM messages ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (MESSAGES_PER_PAGE, offset)
    ).fetchall()
    return render_template("message.html", messages=messages, page=page, total_pages=total_pages)


# ─── Projects ───
@app.route("/projects")
def projects():
    return render_template("projects.html")


# ─── About ───
@app.route("/about")
def about():
    db = get_db()
    links = db.execute("SELECT * FROM friend_links ORDER BY id").fetchall()
    return render_template("about.html", links=links)


# ─── Friend Links page ───
@app.route("/links")
def friend_links():
    db = get_db()
    links = db.execute("SELECT * FROM friend_links ORDER BY id").fetchall()
    return render_template("links.html", links=links)


# ─── Login ───
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db()
        pw = db.execute("SELECT value FROM settings WHERE key='password'").fetchone()["value"]
        if check_password_hash(pw, request.form["password"]):
            session["logged_in"] = True
            session.permanent = True
            return redirect(url_for("admin"))
        flash("密码错误")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("index"))


# ─── Admin ───
@app.route("/admin")
@login_required
def admin():
    db = get_db()
    posts = db.execute(
        "SELECT id, title, tags, category, cover_image, status, created_at FROM posts ORDER BY created_at DESC"
    ).fetchall()
    stats = get_stats()
    return render_template("admin.html", posts=posts, stats=stats)


# ─── Create post ───
@app.route("/create", methods=["GET", "POST"])
@login_required
@csrf_required
def create():
    if request.method == "POST":
        title = request.form["title"].strip()
        content = request.form["content"].strip()
        tags = request.form.get("tags", "").strip()
        category = request.form.get("category", "").strip()
        cover_image = request.form.get("cover_image", "").strip()
        series_id = request.form.get("series_id", type=int)
        status = request.form.get("status", "published")
        if not title or not content:
            flash("标题和内容不能为空")
            return render_template("create.html", series_list=get_series_list())
        db = get_db()
        db.execute(
            "INSERT INTO posts (title, content, tags, category, cover_image, status, series_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (title, content, tags, category, cover_image, status, series_id, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        db.commit()
        rebuild_fts()
        flash("文章发布成功")
        return redirect(url_for("admin"))
    return render_template("create.html", series_list=get_series_list())


# ─── Edit post ───
@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
@csrf_required
def edit(post_id):
    db = get_db()
    p = db.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
    if not p:
        flash("文章不存在")
        return redirect(url_for("admin"))
    if request.method == "POST":
        title = request.form["title"].strip()
        content = request.form["content"].strip()
        tags = request.form.get("tags", "").strip()
        category = request.form.get("category", "").strip()
        cover_image = request.form.get("cover_image", "").strip()
        series_id = request.form.get("series_id", type=int)
        status = request.form.get("status", "published")
        if not title or not content:
            flash("标题和内容不能为空")
            return render_template("edit.html", post=p, series_list=get_series_list())
        db.execute(
            "UPDATE posts SET title=?, content=?, tags=?, category=?, cover_image=?, status=?, series_id=? WHERE id=?",
            (title, content, tags, category, cover_image, status, series_id, post_id),
        )
        db.commit()
        rebuild_fts()
        flash("文章更新成功")
        return redirect(url_for("admin"))
    return render_template("edit.html", post=p, series_list=get_series_list())


# ─── Delete post ───
@app.route("/delete/<int:post_id>", methods=["POST"])
@login_required
@csrf_required
def delete(post_id):
    db = get_db()
    db.execute("DELETE FROM comments WHERE post_id=?", (post_id,))
    db.execute("DELETE FROM posts WHERE id=?", (post_id,))
    db.commit()
    rebuild_fts()
    flash("文章已删除")
    return redirect(url_for("admin"))


# ─── Change password ───
@app.route("/change-password", methods=["GET", "POST"])
@login_required
@csrf_required
def change_password():
    if request.method == "POST":
        old = request.form["old_password"]
        new = request.form["new_password"].strip()
        if not new:
            flash("新密码不能为空")
            return render_template("change_password.html")
        db = get_db()
        pw = db.execute("SELECT value FROM settings WHERE key='password'").fetchone()["value"]
        if not check_password_hash(pw, old):
            flash("旧密码错误")
            return render_template("change_password.html")
        db.execute("UPDATE settings SET value=? WHERE key='password'", (generate_password_hash(new),))
        db.commit()
        flash("密码修改成功")
        return redirect(url_for("admin"))
    return render_template("change_password.html")


# ─── Admin: Friend Links ───
@app.route("/admin/links", methods=["GET", "POST"])
@login_required
@csrf_required
def admin_links():
    db = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        url = request.form.get("url", "").strip()
        desc = request.form.get("description", "").strip()
        link_id = request.form.get("id")
        if not name or not url:
            flash("名称和URL不能为空")
        elif link_id:
            db.execute("UPDATE friend_links SET name=?, url=?, description=? WHERE id=?", (name, url, desc, link_id))
            db.commit()
            flash("友链已更新")
        else:
            db.execute("INSERT INTO friend_links (name, url, description) VALUES (?, ?, ?)", (name, url, desc))
            db.commit()
            flash("友链已添加")
        return redirect(url_for("admin_links"))
    edit_id = request.args.get("edit", type=int)
    edit_link = None
    if edit_id:
        edit_link = db.execute("SELECT * FROM friend_links WHERE id=?", (edit_id,)).fetchone()
    links = db.execute("SELECT * FROM friend_links ORDER BY id").fetchall()
    return render_template("admin_links.html", links=links, edit_link=edit_link)


@app.route("/admin/links/delete/<int:link_id>", methods=["POST"])
@login_required
@csrf_required
def delete_link(link_id):
    db = get_db()
    db.execute("DELETE FROM friend_links WHERE id=?", (link_id,))
    db.commit()
    flash("友链已删除")
    return redirect(url_for("admin_links"))


# ─── Admin: Comments ───
@app.route("/admin/comments")
@login_required
def admin_comments():
    db = get_db()
    pending = db.execute(
        "SELECT c.*, p.title as post_title FROM comments c JOIN posts p ON c.post_id=p.id WHERE c.approved=0 ORDER BY c.created_at DESC"
    ).fetchall()
    approved = db.execute(
        "SELECT c.*, p.title as post_title FROM comments c JOIN posts p ON c.post_id=p.id WHERE c.approved=1 ORDER BY c.created_at DESC"
    ).fetchall()
    return render_template("admin_comments.html", pending=pending, approved=approved)


@app.route("/admin/comments/approve/<int:comment_id>", methods=["POST"])
@login_required
@csrf_required
def approve_comment(comment_id):
    db = get_db()
    db.execute("UPDATE comments SET approved=1 WHERE id=?", (comment_id,))
    db.commit()
    flash("评论已审核通过")
    return redirect(url_for("admin_comments"))


@app.route("/admin/comments/delete/<int:comment_id>", methods=["POST"])
@login_required
@csrf_required
def delete_comment(comment_id):
    db = get_db()
    db.execute("DELETE FROM comments WHERE id=?", (comment_id,))
    db.commit()
    flash("评论已删除")
    return redirect(url_for("admin_comments"))


# ─── Admin: Categories & Tags ───
@app.route("/admin/categories")
@login_required
def admin_categories():
    db = get_db()
    cats = db.execute(
        "SELECT category, COUNT(*) as cnt FROM posts WHERE category != '' GROUP BY category ORDER BY category"
    ).fetchall()
    rows = db.execute("SELECT DISTINCT tags FROM posts WHERE tags != ''").fetchall()
    tag_set = set()
    for row in rows:
        for t in row["tags"].split(","):
            t = t.strip()
            if t:
                tag_set.add(t)
    tags = sorted(tag_set)
    return render_template("admin_categories.html", categories=cats, tags=tags)


@app.route("/admin/categories/rename", methods=["POST"])
@login_required
@csrf_required
def rename_category():
    old = request.form.get("old", "").strip()
    new = request.form.get("new", "").strip()
    if old and new:
        db = get_db()
        db.execute("UPDATE posts SET category=? WHERE category=?", (new, old))
        db.commit()
        flash("分类已重命名")
    return redirect(url_for("admin_categories"))


# ─── Admin: Series ───
@app.route("/admin/series", methods=["GET", "POST"])
@login_required
@csrf_required
def admin_series():
    db = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        desc = request.form.get("description", "").strip()
        series_id = request.form.get("id", type=int)
        if not name:
            flash("系列名称不能为空")
        elif series_id:
            db.execute("UPDATE series SET name=?, description=? WHERE id=?", (name, desc, series_id))
            db.commit()
            flash("系列已更新")
        else:
            db.execute("INSERT INTO series (name, description, created_at) VALUES (?, ?, ?)",
                       (name, desc, datetime.now().strftime("%Y-%m-%d %H:%M")))
            db.commit()
            flash("系列已创建")
        return redirect(url_for("admin_series"))
    edit_id = request.args.get("edit", type=int)
    edit_series = None
    if edit_id:
        edit_series = db.execute("SELECT * FROM series WHERE id=?", (edit_id,)).fetchone()
    series_list = db.execute("SELECT s.*, (SELECT COUNT(*) FROM posts WHERE series_id=s.id) as post_count FROM series s ORDER BY s.name").fetchall()
    return render_template("admin_series.html", series_list=series_list, edit_series=edit_series)


@app.route("/admin/series/delete/<int:series_id>", methods=["POST"])
@login_required
@csrf_required
def delete_series(series_id):
    db = get_db()
    db.execute("UPDATE posts SET series_id=NULL WHERE series_id=?", (series_id,))
    db.execute("DELETE FROM series WHERE id=?", (series_id,))
    db.commit()
    flash("系列已删除")
    return redirect(url_for("admin_series"))


# ─── Admin: Stats ───
@app.route("/admin/stats")
@login_required
def admin_stats():
    db = get_db()
    stats = get_stats()
    daily_views = db.execute(
        "SELECT date, SUM(count) as total FROM pageviews WHERE post_id!=0 AND date >= date('now', '-30 days') GROUP BY date ORDER BY date"
    ).fetchall()
    top_posts = db.execute(
        "SELECT p.id, p.title, COALESCE(SUM(v.count), 0) as views FROM posts p LEFT JOIN pageviews v ON v.post_id=p.id GROUP BY p.id ORDER BY views DESC LIMIT 10"
    ).fetchall()
    max_views = max((d["total"] for d in daily_views), default=1)
    return render_template("admin_stats.html", stats=stats, daily_views=daily_views, top_posts=top_posts, max_views=max_views)


# ─── Image upload ───
@app.route("/upload", methods=["POST"])
@login_required
def upload_image():
    f = request.files.get("file")
    if not f or f.filename == "":
        return {"error": "请选择文件"}, 400
    if not allowed_file(f.filename):
        return {"error": "不支持的文件格式"}, 400
    ext = f.filename.rsplit(".", 1)[1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    f.save(str(UPLOAD_FOLDER / name))
    url = url_for("uploaded_file", filename=name)
    return {"url": url}


@app.route("/static/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ─── Export posts as Markdown ───
@app.route("/admin/export")
@login_required
def export_posts():
    db = get_db()
    posts = db.execute("SELECT * FROM posts ORDER BY created_at DESC").fetchall()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in posts:
            safe_title = re.sub(r'[\\/*?:"<>|]', "_", p["title"])[:80]
            filename = f"{p['created_at'][:10]}_{safe_title}.md"
            content = f"""---
title: {p['title']}
date: {p['created_at']}
category: {p['category']}
tags: {p['tags']}
status: {p['status']}
cover_image: {p['cover_image']}
---

{p['content']}
"""
            zf.writestr(filename, content.encode("utf-8"))
    buf.seek(0)
    return send_file(
        buf, mimetype="application/zip",
        as_attachment=True, download_name=f"blog_export_{datetime.now().strftime('%Y%m%d')}.zip"
    )


# ─── Import posts from Markdown ───
@app.route("/admin/import", methods=["GET", "POST"])
@login_required
@csrf_required
def import_posts():
    if request.method == "POST":
        f = request.files.get("file")
        if not f or f.filename == "":
            flash("请选择文件")
            return redirect(url_for("import_posts"))
        db = get_db()
        count = 0
        if f.filename.endswith(".zip"):
            with zipfile.ZipFile(f, "r") as zf:
                for name in zf.namelist():
                    if name.endswith(".md"):
                        content = zf.read(name).decode("utf-8", errors="replace")
                        if import_markdown_post(db, content):
                            count += 1
        elif f.filename.endswith(".md"):
            content = f.read().decode("utf-8", errors="replace")
            if import_markdown_post(db, content):
                count += 1
        db.commit()
        rebuild_fts()
        flash(f"成功导入 {count} 篇文章")
        return redirect(url_for("admin"))
    return render_template("import_export.html")


def import_markdown_post(db, content):
    title = ""
    category = ""
    tags = ""
    status = "published"
    cover_image = ""
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            front = parts[1]
            body = parts[2].strip()
            for line in front.strip().split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip().lower()
                    v = v.strip()
                    if k == "title":
                        title = v
                    elif k == "category":
                        category = v
                    elif k == "tags":
                        tags = v
                    elif k == "status":
                        status = v
                    elif k == "cover_image":
                        cover_image = v
    if not title:
        lines = body.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("# "):
                title = line[2:].strip()
                body = body.replace(line, "", 1)
                break
    if not title:
        return False
    body = body.strip()
    if not body:
        return False
    db.execute(
        "INSERT INTO posts (title, content, tags, category, cover_image, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (title, body, tags, category, cover_image, status, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    return True


if __name__ == "__main__":
    init_db()
    debug_mode = os.environ.get("FLASK_ENV") != "production"
    app.run(debug=debug_mode, port=5000, use_reloader=False)
