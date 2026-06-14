<div align="center">
  <h1>AI探索笔记 · 个人博客系统</h1>
  <p>轻量级 · 微信风格 UI · Markdown 驱动 · 多语言 · 开箱即用</p>
  <p>
    <a href="#-功能特性">功能特性</a> •
    <a href="#-快速开始">快速开始</a> •
    <a href="#-技术栈">技术栈</a> •
    <a href="#-项目结构">项目结构</a> •
    <a href="#-部署">部署</a>
  </p>
  <br>
</div>

---

## 📸 页面预览

| 页面 | 说明 |
|------|------|
| **首页** | Hero 区域 + 最新文章 + 个人简介 + 网站公告 |
| **文章列表** | 统计看板 + 文章卡片网格（封面图 + 置顶标记） |
| **文章详情** | 目录/大纲 + 代码高亮 + 点赞 + 评论回复 + 分享 + 阅读进度条 + PDF 导出 |
| **项目展示** | 分类筛选的项目 showcase，后台可管理 |
| **归档/分类页** | 时间线归档、分类聚合 |
| **留言板** | 微信聊天气泡风格 |
| **关于页** | 个人名片 + 技能标签 + 联系方式 |
| **暗夜/护眼模式** | 三主题一键切换，持久化偏好 |
| **多语言** | 中 / 英双语，右上角一键切换 |

## ✨ 功能特性

- **Markdown 写作** — 支持代码高亮（highlight.js 11.9，本地主题）、目录/大纲自动生成
- **微信风格 UI** — 底部 Tab 导航，`#07C160` 主色调，圆角卡片，移动优先
- **暗夜模式 + 护眼模式** — CSS Variables 驱动，三主题互斥，localStorage 持久化
- **项目管理** — DB 驱动，后台 CRUD，前台分类筛选
- **留言板** — 访客留言，聊天风格展示
- **文章 CRUD** — 完整管理后台（创建/编辑/删除/置顶/定时发布）
- **文章加密** — 独立密码保护，session 解锁
- **点赞/收藏** — IP 去重，按钮切换
- **评论回复** — 嵌套回复，@提及，实时插入
- **社交分享** — Facebook / Twitter / 微博 / LinkedIn
- **全文搜索** — 标题+内容 LIKE 查询，关键词高亮
- **RSS 订阅** — 全文输出，含 `<content:encoded>`
- **PDF 导出** — 每篇文章可导出为 PDF 下载
- **OpenGraph 标签** — 社交预览图/描述/标题
- **SEO 自定义** — 每篇文章独立描述/关键词
- **自动保存草稿** — localStorage 实时保存，刷新恢复提示
- **网站公告** — 后台 CRUD，首页展示
- **数据备份** — 一键下载 `blog.db` 为 ZIP
- **仪表盘统计** — 文章/草稿/定时/留言/点赞/总浏览看板
- **多语言 i18n** — 中/英双语，300+ 翻译键全覆盖
- **代码高亮主题** — 4 套本地主题（github / github-dark / school-book / atom-one-dark）
- **阅读进度条** — 文章顶部绿色进度指示
- **封面图** — 文章封面图支持和展示
- **编辑器优化** — Ctrl+B/I 快捷键，自动伸缩文本域，折叠高级设置
- **全端适配** — 移动优先，响应式布局
- **零依赖前端** — 原生 CSS，无前端框架负担

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip

### 安装与运行

```bash
# 1. 克隆仓库
git clone https://github.com/ssyveiqpl/AiBlog.git
cd AiBlog

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务
python app.py

# 4. 打开浏览器
# http://127.0.0.1:5000
```

### Docker 部署

```bash
docker-compose up -d
```

### 首次使用

| 步骤 | 说明 |
|------|------|
| 访问首页 | `http://127.0.0.1:5000` |
| 登录管理 | 点击右上角 <i class="fas fa-sign-in-alt"></i> 图标 |
| 默认密码 | `admin123`（登录后建议立即修改） |

## 🛠 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| **后端** | Python Flask 3.1 | 轻量级 Web 框架 |
| **数据库** | SQLite 3 | 零配置嵌入式数据库 |
| **模板** | Jinja2 | 服务端渲染 |
| **Markdown** | Python-Markdown | 支持 fenced_code / toc / codehilite 扩展 |
| **代码高亮** | highlight.js 11.9 | 4 套本地主题，无 CDN 依赖 |
| **前端** | 原生 CSS + Font Awesome 6 | 微信风格 UI，CSS Variables 三主题 |

## 📁 项目结构

```
AiBlog/
├── app.py                 # Flask 应用主入口（路由 + i18n + 数据库）
├── blog.db                # SQLite 数据库（首次启动自动创建）
├── requirements.txt       # Python 依赖
├── WHITEPAPER.md          # 项目白皮书
├── Dockerfile             # Docker 构建
├── docker-compose.yml     # Docker Compose
├── .gitignore
├── static/
│   ├── style.css          # 微信风格 CSS（三主题：亮色/暗夜/护眼）
│   └── highlight/         # highlight.js 主题 CSS（本地托管）
│       ├── github.min.css
│       ├── github-dark.min.css
│       ├── school-book.min.css
│       └── atom-one-dark.min.css
├── templates/
│   ├── base.html               # 基础模板（顶部栏 + 底部 Tab + 主题切换）
│   ├── index.html              # 首页
│   ├── articles.html           # 文章列表
│   ├── post.html               # 文章详情（目录/点赞/评论/分享/阅读进度）
│   ├── post_unlock.html        # 文章密码解锁
│   ├── archive.html            # 归档
│   ├── categories.html         # 分类
│   ├── projects.html           # 项目展示（DB 驱动）
│   ├── message.html            # 留言板
│   ├── about.html              # 关于我
│   ├── links.html              # 友情链接
│   ├── login.html              # 登录
│   ├── error.html              # 错误页
│   ├── admin.html              # 管理后台
│   ├── admin_stats.html        # 仪表盘统计
│   ├── admin_announcements.html # 公告管理
│   ├── admin_categories.html   # 分类管理
│   ├── admin_comments.html     # 评论管理
│   ├── admin_links.html        # 链接管理
│   ├── admin_messages.html     # 留言管理
│   ├── admin_series.html       # 系列管理
│   ├── admin_projects.html     # 项目管理
│   ├── create.html             # 写文章
│   ├── edit.html               # 编辑文章
│   ├── _editor.html            # 编辑器组件（自动保存/快捷键）
│   ├── change_password.html    # 修改密码
│   └── import_export.html      # 导入导出
├── tests/                # 测试
└── migrations/           # 数据库迁移
```

## ⚙️ 配置

关键配置项位于 `app.py` 顶部：

```python
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
```

数据库文件 `blog.db` 首次启动时自动创建，包含以下表：

| 表名 | 说明 |
|------|------|
| `posts` | 文章（含置顶/定时/浏览量/密码/SEO 等字段） |
| `comments` | 评论（支持嵌套回复） |
| `likes` | 点赞（IP 去重） |
| `announcements` | 网站公告 |
| `projects` | 项目管理 |
| `messages` | 访客留言 |
| `links` | 友情链接 |
| `series` | 文章系列 |
| `settings` | 系统设置 |
| `pageviews` | 页面浏览统计 |

## 🌐 部署

### 生产环境建议

```bash
# 使用 Waitress 部署（Windows）
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 app:app

# 使用 Gunicorn 部署（Linux）
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

推荐搭配 Nginx 反向代理 + 域名绑定。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证。
