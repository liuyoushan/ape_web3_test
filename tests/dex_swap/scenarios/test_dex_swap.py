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
    
    log.info("步骤1: 给用户铸造代币")
    swap_amount = "100"
    dex_token_a.mint(user1, swap_amount, sender=deployer)
    balance_A_after_mint = dex_token_a.balanceOf(user1)
    log.debug(f"用户1获得 TokenA: {format_ether(balance_A_after_mint)}")
    
    log.info("步骤2: 记录兑换前状态")
    balance_B_before = dex_token_b.balanceOf(user1)
    log.debug(f"兑换前 - 用户1 TokenB余额: {format_ether(balance_B_before)}")
    
    log.info("步骤3: 用户授权 Router 使用 TokenA")
    dex_token_a.approve(dex_router.contract, parse_ether(swap_amount), sender=user1)
    allowance = dex_token_a.allowance(user1, dex_router.contract)
    log.debug(f"授权完成 - allowance: {format_ether(allowance)}")
    
    log.info("步骤4: 设置兑换路径并执行兑换")
    path = [dex_token_a.address, dex_token_b.address]
    log.debug(f"兑换路径: TokenA -> TokenB")
    tx = dex_router.swap_exact_tokens_for_tokens(
        swap_amount, 0, path, user1, user1
    )
    log.debug("兑换操作完成")
    
    log.info("步骤5: 验证兑换结果")
    balance_B_after = dex_token_b.balanceOf(user1)
    log.debug(f"兑换后 - 用户1 TokenB余额: {format_ether(balance_B_after)}")
    
    assert balance_B_after > balance_B_before, f"TokenB余额未增加，兑换前: {format_ether(balance_B_before)}, 兑换后: {format_ether(balance_B_after)}"
    log.debug("代币兑换验证通过")
    
    log.success("✅ case_012 普通交易测试通过")
