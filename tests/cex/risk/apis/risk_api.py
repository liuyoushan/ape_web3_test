"""
==============================================================================
CEX 风控相关 API 封装
==============================================================================
封装账户权限、KYC 分级、风控冻结等接口。
测试网仅支持 account 接口（可查询权限标志位），其余接口返回 404。
"""
from framework.cex.base_client import CEXBaseClient
from framework.core.logger import log


class RiskAPI:
    """风控接口封装"""

    def __init__(self, client: CEXBaseClient):
        self.client = client

    # ---------- 权限管理 ----------

    def get_api_key_permissions(self) -> dict:
        """
        获取当前 API Key 权限

        Returns:
            dict: 包含 canTrade / canWithdraw / canDeposit 等权限标志位
                  测试网返回 400 (recvWindow) 时返回空 dict
        """
        log.info("[CEX Risk] 获取API Key权限")
        response = self.client.private_get("/api/v3/account")
        if response.status_code == 200:
            return response.json()
        log.warning(f"[CEX Risk] account 接口返回 {response.status_code}，视为无权限信息")
        return {}

    def get_whitelist(self, api_key: str = "") -> dict:
        """
        获取 API Key 白名单（测试网不支持，返回空 dict）

        Args:
            api_key: API Key ID
        """
        log.info(f"[CEX Risk] 获取白名单: {api_key}")
        response = self.client.private_get("/api/v3/whitelist", params={"apiKeyId": api_key})
        if response.status_code == 200:
            return response.json()
        log.warning(f"[CEX Risk] whitelist 接口返回 {response.status_code}，测试网不支持")
        return {"not_supported": True, "status_code": response.status_code}

    # ---------- KYC 分级 ----------

    def get_kyc_status(self) -> dict:
        """获取 KYC 认证状态（测试网不支持，返回空 dict）"""
        log.info("[CEX Risk] 获取KYC状态")
        response = self.client.private_get("/api/v3/account/kyc")
        if response.status_code == 200:
            return response.json()
        log.warning(f"[CEX Risk] kyc 接口返回 {response.status_code}，测试网不支持")
        return {"not_supported": True, "status_code": response.status_code}

    # ---------- 冻结/解冻 ----------

    def freeze_account(self, reason: str = "manual") -> dict:
        """
        冻结账户（测试网不支持，返回空 dict）

        Args:
            reason: 冻结原因
        """
        log.info(f"[CEX Risk] 冻结账户: reason={reason}")
        response = self.client.private_post("/api/v3/account/freeze", params={"reason": reason})
        if response.status_code == 200:
            return response.json()
        log.warning(f"[CEX Risk] freeze 接口返回 {response.status_code}，测试网不支持")
        return {"not_supported": True, "status_code": response.status_code}

    def unfreeze_account(self, appeal_id: str = None) -> dict:
        """
        解冻账户（测试网不支持，返回空 dict）

        Args:
            appeal_id: 申诉ID
        """
        log.info(f"[CEX Risk] 解冻账户: appeal={appeal_id}")
        params = {}
        if appeal_id:
            params["appealId"] = appeal_id
        response = self.client.private_post("/api/v3/account/unfreeze", params=params)
        if response.status_code == 200:
            return response.json()
        log.warning(f"[CEX Risk] unfreeze 接口返回 {response.status_code}，测试网不支持")
        return {"not_supported": True, "status_code": response.status_code}

    def get_freeze_status(self) -> dict:
        """查询账户冻结状态（测试网不支持，返回空 dict）"""
        log.info("[CEX Risk] 查询冻结状态")
        response = self.client.private_get("/api/v3/account/freeze/status")
        if response.status_code == 200:
            return response.json()
        log.warning(f"[CEX Risk] freeze_status 接口返回 {response.status_code}，测试网不支持")
        return {"not_supported": True, "status_code": response.status_code}

    def get_freeze_log(self) -> list:
        """获取冻结操作日志（测试网不支持，返回空列表）"""
        log.info("[CEX Risk] 获取冻结日志")
        response = self.client.private_get("/api/v3/account/freeze/log")
        if response.status_code == 200:
            return response.json()
        log.warning(f"[CEX Risk] freeze_log 接口返回 {response.status_code}，测试网不支持")
        return []

    # ---------- 子账户管控 ----------

    def get_sub_account_list(self) -> list:
        """获取子账户列表（测试网不支持，返回空列表）"""
        log.info("[CEX Risk] 获取子账户列表")
        response = self.client.private_get("/api/v3/sub-accounts")
        if response.status_code == 200:
            return response.json()
        log.warning(f"[CEX Risk] sub-accounts 接口返回 {response.status_code}，测试网不支持")
        return []

    def set_sub_account_permissions(self, sub_account_id: str, permissions: list) -> dict:
        """
        设置子账户权限（测试网不支持，返回空 dict）

        Args:
            sub_account_id: 子账户ID
            permissions: 权限列表 ["trade", "withdraw", "transfer"]
        """
        log.info(f"[CEX Risk] 设置子账户权限: sub={sub_account_id}")
        response = self.client.private_post("/api/v3/sub-account/permissions", params={
            "subAccountId": sub_account_id,
            "permissions": permissions,
        })
        if response.status_code == 200:
            return response.json()
        log.warning(f"[CEX Risk] sub-account/permissions 接口返回 {response.status_code}，测试网不支持")
        return {"not_supported": True, "status_code": response.status_code}
