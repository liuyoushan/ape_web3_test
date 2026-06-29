"""
==============================================================================
测试数据工厂
==============================================================================
支持特性：
  - 生成唯一用户名、邮箱、钱包地址等
  - 避免并发测试数据冲突
  - 支持自定义前缀和格式
==============================================================================
"""

import uuid
import random
import string
import time
from typing import Dict, Any, Optional


class TestDataFactory:
    """
    测试数据工厂
    
    使用方式：
        factory = TestDataFactory()
        
        # 基础数据
        unique_id = factory.unique_id()
        username = factory.unique_username()
        email = factory.unique_email()
        
        # Web3 数据
        wallet_address = factory.unique_wallet_address()
        tx_hash = factory.random_tx_hash()
        token_amount = factory.random_token_amount()
        
        # 完整数据
        user_data = TestDataFactory.create_user_data()
        tx_data = TestDataFactory.create_transaction_data()
    """
    
    def __init__(self, prefix: Optional[str] = None):
        """
        初始化工厂
        
        Args:
            prefix: 数据前缀（可选）
        """
        self.prefix = prefix or ""
        self._counter = 0
    
    def unique_id(self) -> str:
        """生成唯一 ID"""
        self._counter += 1
        timestamp = int(time.time() * 1000)
        return f"{self.prefix}{timestamp}_{self._counter}"
    
    def timestamp(self) -> int:
        """当前时间戳"""
        return int(time.time())
    
    def unique_username(self, length: int = 8) -> str:
        """生成唯一用户名"""
        base = self._random_string(length)
        suffix = self.unique_id()[:8]
        return f"{self.prefix}{base}_{suffix}"
    
    def unique_email(self, domain: str = "test.com") -> str:
        """生成唯一邮箱"""
        username = self.unique_username()
        return f"{username}@{domain}"
    
    def random_password(self, length: int = 12) -> str:
        """生成随机密码"""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choice(chars) for _ in range(length))
    
    def random_phone(self) -> str:
        """生成随机手机号"""
        return f"1{random.randint(30, 99)}{random.randint(10000000, 99999999)}"
    
    def unique_wallet_address(self) -> str:
        """生成唯一钱包地址"""
        return f"0x{uuid.uuid4().hex[:40]}"
    
    def random_tx_hash(self) -> str:
        """生成随机交易哈希"""
        return f"0x{uuid.uuid4().hex}"
    
    def random_token_amount(self, min: float = 1.0, max: float = 1000.0, decimals: int = 18) -> int:
        """
        生成随机代币金额
        
        Args:
            min: 最小金额
            max: 最大金额
            decimals: 小数位数
            
        Returns:
            wei 单位的金额
        """
        amount = random.uniform(min, max)
        return int(amount * 10 ** decimals)
    
    def random_block_number(self, min: int = 1, max: int = 10000000) -> int:
        """生成随机区块号"""
        return random.randint(min, max)
    
    def random_gas_price(self, min: int = 1, max: int = 100) -> int:
        """生成随机 Gas 价格（Gwei）"""
        return random.randint(min, max) * 10 ** 9
    
    def _random_string(self, length: int) -> str:
        """生成随机字符串"""
        return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))
    
    @staticmethod
    def create_user_data(**kwargs) -> Dict[str, Any]:
        """
        创建用户数据
        
        Args:
            **kwargs: 自定义字段
            
        Returns:
            用户数据字典
        """
        factory = TestDataFactory()
        data = {
            "username": factory.unique_username(),
            "email": factory.unique_email(),
            "password": factory.random_password(),
            "phone": factory.random_phone(),
        }
        data.update(kwargs)
        return data
    
    @staticmethod
    def create_transaction_data(**kwargs) -> Dict[str, Any]:
        """
        创建交易数据
        
        Args:
            **kwargs: 自定义字段
            
        Returns:
            交易数据字典
        """
        factory = TestDataFactory()
        data = {
            "from": factory.unique_wallet_address(),
            "to": factory.unique_wallet_address(),
            "value": factory.random_token_amount(),
            "gas": random.randint(21000, 100000),
            "gasPrice": factory.random_gas_price(),
        }
        data.update(kwargs)
        return data
    
    @staticmethod
    def create_contract_data(**kwargs) -> Dict[str, Any]:
        """
        创建合约数据
        
        Args:
            **kwargs: 自定义字段
            
        Returns:
            合约数据字典
        """
        factory = TestDataFactory()
        data = {
            "address": factory.unique_wallet_address(),
            "abi": [],
            "bytecode": f"0x{uuid.uuid4().hex}",
        }
        data.update(kwargs)
        return data


# 全局工厂实例
factory = TestDataFactory()