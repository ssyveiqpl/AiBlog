# AI探索笔记 博客系统 项目白皮书

**版本**：1.0  
**最后更新**：2026-06-14  
**技术栈**：Python Flask + SQLite + Jinja2

---

## 1. 项目概述

AI探索笔记是一个轻量级个人博客系统，支持 Markdown 文章发布、留言互动、项目管理等功能。前端采用微信风格 UI，适配移动端与桌面端，支持暗夜模式切换。

### 1.1 核心定位

- **个人知识沉淀**：Markdown 驱动的技术博客，支持代码高亮
- **作品展示**：项目 showcase 页面，按分类筛选
- **读者互动**：留言板系统，微信聊天风格展示
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
| Markdown | Python-Markdown | 支持 fenced_code / codehilite 扩展 |
| 代码高亮 | Pygments | Markdown 代码块语法高亮 |

### 2.2 前端

| 组件 | 选型 | 说明 |
|------|------|------|
| UI 框架 | 原生 CSS (微信风格) | 自定义 WeChat Green 主题 |
| 图标库 | Font Awesome 6 | 导航栏/卡片图标 |
| 主题切换 | CSS Variables + localStorage | 明暗主题持久化 |
| 布局方案 | CSS Flexbox / Grid | 响应式卡片布局 |

---

## 3. 功能模块

### 3.1 文章系统 `/`, `/articles`, `/post/<id>`

- Markdown 撰写与渲染
- 文章列表页（统计看板 + 卡片列表）
- 文章详情页（代码高亮、引用块、图片等）
- 首页展示 3 篇最新文章

### 3.2 项目管理 `/projects`

- 16 个项目卡片展示
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
- 密码修改
- 默认密码：`admin123`

### 3.6 暗夜模式

- 点击顶部 🌙/☀️ 按钮切换
- CSS Variables 驱动
- localStorage 持久化偏好设置

---

## 4. 数据库设计

使用 SQLite 数据库 `blog.db`，包含 3 张表：

### `posts` — 文章表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| title | TEXT NOT NULL | 文章标题 |
| content | TEXT NOT NULL | Markdown 正文 |
| created_at | TEXT NOT NULL | 创建时间 |

### `messages` — 留言表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| name | TEXT NOT NULL | 留言者姓名 |
| content | TEXT NOT NULL | 留言内容 |
| created_at | TEXT NOT NULL | 留言时间 |

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
| 项目 | `fa-code-branch` | `/projects` |
| 留言 | `fa-comment-dots` | `/message` |
| 我的 | `fa-user` | `/about` |

### 5.3 色彩变量体系

CSS 自定义属性驱动的双主题系统：

- Light 模式：浅灰底色 + 白色卡片 + 深色文字
- Dark 模式：深黑底色 + 深灰卡片 + 浅色文字
- 所有颜色通过 `var(--xxx)` 引用，一键切换

---

## 6. 目录结构

```
blog/
├── app.py              # Flask 应用主入口 / 路由
├── blog.db             # SQLite 数据库
├── static/
│   └── style.css       # 微信风格 CSS（双主题）
└── templates/
    ├── base.html       # 基础模板（顶部栏 + 底部 Tab）
    ├── index.html      # 首页
    ├── articles.html   # 文章列表
    ├── post.html       # 文章详情
    ├── projects.html   # 项目展示
    ├── message.html    # 留言板
    ├── about.html      # 关于我
    ├── login.html      # 登录页
    ├── admin.html      # 管理后台
    ├── create.html     # 写文章
    ├── edit.html       # 编辑文章
    └── change_password.html  # 修改密码
```

---

## 7. 部署指南

### 7.1 环境要求

- Python 3.8+
- pip 包管理

### 7.2 安装与运行

```bash
# 1. 安装依赖
pip install flask markdown Pygments

# 2. 启动服务
python app.py

# 3. 访问
http://127.0.0.1:5000
```

### 7.3 首次使用

1. 访问 `http://127.0.0.1:5000`
2. 点击导航栏右侧「管理」或访问 `/login`
3. 默认密码：`admin123`
4. 进入后台发布文章、修改密码

---

## 8. 安全注意事项

- `app.secret_key` 为硬编码占位符，生产环境需替换为随机密钥
- 会话使用 Flask 内置 Session（客户端签名 Cookie）
- 密码明文存储于 `settings` 表（小型个人项目可接受，生产建议加盐哈希）
- 建议生产环境使用 Waitress / Gunicorn + Nginx 反向代理

---

## 9. 路线图

### v1.1 计划

- [ ] 文章标签 / 分类系统
- [ ] RSS 订阅支持
- [ ] 文章搜索功能
- [ ] 图片上传支持
- [ ] 评论回复功能

### v2.0 规划

- [ ] 后台 Markdown 实时预览
- [ ] 多用户支持
- [ ] API 接口开放
- [ ] 静态站点导出

---

## 10. 项目总结

AI探索笔记博客系统是一个**轻量、美观、实用**的个人博客解决方案。它没有复杂的前后端分离架构，而是以 Flask + Jinja2 服务端渲染为核心，在保持极简部署的同时，通过微信风格的 UI 设计和完整的 CRUD 功能，提供了良好的写作与阅读体验。

项目代码全部开源，欢迎 fork 和定制。

---

*白皮书结束 · © 2026 AI探索笔记*
