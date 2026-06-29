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
    
    lp_balance = dex_pair_api.get_balance(user1)
    log.debug("LP 代币余额: %s", format_ether(lp_balance))
    
    reserves = dex_pair_api.get_reserves()
    log.debug("储备金: tokenA=%s, tokenB=%s", format_ether(reserves[0]), format_ether(reserves[1]))
    
    assert lp_balance > 0
    assert reserves[0] > 0
    assert reserves[1] > 0
    
    log.success("✅ case_011 添加流动性测试通过")