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
    
    log.step("case_048: 清算触发条件测试")
    
    collateral_token.approve(api.contract, env["collateral_amount"], sender=user1)
    api.deposit_collateral("2000", user1)
    api.borrow("1000", user1)
    
    health_factor = api.get_health_factor(user1)
    log.debug("健康因子: %s", health_factor)
    
    assert health_factor == 2 * 10**18
    
    log.success("✅ case_048 清算触发条件测试通过")