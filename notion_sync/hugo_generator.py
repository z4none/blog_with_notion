"""
Hugo 内容生成器
将 Notion 数据转换为 Hugo 兼容的 Markdown 文件
"""

import asyncio
import httpx
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import frontmatter
from pydantic import BaseModel

from .config import HugoConfig
from .notion_client import NotionPost, NotionClient


class HugoGenerator:
    """Hugo 内容生成器"""
    
    def __init__(self, config: HugoConfig):
        self.config = config
        
        # 确保目录存在
        self.config.content_dir.mkdir(parents=True, exist_ok=True)
        self.config.pages_dir.mkdir(parents=True, exist_ok=True)
        self.config.images_dir.mkdir(parents=True, exist_ok=True)
        self.static_dir = Path(self.config.static_dir)
        self.images_dir = Path(self.config.images_dir)
        
        self.http_client = httpx.AsyncClient()
    
    async def generate_posts(self, posts: List[NotionPost], notion_client: NotionClient) -> int:
        """生成 Hugo 文章"""
        generated_count = 0
        
        print(f"开始生成 {len(posts)} 篇文章...")
        
        for i, post in enumerate(posts, 1):
            try:
                print(f"处理第 {i}/{len(posts)} 篇: {post.title}")
                
                # 获取文章内容
                content = await notion_client.get_page_content(post.id)
                
                # 生成文件
                await self._generate_post_file(post, content)
                generated_count += 1
                
            except Exception as e:
                print(f"[ERROR] 生成失败 {post.title}: {e}")
        
        print(f"文章生成完成，共 {generated_count} 篇")
        await self.http_client.aclose()
        return generated_count
        
    async def _download_cover_image(self, image_url: str, post_slug: str) -> str:
        """Download cover image and return relative path"""
        try:
            # Extract image ID for consistent naming
            image_id = self._extract_notion_image_id(image_url)
            if not image_id:
                image_id = str(hash(image_url))
            
            # Get file extension from URL or content type
            ext = ".jpg"  # default
            if "." in image_url:
                url_ext = image_url.split(".")[-1].lower()
                if url_ext in ["jpg", "jpeg", "png", "gif", "webp"]:
                    ext = f".{url_ext}"
            
            # Download image
            filename = f"{post_slug}-{image_id}{ext}"
            local_path = self.images_dir / filename
            
            async with self.http_client.stream("GET", image_url) as response:
                response.raise_for_status()
                with open(local_path, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
            
            return f"/images/{filename}"
        except Exception as e:
            print(f"[ERROR] Failed to download cover image: {e}")
            raise

    async def _generate_post_file(self, post: NotionPost, content: str):
        """生成单篇文章"""
        # 处理内容中的图片
        processed_content = await self._process_images(content, post.slug)

        cover_path = None
        if post.cover_url:
            try:
                cover_path = await self._download_cover_image(post.cover_url, post.slug)
            except Exception as e:
                print(f"[WARNING] Failed to download cover image: {e}")
        
        # 创建 front matter
        front_matter = {
            "title": post.title,
            "date": post.date,
            "lastmod": post.last_edited_time.split("T")[0],
            "slug": post.slug,
            "tags": post.tags,
            "draft": not post.is_published(),
            "summary": post.excerpt,
            "description": post.excerpt,  # 添加 description 字段用于主题显示
            "notion_id": post.id,
            "type": post.post_type,
        }

        if cover_path:
            front_matter["image"] = cover_path
        
        # 创建 post 对象
        post_obj = frontmatter.Post(processed_content, **front_matter)
        
        # 根据文章类型选择目录
        if post.is_page():
            # Page 类型直接放在 content 目录下
            filepath = self.config.pages_dir / f"{post.slug}.md"
        else:
            # Post 类型放在 posts 目录下
            filepath = self.config.content_dir / f"{post.slug}.md"
        
        # 写入文件
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post_obj))
        
        print(f"[OK] 生成文章: {filepath.name}")
    
    async def _process_images(self, content: str, post_slug: str) -> str:
        """处理文章中的图片"""
        # 匹配 Markdown 图片语法
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        
        async def download_and_replace(match):
            alt_text = match.group(1)
            image_url = match.group(2)
            
            # 跳过已经是本地路径的图片
            if not image_url.startswith(("http://", "https://")):
                return match.group(0)
            
            try:
                # 从 Notion URL 中提取稳定的文件 ID
                image_id = self._extract_notion_image_id(image_url)
                
                # 检查图片是否已存在（基于文件 ID）
                existing_file = self._find_existing_image(image_id)
                if existing_file:
                    relative_path = f"/images/{existing_file.name}"
                    print(f"[OK] 使用已存在的图片: {existing_file.name}")
                    return f"![{alt_text}]({relative_path})"
                
                # 下载图片
                response = await self.http_client.get(image_url)
                response.raise_for_status()
                
                # 获取文件扩展名
                content_type = response.headers.get("content-type", "")
                if "jpeg" in content_type or "jpg" in content_type:
                    ext = ".jpg"
                elif "png" in content_type:
                    ext = ".png"
                elif "gif" in content_type:
                    ext = ".gif"
                elif "webp" in content_type:
                    ext = ".webp"
                else:
                    ext = ".jpg"  # 默认扩展名
                
                # 生成本地文件名：post_slug-image_id.ext
                filename = f"{post_slug}-{image_id}{ext}"
                local_path = self.images_dir / filename
                
                # 保存图片
                with open(local_path, "wb") as f:
                    f.write(response.content)
                
                # 返回新的 Markdown 语法
                relative_path = f"/images/{filename}"
                return f"![{alt_text}]({relative_path})"
                
            except Exception as e:
                print(f"[WARNING] 下载图片失败 {image_url}: {e}")
                return match.group(0)
        
        # 使用异步处理所有图片
        tasks = []
        for match in re.finditer(image_pattern, content):
            tasks.append(download_and_replace(match))
        
        if tasks:
            results = await asyncio.gather(*tasks)
            # 替换原内容中的图片链接
            for i, match in enumerate(re.finditer(image_pattern, content)):
                content = content.replace(match.group(0), results[i], 1)
        
        return content
    
    def _extract_notion_image_id(self, image_url: str) -> str:
        """从 Notion 图片 URL 中提取稳定的文件 ID"""
        import hashlib
        
        # Notion 图片 URL 格式通常为：
        # https://prod-files-secure.s3.us-west-2.amazonaws.com/USER_ID/FILE_ID/IMAGE_ID/file_name?expires=...
        # 或者
        # https://file.notion.so/f/FILE_ID/IMAGE_ID/file_name?expires=...
        
        try:
            # 方法1：从 URL 路径中提取文件 ID
            if "file.notion.so" in image_url:
                # 格式：https://file.notion.so/f/FILE_ID/...
                parts = image_url.split("/f/")
                if len(parts) > 1:
                    file_id = parts[1].split("/")[0]
                    return file_id[:8]  # 取前8位
            
            elif "s3.amazonaws.com" in image_url:
                # 格式：https://prod-files-secure.s3.us-west-2.amazonaws.com/USER_ID/FILE_ID/...
                # 查找包含 amazonaws.com 的段，然后取后面的第2个段
                parts = image_url.split("/")
                try:
                    # 找到包含 amazonaws.com 的段
                    for i, part in enumerate(parts):
                        if "amazonaws.com" in part and i + 2 < len(parts):
                            file_id = parts[i + 2]  # USER_ID 后面的段是 FILE_ID
                            if len(file_id) >= 8:
                                return file_id[:8]
                except (ValueError, IndexError):
                    pass
                
                # 备用方法：查找可能的文件 ID 模式
                for part in parts:
                    # 查找看起来像文件 ID 的段（包含字母数字，长度合适）
                    if len(part) >= 8 and any(c.isalpha() for c in part) and any(c.isdigit() for c in part):
                        return part[:8]
            
            # 方法2：如果无法提取文件 ID，使用 URL 的稳定部分生成哈希
            # 移除查询参数（包含时间戳和签名）
            stable_url = image_url.split("?")[0]
            # 移除可能的临时路径部分
            stable_url = re.sub(r'/[^/]*expires[^/]*', '', stable_url)
            
            # 生成稳定哈希
            return hashlib.md5(stable_url.encode()).hexdigest()[:8]
            
        except Exception:
            # 如果所有方法都失败，使用完整的 URL 哈希
            return hashlib.md5(image_url.encode()).hexdigest()[:8]
    
    def _find_existing_image(self, image_id: str) -> Optional[Path]:
        """查找是否已存在相同 ID 的图片"""
        if not self.images_dir.exists():
            return None
        
        # 查找所有包含该图片 ID 的文件
        for image_file in self.images_dir.glob(f"*-{image_id}.*"):
            if image_file.is_file():
                return image_file
        
        return None
    
    def clean_old_posts(self, current_posts: List[NotionPost]):
        """清理不再存在的文章"""
        current_slugs = {post.slug for post in current_posts}
        
        # 扫描现有文件
        existing_files = list(self.config.content_dir.glob("*.md"))
        
        for filepath in existing_files:
            try:
                # 读取文件获取 slug
                with open(filepath, "r", encoding="utf-8") as f:
                    post_obj = frontmatter.load(f)
                    slug = post_obj.get("slug", "")
                
                # 如果文章不在当前列表中，删除文件
                if slug and slug not in current_slugs:
                    filepath.unlink()
                    print(f"[WARNING] 删除旧文章: {filepath.name}")
                    
            except Exception as e:
                print(f"[ERROR] 处理文件失败 {filepath}: {e}")
    
    def clean_unused_images(self, current_posts: List[NotionPost]):
        """清理无用的图片文件"""
        if not self.images_dir.exists():
            return
        
        # 获取所有当前文章中使用的图片
        used_images = set()
        for post in current_posts:
            try:
                # 读取文章内容
                post_file = self.config.content_dir / f"{post.slug}.md"
                if post_file.exists():
                    with open(post_file, "r", encoding="utf-8") as f:
                        content = f.read()
                        # 提取图片路径
                        import re
                        image_matches = re.findall(r'!\[([^\]]*)\]\(/images/([^)]+)\)', content)
                        used_images.update(image_matches)
            except Exception as e:
                print(f"[ERROR] 读取文章 {post.slug} 失败: {e}")
        
        # 扫描所有图片文件
        all_images = set()
        for image_file in self.images_dir.glob("*.*"):
            if image_file.is_file() and image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                all_images.add(image_file.name)
        
        # 删除未使用的图片
        unused_images = all_images - used_images
        for image_name in unused_images:
            try:
                (self.images_dir / image_name).unlink()
                print(f"[OK] 删除无用图片: {image_name}")
            except Exception as e:
                print(f"[ERROR] 删除图片失败 {image_name}: {e}")
        
        if unused_images:
            print(f"[OK] 清理完成，删除了 {len(unused_images)} 个无用图片")
        else:
            print("[OK] 没有无用图片需要清理")
    
    def generate_index(self):
        """生成首页（可选）"""
        index_content = """---
title: "我的博客"
---

欢迎来到我的博客！这里使用 Notion 作为内容管理系统，通过 Hugo 生成静态网站。

## 最新文章

{{< recent_posts >}}
"""
        index_path = self.config.content_dir.parent / "_index.md"
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(index_content)
