"""
Notion API 客户端
处理与 Notion 数据库的交互
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from notion_client import Client
import httpx

from .config import NotionConfig


class NotionPost:
    """Notion 博客文章数据模型"""
    
    def __init__(self, page_data: Dict[str, Any]):
        self.page_data = page_data
        self.id = page_data["id"]
        self.properties = page_data["properties"]
        self.created_time = page_data["created_time"]
        self.last_edited_time = page_data["last_edited_time"]
        
    @property
    def title(self) -> str:
        """获取标题"""
        title_prop = self.properties.get("Title", self.properties.get("title", {}))
        if title_prop.get("type") == "title":
            title_content = title_prop.get("title", [])
            if title_content:
                # 合并所有文本片段
                full_title = "".join([item["text"]["content"] for item in title_content])
                return full_title
        return ""
       
    
    @property
    def slug(self) -> str:
        """获取 slug"""
        slug_prop = self.properties.get("Slug", self.properties.get("slug", {}))
        if slug_prop.get("type") == "rich_text" and slug_prop.get("rich_text"):
            # 合并所有文本片段
            full_slug = "".join([item["text"]["content"] for item in slug_prop["rich_text"]])
            return full_slug
        return ""
    
    @property
    def tags(self) -> List[str]:
        """获取标签"""
        tags_prop = self.properties.get("Tags", self.properties.get("tags", {}))
        if tags_prop.get("type") == "multi_select":
            return [tag["name"] for tag in tags_prop.get("multi_select", [])]
        return []
    
    @property
    def status(self) -> str:
        """获取状态"""
        status_prop = self.properties.get("Status", self.properties.get("status", {}))
        if status_prop.get("type") == "select":
            return status_prop.get("select", {}).get("name", "Draft")
        return "Draft"
    
    @property
    def date(self) -> str:
        """获取日期"""
        date_prop = self.properties.get("Date", self.properties.get("date", {}))
        if date_prop.get("type") == "date" and date_prop.get("date"):
            return date_prop["date"]["start"]
        return self.created_time.split("T")[0]
    
    @property
    def excerpt(self) -> str:
        """获取摘要"""
        excerpt_prop = self.properties.get("Excerpt", self.properties.get("excerpt", {}))
        if excerpt_prop.get("type") == "rich_text" and excerpt_prop.get("rich_text"):
            # 合并所有文本片段
            full_excerpt = "".join([item["text"]["content"] for item in excerpt_prop["rich_text"]])
            return full_excerpt
        return ""
    
    @property
    def post_type(self) -> str:
        """获取文章类型 (Post 或 Page)"""
        type_prop = self.properties.get("Type", self.properties.get("type", {}))
        if type_prop.get("type") == "select":
            return type_prop.get("select", {}).get("name", "Post")
        return "Post"
    
    def is_published(self) -> bool:
        """检查是否为发布状态"""
        return self.status.lower() != "draft"
    
    def is_page(self) -> bool:
        """检查是否为页面"""
        return self.post_type == "Page"

    @property
    def cover_url(self) -> Optional[str]:
        """Get cover image URL if exists"""
        if not self.page_data.get("cover"):
            return None
            
        cover = self.page_data["cover"]
        if cover.get("type") == "external":
            return cover["external"]["url"]
        elif cover.get("type") == "file":
            return cover["file"]["url"]
        return None


class NotionClient:
    """Notion API 客户端封装"""
    
    def __init__(self, config: NotionConfig):
        self.config = config
        self.client = Client(auth=config.token)
        print(f'NotionClient init with token: {config.token}')
    
    async def get_posts(self) -> List[NotionPost]:
        """获取博客文章列表"""
        try:
            print("正在从 Notion 获取文章...")
            
            # 查询所有文章
            response = self.client.search(
                sort={
                    "timestamp": "last_edited_time",
                    "direction": "descending"
                }
            )
            
            results = response.get("results", [])
            
            # 过滤掉没有标题的文章
            valid_posts = []
            for page in results:
                post = NotionPost(page)
                # 检查是否有有效标题（不是默认的无标题文章）
                if post.title:
                    valid_posts.append(post)
            
            print(f"找到 {len(valid_posts)} 篇文章")
            return valid_posts
            
        except Exception as e:
            print(f"获取文章失败: {e}")
            return []
    
    async def get_page_content(self, page_id: str) -> str:
        """获取页面内容（正文）"""
        try:
            # 获取页面的 blocks（内容块）
            blocks = self.client.blocks.children.list(block_id=page_id)
            
            # 将 blocks 转换为 Markdown
            content_parts = []
            for block in blocks.get("results", []):
                content_parts.append(self._block_to_markdown(block))
            
            return "\n\n".join(content_parts)
            
        except Exception as e:
            print(f"获取页面内容失败: {e}")
            return ""
    
    def _block_to_markdown(self, block: Dict[str, Any]) -> str:
        """将 Notion block 转换为 Markdown"""
        block_type = block.get("type", "")
        
        if block_type == "paragraph":
            text = self._extract_rich_text(block.get("paragraph", {}).get("rich_text", []))
            return text if text else ""
        
        elif block_type == "heading_1":
            text = self._extract_rich_text(block.get("heading_1", {}).get("rich_text", []))
            return f"# {text}" if text else ""
        
        elif block_type == "heading_2":
            text = self._extract_rich_text(block.get("heading_2", {}).get("rich_text", []))
            return f"## {text}" if text else ""
        
        elif block_type == "heading_3":
            text = self._extract_rich_text(block.get("heading_3", {}).get("rich_text", []))
            return f"### {text}" if text else ""
        
        elif block_type == "bulleted_list_item":
            text = self._extract_rich_text(block.get("bulleted_list_item", {}).get("rich_text", []))
            return f"- {text}" if text else ""
        
        elif block_type == "numbered_list_item":
            text = self._extract_rich_text(block.get("numbered_list_item", {}).get("rich_text", []))
            return f"1. {text}" if text else ""
        
        elif block_type == "code":
            text = self._extract_rich_text(block.get("code", {}).get("rich_text", []))
            language = block.get("code", {}).get("language", "")
            return f"```{language}\n{text}\n```" if text else ""
        
        elif block_type == "image":
            image_url = block.get("image", {}).get("file", {}).get("url", "") or \
                       block.get("image", {}).get("external", {}).get("url", "")
            return f"![image]({image_url})" if image_url else ""
        
        return ""
    
    def _extract_rich_text(self, rich_text: List[Dict[str, Any]]) -> str:
        """从富文本中提取纯文本"""
        result = []
        for text_item in rich_text:
            content = text_item.get("text", {}).get("content", "")
            if text_item.get("text", {}).get("link"):
                url = text_item["text"]["link"]["url"]
                content = f"[{content}]({url})"
            
            # 处理格式
            if text_item.get("annotations", {}).get("bold"):
                content = f"**{content}**"
            if text_item.get("annotations", {}).get("italic"):
                content = f"*{content}*"
            if text_item.get("annotations", {}).get("strikethrough"):
                content = f"~~{content}~~"
            if text_item.get("annotations", {}).get("code"):
                content = f"`{content}`"
            
            result.append(content)
        
        return "".join(result)
