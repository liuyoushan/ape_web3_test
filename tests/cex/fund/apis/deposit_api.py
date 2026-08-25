"""
==============================================================================
CEX 充币类 API 封装
==============================================================================
封装充值记录查询、链上状态同步等接口。
"""
from framework.cex.base_client import CEXBaseClient
from framework.core.logger import log


class DepositAPI:
    """充币接口封装"""
    
    def __init__(self, client: CEXBaseClient):
        self.client = client
    
    def get_deposit_history(self, symbol: str = None, status: int = None) -> list:
        """
        查询充值历史
        
        Args:
            symbol: 交易对
            status: 充值状态 (0: 等待中, 1: 成功)
        """
        log.info(f"[CEX Fund] 查询充值历史: symbol={symbol}, status={status}")
        params = {}
        if symbol:
            params["coin"] = symbol
        if status is not None:
            params["status"] = status
        response = self.client.private_get("/api/v3/deposit/history", params=params)
        if response.status_code != 200:
            log.warning(f"[CEX Fund] 充值历史查询失败: HTTP {response.status_code}")
            return []
        try:
            return response.json()
        except Exception:
            log.warning("[CEX Fund] 充值历史响应解析失败")
            return []
    
    def get_deposit_address(self, symbol: str) -> dict:
        """
        获取充值地址
        
        Args:
            symbol: 交易对
        """
        log.info(f"[CEX Fund] 获取充值地址: {symbol}")
        response = self.client.private_get("/api/v3/deposit/address", params={"coin": symbol})
        if response.status_code != 200:
            log.warning(f"[CEX Fund] 获取充值地址失败: HTTP {response.status_code}")
            return {}
        try:
            return response.json()
        except Exception:
            log.warning("[CEX Fund] 充值地址响应解析失败")
            return {}
    
    def query_deposit_status(self, tx_hash: str) -> dict:
        """
        根据 TxHash 查询充值状态
        
        Args:
            tx_hash: 交易哈希
        """
        log.info(f"[CEX Fund] 查询充值状态: tx={tx_hash[:10]}...")
        response = self.client.private_get("/api/v3/deposit/status", params={"txHash": tx_hash})
        if response.status_code != 200:
            log.warning(f"[CEX Fund] 充值状态查询失败: HTTP {response.status_code}")
            return {}
        try:
            return response.json()
        except Exception:
            log.warning("[CEX Fund] 充值状态响应解析失败")
            return {}
