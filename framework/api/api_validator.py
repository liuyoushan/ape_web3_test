"""
==============================================================================
API 响应验证器
==============================================================================
支持特性：
  - 状态码验证
  - JSON Schema 验证
  - 响应时间验证
  - 自定义验证规则
==============================================================================
"""

import time
from typing import Dict, Any, List, Optional, Union
import requests
from framework.core.logger import log


class APIValidator:
    """
    API 响应验证器
    
    使用方式：
        validator = APIValidator()
        
        # 状态码验证
        validator.validate_status_code(response, 200)
        validator.validate_status_code_in(response, [200, 201])
        
        # 响应时间验证
        validator.validate_response_time(response, max_time=5.0)
        
        # JSON 结构验证
        validator.validate_json_keys(response, ["id", "name"])
        validator.validate_json_value(response, "status", "success")
        
        # 完整验证
        validator.validate_response(response, status_code=200, json_keys=["id"])
    """
    
    def validate_status_code(
        self,
        response: requests.Response,
        expected: int
    ) -> bool:
        """
        验证状态码
        
        Args:
            response: 响应对象
            expected: 预期状态码
            
        Returns:
            是否匹配
            
        Raises:
            AssertionError: 状态码不匹配
        """
        actual = response.status_code
        
        if actual != expected:
            log.error(f"状态码验证失败: 期望 {expected}, 实际 {actual}")
            raise AssertionError(f"状态码不匹配: 期望 {expected}, 实际 {actual}")
        
        log.success(f"状态码验证成功: {actual}")
        return True
    
    def validate_status_code_in(
        self,
        response: requests.Response,
        expected_list: List[int]
    ) -> bool:
        """
        验证状态码在预期列表中
        
        Args:
            response: 响应对象
            expected_list: 预期状态码列表
            
        Returns:
            是否匹配
            
        Raises:
            AssertionError: 状态码不匹配
        """
        actual = response.status_code
        
        if actual not in expected_list:
            log.error(f"状态码验证失败: 期望 {expected_list}, 实际 {actual}")
            raise AssertionError(f"状态码不在预期列表中: 期望 {expected_list}, 实际 {actual}")
        
        log.success(f"状态码验证成功: {actual}")
        return True
    
    def validate_response_time(
        self,
        response: requests.Response,
        max_time: float
    ) -> bool:
        """
        验证响应时间
        
        Args:
            response: 响应对象
            max_time: 最大时间（秒）
            
        Returns:
            是否符合
            
        Raises:
            AssertionError: 响应时间超时
        """
        actual_time = response.elapsed.total_seconds()
        
        if actual_time > max_time:
            log.error(f"响应时间验证失败: 最大 {max_time}s, 实际 {actual_time:.2f}s")
            raise AssertionError(f"响应时间超时: 最大 {max_time}s, 实际 {actual_time:.2f}s")
        
        log.success(f"响应时间验证成功: {actual_time:.2f}s")
        return True
    
    def validate_json_keys(
        self,
        response: requests.Response,
        expected_keys: List[str]
    ) -> bool:
        """
        验证 JSON 响应包含指定键
        
        Args:
            response: 响应对象
            expected_keys: 预期键列表
            
        Returns:
            是否包含
            
        Raises:
            AssertionError: 缺少键
        """
        try:
            json_data = response.json()
        except Exception as e:
            log.error(f"JSON 解析失败: {e}")
            raise AssertionError(f"响应不是有效的 JSON: {e}")
        
        missing_keys = []
        for key in expected_keys:
            if key not in json_data:
                missing_keys.append(key)
        
        if missing_keys:
            log.error(f"JSON 键验证失败: 缺少 {missing_keys}")
            raise AssertionError(f"响应缺少键: {missing_keys}")
        
        log.success(f"JSON 键验证成功: {expected_keys}")
        return True
    
    def validate_json_value(
        self,
        response: requests.Response,
        key: str,
        expected_value: Any
    ) -> bool:
        """
        验证 JSON 响应中指定键的值
        
        Args:
            response: 响应对象
            key: 键名
            expected_value: 预期值
            
        Returns:
            是否匹配
            
        Raises:
            AssertionError: 值不匹配
        """
        try:
            json_data = response.json()
        except Exception as e:
            log.error(f"JSON 解析失败: {e}")
            raise AssertionError(f"响应不是有效的 JSON: {e}")
        
        if key not in json_data:
            log.error(f"JSON 键不存在: {key}")
            raise AssertionError(f"响应不包含键: {key}")
        
        actual_value = json_data[key]
        
        if actual_value != expected_value:
            log.error(f"JSON 值验证失败: 期望 {expected_value}, 实际 {actual_value}")
            raise AssertionError(f"键 '{key}' 的值不匹配: 期望 {expected_value}, 实际 {actual_value}")
        
        log.success(f"JSON 值验证成功: {key} = {actual_value}")
        return True
    
    def validate_json_type(
        self,
        response: requests.Response,
        key: str,
        expected_type: type
    ) -> bool:
        """
        验证 JSON 响应中指定键的类型
        
        Args:
            response: 响应对象
            key: 键名
            expected_type: 预期类型
            
        Returns:
            是否匹配
            
        Raises:
            AssertionError: 类型不匹配
        """
        try:
            json_data = response.json()
        except Exception as e:
            log.error(f"JSON 解析失败: {e}")
            raise AssertionError(f"响应不是有效的 JSON: {e}")
        
        if key not in json_data:
            log.error(f"JSON 键不存在: {key}")
            raise AssertionError(f"响应不包含键: {key}")
        
        actual_value = json_data[key]
        actual_type = type(actual_value)
        
        if not isinstance(actual_value, expected_type):
            log.error(f"JSON 类型验证失败: 期望 {expected_type.__name__}, 实际 {actual_type.__name__}")
            raise AssertionError(f"键 '{key}' 的类型不匹配: 期望 {expected_type.__name__}, 实际 {actual_type.__name__}")
        
        log.success(f"JSON 类型验证成功: {key} 是 {actual_type.__name__}")
        return True
    
    def validate_response(
        self,
        response: requests.Response,
        status_code: Optional[int] = None,
        json_keys: Optional[List[str]] = None,
        max_time: Optional[float] = None
    ) -> bool:
        """
        综合验证
        
        Args:
            response: 响应对象
            status_code: 预期状态码
            json_keys: 预期 JSON 键
            max_time: 最大响应时间
            
        Returns:
            是否全部通过
        """
        results = []
        
        if status_code:
            results.append(self.validate_status_code(response, status_code))
        
        if json_keys:
            results.append(self.validate_json_keys(response, json_keys))
        
        if max_time:
            results.append(self.validate_response_time(response, max_time))
        
        return all(results)


# 全局验证器
api_validator = APIValidator()