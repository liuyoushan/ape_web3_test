"""
==============================================================================
CEX 行情 API 封装
==============================================================================
封装 K线、盘口深度、实时价格等行情接口。
"""
from framework.cex.base_client import CEXBaseClient
from framework.core.logger import log


class MarketAPI:
    """行情接口封装"""
    
    def __init__(self, client: CEXBaseClient):
        self.client = client
    
    def get_ticker_price(self, symbol: str = None) -> list:
        """
        获取实时价格
        
        Args:
            symbol: 交易对（可选，不传返回所有）
        """
        log.info(f"[CEX Order] 获取实时价格: {symbol}")
        params = {}
        if symbol:
            params["symbol"] = symbol
        response = self.client.public_get("/api/v3/ticker/price", params=params)
        return response.json()
    
    def get_order_book(self, symbol: str, limit: int = 10) -> dict:
        """
        获取盘口深度
        
        Args:
            symbol: 交易对
            limit: 返回档位数量 (5/10/20/50/100)
        """
        log.info(f"[CEX Order] 获取盘口深度: {symbol} limit={limit}")
        response = self.client.public_get("/api/v3/depth", params={"symbol": symbol, "limit": limit})
        return response.json()
    
    def get_24hr_ticker(self, symbol: str = None) -> list:
        """
        获取 24 小时行情统计
        
        Args:
            symbol: 交易对
        """
        log.info(f"[CEX Order] 获取24h行情: {symbol}")
        params = {}
        if symbol:
            params["symbol"] = symbol
        response = self.client.public_get("/api/v3/ticker/24hr", params=params)
        return response.json()
    
    def get_klines(
        self,
        symbol: str,
        interval: str = "1m",
        limit: int = 50,
        start_time: int = None,
        end_time: int = None
    ) -> list:
        """
        获取 K 线数据
        
        Args:
            symbol: 交易对
            interval: 时间周期 (1m/5m/15m/1h/4h/1d)
            limit: 返回数量
            start_time: 开始时间戳
            end_time: 结束时间戳
        """
        log.info(f"[CEX Order] 获取K线: {symbol} interval={interval}")
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        response = self.client.public_get("/api/v3/klines", params=params)
        return response.json()
    
    def get_avg_price(self, symbol: str) -> dict:
        """
        获取当前平均价格
        
        Args:
            symbol: 交易对
        """
        log.info(f"[CEX Order] 获取平均价格: {symbol}")
        response = self.client.public_get("/api/v3/avgPrice", params={"symbol": symbol})
        return response.json()
    
    def get_funding_rate(self, symbol: str) -> dict:
        """
        获取永续合约资金费率
        
        Args:
            symbol: 交易对
        """
        log.info(f"[CEX Order] 获取资金费率: {symbol}")
        response = self.client.public_get("/fapi/v1/fundingRate", params={"symbol": symbol, "limit": 1})
        return response.json()
