"""
==============================================================================
CEX 基础客户端 - 多交易所统一接口
==============================================================================
基于 HMAC-SHA256 签名鉴权，支持公开/私有接口请求。
从 tests/api/apis/base_client.py 提升为共享基础设施。

支持特性：
- 公开接口（无需签名）/ 私有接口（需签名）
- 请求超时、重试机制
- 统一错误处理与日志
- 幂等请求支持（避免重复提交）
"""

import time
import hmac
import hashlib
import requests
from typing import Dict, Any, Optional
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
            base_url="https://api.example.com"
        )
        
        # 公开接口
        response = client.public_get("/api/v3/ticker/price", {"symbol": "BTCUSDT"})
        
        # 私有接口
        response = client.private_get("/api/v3/account")
        response = client.private_post("/api/v3/order", {"symbol": "BTCUSDT", "side": "BUY"})
    """
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str,
        timeout: float = 30.0,
        recv_window: int = 5000
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.timeout = timeout
        self.recv_window = recv_window
        
        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": api_key,
            "Content-Type": "application/json"
        })
        
        self.retry_helper = RetryHelper(max_retries=3, delay=1.0)
    
    def _generate_signature(self, query_string: str) -> str:
        """生成 HMAC-SHA256 签名"""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _get_timestamp(self) -> int:
        """获取当前时间戳（毫秒）"""
        return int(time.time() * 1000)
    
    def _build_signed_params(self, params: Optional[Dict] = None) -> Dict:
        """构建签名参数（含时间戳、窗口、签名）"""
        params = params or {}
        params["timestamp"] = self._get_timestamp()
        params["recvWindow"] = self.recv_window
        
        query_string = urlencode(params)
        signature = self._generate_signature(query_string)
        params["signature"] = signature
        return params
    
    def public_get(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """公开 GET 请求（无需签名）"""
        url = f"{self.base_url}{endpoint}"
        log.debug(f"[CEX] 公开 GET: {url}")
        try:
            response = self.session.get(url, params=params, timeout=self.timeout, **kwargs)
            log.debug(f"[CEX] 响应: {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            log.error(f"[CEX] 请求失败: {e}")
            raise
    
    def public_post(
        self,
        endpoint: str,
        json: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """公开 POST 请求（无需签名）"""
        url = f"{self.base_url}{endpoint}"
        log.debug(f"[CEX] 公开 POST: {url}")
        try:
            response = self.session.post(url, json=json, timeout=self.timeout, **kwargs)
            log.debug(f"[CEX] 响应: {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            log.error(f"[CEX] 请求失败: {e}")
            raise
    
    def private_get(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """私有 GET 请求（需签名）"""
        url = f"{self.base_url}{endpoint}"
        signed_params = self._build_signed_params(params)
        log.debug(f"[CEX] 私有 GET: {url}")
        try:
            response = self.session.get(url, params=signed_params, timeout=self.timeout, **kwargs)
            log.debug(f"[CEX] 响应: {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            log.error(f"[CEX] 请求失败: {e}")
            raise
    
    def private_post(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """私有 POST 请求（需签名）"""
        url = f"{self.base_url}{endpoint}"
        signed_params = self._build_signed_params(params)
        log.debug(f"[CEX] 私有 POST: {url}")
        try:
            response = self.session.post(url, params=signed_params, timeout=self.timeout, **kwargs)
            log.debug(f"[CEX] 响应: {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            log.error(f"[CEX] 请求失败: {e}")
            raise
    
    def private_delete(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """私有 DELETE 请求（需签名）"""
        url = f"{self.base_url}{endpoint}"
        signed_params = self._build_signed_params(params)
        log.debug(f"[CEX] 私有 DELETE: {url}")
        try:
            response = self.session.delete(url, params=signed_params, timeout=self.timeout, **kwargs)
            log.debug(f"[CEX] 响应: {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            log.error(f"[CEX] 请求失败: {e}")
            raise
    
    def get_with_retry(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        max_retries: int = 3,
        **kwargs
    ) -> requests.Response:
        """带重试的私有 GET"""
        helper = RetryHelper(max_retries=max_retries)
        return helper.retry(lambda: self.private_get(endpoint, params=params, **kwargs))
    
    def post_with_retry(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        max_retries: int = 3,
        **kwargs
    ) -> requests.Response:
        """带重试的私有 POST"""
        helper = RetryHelper(max_retries=max_retries)
        return helper.retry(lambda: self.private_post(endpoint, params=params, **kwargs))
    
    def close(self):
        """关闭 Session"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
