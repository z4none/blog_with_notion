# Notion + Hugo + Vercel 自动博客

🚀 **基于 Notion 的全自动博客系统** - 使用 GitHub Actions 自动同步内容并部署到 Vercel

## ✨ 核心特性

- **📝 Notion 写作**：在 Notion 中编写博客，支持富文本、代码块、图片等
- **🔄 自动同步**：GitHub Actions 每小时自动从 Notion 同步内容
- **⚡ 一键部署**：自动构建 Hugo 网站并部署到 Vercel
- **🖼️ 智能图片**：自动下载图片，避免重复，支持清理无用文件
- **🎨 主题定制**：使用 Hugo Stack 主题，支持自定义样式

## 🚀 快速开始

### 1. 克隆并配置

```bash
git clone <your-repo-url>
cd blog_with_notion

# 安装依赖
pip install -e .

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥
```

### 2. Notion 设置

1. **创建 Integration**：访问 [notion.so/my-integrations](https://www.notion.so/my-integrations) 获取 Token
2. **创建数据库**：包含 `Title`、`Status`、`Date` 等字段
3. **授权访问**：将数据库连接到你的 Integration

### 3. GitHub 部署

```bash
git add .
git commit -m "Initial setup"
git push origin main
```

在 GitHub 仓库设置中添加 Secrets：
- `NOTION_TOKEN`：Notion API token
- `NOTION_DATABASE_ID`：Notion 数据库 ID  
- `VERCEL_TOKEN`：Vercel API token
- `VERCEL_ORG_ID`：Vercel 组织 ID
- `VERCEL_PROJECT_ID`：Vercel 项目 ID

## 🔄 自动化部署

### 工作流程

```
Push to GitHub → GitHub Actions → Sync from Notion → Build Hugo → Deploy to Vercel
```

### 触发方式

- **定时同步**：每小时自动检查 Notion 更新
- **代码推送**：修改 `hugo/` 或 `notion_sync/` 时触发
- **手动触发**：在 GitHub Actions 页面手动运行

### 部署状态

GitHub Actions 会自动：
- ✅ 从 Notion 获取最新内容
- ✅ 生成 Hugo Markdown 文件
- ✅ 下载和处理图片
- ✅ 构建静态网站
- ✅ 部署到 Vercel

## 📁 项目结构

```
blog_with_notion/
├── notion_sync/          # Python 同步包
│   ├── main.py          # 主同步逻辑
│   ├── config.py        # 配置管理
│   ├── notion_client.py # Notion API 客户端
│   └── hugo_generator.py # Hugo 生成器
├── hugo/                # Hugo 网站
│   ├── content/         # 博客内容（自动生成）
│   ├── static/          # 静态资源
│   ├── themes/          # Hugo 主题（submodule）
│   └── hugo.yaml        # Hugo 配置
└── .github/workflows/   # 自动化流程
    └── deploy.yml       # 部署工作流
```

## 🛠️ 本地使用

```bash
# 同步 Notion 内容
notion_sync sync

# 同步并清理无用图片
notion_sync sync --clean

# 本地预览
cd hugo && hugo server -D
```

## 📝 Notion 数据库

### 必需字段

| 字段 | 类型 | 说明 |
|------|------|------|
| Title | Title | 文章标题 |
| Status | Select | 发布状态 (Draft/Published) |
| Date | Date | 发布日期 |

### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| Slug | Text | 自定义 URL |
| Tags | Multi-select | 文章标签 |
| Excerpt | Text | 文章摘要 |

## 🎨 自定义

- **主题配置**：编辑 `hugo/hugo.yaml`
- **自定义样式**：修改 `hugo/assets/scss/custom.scss`
- **添加页面**：在 `hugo/content/` 中创建 Markdown 文件

## 🚨 故障排除

### 同步失败
- 检查 `NOTION_TOKEN` 和 `NOTION_DATABASE_ID`
- 确认数据库已授权给 Integration
- 查看字段名称是否匹配

### 部署失败
- 检查 GitHub Secrets 配置
- 确认 Vercel 项目设置
- 查看 GitHub Actions 日志

## 📄 许可证

MIT License

---

🎯 **重点**：配置完成后，只需在 Notion 中写作，系统会自动同步并部署到 Vercel！
