"""
==============================================================================
CEX 账户类 API 封装
==============================================================================
封装账户信息查询、余额查询、子账户管理等接口。
"""
from framework.cex.base_client import CEXBaseClient
from framework.core.logger import log


class AccountAPI:
    """账户接口封装"""
    
    def __init__(self, client: CEXBaseClient):
        self.client = client
    
    def get_account_info(self) -> dict:
        """获取账户信息"""
        log.info("[CEX Fund] 获取账户信息")
        response = self.client.private_get("/api/v3/account")
        return response.json()
    
    def get_balance(self) -> dict:
        """获取账户余额"""
        log.info("[CEX Fund] 获取账户余额")
        response = self.client.private_get("/api/v3/balance")
        return response.json()
    
    def get_sub_accounts(self) -> list:
        """获取子账户列表"""
        log.info("[CEX Fund] 获取子账户列表")
        response = self.client.private_get("/api/v3/sub-accounts")
        return response.json()
