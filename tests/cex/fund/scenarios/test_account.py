"""
==============================================================================
【CEX 账户模块】接口测试
==============================================================================
case_001 ~ case_004：账户基础查询接口
"""
import pytest
from framework.core.logger import log


@pytest.mark.skip(reason="占位待实现")
@pytest.mark.CEX_Fund
@pytest.mark.Account
@pytest.mark.P0
def test_cex_fund_001_get_balance(account_api, cex_fund_test_data):
    """case_001: 获取账户余额 - 查询现货/合约账户余额，校验返回格式与精度"""
    log.step("case_001: 获取账户余额测试")
    # TODO: 调 get_balance() → 校验返回字段、数值精度、非空
    pass
    log.success("✅ case_001 通过 (占位)")


@pytest.mark.skip(reason="占位待实现")
@pytest.mark.CEX_Fund
@pytest.mark.Account
@pytest.mark.P0
def test_cex_fund_002_api_key_permission(account_api, cex_fund_test_data):
    """case_002: API密钥权限校验 - 验证只读/交易/提币等级权限隔离"""
    log.step("case_002: API密钥权限校验测试")
    # TODO: 调权限查询 → 验证当前Key的权限等级
    pass
    log.success("✅ case_002 通过 (占位)")


@pytest.mark.skip(reason="占位待实现")
@pytest.mark.CEX_Fund
@pytest.mark.Account
@pytest.mark.P0
def test_cex_fund_003_get_sub_accounts(account_api, cex_fund_test_data):
    """case_003: 查询子账户列表 - 主账户查询所有子账户信息"""
    log.step("case_003: 查询子账户列表测试")
    # TODO: 调 get_sub_accounts() → 验证子账户列表完整性
    pass
    log.success("✅ case_003 通过 (占位)")


@pytest.mark.skip(reason="占位待实现")
@pytest.mark.CEX_Fund
@pytest.mark.Account
@pytest.mark.P0
def test_cex_fund_004_get_account_info(account_api, cex_fund_test_data):
    """case_004: 获取账户信息 - 全量账户资产概览查询"""
    log.step("case_004: 获取账户信息测试")
    # TODO: 调 get_account_info() → 验证账户类型、资产列表
    pass
    log.success("✅ case_004 通过 (占位)")
