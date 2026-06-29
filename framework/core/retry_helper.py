"""
==============================================================================
重试机制模块
==============================================================================
支持特性：
  - 装饰器方式：@retry_on_failure
  - 手动方式：RetryHelper.retry()
  - 可配置：重试次数、延迟、退避策略
  - 异常过滤：指定重试的异常类型
==============================================================================
"""

import time
import random
from typing import Callable, Type, Tuple, Optional, Any
from functools import wraps


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    jitter: bool = True
):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 退避因子（每次重试延迟 *= backoff）
        exceptions: 重试的异常类型
        jitter: 是否添加随机抖动
        
    Example:
        @retry_on_failure(max_retries=3, delay=1.0)
        def unstable_operation():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # 最后一次重试失败，抛出异常
                        raise
                    
                    # 计算延迟（带抖动）
                    actual_delay = current_delay
                    if jitter:
                        actual_delay += random.uniform(0, 0.1 * current_delay)
                    
                    time.sleep(actual_delay)
                    current_delay *= backoff
            
            # 理论上不会到达这里
            raise last_exception
        
        return wrapper
    return decorator


class RetryHelper:
    """
    手动重试助手
    
    使用方式：
        helper = RetryHelper(max_retries=3, delay=1.0)
        result = helper.retry(lambda: api.call())
        
        # 或使用上下文管理器
        with helper.context() as ctx:
            result = some_operation()
            ctx.retry_if_failed()
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        jitter: bool = True
    ):
        """
        初始化重试助手
        
        Args:
            max_retries: 最大重试次数
            delay: 初始延迟（秒）
            backoff: 退避因子
            exceptions: 重试的异常类型
            jitter: 是否添加随机抖动
        """
        self.max_retries = max_retries
        self.delay = delay
        self.backoff = backoff
        self.exceptions = exceptions
        self.jitter = jitter
    
    def retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        执行重试
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数返回值
        """
        last_exception = None
        current_delay = self.delay
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except self.exceptions as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    raise
                
                actual_delay = current_delay
                if self.jitter:
                    actual_delay += random.uniform(0, 0.1 * current_delay)
                
                time.sleep(actual_delay)
                current_delay *= self.backoff
        
        raise last_exception
    
    def retry_with_condition(
        self,
        func: Callable,
        condition: Callable[[Any], bool],
        *args,
        **kwargs
    ) -> Any:
        """
        条件重试
        
        Args:
            func: 要执行的函数
            condition: 条件函数，返回 False 时重试
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数返回值
        """
        current_delay = self.delay
        
        for attempt in range(self.max_retries + 1):
            result = func(*args, **kwargs)
            
            if condition(result):
                return result
            
            if attempt == self.max_retries:
                raise RuntimeError(f"Condition not satisfied after {self.max_retries} retries")
            
            actual_delay = current_delay
            if self.jitter:
                actual_delay += random.uniform(0, 0.1 * current_delay)
            
            time.sleep(actual_delay)
            current_delay *= self.backoff
        
        raise RuntimeError("Max retries exceeded")


# 全局重试助手
retry_helper = RetryHelper()