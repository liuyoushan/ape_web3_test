"""
==============================================================================
【CEX 账户模块】接口测试（对齐币安测试网 testnet.binance.vision）
==============================================================================
case_001 ~ case_004：账户基础查询接口

⚠️ 测试网环境说明：
- /api/v3/* 现货接口：测试网完整支持 → 真实调用
- /sapi/v1/* 钱包接口：测试网返回 404 → 标记 skip 并说明原因
"""
import pytest
from framework.core.logger import log


@pytest.mark.CEX_Fund
@pytest.mark.Account
@pytest.mark.P0
def test_cex_fund_001_get_balance(account_api, cex_fund_test_data):
    """case_001: 获取账户余额 - 查询现货账户余额，校验返回格式与精度"""
    log.step("case_001: 获取账户余额测试")

    # 1. 查询全部余额
    balances = account_api.get_balance()
    assert isinstance(balances, list), "余额应为列表"
    assert len(balances) > 0, "测试账户应有余额"

    # 2. 校验余额字段结构与精度
    for b in balances[:5]:
        assert "asset" in b and "free" in b and "locked" in b, f"余额字段缺失: {b}"
        # 币安余额为字符串，可转 float（精度校验）
        assert float(b["free"]) >= 0, f"free 非法: {b}"
        assert float(b["locked"]) >= 0, f"locked 非法: {b}"

    # 3. 查询指定币种（USDT）
    usdt = account_api.get_balance("USDT")
    assert usdt.get("asset") == "USDT", "应能查到 USDT 余额"
    log.info(f"USDT 余额: free={usdt['free']}, locked={usdt['locked']}")

    log.success("✅ case_001 通过：账户余额查询正常")


@pytest.mark.skip(reason="币安测试网不支持 /sapi/v1/account/apiRestrictions（返回404），需真实主网只读Key验证")
@pytest.mark.CEX_Fund
@pytest.mark.Account
@pytest.mark.P0
def test_cex_fund_002_api_key_permission(account_api, cex_fund_test_data):
    """case_002: API密钥权限校验 - 验证只读/交易/提币等级权限隔离

    知识点：真实主网通过 GET /sapi/v1/account/apiRestrictions 查询
    返回 enableReading / enableSpotAndMarginTrading / enableWithdrawals
    测试网无此接口，故 skip。
    """
    log.step("case_002: API密钥权限校验测试")
    restrictions = account_api.get_api_restrictions()
    assert restrictions.get("enableReading") is True, "只读权限应开启"


@pytest.mark.CEX_Fund
@pytest.mark.Account
@pytest.mark.P0
def test_cex_fund_003_account_permissions(account_api, cex_fund_test_data):
    """case_003: 账户交易权限校验 - 查询账户 permissions/canTrade（替代子账户，测试网无子账户接口）

    知识点：/api/v3/account 返回 permissions（如 SPOT）、canTrade/canWithdraw/canDeposit
    这是账户级别的权限，可在测试网真实验证。
    """
    log.step("case_003: 账户交易权限校验测试")

    info = account_api.get_account_info()
    # 校验权限字段
    assert "permissions" in info, "应返回 permissions 字段"
    assert isinstance(info["permissions"], list), "permissions 应为列表"
    assert "SPOT" in info["permissions"], "现货账户应有 SPOT 权限"

    # 校验交易开关
    assert info.get("canTrade") is True, "测试账户应可交易"
    assert "canWithdraw" in info, "应返回 canWithdraw 字段"
    assert "canDeposit" in info, "应返回 canDeposit 字段"

    log.info(f"账户权限: {info['permissions']}, canTrade={info['canTrade']}")
    log.success("✅ case_003 通过：账户权限校验正常")


@pytest.mark.CEX_Fund
@pytest.mark.Account
@pytest.mark.P0
def test_cex_fund_004_get_account_info(account_api, cex_fund_test_data):
    """case_004: 获取账户信息 - 全量账户资产概览查询"""
    log.step("case_004: 获取账户信息测试")

    info = account_api.get_account_info()

    # 校验账户核心字段
    assert info.get("accountType") == "SPOT", "账户类型应为 SPOT"
    assert "balances" in info, "应返回 balances 字段"
    assert "makerCommission" in info, "应返回 maker 手续费率"
    assert "takerCommission" in info, "应返回 taker 手续费率"

    # 校验手续费率为合理值（万分之几）
    assert info["makerCommission"] >= 0, "maker 手续费率非法"
    assert info["takerCommission"] >= 0, "taker 手续费率非法"

    log.info(f"账户类型: {info['accountType']}, "
             f"maker费率: {info['makerCommission']}, taker费率: {info['takerCommission']}")
    log.success("✅ case_004 通过：账户信息查询正常")

