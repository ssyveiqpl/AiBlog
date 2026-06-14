"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-14
"""
from alembic import op
import sqlalchemy as sa


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE IF NOT EXISTS posts (
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
    op.execute("""CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        content TEXT NOT NULL,
        approved INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (post_id) REFERENCES posts(id)
    )""")
    op.execute("""CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )""")
    op.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    op.execute("""CREATE TABLE IF NOT EXISTS friend_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        url TEXT NOT NULL,
        description TEXT DEFAULT ''
    )""")
    op.execute("""CREATE TABLE IF NOT EXISTS pageviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER DEFAULT 0,
        date TEXT NOT NULL,
        count INTEGER DEFAULT 1
    )""")
    op.execute("""CREATE TABLE IF NOT EXISTS series (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        created_at TEXT NOT NULL
    )""")
    op.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS posts_fts USING fts5(
        title, content, tags, content=posts, content_rowid=id
    )""")
    op.execute("""INSERT OR IGNORE INTO posts_fts(rowid, title, content, tags)
        SELECT id, title, content, tags FROM posts""")


def downgrade():
    op.execute("DROP TABLE IF EXISTS posts_fts")
    op.execute("DROP TABLE IF EXISTS series")
    op.execute("DROP TABLE IF EXISTS pageviews")
    op.execute("DROP TABLE IF EXISTS friend_links")
    op.execute("DROP TABLE IF EXISTS messages")
    op.execute("DROP TABLE IF EXISTS settings")
    op.execute("DROP TABLE IF EXISTS comments")
    op.execute("DROP TABLE IF EXISTS posts")
