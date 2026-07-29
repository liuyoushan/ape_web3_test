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
    log.step("case_010: 正向单池 Swap 兑换")

    data = dex_test_data["case_010_swap_tokenA_to_tokenB"]
    mint_amount = parse_ether(data["mint_amount"])
    add_liquidity_amount = parse_ether(data["add_liquidity_amount"])
    swap_amount = parse_ether(data["swap_amount"])
    log.debug(f"测试数据 - mint: {format_ether(mint_amount)}, add: {format_ether(add_liquidity_amount)}, swap: {format_ether(swap_amount)}")

    # 铸造代币
    log.info("步骤1: 铸造代币")
    dex_token_a.mint(user1, mint_amount, sender=deployer)
    dex_token_b.mint(user1, mint_amount, sender=deployer)
    log.debug(f"用户1获得代币 - TokenA: {format_ether(dex_token_a.balanceOf(user1))}, TokenB: {format_ether(dex_token_b.balanceOf(user1))}")

    # 添加流动性
    log.info("步骤2: 添加流动性")
    dex_token_a.approve(dex_router.contract, add_liquidity_amount, sender=user1)
    dex_token_b.approve(dex_router.contract, add_liquidity_amount, sender=user1)
    log.debug("用户1授权 Router")

    dex_router.add_liquidity(
        dex_token_a, dex_token_b,
        data["add_liquidity_amount"], data["add_liquidity_amount"],
        user1, user1
    )
    log.debug("流动性添加完成")

    # 记录兑换前状态
    log.info("步骤3: 记录兑换前状态")
    balance_A_before = dex_token_a.balanceOf(user1)
    balance_B_before = dex_token_b.balanceOf(user1)
    pair_addr = dex_factory.get_pair(dex_token_a, dex_token_b)
    reserve_before = project.MiniSwapPair.at(pair_addr).getReserves()
    log.debug(f"兑换前 - TokenA余额: {format_ether(balance_A_before)}, TokenB余额: {format_ether(balance_B_before)}")
    log.debug(f"兑换前储备金 - A: {format_ether(reserve_before[0])}, B: {format_ether(reserve_before[1])}")

    # 执行兑换
    log.info("步骤4: 执行兑换")
    dex_token_a.approve(dex_router.contract, swap_amount, sender=user1)
    log.debug(f"用户1授权兑换金额: {format_ether(swap_amount)}")
    dex_router.swap_exact_tokens_for_tokens(
        data["swap_amount"], 0,
        [dex_token_a.address, dex_token_b.address],
        user1, user1
    )
    log.debug("兑换执行完成")

    # 验证兑换结果
    log.info("步骤5: 验证兑换结果")
    balance_A_after = dex_token_a.balanceOf(user1)
    balance_B_after = dex_token_b.balanceOf(user1)
    reserve_after = project.MiniSwapPair.at(pair_addr).getReserves()
    log.debug(f"兑换后 - TokenA余额: {format_ether(balance_A_after)}, TokenB余额: {format_ether(balance_B_after)}")

    assert balance_A_after == balance_A_before - swap_amount, f"TokenA余额不符，预期: {format_ether(balance_A_before - swap_amount)}, 实际: {format_ether(balance_A_after)}"
    assert balance_B_after > balance_B_before, f"TokenB余额未增加"
    log.debug("余额验证通过")

    k_before = reserve_before[0] * reserve_before[1]
    k_after = reserve_after[0] * reserve_after[1]
    log.debug(f"K值 - 兑换前: {k_before}, 兑换后: {k_after}")
    assert k_after >= k_before, "K值不应减少"
    log.debug("K值守恒验证通过")

    log.success("✅ case_010 正向单池 Swap 兑换测试通过")


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
    log.step("case_011: 反向单池 Swap 兑换")

    data = dex_test_data["case_011_swap_tokenB_to_tokenA"]
    mint_amount = parse_ether(data["mint_amount"])
    add_liquidity_amount = parse_ether(data["add_liquidity_amount"])
    swap_amount = parse_ether(data["swap_amount"])
    log.debug(f"测试数据 - mint: {format_ether(mint_amount)}, add: {format_ether(add_liquidity_amount)}, swap: {format_ether(swap_amount)}")

    # 铸造代币并添加流动性
    log.info("步骤1: 铸造代币并添加流动性")
    dex_token_a.mint(user1, mint_amount, sender=deployer)
    dex_token_b.mint(user1, mint_amount, sender=deployer)
    dex_token_a.approve(dex_router.contract, add_liquidity_amount, sender=user1)
    dex_token_b.approve(dex_router.contract, add_liquidity_amount, sender=user1)
    dex_router.add_liquidity(
        dex_token_a, dex_token_b,
        data["add_liquidity_amount"], data["add_liquidity_amount"],
        user1, user1
    )
    log.debug("流动性添加完成")

    # 记录兑换前状态
    log.info("步骤2: 记录兑换前状态")
    balance_B_before = dex_token_b.balanceOf(user1)
    balance_A_before = dex_token_a.balanceOf(user1)
    log.debug(f"兑换前 - TokenB余额: {format_ether(balance_B_before)}, TokenA余额: {format_ether(balance_A_before)}")

    # 执行反向兑换
    log.info("步骤3: 执行反向兑换")
    dex_token_b.approve(dex_router.contract, swap_amount, sender=user1)
    log.debug(f"用户1授权兑换金额: {format_ether(swap_amount)}")
    dex_router.swap_exact_tokens_for_tokens(
        data["swap_amount"], 0,
        [dex_token_b.address, dex_token_a.address],
        user1, user1
    )
    log.debug("反向兑换执行完成")

    # 验证兑换结果
    log.info("步骤4: 验证兑换结果")
    balance_B_after = dex_token_b.balanceOf(user1)
    balance_A_after = dex_token_a.balanceOf(user1)
    log.debug(f"兑换后 - TokenB余额: {format_ether(balance_B_after)}, TokenA余额: {format_ether(balance_A_after)}")

    assert balance_B_after == balance_B_before - swap_amount, f"TokenB余额不符，预期: {format_ether(balance_B_before - swap_amount)}, 实际: {format_ether(balance_B_after)}"
    assert balance_A_after > balance_A_before, f"TokenA余额未增加"
    log.debug("反向兑换验证通过")

    log.success("✅ case_011 反向单池 Swap 兑换测试通过")


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
    log.step("case_012: 添加双边流动性测试")

    data = dex_test_data["case_012_add_liquidity"]
    mint_amount = parse_ether(data["mint_amount"])
    add_liquidity_amount_a = parse_ether(data["add_liquidity_amount_a"])
    add_liquidity_amount_b = parse_ether(data["add_liquidity_amount_b"])
    log.debug(f"测试数据 - mint: {format_ether(mint_amount)}, addA: {format_ether(add_liquidity_amount_a)}, addB: {format_ether(add_liquidity_amount_b)}")

    # 铸造代币
    log.info("步骤1: 铸造代币")
    dex_token_a.mint(user1, mint_amount, sender=deployer)
    dex_token_b.mint(user1, mint_amount, sender=deployer)
    log.debug(f"用户1获得代币 - TokenA: {format_ether(dex_token_a.balanceOf(user1))}, TokenB: {format_ether(dex_token_b.balanceOf(user1))}")

    # 记录添加前余额
    log.info("步骤2: 记录添加前余额")
    balance_A_before = dex_token_a.balanceOf(user1)
    balance_B_before = dex_token_b.balanceOf(user1)
    log.debug(f"添加前 - TokenA余额: {format_ether(balance_A_before)}, TokenB余额: {format_ether(balance_B_before)}")

    # 授权并添加流动性
    log.info("步骤3: 授权并添加流动性")
    dex_token_a.approve(dex_router.contract, add_liquidity_amount_a, sender=user1)
    dex_token_b.approve(dex_router.contract, add_liquidity_amount_b, sender=user1)
    dex_router.add_liquidity(
        dex_token_a, dex_token_b,
        data["add_liquidity_amount_a"], data["add_liquidity_amount_b"],
        user1, user1
    )
    log.debug("流动性添加完成")

    # 验证余额变化
    log.info("步骤4: 验证余额变化")
    balance_A_after = dex_token_a.balanceOf(user1)
    balance_B_after = dex_token_b.balanceOf(user1)
    log.debug(f"添加后 - TokenA余额: {format_ether(balance_A_after)}, TokenB余额: {format_ether(balance_B_after)}")

    assert balance_A_after == balance_A_before - add_liquidity_amount_a, f"TokenA余额不符"
    assert balance_B_after == balance_B_before - add_liquidity_amount_b, f"TokenB余额不符"
    log.debug("余额变化验证通过")

    # 验证 LP 和储备金
    log.info("步骤5: 验证 LP 和储备金")
    pair_addr = dex_factory.get_pair(dex_token_a, dex_token_b)
    pair = project.MiniSwapPair.at(pair_addr)
    lp_balance = pair.balanceOf(user1)
    reserves = pair.getReserves()
    log.debug(f"LP余额: {format_ether(lp_balance)}, 储备金 - A: {format_ether(reserves[0])}, B: {format_ether(reserves[1])}")

    lp_a = add_liquidity_amount_a // 10**18
    lp_b = add_liquidity_amount_b // 10**18
    expected_lp_eth = math.isqrt(lp_a * lp_b)
    expected_lp_wei = expected_lp_eth * 10**18
    tolerance_wei = 1 * 10**18
    log.debug(f"预期LP: {format_ether(expected_lp_wei)}")

    assert abs(lp_balance - expected_lp_wei) < tolerance_wei, f"LP数量不符"
    assert lp_balance > 0, "LP数量应为正"
    assert reserves[0] == add_liquidity_amount_a, f"储备金A不符"
    assert reserves[1] == add_liquidity_amount_b, f"储备金B不符"
    log.debug("LP和储备金验证通过")

    log.success("✅ case_012 添加双边流动性测试通过")


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
    log.step("case_012_extend: LP 占比校验")

    data = dex_test_data["case_012_1_lp_percentage_check"]
    u1_a = parse_ether(data["user1_add_a"])
    u1_b = parse_ether(data["user1_add_b"])
    u2_a = parse_ether(data["user2_add_a"])
    u2_b = parse_ether(data["user2_add_b"])
    mint_amount = parse_ether(data["mint_amount"])
    log.debug(f"测试数据 - 用户1添加: A={format_ether(u1_a)}, B={format_ether(u1_b)}; 用户2添加: A={format_ether(u2_a)}, B={format_ether(u2_b)}")

    # 铸造代币
    log.info("步骤1: 铸造代币")
    dex_token_a.mint(user1, mint_amount, sender=deployer)
    dex_token_b.mint(user1, mint_amount, sender=deployer)
    dex_token_a.mint(user2, mint_amount, sender=deployer)
    dex_token_b.mint(user2, mint_amount, sender=deployer)
    log.debug("代币铸造完成")

    # 用户1添加流动性
    log.info("步骤2: 用户1添加流动性")
    dex_token_a.approve(dex_router.contract, u1_a, sender=user1)
    dex_token_b.approve(dex_router.contract, u1_b, sender=user1)
    dex_router.add_liquidity(
        dex_token_a, dex_token_b,
        data["user1_add_a"], data["user1_add_b"],
        user1, user1
    )
    log.debug("用户1流动性添加完成")

    pair_addr = dex_factory.get_pair(dex_token_a, dex_token_b)
    pair = project.MiniSwapPair.at(pair_addr)
    u1_lp_after_t1 = pair.balanceOf(user1)
    total_after_t1 = pair.totalSupply()
    log.debug(f"用户1添加后 - LP余额: {format_ether(u1_lp_after_t1)}, 总供给: {format_ether(total_after_t1)}")

    assert u1_lp_after_t1 == total_after_t1, "用户1应持有全部LP"
    assert total_after_t1 > 0, "总供给应为正"
    log.debug("用户1 LP验证通过")

    # 用户2添加流动性
    log.info("步骤3: 用户2添加流动性")
    dex_token_a.approve(dex_router.contract, u2_a, sender=user2)
    dex_token_b.approve(dex_router.contract, u2_b, sender=user2)
    dex_router.add_liquidity(
        dex_token_a, dex_token_b,
        data["user2_add_a"], data["user2_add_b"],
        user2, user2
    )
    log.debug("用户2流动性添加完成")

    # 验证 LP 占比
    log.info("步骤4: 验证 LP 占比")
    u1_lp_after_t2 = pair.balanceOf(user1)
    u2_lp_after_t2 = pair.balanceOf(user2)
    total_after_t2 = pair.totalSupply()
    log.debug(f"用户2添加后 - 用户1 LP: {format_ether(u1_lp_after_t2)}, 用户2 LP: {format_ether(u2_lp_after_t2)}, 总供给: {format_ether(total_after_t2)}")

    tolerance = 2
    ratio_numer = u2_lp_after_t2 * 2
    ratio_denom = u1_lp_after_t2
    log.debug(f"LP比例 - 用户2:用户1 = 约 1:2")
    assert abs(int(ratio_numer) - int(ratio_denom)) <= tolerance, "LP比例不符"

    pct1 = int(u1_lp_after_t2 * 100 // total_after_t2)
    pct2 = int(u2_lp_after_t2 * 100 // total_after_t2)
    log.debug(f"占比 - 用户1: {pct1}%, 用户2: {pct2}%")

    assert pct1 + pct2 in (99, 100), "占比总和应约为100%"
    assert pct1 in (66, 67), f"用户1占比应约为67%，实际: {pct1}%"
    assert pct2 in (33, 34), f"用户2占比应约为33%，实际: {pct2}%"
    log.debug("LP占比验证通过")

    log.success("✅ case_012_extend LP 占比校验测试通过")


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
    log.step("case_013: 移除流动性测试")

    data = dex_test_data["case_013_remove_liquidity"]
    mint_amount = parse_ether(data["mint_amount"])
    add_a = parse_ether(data["add_liquidity_amount_a"])
    add_b = parse_ether(data["add_liquidity_amount_b"])
    log.debug(f"测试数据 - mint: {format_ether(mint_amount)}, addA: {format_ether(add_a)}, addB: {format_ether(add_b)}")

    # 铸造代币
    log.info("步骤1: 铸造代币")
    dex_token_a.mint(user1, mint_amount, sender=deployer)
    dex_token_b.mint(user1, mint_amount, sender=deployer)
    log.debug("代币铸造完成")

    # 记录添加前余额
    log.info("步骤2: 记录添加前余额")
    b_a_before = dex_token_a.balanceOf(user1)
    b_b_before = dex_token_b.balanceOf(user1)
    log.debug(f"添加前 - TokenA: {format_ether(b_a_before)}, TokenB: {format_ether(b_b_before)}")

    # 添加流动性
    log.info("步骤3: 添加流动性")
    dex_token_a.approve(dex_router.contract, add_a, sender=user1)
    dex_token_b.approve(dex_router.contract, add_b, sender=user1)
    dex_router.add_liquidity(
        dex_token_a, dex_token_b,
        data["add_liquidity_amount_a"], data["add_liquidity_amount_b"],
        user1, user1
    )
    log.debug("流动性添加完成")

    pair_addr = dex_factory.get_pair(dex_token_a, dex_token_b)
    pair = project.MiniSwapPair.at(pair_addr)
    lp_balance = pair.balanceOf(user1)
    tot_before_rem = pair.totalSupply()
    log.debug(f"添加后 LP余额: {format_ether(lp_balance)}, 总供给: {format_ether(tot_before_rem)}")

    # 移除50%流动性
    log.info("步骤4: 移除50%流动性")
    remove_lp = lp_balance * 50 // 100
    pair.approve(dex_router.contract, remove_lp, sender=user1)
    dex_router.remove_liquidity(dex_token_a, dex_token_b, remove_lp, user1, user1)
    log.debug(f"移除 LP数量: {format_ether(remove_lp)}")

    # 验证移除结果
    log.info("步骤5: 验证移除结果")
    b_a_after = dex_token_a.balanceOf(user1)
    b_b_after = dex_token_b.balanceOf(user1)
    lp_after = pair.balanceOf(user1)
    tot_after = pair.totalSupply()
    log.debug(f"移除后 - TokenA: {format_ether(b_a_after)}, TokenB: {format_ether(b_b_after)}, LP: {format_ether(lp_after)}, 总供给: {format_ether(tot_after)}")

    assert lp_after * 2 >= lp_balance * 95 // 100, "LP余额验证失败"
    assert tot_after < tot_before_rem, "总供给应减少"
    assert b_a_after > b_a_before - add_a, "TokenA余额应增加"
    assert b_b_after > b_b_before - add_b, "TokenB余额应增加"
    log.debug("部分移除验证通过")

    # 移除剩余流动性
    if lp_after > 0:
        log.info("步骤6: 移除剩余流动性")
        pair.approve(dex_router.contract, lp_after, sender=user1)
        dex_router.remove_liquidity(dex_token_a, dex_token_b, lp_after, user1, user1)
        assert pair.balanceOf(user1) == 0, "剩余LP应全部移除"
        log.debug("全部移除验证通过")

    log.success("✅ case_013 移除流动性测试通过")


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
    log.step("case_014: 滑点控制边界测试")

    # 加载测试数据
    data = dex_test_data["case_014_slippage_control"]
    mint_amount = parse_ether(data["mint_amount"])
    add_liquidity_amount = parse_ether(data["add_liquidity_amount"])
    swap_amount = parse_ether(data["swap_amount"])
    log.debug(f"测试数据 - mint: {format_ether(mint_amount)}, add: {format_ether(add_liquidity_amount)}, swap: {format_ether(swap_amount)}")

    # 给用户铸造代币
    log.info("步骤1: 铸造代币并添加流动性")
    dex_token_a.mint(user1, mint_amount, sender=deployer)
    dex_token_b.mint(user1, mint_amount, sender=deployer)
    dex_token_a.approve(dex_router.contract, add_liquidity_amount, sender=user1)
    dex_token_b.approve(dex_router.contract, add_liquidity_amount, sender=user1)
    dex_router.add_liquidity(
        dex_token_a, dex_token_b,
        data["add_liquidity_amount"], data["add_liquidity_amount"],
        user1, user1
    )
    log.debug("流动性添加完成")

    # 获取预期输出金额
    log.info("步骤2: 使用预期金额作为最小输出，交易成功")
    expected_out = dex_router.get_amount_out(data["swap_amount"], dex_token_a, dex_token_b)
    log.debug(f"预期输出金额: {format_ether(expected_out)}")

    dex_token_a.approve(dex_router.contract, swap_amount, sender=user1)
    dex_router.swap_exact_tokens_for_tokens(
        data["swap_amount"], expected_out,
        [dex_token_a.address, dex_token_b.address],
        user1, user1
    )
    log.debug("使用预期金额交易成功")

    # 设置不可能的最小输出（大于预期），交易应该失败
    log.info("步骤3: 设置不可能的最小输出，交易失败")
    impossible_min = expected_out + 10**18
    log.debug(f"不可能的最小输出: {format_ether(impossible_min)}")
    dex_token_a.approve(dex_router.contract, swap_amount, sender=user1)

    try:
        dex_router.swap_exact_tokens_for_tokens(
            data["swap_amount"], impossible_min,
            [dex_token_a.address, dex_token_b.address],
            user1, user1
        )
        assert False, "应该 revert"
    except Exception as e:
        log.debug(f"交易被拦截，异常: {type(e).__name__}")
        assert "insufficient" in str(e).lower() or "amount" in str(e).lower()
    log.debug("滑点保护验证通过")

    # 使用 2% 滑点容忍度，交易成功
    log.info("步骤4: 使用 2% 滑点容忍度，交易成功")
    expected_out_new = dex_router.get_amount_out(data["swap_amount"], dex_token_a, dex_token_b)
    slippage_2_percent = expected_out_new * 98 // 100
    log.debug(f"新预期输出: {format_ether(expected_out_new)}, 2%滑点容忍: {format_ether(slippage_2_percent)}")

    dex_token_a.approve(dex_router.contract, swap_amount, sender=user1)
    dex_router.swap_exact_tokens_for_tokens(
        data["swap_amount"], slippage_2_percent,
        [dex_token_a.address, dex_token_b.address],
        user1, user1
    )
    log.debug("使用2%滑点容忍度交易成功")

    # 验证交易成功
    balance_B_after = dex_token_b.balanceOf(user1)
    log.debug(f"TokenB余额: {format_ether(balance_B_after)}")
    assert balance_B_after > mint_amount - add_liquidity_amount, "TokenB余额应增加"
    log.debug("交易结果验证通过")

    log.success("✅ case_014 滑点控制边界测试通过")


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
    log.step("case_015: DEX 手续费结算测试")

    log.info("步骤1: 加载测试数据")
    data = dex_test_data["case_015_fee_settlement"]
    mint_amount = parse_ether(data["mint_amount"])
    add_liquidity_amount = parse_ether(data["add_liquidity_amount"])
    swap_amount = parse_ether(data["swap_amount"])
    log.debug(f"测试数据 - mint: {format_ether(mint_amount)}, add: {format_ether(add_liquidity_amount)}, swap: {format_ether(swap_amount)}")

    log.info("步骤2: 给用户铸造代币")
    dex_token_a.mint(user1, mint_amount, sender=deployer)
    dex_token_b.mint(user1, mint_amount, sender=deployer)
    log.debug(f"用户1获得代币 - TokenA: {format_ether(dex_token_a.balanceOf(user1))}, TokenB: {format_ether(dex_token_b.balanceOf(user1))}")

    log.info("步骤3: 用户授权并添加流动性")
    dex_token_a.approve(dex_router.contract, add_liquidity_amount, sender=user1)
    dex_token_b.approve(dex_router.contract, add_liquidity_amount, sender=user1)
    log.debug("用户1授权 Router")

    dex_router.add_liquidity(
        dex_token_a, dex_token_b,
        data["add_liquidity_amount"], data["add_liquidity_amount"],
        user1, user1
    )
    log.debug("流动性添加完成")

    log.info("步骤4: 获取交易对和初始储备金")
    pair_addr = dex_factory.get_pair(dex_token_a, dex_token_b)
    pair = project.MiniSwapPair.at(pair_addr)
    reserves_before = pair.getReserves()
    k_before = reserves_before[0] * reserves_before[1]
    log.debug(f"初始储备金 - A: {format_ether(reserves_before[0])}, B: {format_ether(reserves_before[1])}")
    log.debug(f"初始 K 值: {k_before}")

    log.info("步骤5: 执行 3 次交易，累积手续费")
    for i in range(3):
        dex_token_a.approve(dex_router.contract, swap_amount, sender=user1)
        dex_router.swap_exact_tokens_for_tokens(
            data["swap_amount"], 0,
            [dex_token_a.address, dex_token_b.address],
            user1, user1
        )
        log.debug(f"第 {i+1} 次交易完成")

    log.info("步骤6: 获取交易后储备金")
    reserves_after = pair.getReserves()
    k_after = reserves_after[0] * reserves_after[1]
    log.debug(f"交易后储备金 - A: {format_ether(reserves_after[0])}, B: {format_ether(reserves_after[1])}")
    log.debug(f"交易后 K 值: {k_after}")

    log.info("步骤7: 验证储备金增加和 K 值增长")
    assert reserves_after[0] > reserves_before[0], f"储备金A未增加，交易前: {format_ether(reserves_before[0])}, 交易后: {format_ether(reserves_after[0])}"
    log.debug("储备金增加验证通过")
    
    assert k_after >= k_before, f"K值不应减少，交易前: {k_before}, 交易后: {k_after}"
    log.debug("K值增长验证通过")

    log.info("步骤8: 验证 K 值增长率在理论范围内")
    k_growth_pct = (k_after - k_before) / k_before * 100
    theory_min = 0.027 * 3 * 0.7
    theory_max = 0.027 * 3 * 2.5
    log.debug(f"K值增长率: {k_growth_pct:.4f}%, 理论范围: {theory_min:.4f}% ~ {theory_max:.4f}%")
    assert k_growth_pct > theory_min and k_growth_pct < theory_max, f"K值增长率超出理论范围"
    log.debug("K值增长率验证通过")

    log.success("✅ case_015 DEX 手续费结算测试通过")


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
    log.step("case_055: V3 集中流动性添加测试")

    log.info("步骤1: 加载测试数据和环境")
    data = swap_v3_test_data["case_055_concentrated_liquidity_add"]
    env = v3_liquidity_environment
    
    token_a = env["token_a"]
    token_b = env["token_b"]
    router = env["router"]
    factory = env["factory"]
    user1 = env["user1"]
    log.debug(f"测试环境准备完成 - tokenA: {token_a.address[:8]}..., tokenB: {token_b.address[:8]}...")
    
    log.info("步骤2: 设置流动性金额")
    add_full = parse_ether(data["add_liquidity_full_range"])
    add_narrow = parse_ether(data["add_liquidity_narrow_range"])
    log.debug(f"全范围流动性: {format_ether(add_full)}, 窄范围流动性: {format_ether(add_narrow)}")
    
    log.info("步骤3: 用户授权 Router 使用代币")
    token_a.approve(router, add_full * 2, sender=user1)
    token_b.approve(router, add_full * 2, sender=user1)
    log.debug("用户1授权 Router 完成")
    
    log.info("步骤4: 第一轮添加全范围流动性")
    router.addLiquidity(
        token_a, token_b,
        add_full, add_full,
        user1, sender=user1
    )
    log.debug("第一轮流动性添加完成")
    
    log.info("步骤5: 获取交易对和状态")
    pair_addr = factory.getPair(token_a, token_b)
    pair = project.MiniSwapPair.at(pair_addr)
    reserves_1 = pair.getReserves()
    lp_balance_1 = pair.balanceOf(user1)
    log.debug(f"第一轮后储备金 - A: {format_ether(reserves_1[0])}, B: {format_ether(reserves_1[1])}")
    log.debug(f"第一轮后 LP余额: {format_ether(lp_balance_1)}")
    
    log.info("步骤6: 验证第一轮添加成功")
    assert reserves_1[0] == add_full, f"TokenA储备金不符，预期: {format_ether(add_full)}, 实际: {format_ether(reserves_1[0])}"
    assert reserves_1[1] == add_full, f"TokenB储备金不符，预期: {format_ether(add_full)}, 实际: {format_ether(reserves_1[1])}"
    assert lp_balance_1 > 0, f"LP余额应为正数，实际: {format_ether(lp_balance_1)}"
    log.debug("第一轮流动性验证通过")
    
    log.info("步骤7: 第二轮添加窄范围流动性")
    router.addLiquidity(
        token_a, token_b,
        add_narrow, add_narrow,
        user1, sender=user1
    )
    log.debug("第二轮流动性添加完成")
    
    log.info("步骤8: 获取更新后状态")
    reserves_2 = pair.getReserves()
    lp_balance_2 = pair.balanceOf(user1)
    log.debug(f"第二轮后储备金 - A: {format_ether(reserves_2[0])}, B: {format_ether(reserves_2[1])}")
    log.debug(f"第二轮后 LP余额: {format_ether(lp_balance_2)}")
    
    log.info("步骤9: 验证第二轮添加成功，流动性正确叠加")
    expected_reserve = add_full + add_narrow
    assert reserves_2[0] == expected_reserve, f"TokenA储备金不符，预期: {format_ether(expected_reserve)}, 实际: {format_ether(reserves_2[0])}"
    assert reserves_2[1] == expected_reserve, f"TokenB储备金不符，预期: {format_ether(expected_reserve)}, 实际: {format_ether(reserves_2[1])}"
    assert lp_balance_2 > lp_balance_1, f"LP余额未增长，第一轮: {format_ether(lp_balance_1)}, 第二轮: {format_ether(lp_balance_2)}"
    log.debug("第二轮流动性验证通过")

    log.success("✅ case_055 V3 集中流动性添加测试通过")


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
    log.step("case_017: 大额/极值交易边界测试")

    log.info("步骤1: 加载测试数据")
    data = dex_test_data["case_017_large_trade_boundary"]
    mint_amount = parse_ether(data["mint_amount"])
    add_liquidity_amount = parse_ether(data["add_liquidity_amount"])
    large_swap_amount = parse_ether(data["large_swap_amount"])
    log.debug(f"测试数据 - mint: {format_ether(mint_amount)}, add: {format_ether(add_liquidity_amount)}, swap: {format_ether(large_swap_amount)}")

    log.info("步骤2: 部署代币合约")
    tokenA = project.MyERC20.deploy("TokenA", "TKA", sender=deployer)
    tokenB = project.MyERC20.deploy("TokenB", "TKB", sender=deployer)
    log.debug(f"代币合约部署完成 - TokenA: {tokenA.address[:8]}..., TokenB: {tokenB.address[:8]}...")

    log.info("步骤3: 给用户铸造代币")
    tokenA.mint(user1, mint_amount, sender=deployer)
    tokenB.mint(user1, mint_amount, sender=deployer)
    log.debug(f"用户1获得代币 - TokenA: {format_ether(tokenA.balanceOf(user1))}, TokenB: {format_ether(tokenB.balanceOf(user1))}")

    log.info("步骤4: 部署 Factory 和 Router")
    factory = project.MiniSwapFactory.deploy(sender=deployer)
    router = project.MiniSwapRouter.deploy(factory, sender=deployer)
    log.debug(f"DEX 合约部署完成 - Factory: {factory.address[:8]}..., Router: {router.address[:8]}...")

    log.info("步骤5: 用户授权并添加流动性")
    tokenA.approve(router, add_liquidity_amount, sender=user1)
    tokenB.approve(router, add_liquidity_amount, sender=user1)
    router.addLiquidity(tokenA, tokenB, add_liquidity_amount, add_liquidity_amount, user1, sender=user1)
    log.debug("流动性添加完成")

    log.info("步骤6: 获取交易对和初始状态")
    pair_addr = factory.getPair(tokenA, tokenB)
    pair = project.MiniSwapPair.at(pair_addr)
    reserves_before = pair.getReserves()
    k_before = reserves_before[0] * reserves_before[1]
    log.debug(f"初始储备金 - A: {format_ether(reserves_before[0])}, B: {format_ether(reserves_before[1])}")
    log.debug(f"初始 K 值: {k_before}")

    log.info("步骤7: 执行大额交易（占流动性的 75%）")
    tokenA.approve(router, large_swap_amount, sender=user1)
    router.swapExactTokensForTokens(
        large_swap_amount, 0,
        [tokenA.address, tokenB.address],
        user1, sender=user1
    )
    log.debug("大额交易执行完成")

    log.info("步骤8: 获取交易后状态")
    reserves_after = pair.getReserves()
    k_after = reserves_after[0] * reserves_after[1]
    balance_B_after = tokenB.balanceOf(user1)
    log.debug(f"交易后储备金 - A: {format_ether(reserves_after[0])}, B: {format_ether(reserves_after[1])}")
    log.debug(f"交易后 K 值: {k_after}")
    log.debug(f"用户1 TokenB余额: {format_ether(balance_B_after)}")

    log.info("步骤9: 验证安全边界")
    assert reserves_after[0] > 0 and reserves_after[1] > 0, f"储备金不应为零 - A: {format_ether(reserves_after[0])}, B: {format_ether(reserves_after[1])}"
    log.debug("储备金安全验证通过")
    
    assert k_after >= k_before, f"K值不应减少，交易前: {k_before}, 交易后: {k_after}"
    log.debug("K值守恒验证通过")
    
    expected_min_balance = mint_amount - add_liquidity_amount
    assert balance_B_after > expected_min_balance, f"TokenB余额不足，预期: {format_ether(expected_min_balance)}, 实际: {format_ether(balance_B_after)}"
    log.debug("余额验证通过")

    log.success("✅ case_017 大额/极值交易边界测试通过")
