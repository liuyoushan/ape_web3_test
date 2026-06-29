"""
==============================================================================
HTTP 客户端模块
==============================================================================
支持特性：
  - 统一的请求封装（GET/POST/PUT/DELETE）
  - 超时控制
  - 错误处理和重试
  - 请求日志
  - 响应验证
==============================================================================
"""

import time
import requests
from typing import Dict, Any, Optional, Union
from framework.core.logger import log
from framework.core.retry_helper import RetryHelper


class HTTPClient:
    """
    HTTP 客户端
    
    使用方式：
        client = HTTPClient(base_url="https://api.example.com")
        response = client.get("/users")
        response = client.post("/users", json={"name": "test"})
        
        # 带重试
        response = client.get_with_retry("/users", max_retries=3)
    """
    
    def __init__(
        self,
        base_url: str = "",
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
        retry_helper: Optional[RetryHelper] = None
    ):
        """
        初始化 HTTP 客户端
        
        Args:
            base_url: 基础 URL
            timeout: 超时时间（秒）
            headers: 默认请求头
            retry_helper: 重试助手
        """
        self.base_url = base_url
        self.timeout = timeout
        self.headers = headers or {}
        self.retry_helper = retry_helper or RetryHelper(max_retries=3)
        
        # 创建 Session
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> requests.Response:
        """
        发送请求
        
        Args:
            method: HTTP 方法
            endpoint: API 路径
            params: 查询参数
            json: JSON 数据
            data: 表单数据
            headers: 请求头
            timeout: 超时时间
            **kwargs: 其他参数
            
        Returns:
            响应对象
        """
        url = f"{self.base_url}{endpoint}"
        timeout = timeout or self.timeout
        
        # 合并请求头
        request_headers = {**self.headers, **(headers or {})}
        
        log.debug(f"HTTP {method} {url}")
        if json:
            log.debug(f"Request JSON: {json}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                data=data,
                headers=request_headers,
                timeout=timeout,
                **kwargs
            )
            
            log.debug(f"Response: {response.status_code}")
            return response
            
        except requests.exceptions.RequestException as e:
            log.error(f"HTTP 请求失败: {e}")
            raise
    
    def get(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """GET 请求"""
        return self.request("GET", endpoint, params=params, headers=headers, **kwargs)
    
    def post(
        self,
        endpoint: str,
        json: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """POST 请求"""
        return self.request("POST", endpoint, json=json, data=data, headers=headers, **kwargs)
    
    def put(
        self,
        endpoint: str,
        json: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """PUT 请求"""
        return self.request("PUT", endpoint, json=json, data=data, headers=headers, **kwargs)
    
    def delete(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """DELETE 请求"""
        return self.request("DELETE", endpoint, params=params, headers=headers, **kwargs)
    
    def get_with_retry(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        max_retries: int = 3,
        delay: float = 1.0,
        **kwargs
    ) -> requests.Response:
        """带重试的 GET 请求"""
        helper = RetryHelper(max_retries=max_retries, delay=delay)
        return helper.retry(
            lambda: self.get(endpoint, params=params, **kwargs)
        )
    
    def post_with_retry(
        self,
        endpoint: str,
        json: Optional[Dict] = None,
        max_retries: int = 3,
        delay: float = 1.0,
        **kwargs
    ) -> requests.Response:
        """带重试的 POST 请求"""
        helper = RetryHelper(max_retries=max_retries, delay=delay)
        return helper.retry(
            lambda: self.post(endpoint, json=json, **kwargs)
        )
    
    def close(self):
        """关闭 Session"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 全局 HTTP 客户端（需要配置 base_url）
http_client = HTTPClient()