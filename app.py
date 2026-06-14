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

# ─── i18n ───
TRANSLATIONS = {
    "zh": {
        "site_name": "AI探索笔记",
        "site_desc": "记录人工智能、机器学习与前沿技术的思考、实践与发现",
        "home": "首页",
        "articles": "文章",
        "archive": "归档",
        "categories": "分类",
        "message": "留言",
        "about": "我的",
        "search": "搜索",
        "login": "登录",
        "logout": "退出",
        "admin": "管理",
        "rss": "RSS 订阅",
        "reading_mode": "护眼模式",
        "published": "已发布",
        "draft": "草稿",
        "scheduled": "定时",
        "reading_time": "{n} 分钟阅读",
        "views": "{n} 次阅读",
        "likes": "{n} 点赞",
        "no_articles": "还没有文章",
        "all": "全部",
        "search_placeholder": "搜索文章标题或内容...",
        "original_articles": "原创文章",
        "latest_posts": "最新文章",
        "likes_label": "点赞",
        "related": "相关推荐",
        "comments": "评论 ({n})",
        "leave_comment": "发表评论",
        "your_name": "你的名字",
        "write_comment": "写下你的评论...",
        "submit_comment": "提交评论",
        "reply": "回复",
        "cancel": "取消",
        "share": "分享",
        "read_more": "阅读全文 →",
        "back_home": "← 返回首页",
        "subscribe_rss": "RSS 订阅",
        "password_required": "此文章需要密码访问",
        "unlock": "解锁",
        "enter_password": "请输入文章密码",
        "tag": "标签",
        "category": "分类",
        "series": "系列",
        "current": "当前",
        "about_me": "关于我",
        "projects": "我的开源项目",
        "start_reading": "开始阅读",
        "related_articles": "相关推荐",
        "table_of_contents": "目录",
        "explore_ai": "探索 AI 世界无限可能",
        "profile_bio": "记录人工智能、机器学习与前沿技术的思考、实践与发现",
        "my_projects": "我的开源项目",
        "about_me_title": "关于我",
        "about_me_desc": "我是林良辉，一名AI研究员兼技术博主。专注于大语言模型、计算机视觉和智能体系统的研究与应用。",
        "view_details": "查看详情",
        "articles_desc": "探索人工智能与前沿技术的深度分析与独到见解",
        "search_results": "搜索结果",
        "no_data": "暂无数据",
        "name": "名称",
        "url": "网址",
        "description": "描述",
        "operation": "操作",
        "edit": "编辑",
        "delete": "删除",
        "confirm_delete": "确定删除？",
        "archive_title": "文章归档",
        "archive_desc": "按时间线浏览所有文章",
        "categories_title": "分类浏览",
        "categories_desc": "按分类浏览文章",
        "message_title": "留言板",
        "message_desc": "欢迎留下你的想法和建议",
        "message_name": "你的名字",
        "message_content": "写下你想说的话...",
        "submit_message": "提交留言",
        "prev_page": "« 上一页",
        "next_page": "下一页 »",
        "no_comments": "还没有评论",
        "reading": "次阅读",
        "min_read": "分钟阅读",
        "pinned": "置顶",
        "series_posts": "系列文章",
        "project_title": "我的开源项目",
        "project_desc": "以下是我参与和开发的一些开源项目",
        "password_error": "密码错误",
        "post_not_found": "文章不存在",
        "login_title": "管理登录",
        "login_password": "密码",
        "login_btn": "登录",
        "welcome": "欢迎来到 AI探索笔记",
        "welcome_msg": "这里是记录人工智能、机器学习与前沿技术的博客站点。欢迎阅读和交流！",
        "skills": "专业技能",
        "experience": "职业经历",
        "contact_me": "联系我",
        "access_pwd": "访问密码",
        "access_pwd_hint": "留空表示公开",
        "access_pwd_ph": "设置后需输入密码才能查看",
        "add": "添加",
        "add_link": "添加友链",
        "advanced_settings": "高级设置",
        "ann_content": "内容",
        "ann_content_ph": "公告内容",
        "ann_mgmt": "公告管理",
        "ann_title": "标题",
        "ann_title_ph": "公告标题",
        "approve": "通过",
        "approved": "已审核",
        "back_to_admin": "← 返回后台",
        "backup": "备份",
        "cat_mgmt": "分类管理",
        "cat_ph": "如 AI、Python、生活随笔",
        "cat_tag_mgmt": "分类与标签管理",
        "change_btn": "修改",
        "change_pwd": "修改密码",
        "change_pwd_title": "修改密码",
        "comment_mgmt": "评论管理",
        "confirm_delete_series": "确定删除？相关文章将取消归属",
        "content_col": "内容",
        "content_label": "内容",
        "cover_ph": "https://example.com/image.jpg 或留空",
        "cover_url": "封面图片 URL",
        "create": "创建",
        "create_series": "创建系列",
        "dashboard": "管理后台",
        "demo": "在线体验",
        "edit_ann": "编辑公告",
        "edit_article": "编辑文章",
        "edit_article_title": "编辑文章",
        "edit_link": "编辑友链",
        "edit_series": "编辑系列",
        "editor_ph": "支持 Markdown 语法",
        "error_desc": "抱歉，你访问的页面不存在或发生了错误。",
        "export_desc": "将所有文章导出为 Markdown 文件（ZIP 压缩包），包含 Front Matter 元数据。",
        "export_posts": "导出文章",
        "export_zip": "导出为 ZIP",
        "filter_all": "全部",
        "filter_research": "研究",
        "filter_tools": "工具",
        "friend_links": "友情链接",
        "friend_links_mgmt": "友情链接",
        "hot_articles": "热门文章",
        "import_btn": "导入",
        "import_desc": "支持导入单个 .md 文件或包含多篇 Markdown 的 .zip 压缩包。文件需包含 Front Matter（title/date/category/tags）或一级标题。",
        "import_export": "导入/导出",
        "import_export_title": "导入/导出",
        "import_posts": "导入文章",
        "link_mgmt": "友情链接管理",
        "links_desc": "优质站点推荐",
        "msg_mgmt": "留言管理",
        "new_name_ph": "新名称",
        "new_pwd": "新密码",
        "new_pwd_ph": "输入新密码",
        "no_announcements": "暂无公告",
        "no_category": "无",
        "no_categories": "暂无分类",
        "no_links": "暂无友情链接",
        "no_links_yet": "暂无友情链接",
        "no_messages": "暂无留言",
        "no_series": "暂无系列",
        "no_series_option": "无",
        "no_tags": "无",
        "no_tags_list": "暂无标签",
        "old_pwd": "旧密码",
        "old_pwd_ph": "输入旧密码",
        "optional": "选填",
        "pending_review": "待审核",
        "pin_post": "置顶文章",
        "post_col": "文章",
        "post_count": "文章数",
        "preview": "预览区域",
        "publish": "发布",
        "publish_ann": "发布公告",
        "publish_now": "直接发布",
        "publish_time": "发布时间",
        "recent_30d": "最近30天阅读趋势",
        "rename": "重命名",
        "restore_draft": "检测到未保存的草稿，是否恢复？",
        "save": "保存",
        "save_draft": "存为草稿",
        "schedule_publish": "定时发布",
        "select_file": "选择文件",
        "seo_desc": "SEO 描述",
        "seo_desc_ph": "自定义 meta description，留空自动取正文前200字",
        "seo_desc_ph_edit": "自定义 meta description",
        "seo_keywords": "SEO 关键词",
        "seo_keywords_ph": "用逗号分隔，如 AI, 机器学习, 深度学习",
        "seo_keywords_ph_edit": "用逗号分隔",
        "series_mgmt": "系列管理",
        "series_mgmt_title": "系列管理",
        "series_name_ph": "系列名称",
        "series_desc_ph": "系列描述",
        "share_facebook": "分享到 Facebook",
        "share_linkedin": "分享到 LinkedIn",
        "share_twitter": "分享到 Twitter",
        "share_weibo": "分享到微博",
        "short_desc_ph": "简短描述",
        "site_name_ph": "站点名称",
        "site_stats": "网站统计",
        "stats": "统计",
        "status": "状态",
        "support_md": "支持 Markdown",
        "tags_ph": "用逗号分隔，如 AI, Python, 深度学习",
        "time": "时间",
        "times_read": "次阅读",
        "title_col": "标题",
        "title_ph": "输入文章标题",
        "total_views": "总阅读",
        "update": "更新",
        "upload": "上传",
        "user_col": "用户",
        "views_col": "浏览",
        "write_article": "写文章",
        "write_new": "写新文章",
        "write_new_article": "写新文章",
        "zh_text": "中文",
        "email": "邮箱",
        "location": "位置",
        "top_papers": "顶级论文",
        "blog_readers": "博客读者",
    },
    "en": {
        "site_name": "AI Explorer Notes",
        "site_desc": "Thoughts, practices, and discoveries on AI, machine learning, and cutting-edge technologies",
        "home": "Home",
        "articles": "Articles",
        "archive": "Archive",
        "categories": "Categories",
        "message": "Messages",
        "about": "About",
        "search": "Search",
        "login": "Login",
        "logout": "Logout",
        "admin": "Admin",
        "rss": "RSS Feed",
        "reading_mode": "Reading Mode",
        "published": "Published",
        "draft": "Draft",
        "scheduled": "Scheduled",
        "reading_time": "{n} min read",
        "views": "{n} views",
        "likes": "{n} likes",
        "no_articles": "No articles yet",
        "all": "All",
        "search_placeholder": "Search articles...",
        "original_articles": "Original Articles",
        "latest_posts": "Latest Posts",
        "likes_label": "Likes",
        "related": "Related",
        "comments": "Comments ({n})",
        "leave_comment": "Leave a Comment",
        "your_name": "Your Name",
        "write_comment": "Write a comment...",
        "submit_comment": "Submit",
        "reply": "Reply",
        "cancel": "Cancel",
        "share": "Share",
        "read_more": "Read More →",
        "back_home": "← Back to Home",
        "subscribe_rss": "RSS Feed",
        "password_required": "This post requires a password",
        "unlock": "Unlock",
        "enter_password": "Enter password",
        "tag": "Tag",
        "category": "Category",
        "series": "Series",
        "current": "Current",
        "about_me": "About Me",
        "projects": "My Projects",
        "start_reading": "Start Reading",
        "related_articles": "Related Articles",
        "table_of_contents": "Table of Contents",
        "explore_ai": "Explore the Infinite Possibilities of AI",
        "profile_bio": "Thoughts, practices, and discoveries on AI, machine learning, and cutting-edge technologies",
        "my_projects": "My Open Source Projects",
        "about_me_title": "About Me",
        "about_me_desc": "I am Lin Lianghui, an AI researcher and tech blogger focused on LLMs, computer vision, and agent systems.",
        "view_details": "View Details",
        "articles_desc": "In-depth analysis and insights on AI and cutting-edge technologies",
        "search_results": "Search Results",
        "no_data": "No data",
        "name": "Name",
        "url": "URL",
        "description": "Description",
        "operation": "Actions",
        "edit": "Edit",
        "delete": "Delete",
        "confirm_delete": "Are you sure?",
        "archive_title": "Archive",
        "archive_desc": "Browse all articles by timeline",
        "categories_title": "Categories",
        "categories_desc": "Browse articles by category",
        "message_title": "Message Board",
        "message_desc": "Leave your thoughts and feedback",
        "message_name": "Your Name",
        "message_content": "Write something...",
        "submit_message": "Submit",
        "prev_page": "« Prev",
        "next_page": "Next »",
        "no_comments": "No comments yet",
        "reading": "reads",
        "min_read": "min read",
        "pinned": "Pinned",
        "series_posts": "Series Posts",
        "project_title": "Open Source Projects",
        "project_desc": "Here are some open source projects I've worked on",
        "password_error": "Wrong password",
        "post_not_found": "Post not found",
        "login_title": "Admin Login",
        "login_password": "Password",
        "login_btn": "Login",
        "welcome": "Welcome to AI Explorer Notes",
        "welcome_msg": "A blog about AI, machine learning, and cutting-edge technologies. Welcome!",
        "skills": "Skills",
        "experience": "Experience",
        "contact_me": "Contact Me",
        "access_pwd": "Access Password",
        "access_pwd_hint": "Leave empty for public",
        "access_pwd_ph": "Set a password to restrict access",
        "add": "Add",
        "add_link": "Add Link",
        "advanced_settings": "Advanced Settings",
        "ann_content": "Content",
        "ann_content_ph": "Announcement content",
        "ann_mgmt": "Announcements",
        "ann_title": "Title",
        "ann_title_ph": "Announcement title",
        "approve": "Approve",
        "approved": "Approved",
        "back_to_admin": "← Back to Admin",
        "backup": "Backup",
        "cat_mgmt": "Categories",
        "cat_ph": "e.g. AI, Python, Life",
        "cat_tag_mgmt": "Categories & Tags",
        "change_btn": "Change",
        "change_pwd": "Change Password",
        "change_pwd_title": "Change Password",
        "comment_mgmt": "Comments",
        "confirm_delete_series": "Delete? Posts in this series will be unlinked.",
        "content_col": "Content",
        "content_label": "Content",
        "cover_ph": "https://example.com/image.jpg or leave empty",
        "cover_url": "Cover Image URL",
        "create": "Create",
        "create_series": "Create Series",
        "dashboard": "Dashboard",
        "demo": "Live Demo",
        "edit_ann": "Edit Announcement",
        "edit_article": "Edit Article",
        "edit_article_title": "Edit Article",
        "edit_link": "Edit Link",
        "edit_series": "Edit Series",
        "editor_ph": "Markdown syntax supported",
        "error_desc": "Sorry, the page you requested does not exist or an error occurred.",
        "export_desc": "Export all posts as Markdown files (ZIP archive) with Front Matter metadata.",
        "export_posts": "Export Posts",
        "export_zip": "Download ZIP",
        "filter_all": "All",
        "filter_research": "Research",
        "filter_tools": "Tools",
        "friend_links_mgmt": "Friend Links",
        "hot_articles": "Hot Articles",
        "import_btn": "Import",
        "import_desc": "Import a single .md file or a .zip archive containing multiple Markdown files. Files must include Front Matter (title/date/category/tags) or an h1 heading.",
        "import_export": "Import/Export",
        "import_export_title": "Import/Export",
        "import_posts": "Import Posts",
        "link_mgmt": "Link Management",
        "links_desc": "Recommended Sites",
        "msg_mgmt": "Messages",
        "new_name_ph": "New name",
        "new_pwd": "New Password",
        "new_pwd_ph": "Enter new password",
        "no_announcements": "No announcements yet",
        "no_category": "None",
        "no_categories": "No categories yet",
        "no_links": "No links yet",
        "no_links_yet": "No links yet",
        "no_messages": "No messages yet",
        "no_series": "No series yet",
        "no_series_option": "None",
        "no_tags": "None",
        "no_tags_list": "No tags yet",
        "old_pwd": "Old Password",
        "old_pwd_ph": "Enter old password",
        "optional": "Optional",
        "pending_review": "Pending Review",
        "pin_post": "Pin Post",
        "post_col": "Post",
        "post_count": "Posts",
        "preview": "Preview",
        "publish": "Publish",
        "publish_ann": "Publish Announcement",
        "publish_now": "Publish Now",
        "publish_time": "Publish Time",
        "recent_30d": "Last 30 Days Trend",
        "rename": "Rename",
        "restore_draft": "Unsaved draft found. Restore?",
        "save": "Save",
        "save_draft": "Save as Draft",
        "schedule_publish": "Schedule",
        "select_file": "Select File",
        "seo_desc": "SEO Description",
        "seo_desc_ph": "Custom meta description; leave empty to auto-generate from content",
        "seo_desc_ph_edit": "Custom meta description",
        "seo_keywords": "SEO Keywords",
        "seo_keywords_ph": "Comma separated, e.g. AI, Machine Learning, Deep Learning",
        "seo_keywords_ph_edit": "Comma separated",
        "series_mgmt": "Series",
        "series_mgmt_title": "Series",
        "series_name_ph": "Series name",
        "series_desc_ph": "Series description",
        "share_facebook": "Share on Facebook",
        "share_linkedin": "Share on LinkedIn",
        "share_twitter": "Share on Twitter",
        "share_weibo": "Share on Weibo",
        "short_desc_ph": "Short description",
        "site_name_ph": "Site name",
        "site_stats": "Site Stats",
        "stats": "Stats",
        "status": "Status",
        "support_md": "Markdown supported",
        "tags_ph": "Comma separated, e.g. AI, Python, Deep Learning",
        "time": "Time",
        "times_read": "reads",
        "title_col": "Title",
        "title_ph": "Enter article title",
        "total_views": "Total Views",
        "update": "Update",
        "upload": "Upload",
        "user_col": "User",
        "views_col": "Views",
        "write_article": "Write Article",
        "write_new": "Write New",
        "write_new_article": "Write New Article",
        "zh_text": "中文",
        "friend_links": "Friends Links",
        "email": "Email",
        "location": "Location",
        "top_papers": "Top Papers",
        "blog_readers": "Blog Readers",
    },
}

