"""
配置管理模块
处理环境变量和配置文件
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

# 自动加载 .env 文件
try:
    from dotenv import load_dotenv
    # 尝试加载项目根目录的 .env 文件
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"已加载环境变量文件: {env_file}")
except ImportError:
    print("警告: 未安装 python-dotenv，无法自动加载 .env 文件")
    print("请运行: uv add python-dotenv")


class NotionConfig(BaseModel):
    """Notion API 配置"""
    token: str = Field(..., description="Notion API token")
    database_id: str = Field(..., description="Notion database ID")
    
    @classmethod
    def from_env(cls) -> "NotionConfig":
        """从环境变量加载配置"""
        return cls(
            token=os.getenv("NOTION_TOKEN", ""),
            database_id=os.getenv("NOTION_DATABASE_ID", ""),
        )


class HugoConfig(BaseModel):
    """Hugo 配置"""
    content_dir: Path = Field(default=Path("hugo/content/posts"), description="Hugo 内容目录")
    pages_dir: Path = Field(default=Path("hugo/content"), description="Hugo 页面目录")
    static_dir: Path = Field(default=Path("hugo/static"), description="Hugo 静态资源目录")
    images_dir: Path = Field(default=Path("hugo/static/images"), description="图片存储目录")


class SyncConfig(BaseModel):
    """同步配置"""
    notion: NotionConfig
    hugo: HugoConfig
    
    @classmethod
    def from_env(cls) -> "SyncConfig":
        """从环境变量创建配置"""
        return cls(
            notion=NotionConfig.from_env(),
            hugo=HugoConfig(),
        )


def get_config() -> SyncConfig:
    """获取配置实例"""
    return SyncConfig.from_env()
