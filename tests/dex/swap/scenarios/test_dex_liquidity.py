"""
==============================================================================
【DEX 场景】流动性管理测试
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


@allure.title("case_011 添加流动性测试")
@allure.description("验证用户可以添加流动性并获得 LP 代币")
@allure.tag("DEX", "P0", "功能测试", "流动性")
def test_dex_011_add_liquidity(dex_pair_api, user1):
    """
    case_011 添加流动性测试
    
    验证流动性添加功能：
    - 用户成功获得 LP 代币
    - 池子储备金正确初始化
    - LP 代币余额大于 0
    - 储备金数量大于 0
    """
    log.step("case_011: 添加流动性测试")
    
    log.info("步骤1: 查询用户 LP 代币余额")
    lp_balance = dex_pair_api.get_balance(user1)
    log.debug(f"用户1 LP代币余额: {format_ether(lp_balance)}")
    
    log.info("步骤2: 查询池子储备金")
    reserves = dex_pair_api.get_reserves()
    log.debug(f"池子储备金 - TokenA: {format_ether(reserves[0])}, TokenB: {format_ether(reserves[1])}")
    
    log.info("步骤3: 验证流动性添加结果")
    assert lp_balance > 0, f"LP代币余额应为正数，实际: {format_ether(lp_balance)}"
    log.debug("LP代币余额验证通过")
    
    assert reserves[0] > 0, f"TokenA储备金应为正数，实际: {format_ether(reserves[0])}"
    assert reserves[1] > 0, f"TokenB储备金应为正数，实际: {format_ether(reserves[1])}"
    log.debug("池子储备金验证通过")
    
    log.success("✅ case_011 添加流动性测试通过")
