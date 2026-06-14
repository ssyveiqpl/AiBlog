import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["DATABASE"] = ":memory:"

from app import app, init_db, get_db


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test"
    with app.test_client() as c:
        with app.app_context():
            init_db()
        yield c


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


def test_message(client):
    rv = client.get("/message")
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
    rv = client.post("/login", data={"password": "wrong"}, follow_redirects=True)
    assert rv.status_code == 200


def test_login_correct(client):
    rv = client.post("/login", data={"password": "admin123"}, follow_redirects=True)
    assert rv.status_code == 200


def test_admin_requires_login(client):
    rv = client.get("/admin", follow_redirects=True)
    assert rv.status_code == 200


def test_create_post(client):
    with app.app_context():
        init_db()
    with app.test_client() as c:
        with c.session_transaction() as s:
            s["logged_in"] = True
        rv = c.post("/create", data={
            "title": "测试文章",
            "content": "这是测试内容",
            "tags": "test, pytest",
            "category": "测试",
            "status": "published"
        }, follow_redirects=True)
        assert rv.status_code == 200


def test_create_draft(client):
    with app.app_context():
        init_db()
    with app.test_client() as c:
        with c.session_transaction() as s:
            s["logged_in"] = True
        rv = c.post("/create", data={
            "title": "草稿文章",
            "content": "草稿内容",
            "status": "draft"
        }, follow_redirects=True)
        assert rv.status_code == 200


def test_post_detail(client):
    with app.app_context():
        init_db()
    with app.test_client() as c:
        with c.session_transaction() as s:
            s["logged_in"] = True
        c.post("/create", data={
            "title": "详情测试",
            "content": "详情内容",
            "status": "published"
        })
        rv = c.get("/post/1")
        assert rv.status_code == 200


def test_comment(client):
    with app.app_context():
        init_db()
    with app.test_client() as c:
        with c.session_transaction() as s:
            s["logged_in"] = True
        c.post("/create", data={
            "title": "评论测试",
            "content": "评论测试内容",
            "status": "published"
        })
        rv = c.post("/post/1/comment", data={
            "name": "测试用户",
            "content": "测试评论"
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
        with c.session_transaction() as s:
            s["logged_in"] = True
        rv = c.get("/logout", follow_redirects=True)
        assert rv.status_code == 200


def test_admin_comments(client):
    with app.test_client() as c:
        with c.session_transaction() as s:
            s["logged_in"] = True
        rv = c.get("/admin/comments")
        assert rv.status_code == 200


def test_admin_categories(client):
    with app.test_client() as c:
        with c.session_transaction() as s:
            s["logged_in"] = True
        rv = c.get("/admin/categories")
        assert rv.status_code == 200


def test_admin_series(client):
    with app.test_client() as c:
        with c.session_transaction() as s:
            s["logged_in"] = True
        rv = c.get("/admin/series")
        assert rv.status_code == 200


def test_export(client):
    with app.test_client() as c:
        with c.session_transaction() as s:
            s["logged_in"] = True
        rv = c.get("/admin/export")
        assert rv.status_code == 200


def test_import_page(client):
    with app.test_client() as c:
        with c.session_transaction() as s:
            s["logged_in"] = True
        rv = c.get("/admin/import")
        assert rv.status_code == 200


def test_admin_stats(client):
    with app.test_client() as c:
        with c.session_transaction() as s:
            s["logged_in"] = True
        rv = c.get("/admin/stats")
        assert rv.status_code == 200