def _t(key, **kwargs):
    lang = session.get("lang", "zh")
    text = TRANSLATIONS.get(lang, TRANSLATIONS["zh"]).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 86400 * 7
app.config["TESTING"] = os.environ.get("FLASK_TESTING") == "1"

DATABASE = Path(__file__).parent / "blog.db"
UPLOAD_FOLDER = Path(__file__).parent / "static" / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.jinja_env.globals["_t"] = _t
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
    db.execute("""CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        ip TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(post_id, ip)
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    # Migrations for new columns
    for col in ("category", "cover_image", "status", "series_id"):
        try:
            db.execute(f"ALTER TABLE posts ADD COLUMN {col} TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass
    for col in [
        ("pinned", "INTEGER DEFAULT 0"),
        ("scheduled_at", "TEXT DEFAULT NULL"),
        ("views", "INTEGER DEFAULT 0"),
        ("access_password", "TEXT DEFAULT ''"),
        ("seo_desc", "TEXT DEFAULT ''"),
        ("seo_keywords", "TEXT DEFAULT ''"),
    ]:
        try:
            db.execute(f"ALTER TABLE posts ADD COLUMN {col[0]} {col[1]}")
        except sqlite3.OperationalError:
            pass
    try:
        db.execute("ALTER TABLE comments ADD COLUMN approved INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        db.execute("ALTER TABLE comments ADD COLUMN parent_id INTEGER DEFAULT NULL")
    except sqlite3.OperationalError:
        pass
    try:
        db.execute("ALTER TABLE comments ADD COLUMN replied INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    # Indexes
    for idx_sql in [
        "CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status)",
        "CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_posts_pinned ON posts(pinned)",
        "CREATE INDEX IF NOT EXISTS idx_pageviews_post_date ON pageviews(post_id, date)",
        "CREATE INDEX IF NOT EXISTS idx_likes_post ON likes(post_id)",
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
    # Default announcements
    if not db.execute("SELECT 1 FROM announcements").fetchone():
        db.execute("INSERT INTO announcements (title, content, created_at) VALUES (?, ?, ?)",
                   ("欢迎来到 AI探索笔记", "这里是记录人工智能、机器学习与前沿技术的博客站点。欢迎阅读和交流！",
                    datetime.now().strftime("%Y-%m-%d %H:%M")))
    db.commit()
    db.close()


def publish_scheduled():
    """Auto-publish posts whose scheduled_at has passed."""
    db = get_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    db.execute(
        "UPDATE posts SET status='published', scheduled_at=NULL WHERE status='scheduled' AND scheduled_at IS NOT NULL AND scheduled_at <= ?",
        (now,)
    )
    db.commit()


def generate_toc(md_text):
    """Generate table of contents from markdown headings."""
    toc = []
    for line in md_text.split("\n"):
        m = re.match(r'^(#{1,4})\s+(.+)$', line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            anchor = re.sub(r'[^\w\u4e00-\u9fff-]', '-', title).lower()
            anchor = re.sub(r'-+', '-', anchor).strip('-')
            toc.append((level, title, anchor))
    return toc


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
        (SELECT COUNT(*) FROM posts WHERE status='scheduled') as scheduled,
        (SELECT COUNT(*) FROM comments) as comments,
        (SELECT COUNT(*) FROM comments WHERE approved=0) as pending_comments,
        (SELECT COUNT(*) FROM messages) as messages,
        (SELECT COALESCE(SUM(count),0) FROM pageviews WHERE post_id!=0) as views,
        (SELECT COALESCE(SUM(views),0) FROM posts) as total_views,
        (SELECT COUNT(*) FROM likes) as likes
    """).fetchone()
    return dict(row)


