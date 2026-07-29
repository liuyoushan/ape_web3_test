"""
==============================================================================
【清算场景】清算流程测试
==============================================================================
"""
try:
    import allure
except ImportError:
    class dummy_allure:
        @staticmethod
        def title(*args, **kwargs):
            return lambda f: f
        @staticmethod
        def description(*args, **kwargs):
            return lambda f: f
        @staticmethod
        def tag(*args, **kwargs):
            return lambda f: f
    allure = dummy_allure()

from framework.core.logger import log
from framework.core.formatters import format_ether


@allure.title("case_048 清算触发条件测试")
@allure.description("验证健康因子低于阈值时触发清算")
@allure.tag("Liquidation", "P0", "功能测试", "清算")
def test_liquidation_048_trigger(liquidation_env, user1, deployer):
    """
    case_048 清算触发条件测试
    
    验证清算触发条件的正确性：
    - 用户存入抵押资产并借款
    - 健康因子计算正确（抵押/债务 = 健康因子）
    - 当健康因子低于阈值时触发清算
    """
    env = liquidation_env
    api = env["liquidation_api"]
    collateral_token = env["collateral_token"]
    debt_token = env["debt_token"]
    
    log.step("case_048: 清算触发条件测试")
    
    log.info("步骤1: 用户授权并存入抵押品")
    collateral_token.approve(api.contract, env["collateral_amount"], sender=user1)
    log.debug(f"用户1授权清算合约使用抵押品: {format_ether(env['collateral_amount'])}")
    api.deposit_collateral("2000", user1)
    collateral_balance = api.get_collateral(user1)
    log.debug(f"用户1抵押品余额: {format_ether(collateral_balance)}")
    
    log.info("步骤2: 用户借入债务")
    api.borrow("1000", user1)
    debt_balance = api.get_debt(user1)
    log.debug(f"用户1债务余额: {format_ether(debt_balance)}")
    
    log.info("步骤3: 验证健康因子")
    health_factor = api.get_health_factor(user1)
    log.debug(f"健康因子: {format_ether(health_factor)}")
    
    expected_hf = 2 * 10**18
    assert health_factor == expected_hf, f"健康因子不符，预期: {format_ether(expected_hf)}, 实际: {format_ether(health_factor)}"
    log.debug("健康因子验证通过")
    
    log.success("✅ case_048 清算触发条件测试通过")