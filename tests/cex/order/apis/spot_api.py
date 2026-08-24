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
    
    def _build_order_params(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float = None,
        quote_order_qty: float = None,
        price: float = None,
        time_in_force: str = "GTC"
    ) -> dict:
        """组装下单参数（币安 /api/v3/order 规则）"""
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
        }
        if quantity is not None:
            params["quantity"] = quantity
        # 市价买单常用 quoteOrderQty（按花多少 USDT 买），而非指定 BTC 数量
        if quote_order_qty is not None:
            params["quoteOrderQty"] = quote_order_qty
        if price is not None:
            params["price"] = price
        if order_type == "LIMIT":
            params["timeInForce"] = time_in_force
        return params

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float = None,
        quote_order_qty: float = None,
        price: float = None,
        time_in_force: str = "GTC"
    ) -> dict:
        """
        下单（真实提交）
        币安接口：POST /api/v3/order

        Args:
            symbol: 交易对 (BTCUSDT)
            side: 买卖方向 (BUY/SELL)
            order_type: 订单类型 (LIMIT/MARKET)
            quantity: 数量（按 base 资产计，如 0.001 BTC）
            quote_order_qty: 市价单按报价资产计（如花 50 USDT），与 quantity 二选一
            price: 价格（限价单必填）
            time_in_force: 生效方式 (GTC/IOC/FOK)
        """
        log.info(f"[CEX Order] 下单: {side} {order_type} {symbol} "
                 f"qty={quantity} quoteQty={quote_order_qty} price={price}")
        params = self._build_order_params(
            symbol, side, order_type, quantity, quote_order_qty, price, time_in_force
        )
        response = self.client.private_post("/api/v3/order", params=params)
        return response.json()

    def place_test_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float = None,
        quote_order_qty: float = None,
        price: float = None,
        time_in_force: str = "GTC"
    ) -> dict:
        """
        测试下单（只校验参数，不进撮合、不冻结资产）
        币安接口：POST /api/v3/order/test
        成功返回空 dict {}，参数非法则返回错误。
        """
        log.info(f"[CEX Order] 测试下单: {side} {order_type} {symbol} "
                 f"qty={quantity} price={price}")
        params = self._build_order_params(
            symbol, side, order_type, quantity, quote_order_qty, price, time_in_force
        )
        response = self.client.private_post("/api/v3/order/test", params=params)
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
    
    def cancel_all_open_orders(self, symbol: str) -> list:
        """
        撤销所有挂单
        
        Args:
            symbol: 交易对
        """
        log.info(f"[CEX Order] 撤销所有挂单: {symbol}")
        response = self.client.private_delete("/api/v3/openOrders", params={"symbol": symbol})
        return response.json()
