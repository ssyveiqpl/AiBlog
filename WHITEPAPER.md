# AI探索笔记 博客系统 项目白皮书

**版本**：1.5  
**最后更新**：2026-06-14  
**技术栈**：Python Flask + SQLite + Jinja2

---

## 1. 项目概述

AI探索笔记是一个轻量级个人博客系统，支持 Markdown 文章发布、留言互动、项目管理等功能。前端采用微信风格 UI，适配移动端与桌面端，支持暗夜模式与护眼模式。

### 1.1 核心定位

- **个人知识沉淀**：Markdown 驱动的技术博客，支持代码高亮
- **作品展示**：项目 showcase 页面，按分类筛选
- **读者互动**：留言板系统，微信聊天风格展示，评论回复
- **全端适配**：底部 Tab 导航栏，移动优先设计

### 1.2 适用场景

- 个人技术博客 / 知识笔记站
- 开发者作品集展示
- 轻量级内容管理系统

---

## 2. 技术架构

### 2.1 后端

| 组件 | 选型 | 说明 |
|------|------|------|
| Web 框架 | Flask 3.1 | Python 轻量级 Web 框架 |
| 数据库 | SQLite 3 | 零配置嵌入式数据库 |
| 模板引擎 | Jinja2 | Flask 内置模板引擎 |
| Markdown | Python-Markdown | 支持 fenced_code / codehilite / toc 扩展 |
| 代码高亮 | highlight.js 11.9 | 本地托管，支持 4 种主题 |

### 2.2 前端

| 组件 | 选型 | 说明 |
|------|------|------|
| UI 框架 | 原生 CSS (微信风格) | 自定义 WeChat Green 主题 |
| 图标库 | Font Awesome 6 | 导航栏/卡片图标 |
| 主题系统 | CSS Variables + localStorage | 明暗/护眼三模式持久化 |
| 代码高亮 | highlight.js | 本地 CSS 文件，不依赖 CDN |
| 布局方案 | CSS Flexbox / Grid | 响应式卡片布局 |

---

## 3. 功能模块

### 3.1 文章系统 `/`, `/articles`, `/post/<id>`

- Markdown 撰写与渲染，支持代码高亮 + 行号
- 文章列表页（统计看板 + 卡片列表 + 封面图）
- 文章详情页（代码高亮、引用块、图片、目录/大纲、阅读进度条）
- 首页展示最新文章，置顶文章优先显示
- 文章浏览量统计与展示
- 点赞/取消点赞（IP 去重）
- 评论回复（嵌套回复 + @提及）
- 社交媒体分享（Facebook / Twitter / 微博 / LinkedIn）
- 文章加密访问（密码保护）
- PDF 导出
- OpenGraph 预览标签
- SEO 自定义描述/关键词
- RSS 全文输出（含 `<content:encoded>`）

### 3.2 项目管理 `/projects`

- 16+ 个项目卡片展示
- 分类筛选（全部 / AI/ML / Web开发 / 工具 / 研究）
- 项目信息卡片（图标 + 标签 + 描述 + 链接）

### 3.3 留言板 `/message`

- 访客留言提交（姓名 + 内容）
- 微信聊天气泡风格展示
- 按时间倒序排列

### 3.4 关于页 `/about`

- 个人名片（头像 + 姓名 + 简介）
- 技能标签展示
- 职业经历时间线
- 成就统计 + 联系方式

### 3.5 管理后台 `/admin`（需登录）

- 文章 CRUD（创建 / 编辑 / 删除）
- 密码修改（默认密码：`admin123`）
- 文章状态管理（已发布 / 草稿 / 定时发布）
- 文章置顶设置
- 分类 / 系列 / 评论 / 留言管理
- 网站公告 CRUD
- 仪表盘统计（文章数、草稿、定时、留言、点赞、总浏览）
- 数据库备份下载
- 数据导入导出

### 3.6 文章编辑器

- 封面图上传 + 实时预览
- 定时发布（选择日期时间）
- 文章加密密码设置
- SEO 自定义字段（描述、关键词）
- 自动保存草稿（localStorage，刷新恢复提示）
- Ctrl+B / Ctrl+I 快捷键（加粗/斜体）
- 可折叠高级设置区域

