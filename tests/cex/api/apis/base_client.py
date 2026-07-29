"""
==============================================================================
CEX 基础客户端
==============================================================================
支持特性：
  - API 签名（HMAC SHA256）
  - 请求封装（GET/POST/DELETE）
  - 时间戳生成
  - 错误处理
==============================================================================
"""

import time
import hmac
import hashlib
import requests
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode
from framework.core.logger import log
from framework.core.retry_helper import RetryHelper


class CEXBaseClient:
    """
    CEX API 基础客户端
    
    使用方式：
        client = CEXBaseClient(
            api_key="your_api_key",
            api_secret="your_api_secret",
            base_url="https://api.binance.com"
        )
        
        # 公开接口（无需签名）
        response = client.public_get("/api/v3/ticker/price", {"symbol": "BTCUSDT"})
        
        # 私有接口（需要签名）
        response = client.private_get("/api/v3/account")
        response = client.private_post("/api/v3/order", {"symbol": "BTCUSDT", "side": "BUY", "type": "LIMIT"})
    """
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str,
        timeout: float = 30.0,
        recv_window: int = 5000
    ):
        """
        初始化 CEX 客户端
        
        Args:
            api_key: API Key
            api_secret: API Secret
            base_url: API 基础 URL
            timeout: 超时时间（秒）
            recv_window: 接收窗口（毫秒）
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.timeout = timeout
        self.recv_window = recv_window
        
        # 创建 Session
        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": api_key,
            "Content-Type": "application/json"
        })
        
        # 重试助手
        self.retry_helper = RetryHelper(max_retries=3, delay=1.0)
    
    def _generate_signature(self, query_string: str) -> str:
        """
        生成签名
        
        Args:
            query_string: 查询字符串
            
        Returns:
            HMAC SHA256 签名
        """
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _get_timestamp(self) -> int:
        """
        获取当前时间戳（毫秒）
        
        Returns:
            时间戳
        """
        return int(time.time() * 1000)
    
    def _build_signed_params(self, params: Optional[Dict] = None) -> Dict:
        """
        构建签名参数
        
        Args:
            params: 原始参数
            
        Returns:
            带签名的参数
        """
        params = params or {}
        
        # 添加时间戳和接收窗口
        params["timestamp"] = self._get_timestamp()
        params["recvWindow"] = self.recv_window
        
        # 生成查询字符串
        query_string = urlencode(params)
        
        # 生成签名
        signature = self._generate_signature(query_string)
        params["signature"] = signature
        
        return params
    
    def public_get(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """
        公开 GET 请求（无需签名）
        
        Args:
            endpoint: API 路径
            params: 查询参数
            **kwargs: 其他参数
            
        Returns:
            响应对象
        """
        url = f"{self.base_url}{endpoint}"
        
        log.debug(f"公开 GET 请求: {url}")
        
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout,
                **kwargs
            )
            
            log.debug(f"响应状态码: {response.status_code}")
            return response
            
        except requests.exceptions.RequestException as e:
            log.error(f"请求失败: {e}")
            raise
    
    def private_get(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """
        私有 GET 请求（需要签名）
        
        Args:
            endpoint: API 路径
            params: 查询参数
            **kwargs: 其他参数
            
        Returns:
            响应对象
        """
        url = f"{self.base_url}{endpoint}"
        
        # 构建签名参数
        signed_params = self._build_signed_params(params)
        
        log.debug(f"私有 GET 请求: {url}")
        
        try:
            response = self.session.get(
                url,
                params=signed_params,
                timeout=self.timeout,
                **kwargs
            )
            
            log.debug(f"响应状态码: {response.status_code}")
            return response
            
        except requests.exceptions.RequestException as e:
            log.error(f"请求失败: {e}")
            raise
    
    def private_post(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """
        私有 POST 请求（需要签名）
        
        Args:
            endpoint: API 路径
            params: 请求参数
            **kwargs: 其他参数
            
        Returns:
            响应对象
        """
        url = f"{self.base_url}{endpoint}"
        
        # 构建签名参数
        signed_params = self._build_signed_params(params)
        
        log.debug(f"私有 POST 请求: {url}")
        
        try:
            response = self.session.post(
                url,
                params=signed_params,
                timeout=self.timeout,
                **kwargs
            )
            
            log.debug(f"响应状态码: {response.status_code}")
            return response
            
        except requests.exceptions.RequestException as e:
            log.error(f"请求失败: {e}")
            raise
    
    def private_delete(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """
        私有 DELETE 请求（需要签名）
        
        Args:
            endpoint: API 路径
            params: 请求参数
            **kwargs: 其他参数
            
        Returns:
            响应对象
        """
        url = f"{self.base_url}{endpoint}"
        
        # 构建签名参数
        signed_params = self._build_signed_params(params)
        
        log.debug(f"私有 DELETE 请求: {url}")
        
        try:
            response = self.session.delete(
                url,
                params=signed_params,
                timeout=self.timeout,
                **kwargs
            )
            
            log.debug(f"响应状态码: {response.status_code}")
            return response
            
        except requests.exceptions.RequestException as e:
            log.error(f"请求失败: {e}")
            raise
    
    def close(self):
        """关闭 Session"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()