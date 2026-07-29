"""
==============================================================================
CEX 现货交易 API 封装
==============================================================================
封装限价/市价挂单、撤单、订单查询等接口。
"""
from framework.cex.base_client import CEXBaseClient
from framework.core.logger import log


class SpotAPI:
    """现货交易接口封装"""
    
    def __init__(self, client: CEXBaseClient):
        self.client = client
    
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float = None,
        price: float = None,
        time_in_force: str = "GTC"
    ) -> dict:
        """
        下单
        
        Args:
            symbol: 交易对 (BTCUSDT)
            side: 买卖方向 (BUY/SELL)
            order_type: 订单类型 (LIMIT/MARKET/STOP_LOSS/... )
            quantity: 数量
            price: 价格（限价单必填）
            time_in_force: 生效方式 (GTC/IOC/FOK)
        """
        log.info(f"[CEX Order] 下单: {side} {order_type} {symbol} qty={quantity} price={price}")
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
        }
        if quantity:
            params["quantity"] = quantity
        if price:
            params["price"] = price
        if order_type == "LIMIT":
            params["timeInForce"] = time_in_force
        
        response = self.client.private_post("/api/v3/order", params=params)
        return response.json()
    
    def cancel_order(self, symbol: str, order_id: str) -> dict:
        """
        撤销订单
        
        Args:
            symbol: 交易对
            order_id: 订单ID
        """
        log.info(f"[CEX Order] 撤单: {symbol} orderId={order_id}")
        response = self.client.private_delete("/api/v3/order", params={"symbol": symbol, "orderId": order_id})
        return response.json()
    
    def get_order_status(self, symbol: str, order_id: str) -> dict:
        """
        查询订单状态
        
        Args:
            symbol: 交易对
            order_id: 订单ID
        """
        log.info(f"[CEX Order] 查询订单: {symbol} orderId={order_id}")
        response = self.client.private_get("/api/v3/order", params={"symbol": symbol, "orderId": order_id})
        return response.json()
    
    def get_open_orders(self, symbol: str = None) -> list:
        """
        查询当前挂单
        
        Args:
            symbol: 交易对（可选）
        """
        log.info(f"[CEX Order] 查询挂单: {symbol}")
        params = {}
        if symbol:
            params["symbol"] = symbol
        response = self.client.private_get("/api/v3/openOrders", params=params)
        return response.json()
    
    def get_order_history(self, symbol: str = None, limit: int = 50) -> list:
        """
        查询历史订单
        
        Args:
            symbol: 交易对
            limit: 返回数量
        """
        log.info(f"[CEX Order] 查询历史订单: {symbol}")
        params = {"limit": limit}
        if symbol:
            params["symbol"] = symbol
        response = self.client.private_get("/api/v3/allOrders", params=params)
        return response.json()
    
    def get_trade_history(self, symbol: str = None, limit: int = 50) -> list:
        """
        查询成交历史
        
        Args:
            symbol: 交易对
            limit: 返回数量
        """
        log.info(f"[CEX Order] 查询成交历史: {symbol}")
        params = {"limit": limit}
        if symbol:
            params["symbol"] = symbol
        response = self.client.private_get("/api/v3/myTrades", params=params)
        return response.json()
    
    def cancel_all_open_orders(self, symbol: str) -> dict:
        """
        撤销所有挂单
        
        Args:
            symbol: 交易对
        """
        log.info(f"[CEX Order] 撤销所有挂单: {symbol}")
        response = self.client.private_delete("/api/v3/openOrders", params={"symbol": symbol})
        return response.json()
