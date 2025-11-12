"""
图片处理配置模块
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class ImageNamingStrategy(str, Enum):
    """图片命名策略"""
    HASH = "hash"          # 基于URL哈希
    TIMESTAMP = "timestamp" # 基于时间戳
    SEQUENTIAL = "sequential" # 基于序号


class ImageConfig(BaseModel):
    """图片处理配置"""
    
    # 命名策略
    naming_strategy: ImageNamingStrategy = ImageNamingStrategy.HASH
    
    # 哈希长度（当使用hash策略时）
    hash_length: int = 8
    
    # 是否启用重复检查
    enable_duplicate_check: bool = True
    
    # 支持的图片格式
    supported_formats: list = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    
    # 默认图片格式
    default_format: str = ".jpg"
    
    # 是否自动清理无用图片
    auto_cleanup: bool = False
    
    # 图片文件名模板
    filename_template: str = "{post_slug}-{identifier}{ext}"


# 默认配置
DEFAULT_IMAGE_CONFIG = ImageConfig()


def get_image_config() -> ImageConfig:
    """获取图片配置实例"""
    return DEFAULT_IMAGE_CONFIG
