<div align="center">
  <h1>AI探索笔记 · 个人博客系统</h1>
  <p>轻量级 · 微信风格 UI · Markdown 驱动 · 开箱即用</p>
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
| **首页** | Hero 区域 + 最新文章 + 个人简介 |
| **文章列表** | 统计看板 + 文章卡片网格 |
| **项目展示** | 分类筛选的项目 showcase |
| **留言板** | 微信聊天气泡风格 |
| **关于页** | 个人名片 + 技能标签 + 联系方式 |
| **暗夜模式** | 一键切换，持久化偏好 |

## ✨ 功能特性

- **Markdown 写作** — 支持代码高亮、引用块、图片等
- **微信风格 UI** — 底部 Tab 导航，`#07C160` 主色调，圆角卡片
- **暗夜模式** — CSS Variables 驱动，localStorage 持久化
- **项目管理** — 16 个项目卡片，支持分类筛选
- **留言板** — 访客留言，聊天风格展示
- **文章 CRUD** — 完整的管理后台（创建 / 编辑 / 删除）
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

### 首次使用

| 步骤 | 说明 |
|------|------|
| 访问首页 | `http://127.0.0.1:5000` |
| 登录管理 | `http://127.0.0.1:5000/login` |
| 默认密码 | `admin123`（登录后建议立即修改） |

## 🛠 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| **后端** | Python Flask | 轻量级 Web 框架 |
| **数据库** | SQLite | 零配置嵌入式数据库 |
| **模板** | Jinja2 | 服务端渲染 |
| **Markdown** | Python-Markdown + Pygments | Markdown 渲染 + 代码高亮 |
| **前端** | 原生 CSS + Font Awesome 6 | 微信风格 UI，CSS Variables 双主题 |

## 📁 项目结构

```
AiBlog/
├── app.py                 # Flask 应用主入口（路由 + 数据库）
├── requirements.txt       # Python 依赖
├── WHITEPAPER.md          # 项目白皮书
├── .gitignore
├── static/
│   └── style.css          # 微信风格 CSS（双主题）
└── templates/
    ├── base.html          # 基础模板（顶部栏 + 底部 Tab）
    ├── index.html         # 首页
    ├── articles.html      # 文章列表
    ├── post.html          # 文章详情
    ├── projects.html      # 项目展示
    ├── message.html       # 留言板
    ├── about.html         # 关于我
    ├── login.html         # 登录
    ├── admin.html         # 管理后台
    ├── create.html        # 写文章
    ├── edit.html          # 编辑文章
    └── change_password.html # 修改密码
```

## ⚙️ 配置

关键配置项位于 `app.py` 顶部：

```python
app.secret_key = "your-secret-key-change-in-production"  # 生产环境务必修改
```

数据库文件 `blog.db` 首次启动时自动创建，包含 `posts`、`messages`、`settings` 三张表。

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
