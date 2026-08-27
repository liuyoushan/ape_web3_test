"""
==============================================================================
CEX 资金划转 API 封装
==============================================================================
封装现货↔合约、现货↔理财等跨账户划转接口。
"""
from framework.cex.base_client import CEXBaseClient
from framework.core.logger import log


class TransferAPI:
    """资金划转接口封装"""
    
    def __init__(self, client: CEXBaseClient):
        self.client = client
    
    def spot_to_futures(self, symbol: str, amount: float, side: str = "TO_MARGIN") -> dict:
        """
        现货账户划转至合约账户
        
        Args:
            symbol: 交易对
            amount: 划转金额
            side: 划转方向 (TO_MARGIN: 现货→合约, TO_SPOT: 合约→现货)
        """
        log.info(f"[CEX Fund] 划转: spot <-> futures {symbol} {amount} ({side})")
        params = {
            "asset": symbol,
            "amount": amount,
            "type": side,  # 1: 现货→合约, 2: 合约→现货
        }
        response = self.client.private_post("/sapi/v1/futures/transfer", params=params)
        if response.status_code != 200:
            log.warning(f"[CEX Fund] 划转失败: HTTP {response.status_code}")
            return {"error": True, "status_code": response.status_code}
        try:
            return response.json()
        except Exception:
            log.warning("[CEX Fund] 划转响应解析失败（可能返回非JSON）")
            return {"error": True, "msg": "response is not JSON"}
    
    def spot_to_margin(self, symbol: str, amount: float, side: int = 1) -> dict:
        """
        现货账户划转至杠杆账户
        
        Args:
            symbol: 交易对
            amount: 划转金额
            side: 划转方向 (1: 现货→杠杆, 2: 杠杆→现货)
        """
        log.info(f"[CEX Fund] 划转: spot <-> margin {symbol} {amount}")
        params = {
            "asset": symbol,
            "amount": amount,
            "type": side,
        }
        response = self.client.private_post("/sapi/v1/margin/transfer", params=params)
        if response.status_code != 200:
            log.warning(f"[CEX Fund] 杠杆划转失败: HTTP {response.status_code}")
            return {"error": True, "status_code": response.status_code}
        try:
            return response.json()
        except Exception:
            log.warning("[CEX Fund] 杠杆划转响应解析失败")
            return {"error": True, "msg": "response is not JSON"}
    
    def get_transfer_history(self, symbol: str = None) -> list:
        """
        查询划转历史
        
        Args:
            symbol: 交易对
        """
        log.info(f"[CEX Fund] 查询划转历史: {symbol}")
        params = {}
        if symbol:
            params["asset"] = symbol
        response = self.client.private_get("/sapi/v1/futures/transfer", params=params)
        if response.status_code != 200:
            log.warning(f"[CEX Fund] 划转历史查询失败: HTTP {response.status_code}")
            return []
        try:
            return response.json()
        except Exception:
            log.warning("[CEX Fund] 划转历史响应解析失败")
            return []
