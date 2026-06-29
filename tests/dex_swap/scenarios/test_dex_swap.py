"""
==============================================================================
【DEX 场景】交易交换测试
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
from framework.core.formatters import format_ether, parse_ether


@allure.title("case_012 普通交易测试")
@allure.description("验证用户可以在交易对中进行代币交换")
@allure.tag("DEX", "P0", "功能测试", "交易")
def test_dex_012_swap_tokens(dex_token_a, dex_token_b, dex_router, dex_pair_api, deployer, user1):
    """
    case_012 普通交易测试
    
    验证基本的代币兑换功能：
    - 用户持有 TokenA，可以兑换为 TokenB
    - 兑换后 TokenB 余额增加
    """
    log.step("case_012: 普通交易测试")
    
    swap_amount = "100"
    dex_token_a.mint(user1, swap_amount, sender=deployer)
    
    balance_before = dex_token_b.balanceOf(user1)
    log.debug("user1 tokenB 余额: %s", format_ether(balance_before))
    
    dex_token_a.approve(dex_router.contract, parse_ether(swap_amount), sender=user1)
    path = [dex_token_a.address, dex_token_b.address]
    
    tx = dex_router.swap_exact_tokens_for_tokens(
        swap_amount, 0, path, user1, user1
    )
    
    balance_after = dex_token_b.balanceOf(user1)
    log.debug("user1 tokenB 余额: %s", format_ether(balance_after))
    
    assert balance_after > balance_before
    
    log.success("✅ case_012 普通交易测试通过")