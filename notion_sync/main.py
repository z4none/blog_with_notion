"""
主同步模块
整合 Notion 客户端和 Hugo 生成器
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import click
from rich.console import Console
from rich.table import Table

from .config import SyncConfig, get_config
from .notion_client import NotionClient, NotionPost
from .hugo_generator import HugoGenerator


class BlogSyncer:
    """博客同步器主类"""
    
    def __init__(self, config: Optional[SyncConfig] = None):
        self.config = config or get_config()
        self.console = Console()
        
        # 初始化客户端
        self.notion_client = NotionClient(self.config.notion)
        self.hugo_generator = HugoGenerator(self.config.hugo)
    
    async def sync(self, force: bool = False) -> bool:
        """执行同步操作"""
        try:
            print("开始同步 Notion 到 Hugo...")
            
            # 从 Notion 获取所有文章
            posts = await self.notion_client.get_posts()
            
            if not posts:
                print("[OK] 没有找到文章")
                return True
            
            # 显示同步概览
            self._show_sync_summary(posts)
            
            # 清理旧文章
            self.hugo_generator.clean_old_posts(posts)
            
            # 生成 Hugo 文章
            generated_count = await self.hugo_generator.generate_posts(posts, self.notion_client)
            
            print(f"[OK] 同步完成！生成了 {generated_count} 篇文章")
            return True
            
        except Exception as e:
            print(f"[ERROR] 同步失败: {e}")
            return False
    
    def _show_sync_summary(self, posts):
        """显示同步概览"""
        published_count = sum(1 for post in posts if post.is_published())
        draft_count = len(posts) - published_count
        
        print(f"同步概览:")
        print(f"  发布文章: {published_count} 篇")
        print(f"  草稿文章: {draft_count} 篇")
        print(f"  总计: {len(posts)} 篇")
        
        # 显示文章列表
        if len(posts) <= 10:
            posts_table = Table(title="文章列表")
            posts_table.add_column("标题", style="cyan")
            posts_table.add_column("状态", style="green")
            posts_table.add_column("标签", style="yellow")
            
            for post in posts:
                status = "发布" if post.is_published() else "草稿"
                tags = ", ".join(post.tags) if post.tags else "无"
                posts_table.add_row(post.title, status, tags)
            
            self.console.print(posts_table)


def cli():
    """Notion-Hugo 同步工具"""
    
    @click.group()
    def main():
        """Notion-Hugo 同步工具"""
        pass
    
    @main.command()
    @click.option("--clean", is_flag=True, help="清理无用的图片文件")
    def sync(clean):
        """同步 Notion 内容到 Hugo"""
        syncer = BlogSyncer()
        
        async def run_sync():
            success = await syncer.sync()
            
            # 如果指定了清理选项，清理无用图片
            if success and clean:
                print("\n开始清理无用图片...")
                # 需要重新获取文章列表来进行清理
                posts = await syncer.notion_client.get_posts()
                syncer.hugo_generator.clean_unused_images(posts)
            
            sys.exit(0 if success else 1)
        
        asyncio.run(run_sync())

    main()
