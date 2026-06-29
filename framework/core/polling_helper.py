"""
==============================================================================
轮询机制模块
==============================================================================
支持特性：
  - 等待交易回执确认
  - 等待链上状态变化
  - 可配置：超时、轮询间隔、条件判断
  - 支持 Web3.py 和 Ape Framework
==============================================================================
"""

import time
from typing import Callable, Any, Optional
from framework.core.logger import log


class PollingHelper:
    """
    轮询助手
    
    使用方式：
        helper = PollingHelper()
        
        # 等待交易回执
        receipt = helper.poll_transaction_receipt(
            get_receipt_func,
            tx_hash,
            timeout=120.0,
            interval=3.0
        )
        
        # 等待条件满足
        result = helper.poll_until(
            condition_func,
            timeout=60.0,
            interval=1.0
        )
    """
    
    def __init__(self, default_timeout: float = 120.0, default_interval: float = 3.0):
        """
        初始化轮询助手
        
        Args:
            default_timeout: 默认超时时间（秒）
            default_interval: 默认轮询间隔（秒）
        """
        self.default_timeout = default_timeout
        self.default_interval = default_interval
    
    def poll_transaction_receipt(
        self,
        get_receipt_func: Callable,
        tx_hash: str,
        timeout: Optional[float] = None,
        interval: Optional[float] = None
    ) -> Any:
        """
        轮询交易回执
        
        Args:
            get_receipt_func: 获取回执的函数
            tx_hash: 交易哈希
            timeout: 超时时间（秒）
            interval: 轮询间隔（秒）
            
        Returns:
            交易回执
            
        Raises:
            TimeoutError: 超时未获取到回执
        """
        timeout = timeout or self.default_timeout
        interval = interval or self.default_interval
        
        log.debug(f"开始轮询交易回执: {tx_hash}")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            receipt = get_receipt_func(tx_hash)
            
            if receipt is not None:
                log.success(f"获取到交易回执: {tx_hash}")
                return receipt
            
            log.debug(f"交易未确认，等待 {interval} 秒...")
            time.sleep(interval)
        
        raise TimeoutError(f"交易回执轮询超时: {tx_hash}")
    
    def poll_until(
        self,
        condition_func: Callable,
        timeout: Optional[float] = None,
        interval: Optional[float] = None,
        message: Optional[str] = None
    ) -> Any:
        """
        轮询直到条件满足
        
        Args:
            condition_func: 条件函数，返回非 None/False 时停止
            timeout: 超时时间（秒）
            interval: 轮询间隔（秒）
            message: 日志消息
            
        Returns:
            条件函数的返回值
            
        Raises:
            TimeoutError: 超时未满足条件
        """
        timeout = timeout or self.default_timeout
        interval = interval or self.default_interval
        
        log_msg = message or "等待条件满足"
        log.debug(f"{log_msg}，超时: {timeout} 秒")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = condition_func()
            
            if result:
                log.success(f"{log_msg} 完成")
                return result
            
            log.debug(f"条件未满足，等待 {interval} 秒...")
            time.sleep(interval)
        
        raise TimeoutError(f"{log_msg} 超时")
    
    def poll_block_number(
        self,
        web3_client: Any,
        target_block: int,
        timeout: Optional[float] = None,
        interval: Optional[float] = None
    ) -> int:
        """
        轮询区块号
        
        Args:
            web3_client: Web3 客户端
            target_block: 目标区块号
            timeout: 超时时间（秒）
            interval: 轮询间隔（秒）
            
        Returns:
            当前区块号
            
        Raises:
            TimeoutError: 超时未达到目标区块
        """
        timeout = timeout or self.default_timeout
        interval = interval or self.default_interval
        
        log.debug(f"等待区块 #{target_block}")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            current_block = web3_client.eth.block_number
            
            if current_block >= target_block:
                log.success(f"区块已达到 #{current_block}")
                return current_block
            
            log.debug(f"当前区块 #{current_block}，等待 {interval} 秒...")
            time.sleep(interval)
        
        raise TimeoutError(f"区块轮询超时，目标: #{target_block}")
    
    def poll_balance(
        self,
        get_balance_func: Callable,
        address: str,
        expected_balance: int,
        timeout: Optional[float] = None,
        interval: Optional[float] = None
    ) -> int:
        """
        轮询账户余额
        
        Args:
            get_balance_func: 获取余额的函数
            address: 账户地址
            expected_balance: 预期余额
            timeout: 超时时间（秒）
            interval: 轮询间隔（秒）
            
        Returns:
            当前余额
            
        Raises:
            TimeoutError: 超时未达到预期余额
        """
        timeout = timeout or self.default_timeout
        interval = interval or self.default_interval
        
        log.debug(f"等待账户 {address} 余额达到 {expected_balance}")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            balance = get_balance_func(address)
            
            if balance >= expected_balance:
                log.success(f"余额已达到 {balance}")
                return balance
            
            log.debug(f"当前余额 {balance}，等待 {interval} 秒...")
            time.sleep(interval)
        
        raise TimeoutError(f"余额轮询超时")


# 全局轮询助手
polling_helper = PollingHelper()