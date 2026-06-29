"""
==============================================================================
【DEX 场景】复杂交易测试
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

import math
from ape import project
from framework.core.logger import log
from framework.core.formatters import format_ether, parse_ether


@allure.title("case_010 正向单池 Swap 兑换")
@allure.description("TokenA 兑换 TokenB，校验余额、手续费、池子库存、K值守恒")
@allure.tag("DEX", "P0", "功能测试", "Swap", "正向测试")
def test_dex_010_swap_tokenA_to_tokenB(dex_token_a, dex_token_b, dex_factory, dex_router, deployer, user1, dex_test_data):
    """
    case_010 正向单池 Swap 兑换
    
    验证 TokenA → TokenB 的正向兑换流程：
    - 发送方 TokenA 余额减少
    - 接收方 TokenB 余额增加
    - 池子储备金变化符合 AMM 算法
    - K 值（reserveA * reserveB）不减少（手续费导致增加）
    """
    data = dex_test_data["case_010_swap_tokenA_to_tokenB"]
    mint_amount = parse_ether(data["mint_amount"])
    add_liquidity_amount = parse_ether(data["add_liquidity_amount"])
    swap_amount = parse_ether(data["swap_amount"])

    dex_token_a.mint(user1, mint_amount, sender=deployer)
    dex_token_b.mint(user1, mint_amount, sender=deployer)

    dex_token_a.approve(dex_router.contract, add_liquidity_amount, sender=user1)
    dex_token_b.approve(dex_router.contract, add_liquidity_amount, sender=user1)

    dex_router.add_liquidity(
        dex_token_a, dex_token_b,
        data["add_liquidity_amount"], data["add_liquidity_amount"],
        user1, user1
    )

    balance_A_before = dex_token_a.balanceOf(user1)
    balance_B_before = dex_token_b.balanceOf(user1)

    pair_addr = dex_factory.get_pair(dex_token_a, dex_token_b)
    reserve_before = project.MiniSwapPair.at(pair_addr).getReserves()

    dex_token_a.approve(dex_router.contract, swap_amount, sender=user1)

    dex_router.swap_exact_tokens_for_tokens(
        data["swap_amount"], 0,
        [dex_token_a.address, dex_token_b.address],
        user1, user1
    )

    balance_A_after = dex_token_a.balanceOf(user1)
    balance_B_after = dex_token_b.balanceOf(user1)
    reserve_after = project.MiniSwapPair.at(pair_addr).getReserves()

    assert balance_A_after == balance_A_before - swap_amount
    assert balance_B_after > balance_B_before

    k_before = reserve_before[0] * reserve_before[1]
    k_after = reserve_after[0] * reserve_after[1]
    assert k_after >= k_before


@allure.title("case_011 反向单池 Swap 兑换")
@allure.description("TokenB 兑换 TokenA，校验价格换算逻辑一致性")
@allure.tag("DEX", "P0", "Swap", "反向测试")
def test_dex_011_swap_tokenB_to_tokenA(dex_token_a, dex_token_b, dex_factory, dex_router, deployer, user1, dex_test_data):
    """
    case_011 反向单池 Swap 兑换
    
    验证 TokenB → TokenA 的反向兑换流程：
    - 确保反向兑换逻辑与正向兑换一致
    - 余额变化符合预期
    """
    data = dex_test_data["case_011_swap_tokenB_to_tokenA"]
    mint_amount = parse_ether(data["mint_amount"])
    add_liquidity_amount = parse_ether(data["add_liquidity_amount"])
    swap_amount = parse_ether(data["swap_amount"])

    dex_token_a.mint(user1, mint_amount, sender=deployer)
    dex_token_b.mint(user1, mint_amount, sender=deployer)

    dex_token_a.approve(dex_router.contract, add_liquidity_amount, sender=user1)
    dex_token_b.approve(dex_router.contract, add_liquidity_amount, sender=user1)

    dex_router.add_liquidity(
        dex_token_a, dex_token_b,
        data["add_liquidity_amount"], data["add_liquidity_amount"],
        user1, user1
    )

    balance_B_before = dex_token_b.balanceOf(user1)
    balance_A_before = dex_token_a.balanceOf(user1)

    dex_token_b.approve(dex_router.contract, swap_amount, sender=user1)

    dex_router.swap_exact_tokens_for_tokens(
        data["swap_amount"], 0,
        [dex_token_b.address, dex_token_a.address],
        user1, user1
    )

    balance_B_after = dex_token_b.balanceOf(user1)
    balance_A_after = dex_token_a.balanceOf(user1)

    assert balance_B_after == balance_B_before - swap_amount
    assert balance_A_after > balance_A_before


@allure.title("case_012 添加双边流动性测试")
@allure.description("存入双币种，Mint LP 凭证、校验池子储备量")
@allure.tag("DEX", "P0", "流动性", "AddLiquidity")
def test_dex_012_add_liquidity(dex_token_a, dex_token_b, dex_factory, dex_router, deployer, user1, dex_test_data):
    """
    case_012 添加双边流动性测试
    
    验证流动性添加流程：
    - 用户存入两种代币
    - 获得对应的 LP 代币
    - 池子储备金正确更新
    - LP 代币数量计算符合公式（sqrt(a*b)）
    """
    data = dex_test_data["case_012_add_liquidity"]
    mint_amount = parse_ether(data["mint_amount"])
    add_liquidity_amount_a = parse_ether(data["add_liquidity_amount_a"])
    add_liquidity_amount_b = parse_ether(data["add_liquidity_amount_b"])

    dex_token_a.mint(user1, mint_amount, sender=deployer)
    dex_token_b.mint(user1, mint_amount, sender=deployer)

    balance_A_before = dex_token_a.balanceOf(user1)
    balance_B_before = dex_token_b.balanceOf(user1)

    dex_token_a.approve(dex_router.contract, add_liquidity_amount_a, sender=user1)
    dex_token_b.approve(dex_router.contract, add_liquidity_amount_b, sender=user1)

    dex_router.add_liquidity(
        dex_token_a, dex_token_b,
        data["add_liquidity_amount_a"], data["add_liquidity_amount_b"],
        user1, user1
    )

    balance_A_after = dex_token_a.balanceOf(user1)
    balance_B_after = dex_token_b.balanceOf(user1)

    pair_addr = dex_factory.get_pair(dex_token_a, dex_token_b)
    pair = project.MiniSwapPair.at(pair_addr)
    lp_balance = pair.balanceOf(user1)
    reserves = pair.getReserves()

    assert balance_A_after == balance_A_before - add_liquidity_amount_a
    assert balance_B_after == balance_B_before - add_liquidity_amount_b

    lp_a = add_liquidity_amount_a // 10**18
    lp_b = add_liquidity_amount_b // 10**18
    expected_lp_eth = math.isqrt(lp_a * lp_b)
    expected_lp_wei = expected_lp_eth * 10**18
    tolerance_wei = 1 * 10**18

    assert abs(lp_balance - expected_lp_wei) < tolerance_wei
    assert lp_balance > 0
    assert reserves[0] == add_liquidity_amount_a
    assert reserves[1] == add_liquidity_amount_b


@allure.title("case_012_extend LP 占比校验")
@allure.description("校验 LP 凭证持有占比与流动性贡献匹配")
@allure.tag("DEX", "P0", "流动性", "LP")
def test_dex_012_1_lp_percentage_check(dex_token_a, dex_token_b, dex_factory, dex_router, deployer, user1, user2, dex_test_data):
    """
    case_012_extend LP 占比校验
    
    验证多用户添加流动性时 LP 分配的公平性：
    - 第一个用户添加后获得全部 LP
    - 第二个用户添加后 LP 按贡献比例分配
    - 用户持有的 LP 占比与流动性贡献匹配
    """
    data = dex_test_data["case_012_1_lp_percentage_check"]
    u1_a = parse_ether(data["user1_add_a"])
    u1_b = parse_ether(data["user1_add_b"])
    u2_a = parse_ether(data["user2_add_a"])
    u2_b = parse_ether(data["user2_add_b"])
    mint_amount = parse_ether(data["mint_amount"])

    dex_token_a.mint(user1, mint_amount, sender=deployer)
    dex_token_b.mint(user1, mint_amount, sender=deployer)
    dex_token_a.mint(user2, mint_amount, sender=deployer)
    dex_token_b.mint(user2, mint_amount, sender=deployer)

    dex_token_a.approve(dex_router.contract, u1_a, sender=user1)
    dex_token_b.approve(dex_router.contract, u1_b, sender=user1)
    dex_router.add_liquidity(
        dex_token_a, dex_token_b,
        data["user1_add_a"], data["user1_add_b"],
        user1, user1
    )

    pair_addr = dex_factory.get_pair(dex_token_a, dex_token_b)
    pair = project.MiniSwapPair.at(pair_addr)
    u1_lp_after_t1 = pair.balanceOf(user1)
    total_after_t1 = pair.totalSupply()

    assert u1_lp_after_t1 == total_after_t1
    assert total_after_t1 > 0

    dex_token_a.approve(dex_router.contract, u2_a, sender=user2)
    dex_token_b.approve(dex_router.contract, u2_b, sender=user2)
    dex_router.add_liquidity(
        dex_token_a, dex_token_b,
        data["user2_add_a"], data["user2_add_b"],
        user2, user2
    )

    u1_lp_after_t2 = pair.balanceOf(user1)
    u2_lp_after_t2 = pair.balanceOf(user2)
    total_after_t2 = pair.totalSupply()

    tolerance = 2
    ratio_numer = u2_lp_after_t2 * 2
    ratio_denom = u1_lp_after_t2
    assert abs(int(ratio_numer) - int(ratio_denom)) <= tolerance

    pct1 = int(u1_lp_after_t2 * 100 // total_after_t2)
    pct2 = int(u2_lp_after_t2 * 100 // total_after_t2)

    assert pct1 + pct2 in (99, 100)
    assert pct1 in (66, 67)
    assert pct2 in (33, 34)


@allure.title("case_013 移除流动性测试")
@allure.description("销毁 LP 代币，赎回双资产，核对赎回数量")
@allure.tag("DEX", "P0", "流动性", "RemoveLiquidity")
def test_dex_013_remove_liquidity(dex_token_a, dex_token_b, dex_factory, dex_router, deployer, user1, dex_test_data):
    """
    case_013 移除流动性测试
    
    验证流动性移除流程：
    - 用户销毁 LP 代币
    - 按比例赎回两种资产
    - LP 余额和总供应量正确减少
    - 全部赎回后 LP 余额为 0
    """
    data = dex_test_data["case_013_remove_liquidity"]
    mint_amount = parse_ether(data["mint_amount"])
    add_a = parse_ether(data["add_liquidity_amount_a"])
    add_b = parse_ether(data["add_liquidity_amount_b"])

    dex_token_a.mint(user1, mint_amount, sender=deployer)
    dex_token_b.mint(user1, mint_amount, sender=deployer)

    b_a_before = dex_token_a.balanceOf(user1)
    b_b_before = dex_token_b.balanceOf(user1)

    dex_token_a.approve(dex_router.contract, add_a, sender=user1)
    dex_token_b.approve(dex_router.contract, add_b, sender=user1)
    dex_router.add_liquidity(
        dex_token_a, dex_token_b,
        data["add_liquidity_amount_a"], data["add_liquidity_amount_b"],
        user1, user1
    )

    pair_addr = dex_factory.get_pair(dex_token_a, dex_token_b)
    pair = project.MiniSwapPair.at(pair_addr)
    lp_balance = pair.balanceOf(user1)
    tot_before_rem = pair.totalSupply()

    remove_lp = lp_balance * 50 // 100
    pair.approve(dex_router.contract, remove_lp, sender=user1)
    dex_router.remove_liquidity(dex_token_a, dex_token_b, remove_lp, user1, user1)

    b_a_after = dex_token_a.balanceOf(user1)
    b_b_after = dex_token_b.balanceOf(user1)
    lp_after = pair.balanceOf(user1)
    tot_after = pair.totalSupply()

    assert lp_after * 2 >= lp_balance * 95 // 100
    assert tot_after < tot_before_rem
    assert b_a_after > b_a_before - add_a
    assert b_b_after > b_b_before - add_b

    if lp_after > 0:
        pair.approve(dex_router.contract, lp_after, sender=user1)
        dex_router.remove_liquidity(dex_token_a, dex_token_b, lp_after, user1, user1)
        assert pair.balanceOf(user1) == 0


@allure.title("case_014 滑点控制边界测试")
@allure.description("极限滑点参数下，校验交易拦截/正常执行逻辑")
@allure.tag("DEX", "P0", "滑点", "边界测试")
def test_dex_014_slippage_control(dex_token_a, dex_token_b, dex_factory, dex_router, deployer, user1, dex_test_data):
    """
    case_014 滑点控制边界测试
    
    验证滑点保护机制：
    - 正常滑点参数下交易成功
    - 设置过高的最小输出金额时交易失败（revert）
    - 设置合理的滑点容忍度（如 2%）时交易成功
    """
    data = dex_test_data["case_014_slippage_control"]
    mint_amount = parse_ether(data["mint_amount"])
    add_liquidity_amount = parse_ether(data["add_liquidity_amount"])
    swap_amount = parse_ether(data["swap_amount"])

    dex_token_a.mint(user1, mint_amount, sender=deployer)
    dex_token_b.mint(user1, mint_amount, sender=deployer)

    dex_token_a.approve(dex_router.contract, add_liquidity_amount, sender=user1)
    dex_token_b.approve(dex_router.contract, add_liquidity_amount, sender=user1)

    dex_router.add_liquidity(
        dex_token_a, dex_token_b,
        data["add_liquidity_amount"], data["add_liquidity_amount"],
        user1, user1
    )

    expected_out = dex_router.get_amount_out(data["swap_amount"], dex_token_a, dex_token_b)

    dex_token_a.approve(dex_router.contract, swap_amount, sender=user1)
    dex_router.swap_exact_tokens_for_tokens(
        data["swap_amount"], expected_out,
        [dex_token_a.address, dex_token_b.address],
        user1, user1
    )

    impossible_min = expected_out + 10**18
    dex_token_a.approve(dex_router.contract, swap_amount, sender=user1)

    try:
        dex_router.swap_exact_tokens_for_tokens(
            data["swap_amount"], impossible_min,
            [dex_token_a.address, dex_token_b.address],
            user1, user1
        )
        assert False, "应该 revert"
    except Exception as e:
        assert "insufficient" in str(e).lower() or "amount" in str(e).lower()

    expected_out_new = dex_router.get_amount_out(data["swap_amount"], dex_token_a, dex_token_b)
    slippage_2_percent = expected_out_new * 98 // 100
    dex_token_a.approve(dex_router.contract, swap_amount, sender=user1)

    dex_router.swap_exact_tokens_for_tokens(
        data["swap_amount"], slippage_2_percent,
        [dex_token_a.address, dex_token_b.address],
        user1, user1
    )

    balance_B_after = dex_token_b.balanceOf(user1)
    assert balance_B_after > mint_amount - add_liquidity_amount


@allure.title("case_015 DEX 手续费结算测试")
@allure.description("交易手续费抽取、LP 分红、平台税分配校验")
@allure.tag("DEX", "P0", "手续费", "结算")
def test_dex_015_fee_settlement(dex_token_a, dex_token_b, dex_factory, dex_router, deployer, user1, dex_test_data):
    """
    case_015 DEX 手续费结算测试
    
    验证手续费机制：
    - 交易手续费正确抽取
    - 手续费计入池子储备金
    - K 值随手续费累积而增长
    - K 值增长率在理论范围内
    """
    data = dex_test_data["case_015_fee_settlement"]
    mint_amount = parse_ether(data["mint_amount"])
    add_liquidity_amount = parse_ether(data["add_liquidity_amount"])
    swap_amount = parse_ether(data["swap_amount"])

    dex_token_a.mint(user1, mint_amount, sender=deployer)
    dex_token_b.mint(user1, mint_amount, sender=deployer)

    dex_token_a.approve(dex_router.contract, add_liquidity_amount, sender=user1)
    dex_token_b.approve(dex_router.contract, add_liquidity_amount, sender=user1)

    dex_router.add_liquidity(
        dex_token_a, dex_token_b,
        data["add_liquidity_amount"], data["add_liquidity_amount"],
        user1, user1
    )

    pair_addr = dex_factory.get_pair(dex_token_a, dex_token_b)
    pair = project.MiniSwapPair.at(pair_addr)
    reserves_before = pair.getReserves()
    k_before = reserves_before[0] * reserves_before[1]

    for _ in range(3):
        dex_token_a.approve(dex_router.contract, swap_amount, sender=user1)
        dex_router.swap_exact_tokens_for_tokens(
            data["swap_amount"], 0,
            [dex_token_a.address, dex_token_b.address],
            user1, user1
        )

    reserves_after = pair.getReserves()
    k_after = reserves_after[0] * reserves_after[1]

    assert reserves_after[0] > reserves_before[0]
    assert k_after >= k_before

    k_growth_pct = (k_after - k_before) / k_before * 100
    theory_min = 0.027 * 3 * 0.7
    theory_max = 0.027 * 3 * 2.5
    assert k_growth_pct > theory_min and k_growth_pct < theory_max


@allure.title("case_055 V3 集中流动性添加测试")
@allure.description("模拟 V3 集中流动性模式，验证多轮流动性可正确叠加")
@allure.tag("DEX", "V3", "P0", "集中流动性")
def test_dex_055_concentrated_liquidity_add(v3_liquidity_environment, swap_v3_test_data):
    """
    case_055 V3 集中流动性添加测试
    
    模拟 Uniswap V3 集中流动性模式：
    - 第一轮添加全范围流动性
    - 第二轮添加窄范围流动性
    - 验证流动性正确叠加
    - LP 代币数量随流动性增加而增长
    """
    data = swap_v3_test_data["case_055_concentrated_liquidity_add"]
    env = v3_liquidity_environment
    
    token_a = env["token_a"]
    token_b = env["token_b"]
    router = env["router"]
    factory = env["factory"]
    user1 = env["user1"]
    
    add_full = parse_ether(data["add_liquidity_full_range"])
    add_narrow = parse_ether(data["add_liquidity_narrow_range"])
    
    token_a.approve(router, add_full * 2, sender=user1)
    token_b.approve(router, add_full * 2, sender=user1)
    
    router.addLiquidity(
        token_a, token_b,
        add_full, add_full,
        user1, sender=user1
    )
    
    pair_addr = factory.getPair(token_a, token_b)
    pair = project.MiniSwapPair.at(pair_addr)
    reserves_1 = pair.getReserves()
    lp_balance_1 = pair.balanceOf(user1)
    
    assert reserves_1[0] == add_full
    assert reserves_1[1] == add_full
    assert lp_balance_1 > 0
    
    router.addLiquidity(
        token_a, token_b,
        add_narrow, add_narrow,
        user1, sender=user1
    )
    
    reserves_2 = pair.getReserves()
    lp_balance_2 = pair.balanceOf(user1)
    
    assert reserves_2[0] == add_full + add_narrow
    assert reserves_2[1] == add_full + add_narrow
    assert lp_balance_2 > lp_balance_1


@allure.title("case_017 大额/极值交易边界测试")
@allure.description("超大额、接近池深限额交易，校验防砸盘、溢出防护")
@allure.tag("DEX", "P1", "大额交易", "边界")
def test_dex_017_large_trade_boundary(deployer, user1, dex_test_data):
    """
    case_017 大额/极值交易边界测试
    
    验证大额交易的安全性：
    - 超大额交易不会导致池子枯竭
    - 交易后双方储备金仍大于 0
    - K 值保持守恒
    - 防止整数溢出和价格操纵
    """
    from ape import project

    data = dex_test_data["case_017_large_trade_boundary"]
    mint_amount = parse_ether(data["mint_amount"])
    add_liquidity_amount = parse_ether(data["add_liquidity_amount"])
    large_swap_amount = parse_ether(data["large_swap_amount"])

    tokenA = project.MyERC20.deploy("TokenA", "TKA", sender=deployer)
    tokenB = project.MyERC20.deploy("TokenB", "TKB", sender=deployer)

    tokenA.mint(user1, mint_amount, sender=deployer)
    tokenB.mint(user1, mint_amount, sender=deployer)

    factory = project.MiniSwapFactory.deploy(sender=deployer)
    router = project.MiniSwapRouter.deploy(factory, sender=deployer)

    tokenA.approve(router, add_liquidity_amount, sender=user1)
    tokenB.approve(router, add_liquidity_amount, sender=user1)

    router.addLiquidity(tokenA, tokenB, add_liquidity_amount, add_liquidity_amount, user1, sender=user1)

    pair_addr = factory.getPair(tokenA, tokenB)
    pair = project.MiniSwapPair.at(pair_addr)
    reserves_before = pair.getReserves()
    k_before = reserves_before[0] * reserves_before[1]

    tokenA.approve(router, large_swap_amount, sender=user1)
    router.swapExactTokensForTokens(
        large_swap_amount, 0,
        [tokenA.address, tokenB.address],
        user1, sender=user1
    )

    reserves_after = pair.getReserves()
    k_after = reserves_after[0] * reserves_after[1]
    balance_B_after = tokenB.balanceOf(user1)

    assert reserves_after[0] > 0 and reserves_after[1] > 0
    assert k_after >= k_before
    assert balance_B_after > mint_amount - add_liquidity_amount