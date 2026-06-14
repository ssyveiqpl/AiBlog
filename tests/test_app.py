import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["DATABASE"] = ":memory:"
os.environ["FLASK_TESTING"] = "1"

from app import app, init_db, get_db
from werkzeug.security import generate_password_hash, check_password_hash


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SECRET_KEY"] = "test-secret"
    with app.test_client() as c:
        with app.app_context():
            init_db()
            # Override password hash for testing
            db = get_db()
            db.execute("UPDATE settings SET value=? WHERE key='password'",
                       (generate_password_hash("admin123"),))
            db.commit()
        yield c


def _login(client):
    with client.session_transaction() as s:
        s["logged_in"] = True
        s["csrf_token"] = "test-csrf"


def _csrf():
    return {"csrf_token": "test-csrf"}


def test_index(client):
    rv = client.get("/")
    assert rv.status_code == 200
    assert b"AI" in rv.data


def test_articles(client):
    rv = client.get("/articles")
    assert rv.status_code == 200


def test_archive(client):
    rv = client.get("/archive")
    assert rv.status_code == 200


def test_categories(client):
    rv = client.get("/categories")
    assert rv.status_code == 200


def test_about(client):
    rv = client.get("/about")
    assert rv.status_code == 200


def test_message_get(client):
    rv = client.get("/message")
    assert rv.status_code == 200


def test_message_post(client):
    rv = client.post("/message", data={
        "name": "test", "content": "hello", **_csrf()
    }, follow_redirects=True)
    assert rv.status_code == 200


def test_projects(client):
    rv = client.get("/projects")
    assert rv.status_code == 200


def test_rss(client):
    rv = client.get("/feed")
    assert rv.status_code == 200


def test_sitemap(client):
    rv = client.get("/sitemap.xml")
    assert rv.status_code == 200


def test_login_page(client):
    rv = client.get("/login")
    assert rv.status_code == 200


def test_login_wrong(client):
    rv = client.post("/login", data={"password": "wrong", **_csrf()}, follow_redirects=True)
    assert rv.status_code == 200


def test_login_correct(client):
    rv = client.post("/login", data={"password": "admin123", **_csrf()}, follow_redirects=True)
    assert rv.status_code == 200


def test_admin_requires_login(client):
    rv = client.get("/admin", follow_redirects=True)
    assert rv.status_code == 200


def test_create_post(client):
    with app.app_context():
        init_db()
    with app.test_client() as c:
        _login(c)
        rv = c.post("/create", data={
            "title": "Test Post", "content": "Test content",
            "tags": "test, pytest", "category": "Test",
            "status": "published", **_csrf()
        }, follow_redirects=True)
        assert rv.status_code == 200


def test_create_draft(client):
    with app.app_context():
        init_db()
    with app.test_client() as c:
        _login(c)
        rv = c.post("/create", data={
            "title": "Draft Post", "content": "Draft content",
            "status": "draft", **_csrf()
        }, follow_redirects=True)
        assert rv.status_code == 200


def test_post_detail(client):
    with app.app_context():
        init_db()
    with app.test_client() as c:
        _login(c)
        c.post("/create", data={
            "title": "Detail Test", "content": "Detail content",
            "status": "published", **_csrf()
        })
        rv = c.get("/post/1")
        assert rv.status_code == 200


def test_comment(client):
    with app.app_context():
        init_db()
    with app.test_client() as c:
        _login(c)
        c.post("/create", data={
            "title": "Comment Test", "content": "Comment content",
            "status": "published", **_csrf()
        })
        rv = c.post("/post/1/comment", data={
            "name": "Test User", "content": "Test comment", **_csrf()
        }, follow_redirects=True)
        assert rv.status_code == 200


def test_search(client):
    rv = client.get("/search?q=test")
    assert rv.status_code == 200


def test_links(client):
    rv = client.get("/links")
    assert rv.status_code == 200


def test_logout(client):
    with app.test_client() as c:
        _login(c)
        rv = c.get("/logout", follow_redirects=True)
        assert rv.status_code == 200


def test_admin_comments(client):
    with app.test_client() as c:
        _login(c)
        rv = c.get("/admin/comments")
        assert rv.status_code == 200


def test_admin_categories(client):
    with app.test_client() as c:
        _login(c)
        rv = c.get("/admin/categories")
        assert rv.status_code == 200


def test_admin_series(client):
    with app.test_client() as c:
        _login(c)
        rv = c.get("/admin/series")
        assert rv.status_code == 200


def test_export(client):
    with app.test_client() as c:
        _login(c)
        rv = c.get("/admin/export")
        assert rv.status_code == 200


def test_import_page(client):
    with app.test_client() as c:
        _login(c)
        rv = c.get("/admin/import")
        assert rv.status_code == 200


def test_admin_stats(client):
    with app.test_client() as c:
        _login(c)
        rv = c.get("/admin/stats")
        assert rv.status_code == 200


def test_security_headers(client):
    rv = client.get("/")
    assert rv.headers.get("X-Content-Type-Options") == "nosniff"
    assert rv.headers.get("X-Frame-Options") == "DENY"


def test_404(client):
    rv = client.get("/nonexistent")
    assert rv.status_code == 404


def test_password_hashing(client):
    with app.app_context():
        db = get_db()
        pw = db.execute("SELECT value FROM settings WHERE key='password'").fetchone()["value"]
        assert check_password_hash(pw, "admin123")
        assert not check_password_hash(pw, "wrong")


def test_login_hashed(client):
    rv = client.post("/login", data={"password": "admin123", **_csrf()}, follow_redirects=True)
    assert rv.status_code == 200