def get_series_list():
    db = get_db()
    return db.execute("SELECT * FROM series ORDER BY name").fetchall()


# ─── CSRF token injection & scheduled publish ───
@app.before_request
def before_request():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    if not request.path.startswith("/static/"):
        try:
            publish_scheduled()
        except Exception:
            pass


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


# ─── Language switcher ───
@app.route("/lang/<lang>")
def set_lang(lang):
    if lang in ("zh", "en"):
        session["lang"] = lang
    return redirect(request.referrer or url_for("index"))


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
        "SELECT id, title, tags, category, cover_image, created_at, pinned FROM posts WHERE status='published' ORDER BY pinned DESC, created_at DESC LIMIT 5"
    ).fetchall()
    announcements = db.execute("SELECT * FROM announcements ORDER BY created_at DESC LIMIT 1").fetchall()
    return render_template("index.html", posts=posts, announcements=announcements)


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
        f"SELECT id, title, tags, category, cover_image, created_at, pinned FROM posts{where_sql} ORDER BY pinned DESC, created_at DESC LIMIT ? OFFSET ?",
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
    like = f"%{q}%"
    rows = db.execute(
        "SELECT id, title, tags, category, cover_image, created_at, pinned FROM posts "
        "WHERE status='published' AND (title LIKE ? OR content LIKE ?) ORDER BY pinned DESC, created_at DESC LIMIT 50",
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
        "SELECT id, title, category, created_at, pinned FROM posts WHERE category != '' AND status='published' ORDER BY pinned DESC, created_at DESC"
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
        "SELECT id, title, created_at, pinned FROM posts WHERE status='published' ORDER BY pinned DESC, created_at DESC"
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
    if p["status"] in ("draft", "scheduled") and not session.get("logged_in"):
        flash("文章不存在")
        return redirect(url_for("index"))
    # Password-protected post
    if p["access_password"] and not session.get(f"post_unlocked_{post_id}"):
        if request.args.get("unlock"):
            if request.args.get("pwd") == p["access_password"]:
                session[f"post_unlocked_{post_id}"] = True
            else:
                flash("密码错误")
                return render_template("post_unlock.html", post=p)
        else:
            return render_template("post_unlock.html", post=p)
    # Increment view counter
    db.execute("UPDATE posts SET views=views+1 WHERE id=?", (post_id,))
    db.commit()
    # Fetch comments with parent info for reply notifications
    comments = db.execute(
        "SELECT c.*, pc.name as parent_name FROM comments c LEFT JOIN comments pc ON pc.id=c.parent_id WHERE c.post_id=? AND c.approved=1 ORDER BY c.created_at ASC", (post_id,)
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
        ) + " ORDER BY pinned DESC, created_at DESC LIMIT 5"
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
    # TOC
    toc = generate_toc(p["content"])
    # Likes
    client_ip = request.remote_addr or "unknown"
    liked = bool(db.execute("SELECT 1 FROM likes WHERE post_id=? AND ip=?", (post_id, client_ip)).fetchone())
    like_count = db.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (post_id,)).fetchone()[0]
    return render_template(
        "post.html", post=p, content_html=render_md(p["content"]),
        comments=comments, related=related, series=series, series_posts=series_posts,
        reading_time=reading_time, toc=toc, liked=liked, like_count=like_count,
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
    parent_id = request.form.get("parent_id", type=int)
    if not name or not content:
        flash("姓名和内容不能为空")
    else:
        db.execute(
            "INSERT INTO comments (post_id, name, content, parent_id, approved, created_at) VALUES (?, ?, ?, ?, 0, ?)",
            (post_id, name, content, parent_id, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        db.commit()
        # Mark parent as replied
        if parent_id:
            db.execute("UPDATE comments SET replied=1 WHERE id=?", (parent_id,))
            db.commit()
        flash("评论成功，等待审核")
    return redirect(url_for("post", post_id=post_id))


# ─── Like/Unlike post ───
@app.route("/post/<int:post_id>/like", methods=["POST"])
@csrf_required
def like_post(post_id):
    db = get_db()
    p = db.execute("SELECT 1 FROM posts WHERE id=?", (post_id,)).fetchone()
    if not p:
        return {"error": "文章不存在"}, 404
    ip = request.remote_addr or "unknown"
    existing = db.execute("SELECT 1 FROM likes WHERE post_id=? AND ip=?", (post_id, ip)).fetchone()
    if existing:
        db.execute("DELETE FROM likes WHERE post_id=? AND ip=?", (post_id, ip))
        liked = False
    else:
        db.execute("INSERT INTO likes (post_id, ip, created_at) VALUES (?, ?, ?)",
                   (post_id, ip, datetime.now().strftime("%Y-%m-%d %H:%M")))
        liked = True
    db.commit()
    count = db.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (post_id,)).fetchone()[0]
    return {"liked": liked, "count": count}


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
        content_html = render_md(p['content'])
        items.append(f"""    <item>
      <title>{xml_escape(p['title'])}</title>
      <link>{site_url}/post/{p['id']}</link>
      <description><![CDATA[{content_html}]]></description>
      <content:encoded><![CDATA[{content_html}]]></content:encoded>
      <pubDate>{xml_escape(p['created_at'])}</pubDate>
      <guid>{site_url}/post/{p['id']}</guid>
    </item>""")
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{xml_escape(_t('site_name'))}</title>
    <link>{site_url}</link>
    <description>{xml_escape(_t('site_desc'))}</description>
    <language>{'zh-CN' if session.get('lang', 'zh') == 'zh' else 'en'}</language>
    {"\n".join(items)}
  </channel>
</rss>"""
    return Response(xml, mimetype="application/xml")


# ─── Sitemap ───
@app.route("/sitemap.xml")
def sitemap():
    db = get_db()
    posts = db.execute(
        "SELECT id, created_at FROM posts WHERE status='published' AND (scheduled_at IS NULL OR scheduled_at <= datetime('now')) ORDER BY created_at DESC"
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
        "SELECT id, title, tags, category, cover_image, status, created_at, pinned FROM posts ORDER BY pinned DESC, created_at DESC"
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
        pinned = 1 if request.form.get("pinned") else 0
        access_password = request.form.get("access_password", "").strip()
        seo_desc = request.form.get("seo_desc", "").strip()
        seo_keywords = request.form.get("seo_keywords", "").strip()
        scheduled_at_str = None
        if status == "scheduled" and request.form.get("scheduled_at"):
            scheduled_at_str = request.form["scheduled_at"].strip()
        if not title or not content:
            flash("标题和内容不能为空")
            return render_template("create.html", series_list=get_series_list())
        db = get_db()
        db.execute(
            "INSERT INTO posts (title, content, tags, category, cover_image, status, series_id, pinned, access_password, seo_desc, seo_keywords, scheduled_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (title, content, tags, category, cover_image, status, series_id, pinned, access_password, seo_desc, seo_keywords, scheduled_at_str, datetime.now().strftime("%Y-%m-%d %H:%M")),
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
        pinned = 1 if request.form.get("pinned") else 0
        access_password = request.form.get("access_password", "").strip()
        seo_desc = request.form.get("seo_desc", "").strip()
        seo_keywords = request.form.get("seo_keywords", "").strip()
        scheduled_at_str = None
        if status == "scheduled" and request.form.get("scheduled_at"):
            scheduled_at_str = request.form["scheduled_at"].strip()
        if not title or not content:
            flash("标题和内容不能为空")
            return render_template("edit.html", post=p, series_list=get_series_list())
        db.execute(
            "UPDATE posts SET title=?, content=?, tags=?, category=?, cover_image=?, status=?, series_id=?, pinned=?, access_password=?, seo_desc=?, seo_keywords=?, scheduled_at=? WHERE id=?",
            (title, content, tags, category, cover_image, status, series_id, pinned, access_password, seo_desc, seo_keywords, scheduled_at_str, post_id),
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


# ─── Admin: Messages ───
@app.route("/admin/messages")
@login_required
def admin_messages():
    db = get_db()
    messages = db.execute("SELECT * FROM messages ORDER BY created_at DESC").fetchall()
    return render_template("admin_messages.html", messages=messages)


@app.route("/admin/messages/delete/<int:msg_id>", methods=["POST"])
@login_required
@csrf_required
def delete_message(msg_id):
    db = get_db()
    db.execute("DELETE FROM messages WHERE id=?", (msg_id,))
    db.commit()
    flash("留言已删除")
    return redirect(url_for("admin_messages"))


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


# ─── Admin: Announcements ───
@app.route("/admin/announcements", methods=["GET", "POST"])
@login_required
@csrf_required
def admin_announcements():
    db = get_db()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        ann_id = request.form.get("id", type=int)
        if not title or not content:
            flash("标题和内容不能为空")
        elif ann_id:
            db.execute("UPDATE announcements SET title=?, content=? WHERE id=?", (title, content, ann_id))
            db.commit()
            flash("公告已更新")
        else:
            db.execute("INSERT INTO announcements (title, content, created_at) VALUES (?, ?, ?)",
                       (title, content, datetime.now().strftime("%Y-%m-%d %H:%M")))
            db.commit()
            flash("公告已发布")
        return redirect(url_for("admin_announcements"))
    edit_id = request.args.get("edit", type=int)
    edit_ann = None
    if edit_id:
        edit_ann = db.execute("SELECT * FROM announcements WHERE id=?", (edit_id,)).fetchone()
    anns = db.execute("SELECT * FROM announcements ORDER BY created_at DESC").fetchall()
    return render_template("admin_announcements.html", announcements=anns, edit_ann=edit_ann)


@app.route("/admin/announcements/delete/<int:ann_id>", methods=["POST"])
@login_required
@csrf_required
def delete_announcement(ann_id):
    db = get_db()
    db.execute("DELETE FROM announcements WHERE id=?", (ann_id,))
    db.commit()
    flash("公告已删除")
    return redirect(url_for("admin_announcements"))


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


# ─── DB Backup ───
@app.route("/admin/backup")
@login_required
def backup_db():
    db = get_db()
    db.commit()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATABASE, "blog.db")
    buf.seek(0)
    return send_file(
        buf, mimetype="application/zip", as_attachment=True,
        download_name=f"blog_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    )


# ─── PDF Export ───
@app.route("/post/<int:post_id>/pdf")
def export_pdf(post_id):
    db = get_db()
    p = db.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
    if not p or (p["status"] != "published" and not session.get("logged_in")):
        flash("文章不存在")
        return redirect(url_for("index"))
    html_content = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{xml_escape(p['title'])}</title>
<style>
body {{ font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.8; color: #333; }}
h1 {{ font-size: 1.6em; margin-bottom: 8px; }}
.meta {{ color: #888; font-size: .85em; margin-bottom: 24px; }}
pre {{ background: #f5f5f5; padding: 12px; border-radius: 6px; overflow-x: auto; }}
code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: .9em; }}
pre code {{ background: none; padding: 0; }}
img {{ max-width: 100%; }}
blockquote {{ border-left: 4px solid #ddd; margin: 0; padding-left: 16px; color: #666; }}
</style></head><body>
<h1>{xml_escape(p['title'])}</h1>
<div class="meta">{xml_escape(p['created_at'])} | {xml_escape(p['category'] or '未分类')}</div>
{render_md(p['content'])}
</body></html>"""
    from flask import make_response
    resp = make_response(html_content)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    resp.headers["Content-Disposition"] = f"attachment; filename={p['id']}_{p['title'][:30]}.html"
    return resp


if __name__ == "__main__":
    init_db()
    debug_mode = os.environ.get("FLASK_ENV") != "production"
    app.run(debug=debug_mode, port=5000, use_reloader=False)
