"""
==============================================================================
【CEX 提币模块】接口测试
==============================================================================
case_016 ~ case_020：提币核心接口
case_031：差异化资损场景（简历亮点）
"""
import pytest
from framework.core.logger import log


@pytest.mark.skip(reason="占位待实现")
@pytest.mark.CEX_Fund
@pytest.mark.Withdraw
@pytest.mark.P0
def test_cex_fund_016_submit_withdraw(withdraw_api, cex_fund_test_data):
    """case_016: 提币提交 - 发起提币申请，校验余额扣减与风控"""
    log.step("case_016: 提币提交测试")
    # TODO: 调 submit_withdraw() → 验证余额扣减、风控校验通过
    pass
    log.success("✅ case_016 通过 (占位)")


@pytest.mark.skip(reason="占位待实现")
@pytest.mark.CEX_Fund
@pytest.mark.Withdraw
@pytest.mark.P0
def test_cex_fund_017_query_withdraw_progress(withdraw_api, cex_fund_test_data):
    """case_017: 提币进度查询 - 查询提币链上广播/确认状态"""
    log.step("case_017: 提币进度查询测试")
    # TODO: 调 query_withdraw_status() → 验证状态机流转
    pass
    log.success("✅ case_017 通过 (占位)")


@pytest.mark.skip(reason="占位待实现")
@pytest.mark.CEX_Fund
@pytest.mark.Withdraw
@pytest.mark.P0
def test_cex_fund_018_cancel_withdraw(withdraw_api, cex_fund_test_data):
    """case_018: 提币撤销 - 处理中状态可撤销，资金返还"""
    log.step("case_018: 提币撤销测试")
    # TODO: 调 cancel_withdraw() → 验证资金返还、状态变更
    pass
    log.success("✅ case_018 通过 (占位)")


@pytest.mark.skip(reason="占位待实现")
@pytest.mark.CEX_Fund
@pytest.mark.Withdraw
@pytest.mark.P0
def test_cex_fund_019_get_withdraw_history(withdraw_api, cex_fund_test_data):
    """case_019: 提币历史查询 - 查询历史提币记录"""
    log.step("case_019: 提币历史查询测试")
    # TODO: 调 get_withdraw_history() → 验证记录完整性与筛选
    pass
    log.success("✅ case_019 通过 (占位)")


@pytest.mark.skip(reason="占位待实现")
@pytest.mark.CEX_Fund
@pytest.mark.Withdraw
@pytest.mark.P0
def test_cex_fund_020_low_gas_withdraw(withdraw_api, cex_fund_test_data):
    """case_020: 低Gas提币拦截 - 低于网络要求的Gas被拦截"""
    log.step("case_020: 低Gas提币拦截测试")
    # TODO: 用极低Gas调 submit_withdraw() → 验证系统拒绝
    pass
    log.success("✅ case_020 通过 (占位)")


@pytest.mark.skip(reason="占位待实现")
@pytest.mark.CEX_Fund
@pytest.mark.Withdraw
@pytest.mark.P1
def test_cex_fund_031_withdraw_chain_failure(withdraw_api, mock_chain, account_api, cex_fund_test_data):
    """case_031: 提币链上失败回滚 - 内部扣减但链上失败，资金退回"""
    log.step("case_031: 提币链上失败回滚测试")
    # TODO: 提币成功扣减 → 模拟链上失败 → 查余额验证已退回
    pass
    log.success("✅ case_031 通过 (占位)")
