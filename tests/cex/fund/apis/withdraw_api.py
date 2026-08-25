"""
==============================================================================
CEX 提币类 API 封装
==============================================================================
封装提币申请、提币进度查询、提币撤销等接口。
"""
from framework.cex.base_client import CEXBaseClient
from framework.core.logger import log


class WithdrawAPI:
    """提币接口封装"""
    
    def __init__(self, client: CEXBaseClient):
        self.client = client
    
    def submit_withdraw(
        self,
        symbol: str,
        amount: float,
        address: str,
        tag: str = None
    ) -> dict:
        """
        提交提币申请
        
        Args:
            symbol: 交易对
            amount: 提币金额
            address: 接收地址
            tag: 地址标签（XRP等需要）
        """
        log.info(f"[CEX Fund] 提交提币: {symbol} {amount} -> {address[:10]}...")
        params = {
            "coin": symbol,
            "amount": amount,
            "address": address,
        }
        if tag:
            params["addressTag"] = tag
        response = self.client.private_post("/api/v3/withdraw", params=params)
        if response.status_code != 200:
            log.warning(f"[CEX Fund] 提币提交失败: HTTP {response.status_code}")
            return {"error": True, "status_code": response.status_code}
        try:
            return response.json()
        except Exception:
            log.warning("[CEX Fund] 提币响应解析失败")
            return {"error": True, "msg": "response parse failed"}
    
    def get_withdraw_history(self, symbol: str = None, status: int = None) -> list:
        """
        查询提币历史
        
        Args:
            symbol: 交易对
            status: 提币状态 (0: 邮件待确认, 1: 处理中, 2: 成功, 3: 失败, 4: 取消)
        """
        log.info(f"[CEX Fund] 查询提币历史: symbol={symbol}")
        params = {}
        if symbol:
            params["coin"] = symbol
        if status is not None:
            params["status"] = status
        response = self.client.private_get("/api/v3/withdraw/history", params=params)
        if response.status_code != 200:
            log.warning(f"[CEX Fund] 提币历史查询失败: HTTP {response.status_code}")
            return []
        try:
            return response.json()
        except Exception:
            log.warning("[CEX Fund] 提币历史响应解析失败")
            return []
    
    def query_withdraw_status(self, withdraw_id: str) -> dict:
        """
        查询提币状态
        
        Args:
            withdraw_id: 提币ID
        """
        log.info(f"[CEX Fund] 查询提币状态: id={withdraw_id}")
        response = self.client.private_get("/api/v3/withdraw/status", params={"withdrawId": withdraw_id})
        if response.status_code != 200:
            log.warning(f"[CEX Fund] 提币状态查询失败: HTTP {response.status_code}")
            return {}
        try:
            return response.json()
        except Exception:
            log.warning("[CEX Fund] 提币状态响应解析失败")
            return {}
    
    def cancel_withdraw(self, withdraw_id: str) -> dict:
        """
        取消提币申请（仅处理中状态可取消）
        
        Args:
            withdraw_id: 提币ID
        """
        log.info(f"[CEX Fund] 取消提币: id={withdraw_id}")
        response = self.client.private_delete("/api/v3/withdraw", params={"withdrawId": withdraw_id})
        if response.status_code != 200:
            log.warning(f"[CEX Fund] 取消提币失败: HTTP {response.status_code}")
            return {"error": True, "status_code": response.status_code}
        try:
            return response.json()
        except Exception:
            log.warning("[CEX Fund] 取消提币响应解析失败")
            return {"error": True, "msg": "response parse failed"}