### 3.7 主题系统

- **亮色模式**：默认浅灰底色 + 白色卡片
- **暗夜模式**：深黑底色 + 深灰卡片，🌙/☀️ 切换
- **护眼模式**：暖黄纸张底色 + 棕褐文字，📖 切换
- CSS Variables 驱动，localStorage 持久化，三种模式互斥

### 3.8 多语言 i18n

- 中 / 英双语支持
- `_t()` Jinja2 全局函数 + TRANSLATIONS 字典（约 300+ 键）
- 语言切换器（右上角 globe 图标）
- 所有公开页面和管理页面均已汉化/英化
- 会话级偏好存储

### 3.9 其他功能

- **文章搜索**：标题 + 内容 LIKE 查询，关键词高亮显示
- **阅读进度条**：文章顶部绿色进度指示条
- **网站公告**：首页展示，后台 CRUD 管理
- **友情链接**：后台管理，首页展示
- **自动备份**：一键下载 `blog.db` 为 ZIP

---

## 4. 数据库设计

使用 SQLite 数据库 `blog.db`，包含以下表：

### `posts` — 文章表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| title | TEXT NOT NULL | 文章标题 |
| content | TEXT NOT NULL | Markdown 正文 |
| created_at | TEXT NOT NULL | 创建时间 |
| category | TEXT | 分类 |
| tags | TEXT | 标签（逗号分隔） |
| cover_image | TEXT | 封面图 URL |
| series_id | INTEGER | 所属系列 |
| pinned | INTEGER DEFAULT 0 | 是否置顶 |
| status | TEXT DEFAULT 'published' | published / draft / scheduled |
| scheduled_at | TEXT | 定时发布时间 |
| views | INTEGER DEFAULT 0 | 浏览量 |
| access_password | TEXT | 文章访问密码 |
| seo_desc | TEXT | SEO 描述 |
| seo_keywords | TEXT | SEO 关键词 |

### `messages` — 留言表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| name | TEXT NOT NULL | 留言者姓名 |
| content | TEXT NOT NULL | 留言内容 |
| created_at | TEXT NOT NULL | 留言时间 |

### `comments` — 评论表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| post_id | INTEGER | 所属文章 |
| name | TEXT | 评论者 |
| content | TEXT | 评论内容 |
| created_at | TEXT | 评论时间 |
| parent_id | INTEGER | 父评论 ID（回复） |
| replied | TEXT | 被回复者名称 |

### `likes` — 点赞表

| 字段 | 类型 | 说明 |
|------|------|------|
| post_id | INTEGER | 文章 ID |
| ip | TEXT | 点赞者 IP |
| PRIMARY KEY | (post_id, ip) | 联合主键防重复 |

### `announcements` — 公告表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| content | TEXT | 公告内容 |
| created_at | TEXT | 创建时间 |

### `settings` — 设置表

| 字段 | 类型 | 说明 |
|------|------|------|
| key | TEXT PK | 配置键名 |
| value | TEXT NOT NULL | 配置值 |

---

## 5. UI/UX 设计

### 5.1 设计风格

- **灵感来源**：微信 iOS 端 UI
- **主色调**：`#07C160`（微信绿）
- **圆角规范**：10px（卡片）、6px（输入框）、20px（筛选标签）
- **字体**：系统原生字体栈（SF Pro / Helvetica Neue）

### 5.2 底部 Tab 导航

| Tab | 图标 | 路由 |
|-----|------|------|
| 首页 | `fa-newspaper` | `/` |
| 文章 | `fa-file-alt` | `/articles` |
| 归档 | `fa-archive` | `/archive` |
| 分类 | `fa-folder` | `/categories` |
| 留言 | `fa-comment-dots` | `/message` |
| 我的 | `fa-user` | `/about` |

### 5.3 色彩变量体系

CSS 自定义属性驱动的三主题系统：

