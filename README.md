# Notion + Hugo 静态博客生成器

使用 Notion 作为内容管理系统，通过 Hugo 生成静态博客，自动部署到 Vercel。

## 🚀 快速开始

### 1. 环境准备

确保你的系统已安装：
- Python 3.11+
- Hugo (扩展版本)
- Node.js 18+
- uv (Python 包管理器)
- Git

### 2. 项目设置

```bash
# 克隆项目
git clone <your-repo-url>
cd blog_with_notion

# 初始化项目并安装依赖
uv sync

# 设置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥
```

### 3. Notion 配置

1. **创建 Notion Integration**
   - 访问 [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
   - 创建新的 Integration，获取 Token

2. **设置 Notion 数据库**
   - 创建数据库，包含以下字段：
     - `Title` (标题)
     - `Slug` (URL 路径，可选)
     - `Tags` (标签，多选)
     - `Status` (状态，单选：Draft/Published/Archived)
     - `Date` (发布日期)
     - `Excerpt` (摘要，可选)

3. **授权访问**
   - 在数据库页面点击右上角 "..." → "Connect to" → 选择你的 Integration

### 4. 首次同步

```bash
# 同步 Notion 内容
uv run notion-sync sync

# 本地预览
cd hugo_site
hugo server -D
```

### 5. 图片管理

#### 图片命名规则
为了避免重复同步导致的重复文件，系统采用以下命名策略：

- **命名格式**: `{post_slug}-{image_id}.{ext}`
- **图片 ID**: 基于 Notion 图片 URL 提取的稳定文件标识符
- **重复检查**: 自动检测已存在的图片，避免重复下载
- **示例**: `my-post-s1234567.jpg`

#### 清理无用文件
```bash
# 同步时清理无用图片
uv run notion-sync sync --clean
```

### 6. 部署到 Vercel

#### 自动化部署流程
项目使用 GitHub Actions 进行自动化部署：

1. **推送代码到 GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **配置 GitHub Secrets**
   在 GitHub 仓库设置中添加以下 Secrets：
   - `NOTION_TOKEN`: Notion API token
   - `NOTION_DATABASE_ID`: Notion 数据库 ID
   - `VERCEL_TOKEN`: Vercel API token
   - `VERCEL_ORG_ID`: Vercel 组织 ID
   - `VERCEL_PROJECT_ID`: Vercel 项目 ID

#### 部署策略

**定时部署**
- 每小时自动检查 Notion 更新
- 同步所有文章并重新构建部署

**手动触发部署**
- 在 GitHub Actions 页面手动触发
- 支持清理无用图片选项

**图片管理优势**
- ✅ 智能图片命名，避免重复下载
- ✅ 自动检测已存在的图片文件
- ✅ 支持清理无用的孤立图片

#### 部署状态

部署流程会：
- 从 Notion 同步所有内容
- 构建 Hugo 网站
- 部署到 Vercel
- 失败时发送通知

## 📁 项目结构

```
blog_with_notion/
├── notion_hugo_sync/     # Python 同步脚本包
│   ├── main.py          # 主同步逻辑和 CLI
│   ├── config.py        # 配置管理
│   ├── notion_client.py # Notion API 客户端
│   ├── hugo_generator.py # Hugo 内容生成器
│   └── __init__.py      # 包初始化
├── hugo_site/           # Hugo 网站目录
│   ├── content/         # 博客内容
│   │   ├── posts/       # 文章目录
│   │   └── about.md     # 关于页面
│   ├── static/          # 静态资源
│   │   └── images/      # 图片存储
│   ├── themes/          # 主题目录
│   └── hugo.yaml        # Hugo 配置
├── .github/workflows/   # GitHub Actions
│   └── deploy.yml       # 自动部署工作流
├── scripts/             # 构建脚本
│   └── build.sh         # 本地构建脚本
├── .env.example         # 环境变量示例
├── .gitignore           # Git 忽略文件
├── pyproject.toml       # Python 项目配置
└── README.md            # 项目说明
```

## 🛠️ 使用指南

### 同步命令

```bash
# 同步新内容
uv run notion-sync sync

# 强制完整同步
uv run notion-sync sync --force

# 查看同步状态
uv run notion-sync status

# 初始化项目
uv run notion-sync init
```

### 本地开发

```bash
# 构建项目
./scripts/build.sh

# 本地预览 (包含草稿)
cd hugo_site && hugo server -D

# 生产构建
cd hugo_site && hugo --minify
```

### 主题定制

1. **安装主题**
   ```bash
   cd hugo_site
   git submodule add https://github.com/CaiJimmy/hugo-theme-stack.git themes/hugo-theme-stack
   ```

2. **修改配置**
   编辑 `hugo_site/hugo.yaml` 文件，自定义主题配置

3. **自定义样式**
   在 `hugo_site/static/css/` 目录下添加自定义 CSS

## 🔄 自动化流程

### GitHub Actions

项目配置了自动部署流程，支持：

- **定时触发**: 每小时检查 Notion 更新
- **手动触发**: 在 GitHub Actions 页面手动运行
- **代码推送**: 推送相关文件时自动触发

### 部署流程

1. 从 Notion API 获取最新内容
2. 生成 Hugo 兼容的 Markdown 文件
3. 下载和处理图片资源
4. 构建 Hugo 静态网站
5. 部署到 Vercel

## 📝 Notion 数据库设计

### 必需字段

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| Title | Title | 文章标题 | "我的第一篇博客" |
| Status | Select | 发布状态 | "Published" |
| Date | Date | 发布日期 | "2024-01-01" |

### 可选字段

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| Slug | Rich Text | 自定义 URL | "my-first-post" |
| Tags | Multi-select | 文章标签 | ["技术", "Python"] |
| Excerpt | Rich Text | 文章摘要 | "这是一篇关于..." |

### 内容格式

- 支持所有 Notion 块类型
- 自动转换为 Markdown 格式
- 图片自动下载到本地
- 支持代码块、表格、列表等

## 🚨 故障排除

### 常见问题

1. **同步失败**
   - 检查 NOTION_TOKEN 是否正确
   - 确认数据库已授权给 Integration
   - 查看字段名称是否匹配

2. **构建失败**
   - 检查 Hugo 版本 (需要扩展版本)
   - 确认主题配置正确
   - 查看构建日志

3. **部署失败**
   - 检查 Vercel 配置
   - 确认 GitHub Secrets 设置
   - 查看 GitHub Actions 日志

### 调试模式

```bash
# 启用详细日志
export RICH_LOG_LEVEL=DEBUG
uv run notion-sync sync
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Notion API](https://developers.notion.com/) - 内容管理
- [Hugo](https://gohugo.io/) - 静态网站生成
- [Vercel](https://vercel.com/) - 部署平台
- [uv](https://github.com/astral-sh/uv) - Python 包管理
