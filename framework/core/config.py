"""
==============================================================================
配置管理模块
==============================================================================
支持特性：
  - 多环境配置：local、dev、prod
  - 敏感信息存储在 .env 文件
  - YAML 配置文件支持
  - 环境变量覆盖
==============================================================================
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv


class Config:
    """
    统一配置管理器
    
    使用方式：
        config = Config()
        config.get("api.base_url")
        config.get("web3.chain_id", default=1)
        
    配置优先级：
        1. 环境变量（最高）
        2. config/{env}.yaml
        3. config/config.example.yaml（默认）
    """
    
    _instance = None
    _config_data = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置"""
        if self._config_data is None:
            self._load_config()
    
    def _load_config(self):
        """加载配置文件和环境变量"""
        # 加载 .env 文件
        load_dotenv()
        
        # 确定环境
        env = os.environ.get("TEST_ENV", "local")
        
        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent
        
        # 配置文件路径
        config_dir = project_root / "config"
        
        # 加载默认配置
        default_config_path = config_dir / "config.example.yaml"
        env_config_path = config_dir / f"{env}.yaml"
        
        self._config_data = {}
        
        # 加载默认配置
        if default_config_path.exists():
            with open(default_config_path, encoding="utf-8") as f:
                self._config_data = yaml.safe_load(f) or {}
        
        # 加载环境配置（覆盖默认配置）
        if env_config_path.exists():
            with open(env_config_path, encoding="utf-8") as f:
                env_config = yaml.safe_load(f) or {}
                self._deep_merge(self._config_data, env_config)
    
    def _deep_merge(self, base: Dict, override: Dict):
        """深度合并两个字典"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持嵌套（如 "api.base_url"）
            default: 默认值
            
        Returns:
            配置值
        """
        # 先检查环境变量
        env_key = key.replace(".", "_").upper()
        env_value = os.environ.get(env_key)
        if env_value is not None:
            return env_value
        
        # 从配置文件获取
        keys = key.split(".")
        value = self._config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        获取环境变量
        
        Args:
            key: 环境变量名
            default: 默认值
            
        Returns:
            环境变量值
        """
        return os.environ.get(key, default)
    
    def reload(self):
        """重新加载配置"""
        self._config_data = None
        self._load_config()
    
    @property
    def env(self) -> str:
        """当前环境"""
        return os.environ.get("TEST_ENV", "local")
    
    @property
    def is_local(self) -> bool:
        """是否是本地环境"""
        return self.env == "local"
    
    @property
    def is_prod(self) -> bool:
        """是否是生产环境"""
        return self.env == "prod"


# 全局配置实例
config = Config()