- Light 模式：浅灰底色 + 白色卡片 + 深色文字
- Dark 模式：深黑底色 + 深灰卡片 + 浅色文字
- Sepia 护眼模式：暖黄底色 + 棕褐文字
- 所有颜色通过 `var(--xxx)` 引用，一键切换

---

## 6. 目录结构

```
blog/
├── app.py              # Flask 应用主入口 / 路由 / i18n 翻译
├── blog.db             # SQLite 数据库
├── WHITEPAPER.md       # 项目白皮书
├── requirements.txt    # Python 依赖
├── Dockerfile          # Docker 构建
├── docker-compose.yml  # Docker Compose
├── static/
│   ├── style.css       # 微信风格 CSS（三主题）
│   └── highlight/      # highlight.js 主题 CSS（本地托管）
│       ├── github.min.css
│       ├── github-dark.min.css
│       ├── school-book.min.css
│       └── atom-one-dark.min.css
├── templates/
│   ├── base.html             # 基础模板（顶部栏 + 底部 Tab + 主题切换）
│   ├── index.html            # 首页
│   ├── articles.html         # 文章列表
│   ├── post.html             # 文章详情（目录/点赞/评论/分享/阅读进度）
│   ├── post_unlock.html      # 文章密码解锁
│   ├── search.html           # 搜索结果
│   ├── archive.html          # 归档
│   ├── categories.html       # 分类
│   ├── projects.html         # 项目展示
│   ├── message.html          # 留言板
│   ├── about.html            # 关于我
│   ├── links.html            # 友情链接
│   ├── login.html            # 登录页
│   ├── admin.html            # 管理后台
│   ├── admin_stats.html      # 仪表盘统计
│   ├── admin_announcements.html # 公告管理
│   ├── admin_categories.html # 分类管理
│   ├── admin_comments.html   # 评论管理
│   ├── admin_links.html      # 链接管理
│   ├── admin_messages.html   # 留言管理
│   ├── admin_series.html     # 系列管理
│   ├── create.html           # 写文章
│   ├── edit.html             # 编辑文章
│   ├── _editor.html          # 编辑器组件（自动保存/快捷键）
│   ├── change_password.html  # 修改密码
│   ├── import_export.html    # 导入导出
│   └── error.html            # 错误页
├── tests/               # 测试
├── migrations/          # 数据库迁移
├── .env.example         # 环境变量示例
└── .gitignore
```

---

## 7. 部署指南

### 7.1 环境要求

- Python 3.8+
- pip 包管理

### 7.2 安装与运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务
python app.py

# 3. 访问
http://127.0.0.1:5000
```

### 7.3 Docker 部署

```bash
docker-compose up -d
```

### 7.4 首次使用

1. 访问 `http://127.0.0.1:5000`
2. 点击导航栏右上角 `fa-sign-in-alt` 图标或访问 `/login`
3. 默认密码：`admin123`
4. 进入后台发布文章、修改密码

---

## 8. 安全注意事项

- `app.secret_key` 为硬编码占位符，生产环境需替换为随机密钥
- 会话使用 Flask 内置 Session（客户端签名 Cookie）
- 密码明文存储于 `settings` 表（小型个人项目可接受，生产建议加盐哈希）
- CSRF 保护：基于 session 的 token 验证
- 建议生产环境使用 Waitress / Gunicorn + Nginx 反向代理

---

## 9. 路线图

### v1.6 计划

- [ ] 文章归档按月分组
- [ ] 图片上传支持（本地/OSS）
- [ ] 后台 Markdown 实时预览
- [ ] 评论管理（删除/审核）

### v2.0 规划

- [ ] 多用户支持
- [ ] API 接口开放
- [ ] 静态站点导出
- [ ] 全文搜索（FTS5）

---

## 10. 项目总结

AI探索笔记博客系统是一个**轻量、美观、实用**的个人博客解决方案。它没有复杂的前后端分离架构，而是以 Flask + Jinja2 服务端渲染为核心，在保持极简部署的同时，通过微信风格的 UI 设计和完整的 CRUD 功能，提供了良好的写作与阅读体验。

项目代码全部开源，欢迎 fork 和定制。

---

*白皮书结束 · © 2026 AI探索笔记*
