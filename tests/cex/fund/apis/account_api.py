"""
==============================================================================
CEX 账户类 API 封装（对齐币安测试网真实接口 testnet.binance.vision）
==============================================================================
封装账户信息查询、余额查询、API Key 权限查询等接口。

币安真实接口对照：
- 账户信息 + 余额：GET /api/v3/account       （余额在返回的 balances 字段里）
- API Key 权限：    GET /sapi/v1/account/apiRestrictions
- 账户交易状态：    GET /sapi/v1/account/status
"""
from framework.cex.base_client import CEXBaseClient
from framework.core.logger import log


class AccountAPI:
    """账户接口封装"""

    def __init__(self, client: CEXBaseClient):
        self.client = client

    def get_account_info(self) -> dict:
        """
        获取账户信息（含全量余额）
        币安接口：GET /api/v3/account
        返回：accountType / permissions / canTrade / balances[...]
        """
        log.info("[CEX Fund] 获取账户信息 GET /api/v3/account")
        response = self.client.private_get("/api/v3/account")
        return response.json()

    def get_balance(self, asset: str = None) -> dict:
        """
        获取账户余额（从 /api/v3/account 的 balances 中解析）
        币安没有独立的 balance 接口，余额随账户信息一起返回。

        Args:
            asset: 指定币种（如 "USDT"），不传则返回全部余额列表

        Returns:
            asset 指定时返回单币种 dict {asset, free, locked}；
            否则返回 balances 列表
        """
        log.info(f"[CEX Fund] 获取账户余额 asset={asset or 'ALL'}")
        data = self.get_account_info()
        balances = data.get("balances", [])
        if asset:
            for b in balances:
                if b["asset"] == asset.upper():
                    return b
            return {}
        return balances

    def get_api_restrictions(self) -> dict:
        """
        查询 API Key 权限限制
        币安接口：GET /sapi/v1/account/apiRestrictions
        返回：enableReading / enableSpotAndMarginTrading / enableWithdrawals 等
        """
        log.info("[CEX Fund] 查询 API Key 权限 GET /sapi/v1/account/apiRestrictions")
        response = self.client.private_get("/sapi/v1/account/apiRestrictions")
        return response.json()
