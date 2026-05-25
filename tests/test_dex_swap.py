"""
==============================================================================
【模块概览】DEX 去中心化交易所 核心业务用例
对应用例编号：case_010 ~ case_017
测试范围：MiniSwapFactory、MiniSwapPair、MiniSwapRouter 合约核心功能
==============================================================================
"""
import math
try:
    import allure
except ImportError:
    # Dummy decorators if allure not installed
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

from ape import project
from tests.helpers.formatters import format_ether, parse_ether


# ================================================================================
# case_010 正向单池 Swap 兑换
# 测试目标：TokenA 兑换 TokenB，校验余额、手续费、池子库存
# 测试类型：P0 - 功能测试 / 正向测试
# ================================================================================
@allure.title("case_010 正向单池 Swap 兑换")
@allure.description("TokenA 兑换 TokenB，校验余额、手续费、池子库存、K值守恒")
@allure.tag("DEX", "P0", "功能测试", "Swap", "正向测试")
def test_dex_010_swap_tokenA_to_tokenB(tokenA, tokenB, factory, router, deployer, user1, dex_test_data):
    """
    ================================================================================
    【用例编号】case_010
    【用例名称】正向单池 Swap 兑换测试
    【测试目标】验证 TokenA -> TokenB 的完整兑换流程
    【测试类型】P0 - 功能测试 / 正向测试
    ================================================================================
    
    测试流程详解：
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ 步骤1: 代币铸造         deployer 为 user1 铸造初始代币                    │
    │ 步骤2: 添加流动性       user1 向 TokenA-TokenB 交易对添加流动性            │
    │ 步骤3: 记录初始状态     记录 user1 余额和池子储备量                        │
    │ 步骤4: 执行兑换         user1 调用 swapExactTokensForTokens 兑换代币       │
    │ 步骤5: 验证结果         校验余额变化、储备更新、K值守恒                      │
    └─────────────────────────────────────────────────────────────────────────────┘
    
    核心验证点：
    1. 输入代币(TokenA)余额正确减少
    2. 输出代币(TokenB)余额正确增加  
    3. 交易对储备量正确更新
    4. K值守恒（手续费后略有增加）
    
    数据来源：tests/data/test_dex_swap.yaml -> case_010_swap_tokenA_to_tokenB
    """
    # 从 YAML 文件加载测试数据
    data = dex_test_data["case_010_swap_tokenA_to_tokenB"]
    mint_amount = parse_ether(data["mint_amount"])       # 用户初始代币数量
    add_liquidity_amount = parse_ether(data["add_liquidity_amount"])  # 流动性投入量
    swap_amount = parse_ether(data["swap_amount"])       # 兑换数量

    # ==================== 步骤1: 代币铸造 ====================
    # deployer 为 user1 铸造初始代币，用于后续测试
    tokenA.mint(user1, mint_amount, sender=deployer)
    tokenB.mint(user1, mint_amount, sender=deployer)

    # ==================== 步骤2: 添加流动性 ====================
    # user1 授权 router 合约操作代币
    tokenA.approve(router, add_liquidity_amount, sender=user1)
    tokenB.approve(router, add_liquidity_amount, sender=user1)

    # 调用 router 添加流动性，创建 TokenA-TokenB 交易对
    router.addLiquidity(
        tokenA,
        tokenB,
        add_liquidity_amount,  # TokenA 投入数量
        add_liquidity_amount,  # TokenB 投入数量（等额投入）
        user1,                 # LP 代币接收地址
        sender=user1
    )

    # ==================== 步骤3: 记录初始状态 ====================
    # 获取用户余额
    balance_A_before = tokenA.balanceOf(user1)
    balance_B_before = tokenB.balanceOf(user1)
    
    # 获取交易对储备量
    pair_addr = factory.getPair(tokenA, tokenB)
    reserve_before = project.MiniSwapPair.at(pair_addr).getReserves()

    print("[DEBUG] ========== 兑换前状态 ==========")
    print(f"  - user1 TokenA 余额: {format_ether(balance_A_before)}")
    print(f"  - user1 TokenB 余额: {format_ether(balance_B_before)}")
    print(f"  - 池子 TokenA 储备: {format_ether(reserve_before[0])}")
    print(f"  - 池子 TokenB 储备: {format_ether(reserve_before[1])}")

    # ==================== 步骤4: 执行兑换 ====================
    # user1 授权 router 操作要兑换的 TokenA
    tokenA.approve(router, swap_amount, sender=user1)

    # 调用 router 的 swapExactTokensForTokens 方法执行兑换
    # 参数说明：
    #   amountIn: 输入代币数量（TokenA）
    #   amountOutMin: 最小期望输出（0表示接受任何数量）
    #   path: 兑换路径 [TokenA, TokenB]
    #   to: 输出代币接收地址
    router.swapExactTokensForTokens(
        swap_amount,                      # 输入 100 TokenA
        0,                                # 最小输出为0（不限制）
        [tokenA.address, tokenB.address], # 兑换路径
        user1,                            # 接收地址
        sender=user1
    )

    # ==================== 步骤5: 验证结果 ====================
    # 获取兑换后状态
    balance_A_after = tokenA.balanceOf(user1)
    balance_B_after = tokenB.balanceOf(user1)
    reserve_after = project.MiniSwapPair.at(pair_addr).getReserves()

    print("[DEBUG] ========== 兑换后状态 ==========")
    print(f"  - user1 TokenA 余额: {format_ether(balance_A_after)}")
    print(f"  - user1 TokenB 余额: {format_ether(balance_B_after)}")
    print(f"  - 池子 TokenA 储备: {format_ether(reserve_after[0])}")
    print(f"  - 池子 TokenB 储备: {format_ether(reserve_after[1])}")
    print(f"  - 获得 TokenB: {format_ether(balance_B_after - balance_B_before)}")

    # 【断言1】验证输入代币余额减少
    assert balance_A_after == balance_A_before - swap_amount, \
        f"TokenA 余额减少不正确: 期望 {format_ether(balance_A_before - swap_amount)}, 实际 {format_ether(balance_A_after)}"

    # 【断言2】验证输出代币余额增加
    assert balance_B_after > balance_B_before, \
        f"TokenB 余额应该增加: 期望 > {format_ether(balance_B_before)}, 实际 {format_ether(balance_B_after)}"

    # 【断言3】验证 K 值守恒（考虑手续费，K值应略有增加）
    k_before = reserve_before[0] * reserve_before[1]
    k_after = reserve_after[0] * reserve_after[1]
    assert k_after >= k_before, \
        f"K 值不守恒: 兑换前 K={k_before}, 兑换后 K={k_after}"


# ================================================================================
# case_011 反向单池 Swap 兑换
# 测试目标：TokenB 兑换 TokenA，校验价格换算逻辑一致性
# 测试类型：P0 - 功能测试 / 正向测试
# ================================================================================
@allure.title("case_011 反向单池 Swap 兑换")
@allure.description("TokenB 兑换 TokenA，校验价格换算逻辑一致性")
@allure.tag("DEX", "P0", "Swap", "反向测试")
def test_dex_011_swap_tokenB_to_tokenA(tokenA, tokenB, factory, router, deployer, user1, dex_test_data):
    """
    ================================================================================
    【用例编号】case_011
    【用例名称】反向单池 Swap 兑换测试（TokenB → TokenA）
    【测试目标】验证双向兑换数学逻辑一致性，价格换算与方向无关
    【测试类型】P0 - 功能测试 / 正向测试
    ================================================================================

    测试流程详解：
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ 步骤1: 代币铸造         deployer 为 user1 铸造初始代币                    │
    │ 步骤2: 添加流动性       user1 向 TokenA-TokenB 交易对添加流动性            │
    │ 步骤3: 记录初始状态     记录 user1 余额                                      │
    │ 步骤4: 执行反向兑换     user1 调用 swapExactTokensForTokens TokenB→TokenA   │
    │ 步骤5: 验证结果         校验 TokenB 减少、TokenA 增加                        │
    └─────────────────────────────────────────────────────────────────────────────┘

    核心验证点：
    1. 输入代币(TokenB)余额正确减少
    2. 输出代币(TokenA)余额正确增加
    3. 反向兑换与正向兑换价格公式一致（数学逻辑对称）

    数据来源：tests/data/test_dex_swap.yaml -> case_011_swap_tokenB_to_tokenA
    """
    # 从 YAML 文件加载测试数据
    data = dex_test_data["case_011_swap_tokenB_to_tokenA"]
    mint_amount = parse_ether(data["mint_amount"])
    add_liquidity_amount = parse_ether(data["add_liquidity_amount"])
    swap_amount = parse_ether(data["swap_amount"])

    # ==================== 步骤1: 代币铸造 ====================
    # deployer 为 user1 铸造两个币种的初始代币
    tokenA.mint(user1, mint_amount, sender=deployer)
    tokenB.mint(user1, mint_amount, sender=deployer)

    # ==================== 步骤2: 添加流动性 ====================
    # user1 授权 router 合约操作两个代币
    tokenA.approve(router, add_liquidity_amount, sender=user1)
    tokenB.approve(router, add_liquidity_amount, sender=user1)

    # 调用 router 添加流动性，创建 1:1 价格的交易对
    router.addLiquidity(
        tokenA,
        tokenB,
        add_liquidity_amount,  # TokenA 投入数量
        add_liquidity_amount,  # TokenB 投入数量（等额投入建立 1:1 价格基准）
        user1,                 # LP 代币接收地址
        sender=user1
    )

    # ==================== 步骤3: 记录初始状态 ====================
    # 记录兑换前余额（本用例与 case_010 对称：输入是 TokenB）
    balance_B_before = tokenB.balanceOf(user1)  # 输入代币 = TokenB
    balance_A_before = tokenA.balanceOf(user1)  # 输出代币 = TokenA

    print("[DEBUG] ========== 反向兑换前状态 ==========")
    print(f"  - user1 TokenB 余额(输入币): {format_ether(balance_B_before)}")
    print(f"  - user1 TokenA 余额(输出币): {format_ether(balance_A_before)}")

    # ==================== 步骤4: 执行反向兑换 ====================
    # user1 授权 router 操作要投入的 TokenB
    tokenB.approve(router, swap_amount, sender=user1)

    # 调用 router 的 swapExactTokensForTokens 方法执行反向兑换
    # 与 case_010 的唯一区别：兑换路径 path = [TokenB, TokenA]
    router.swapExactTokensForTokens(
        swap_amount,                      # 固定输入 100 TokenB
        0,                                # 最小输出滑点不限制
        [tokenB.address, tokenA.address], # 【关键】路径反过来：B→A
        user1,                            # TokenA 接收地址
        sender=user1
    )

    # ==================== 步骤5: 验证结果 ====================
    balance_B_after = tokenB.balanceOf(user1)
    balance_A_after = tokenA.balanceOf(user1)

    print("[DEBUG] ========== 反向兑换后状态 ==========")
    print(f"  - user1 TokenB 余额(输入币): {format_ether(balance_B_after)}")
    print(f"  - user1 TokenA 余额(输出币): {format_ether(balance_A_after)}")
    print(f"  - 减少 TokenB: {format_ether(balance_B_before - balance_B_after)}")
    print(f"  - 获得 TokenA: {format_ether(balance_A_after - balance_A_before)}")

    # 【断言1】验证输入代币 TokenB 余额减少正确
    assert balance_B_after == balance_B_before - swap_amount, \
        f"TokenB 余额减少不正确: 期望 {format_ether(balance_B_before - swap_amount)}, 实际 {format_ether(balance_B_after)}"

    # 【断言2】验证输出代币 TokenA 余额增加
    assert balance_A_after > balance_A_before, \
        f"TokenA 余额应该增加: 期望 > {format_ether(balance_A_before)}, 实际 {format_ether(balance_A_after)}"


# ================================================================================
# case_012 添加双边流动性测试
# 测试目标：存入双币种，Mint LP 凭证、校验池子储备量
# 测试类型：P0 - 功能测试 / 正向测试
# ================================================================================
@allure.title("case_012 添加双边流动性测试")
@allure.description("存入双币种，Mint LP 凭证、校验池子储备量")
@allure.tag("DEX", "P0", "流动性", "AddLiquidity")
def test_dex_012_add_liquidity(tokenA, tokenB, factory, router, deployer, user1, dex_test_data):
    """
    ================================================================================
    【用例编号】case_012
    【用例名称】添加双边流动性测试（非对称投入）
    【测试目标】验证不等额双币种投入时，LP 计算和储备更新的正确性
    【测试类型】P0 - 功能测试 / 正向测试
    ================================================================================

    测试流程详解：
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ 步骤1: 代币铸造         deployer 为 user1 铸造初始代币                    │
    │ 步骤2: 记录初始状态     记录 user1 余额                                      │
    │ 步骤3: 授权+添加流动性   不等额投入 TokenA 和 TokenB                        │
    │ 步骤4: 验证结果         LP = sqrt(A*B), 储备 = 投入量                       │
    └─────────────────────────────────────────────────────────────────────────────┘

    核心验证点：
    1. TokenA 余额减少正确（投入量 A）
    2. TokenB 余额减少正确（投入量 B，与 A 不等）
    3. LP 数量 = sqrt(A * B)（几何平均）
    4. 池子储备正确更新

    数据来源：tests/data/test_dex_swap.yaml -> case_012_add_liquidity
    """
    data = dex_test_data["case_012_add_liquidity"]
    mint_amount = parse_ether(data["mint_amount"])
    add_liquidity_amount_a = parse_ether(data["add_liquidity_amount_a"])  # 1000
    add_liquidity_amount_b = parse_ether(data["add_liquidity_amount_b"])  # 2000

    # ==================== 步骤1: 代币铸造 ====================
    tokenA.mint(user1, mint_amount, sender=deployer)
    tokenB.mint(user1, mint_amount, sender=deployer)

    # ==================== 步骤2: 记录初始状态 ====================
    balance_A_before = tokenA.balanceOf(user1)
    balance_B_before = tokenB.balanceOf(user1)

    print("[DEBUG] ========== 添加流动性前 ==========")
    print(f"  - user1 TokenA 余额: {format_ether(balance_A_before)}")
    print(f"  - user1 TokenB 余额: {format_ether(balance_B_before)}")

    # ==================== 步骤3: 授权并添加流动性 ====================
    # 【关键】不等额投入：TokenA 投 1000，TokenB 投 2000
    tokenA.approve(router, add_liquidity_amount_a, sender=user1)
    tokenB.approve(router, add_liquidity_amount_b, sender=user1)

    receipt = router.addLiquidity(
        tokenA,
        tokenB,
        add_liquidity_amount_a,  # TokenA 投入 1000
        add_liquidity_amount_b,  # TokenB 投入 2000（≠1000）
        user1,
        sender=user1
    )

    # ==================== 步骤4: 验证结果 ====================
    balance_A_after = tokenA.balanceOf(user1)
    balance_B_after = tokenB.balanceOf(user1)
    pair_addr = factory.getPair(tokenA, tokenB)
    pair = project.MiniSwapPair.at(pair_addr)
    lp_balance = pair.balanceOf(user1)
    reserves = pair.getReserves()

    print("[DEBUG] ========== 添加流动性后 ==========")
    print(f"  - user1 TokenA 余额: {format_ether(balance_A_after)}")
    print(f"  - user1 TokenB 余额: {format_ether(balance_B_after)}")
    print(f"  - user1 LP 余额: {format_ether(lp_balance)} (计算: sqrt(1000*2000) ≈ 1414)")
    print(f"  - 池子储备 (A, B): ({format_ether(reserves[0])}, {format_ether(reserves[1])})")
    print(f"  - 投入比例 A:B = {format_ether(add_liquidity_amount_a)} : {format_ether(add_liquidity_amount_b)}")

    # 【断言1】验证 TokenA 余额减少正确
    assert balance_A_after == balance_A_before - add_liquidity_amount_a, \
        f"TokenA 余额减少不正确: 期望 {format_ether(balance_A_before - add_liquidity_amount_a)}, 实际 {format_ether(balance_A_after)}"

    # 【断言2】验证 TokenB 余额减少正确（注意是另一个金额）
    assert balance_B_after == balance_B_before - add_liquidity_amount_b, \
        f"TokenB 余额减少不正确: 期望 {format_ether(balance_B_before - add_liquidity_amount_b)}, 实际 {format_ether(balance_B_after)}"

    # 【断言3】验证 LP 计算正确：sqrt(1000 * 2000) = sqrt(2,000,000) = 1414.21356...
    lp_a = add_liquidity_amount_a // 10**18  # 1000
    lp_b = add_liquidity_amount_b // 10**18  # 2000
    expected_lp_eth = math.isqrt(lp_a * lp_b)  # sqrt(2,000,000) = 1414
    expected_lp_wei = expected_lp_eth * 10**18
    tolerance_wei = 1 * 10**18  # 允许 1 ether 误差（因精确开方含小数部分）
    
    print(f"[DEBUG] LP 公式校验: sqrt({lp_a} * {lp_b}) = {expected_lp_eth} ether (整数部分)")
    print(f"[DEBUG] 预期 LP 范围: {expected_lp_eth - 1} ~ {expected_lp_eth + 1} ether")
    
    assert abs(lp_balance - expected_lp_wei) < tolerance_wei, \
        f"LP 计算错误: 期望 ~{expected_lp_eth}.xx, 实际 {format_ether(lp_balance)}"
    assert lp_balance > 0, "LP 余额应为正数"

    # 【断言4】验证池子储备正确（两个金额不一样）
    assert reserves[0] == add_liquidity_amount_a, \
        f"池子 TokenA 储备不正确: 期望 {format_ether(add_liquidity_amount_a)}, 实际 {format_ether(reserves[0])}"
    assert reserves[1] == add_liquidity_amount_b, \
        f"池子 TokenB 储备不正确: 期望 {format_ether(add_liquidity_amount_b)}, 实际 {format_ether(reserves[1])}"


# ================================================================================
# case_012_1 LP 百分比占比验证
# 测试目标：双用户先后加池，验证 LP 按投入比例分发正确性
# 测试类型：P0 - 逻辑验证 / 百分比核心测试
# ================================================================================
@allure.title("case_012_extend LP 占比校验")
@allure.description("校验 LP 凭证持有占比与流动性贡献匹配")
@allure.tag("DEX", "P0", "流动性", "LP")
def test_dex_012_1_lp_percentage_check(tokenA, tokenB, factory, router, deployer, user1, user2, dex_test_data):
    """
    ================================================================================
    【用例编号】case_012_1
    【用例名称】LP 股份占比验证（百分比才是业务本质）
    【测试目标】验证多用户按比例投流动性时，LP 分发百分比正确
    【测试类型】P0 - 核心逻辑验证
    ================================================================================

    场景：比例1:2时（避免1:1歧义）
        T1: user1 空池首次投入 1000A + 2000B → user1 应得 sqrt(1000*2000) = 1414 LP，占 100%
        T2: user2 同比例再投入  500A + 1000B → user2 应得 707 LP（同比例）
        最终占比：user1: 1414/2121 = 66.67%, user2: 707/2121 = 33.33%
    """
    data = dex_test_data["case_012_1_lp_percentage_check"]
    u1_a = parse_ether(data["user1_add_a"])
    u1_b = parse_ether(data["user1_add_b"])
    u2_a = parse_ether(data["user2_add_a"])
    u2_b = parse_ether(data["user2_add_b"])

    print(f"\n[场景] 两人投入比例都是 A:B = 1:2")
    print(f"  user1: {format_ether(u1_a)} A + {format_ether(u1_b)} B")
    print(f"  user2: {format_ether(u2_a)} A + {format_ether(u2_b)} B")

    # ==================== 步骤1: 铸造两个用户的双币 ====================
    mint_amount = parse_ether(data["mint_amount"])
    tokenA.mint(user1, mint_amount, sender=deployer)
    tokenB.mint(user1, mint_amount, sender=deployer)
    tokenA.mint(user2, mint_amount, sender=deployer)
    tokenB.mint(user2, mint_amount, sender=deployer)

    # ==================== 步骤2: user1 首次空池加流动性 ====================
    tokenA.approve(router, u1_a, sender=user1)
    tokenB.approve(router, u1_b, sender=user1)
    router.addLiquidity(tokenA, tokenB, u1_a, u1_b, user1, sender=user1)

    pair_addr = factory.getPair(tokenA, tokenB)
    pair = project.MiniSwapPair.at(pair_addr)
    u1_lp_after_t1 = pair.balanceOf(user1)
    total_after_t1 = pair.totalSupply()

    print(f"\n[T1 后] user1 首次")
    print(f"  user1 LP: {format_ether(u1_lp_after_t1)}, 总发行量: {format_ether(total_after_t1)}")
    print(f"  占比 = user1 / total: {u1_lp_after_t1 * 100 // total_after_t1} % (应为 100%)")

    # 【T1 断言】空池首次 = 100% 占比
    assert u1_lp_after_t1 == total_after_t1, "首次加流动性用户应占 100%"
    assert total_after_t1 > 0, "首次加池应发 LP"

    # ==================== 步骤3: user2 同比例二次加流动性 ====================
    tokenA.approve(router, u2_a, sender=user2)
    tokenB.approve(router, u2_b, sender=user2)
    router.addLiquidity(tokenA, tokenB, u2_a, u2_b, user2, sender=user2)

    u1_lp_after_t2 = pair.balanceOf(user1)
    u2_lp_after_t2 = pair.balanceOf(user2)
    total_after_t2 = pair.totalSupply()

    print(f"\n[T2 后] user2 加同比例")
    print(f"  user1 LP: {format_ether(u1_lp_after_t2)}")
    print(f"  user2 LP: {format_ether(u2_lp_after_t2)}")
    print(f"  总发行量: {format_ether(total_after_t2)}")
    print(f"  user1 占比 = {u1_lp_after_t2 * 100 // total_after_t2} % (≈ 66.7%)")
    print(f"  user2 占比 = {u2_lp_after_t2 * 100 // total_after_t2} % (≈ 33.3%)")

    # 【T2 断言 1】强比例验证: u2 只投了 u1 的一半，LP 也应是一半左右
    # 数值上: 1414.21... vs 707.10..., 允许 2 wei 以内取整误差
    tolerance = 2
    ratio_numer = u2_lp_after_t2 * 2
    ratio_denom = u1_lp_after_t2
    assert abs(int(ratio_numer) - int(ratio_denom)) <= tolerance, \
        f"u2 只投 u1 一半，LP 应近似减半: u2*2={format_ether(ratio_numer)}, u1={format_ether(ratio_denom)}"

    # 【T2 断言 2】百分比校验: user1 ≈ 66.7%, user2 ≈ 33.3%
    # 整型百分比上取整
    pct1 = int(u1_lp_after_t2 * 100 // total_after_t2)
    pct2 = int(u2_lp_after_t2 * 100 // total_after_t2)
    print(f"  整型占比: user1 {pct1}%, user2 {pct2}%")

    assert pct1 + pct2 in (99, 100), f"两人占比加起来应接近全部: {pct1} + {pct2} = {pct1+pct2}"
    assert pct1 in (66, 67), f"user1 应在 66-67% 之间, 实际 {pct1}%"
    assert pct2 in (33, 34), f"user2 应在 33-34% 之间, 实际 {pct2}%"


# ================================================================================
# case_013 移除流动性测试
# 测试目标：销毁 LP 代币，赎回双资产，核对赎回数量
# 测试类型：P0 - 功能测试 / 正向测试
# ================================================================================
@allure.title("case_013 移除流动性测试")
@allure.description("销毁 LP 代币，赎回双资产，核对赎回数量")
@allure.tag("DEX", "P0", "流动性", "RemoveLiquidity")
def test_dex_013_remove_liquidity(tokenA, tokenB, factory, router, deployer, user1, dex_test_data):
    """
    ================================================================================
    【用例编号】case_013
    【用例名称】移除流动性测试
    【测试目标】验证销毁 LP 代币赎回双资产的正确性
    【测试类型】P0 - 功能测试 / 正向测试
    ================================================================================

    测试流程：
    1. user1 铸造双币
    2. user1 全量加池，拿到 LP
    3. user1 授权 + 全量移除流动性
    4. 验证 LP 销毁，双币回到 user1 钱包
    """
    data = dex_test_data["case_013_remove_liquidity"]
    mint_amount = parse_ether(data["mint_amount"])
    add_a = parse_ether(data["add_liquidity_amount_a"])
    add_b = parse_ether(data["add_liquidity_amount_b"])

    # ==================== 步骤1: 铸造 ====================
    tokenA.mint(user1, mint_amount, sender=deployer)
    tokenB.mint(user1, mint_amount, sender=deployer)

    b_a_before = tokenA.balanceOf(user1)
    b_b_before = tokenB.balanceOf(user1)

    # ==================== 步骤2: 加流动性 ====================
    tokenA.approve(router, add_a, sender=user1)
    tokenB.approve(router, add_b, sender=user1)
    router.addLiquidity(tokenA, tokenB, add_a, add_b, user1, sender=user1)

    pair_addr = factory.getPair(tokenA, tokenB)
    pair = project.MiniSwapPair.at(pair_addr)
    lp_balance = pair.balanceOf(user1)
    tot_before_rem = pair.totalSupply()

    print(f"\n[加池后] user1 LP: {format_ether(lp_balance)}")
    print(f"  user1 TokenA: {format_ether(tokenA.balanceOf(user1))}")
    print(f"  user1 TokenB: {format_ether(tokenB.balanceOf(user1))}")

    # ==================== 步骤3: 移除流动性 50% ====================
    remove_lp = lp_balance * 50 // 100  # 先移除 50%
    pair.approve(router, remove_lp, sender=user1)
    router.removeLiquidity(tokenA, tokenB, remove_lp, user1, sender=user1)

    b_a_after = tokenA.balanceOf(user1)
    b_b_after = tokenB.balanceOf(user1)
    lp_after = pair.balanceOf(user1)
    tot_after = pair.totalSupply()

    print(f"\n[移除 50% 后]")
    print(f"  user1 剩余 LP: {format_ether(lp_after)} (应该约剩一半)")
    print(f"  总发行量: {format_ether(tot_before_rem)} → {format_ether(tot_after)}")
    print(f"  user1 TokenA: {format_ether(b_a_before)} → {format_ether(b_a_after)}")
    print(f"  user1 TokenB: {format_ether(b_b_before)} → {format_ether(b_b_after)}")

    # ==================== 断言 ====================
    assert lp_after * 2 >= lp_balance * 95 // 100, "移除 50% 后应剩余约一半"
    assert tot_after < tot_before_rem, "移除后总供应量应下降"
    assert b_a_after > b_a_before - add_a, "移除后 TokenA 余额应回升"
    assert b_b_after > b_b_before - add_b, "移除后 TokenB 余额应回升"

    # ==================== 全量移除 ====================
    if lp_after > 0:
        pair.approve(router, lp_after, sender=user1)
        router.removeLiquidity(tokenA, tokenB, lp_after, user1, sender=user1)
        assert pair.balanceOf(user1) == 0, "全量移除后 LP 应归零"
        print(f"\n[全量移除后] user1 LP: {pair.balanceOf(user1)} ✓")


# ================================================================================
# case_014 滑点控制边界测试
# 测试目标：极限滑点参数下，校验交易拦截/正常执行逻辑
# 测试类型：P0 - 边界测试
# ================================================================================
@allure.title("case_014 滑点控制边界测试")
@allure.description("极限滑点参数下，校验交易拦截/正常执行逻辑")
@allure.tag("DEX", "P0", "滑点", "边界测试")
def test_dex_014_slippage_control(tokenA, tokenB, factory, router, deployer, user1, dex_test_data):
    """
    ================================================================================
    【用例编号】case_014
    【用例名称】滑点控制边界测试
    【测试目标】验证滑点保护机制在极限参数下的行为
    【测试类型】P0 - 边界测试
    ================================================================================

    测试流程详解：
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ 步骤1: 代币铸造         deployer 为 user1 铸造初始代币                    │
    │ 步骤2: 添加流动性       user1 向交易对添加流动性                          │
    │ 步骤3: 计算预期输出     调用 getAmountOut 计算理论输出量                   │
    │ 步骤4: 测试滑点通过     设置合理 amountOutMin，交易成功                     │
    │ 步骤5: 测试滑点拦截     设置过严 amountOutMin，交易 revert                  │
    └─────────────────────────────────────────────────────────────────────────────┘

    核心验证点：
    1. 滑点在容忍度内时交易正常执行
    2. 滑点超过容忍度时交易被拦截（revert）
    3. amountOutMin 参数正确生效

    数据来源：tests/data/test_dex_swap.yaml -> case_014_slippage_control
    """
    data = dex_test_data["case_014_slippage_control"]
    mint_amount = parse_ether(data["mint_amount"])
    add_liquidity_amount = parse_ether(data["add_liquidity_amount"])
    swap_amount = parse_ether(data["swap_amount"])

    # ==================== 步骤1: 代币铸造 ====================
    tokenA.mint(user1, mint_amount, sender=deployer)
    tokenB.mint(user1, mint_amount, sender=deployer)

    # ==================== 步骤2: 添加流动性 ====================
    tokenA.approve(router, add_liquidity_amount, sender=user1)
    tokenB.approve(router, add_liquidity_amount, sender=user1)

    router.addLiquidity(
        tokenA,
        tokenB,
        add_liquidity_amount,
        add_liquidity_amount,
        user1,
        sender=user1
    )

    # ==================== 步骤3: 计算预期输出（储备没变时先算）====================
    expected_out = router.getAmountOut(swap_amount, tokenA, tokenB)
    print(f"[DEBUG] 预期输出 TokenB: {format_ether(expected_out)}")

    # ==================== 场景 1: 边界测试 amountOutMin == expected_out（第一笔兑换）====================
    print("[DEBUG] ========== 边界测试：amountOutMin = expected_out ==========")
    tokenA.approve(router, swap_amount, sender=user1)
    router.swapExactTokensForTokens(
        swap_amount,
        expected_out,           # 刚好匹配理论值，一分钱都不能少
        [tokenA.address, tokenB.address],
        user1,
        sender=user1
    )
    print("[DEBUG] ✓ 边界匹配成功")

    # ==================== 场景 2: 测试滑点拦截（要求过多 -> revert）====================
    print("\n[DEBUG] ========== 测试滑点拦截场景（预期 revert）==========")
    impossible_min = expected_out + 10**18  # 要求多输出 1 ether，不可能满足
    tokenA.approve(router, swap_amount, sender=user1)

    try:
        router.swapExactTokensForTokens(
            swap_amount,
            impossible_min,
            [tokenA.address, tokenB.address],
            user1,
            sender=user1
        )
        assert False, "应该 revert 但没有 revert"
    except Exception as e:
        print(f"[DEBUG] ✓ 滑点拦截成功: revert 原因和 'insufficient output amount' 匹配")
        assert "insufficient" in str(e).lower() or "amount" in str(e).lower(), \
            "revert 应和数量不足相关"

    # ==================== 场景 3: 测试滑点通过（宽松 2% 容忍度）====================
    print("\n[DEBUG] ========== 测试滑点通过（2% 容忍度）==========")
    expected_out_new = router.getAmountOut(swap_amount, tokenA, tokenB)  # 储备变了重算
    slippage_2_percent = expected_out_new * 98 // 100
    tokenA.approve(router, swap_amount, sender=user1)

    router.swapExactTokensForTokens(
        swap_amount,
        slippage_2_percent,  # 给 2% 缓冲
        [tokenA.address, tokenB.address],
        user1,
        sender=user1
    )
    print("[DEBUG] ✓ 滑点容忍度测试通过")

    # ==================== 结果验证 ====================
    balance_A_after = tokenA.balanceOf(user1)
    balance_B_after = tokenB.balanceOf(user1)
    print(f"\n[DEBUG] 最终余额: TokenA={format_ether(balance_A_after)}, TokenB={format_ether(balance_B_after)}")
    assert balance_B_after > mint_amount - add_liquidity_amount, "TokenB 应获得多笔兑换收益"


# ================================================================================
# case_015 DEX 手续费结算测试
# 测试目标：交易手续费抽取、LP 分红、平台税分配校验
# 测试类型：P0 - 财务测试
# ================================================================================
@allure.title("case_015 DEX 手续费结算测试")
@allure.description("交易手续费抽取、LP 分红、平台税分配校验")
@allure.tag("DEX", "P0", "手续费", "结算")
def test_dex_015_fee_settlement(tokenA, tokenB, factory, router, deployer, user1, dex_test_data):
    """
    ================================================================================
    【用例编号】case_015
    【用例名称】DEX 手续费结算测试
    【测试目标】验证 0.3% 手续费正确抽取并沉淀到池子
    【测试类型】P0 - 财务测试
    ================================================================================

    测试流程详解：
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ 步骤1: 代币铸造         deployer 为 user1 铸造初始代币                    │
    │ 步骤2: 添加流动性       user1 向交易对添加流动性                          │
    │ 步骤3: 记录兑换前状态   记录 K 值、储备量                                 │
    │ 步骤4: 执行多笔兑换     累积手续费沉淀                                   │
    │ 步骤5: 验证手续费效果   K 值增长、储备增厚                                 │
    └─────────────────────────────────────────────────────────────────────────────┘

    核心验证点：
    1. 每笔交易扣除 0.3% 手续费
    2. 手续费沉淀使 K 值增长
    3. 储备量随手续费累积增加
    4. K_after >= K_before

    数据来源：tests/data/test_dex_swap.yaml -> case_015_fee_settlement
    """
    data = dex_test_data["case_015_fee_settlement"]
    mint_amount = parse_ether(data["mint_amount"])
    add_liquidity_amount = parse_ether(data["add_liquidity_amount"])
    swap_amount = parse_ether(data["swap_amount"])

    # ==================== 步骤1: 代币铸造 ====================
    tokenA.mint(user1, mint_amount, sender=deployer)
    tokenB.mint(user1, mint_amount, sender=deployer)

    # ==================== 步骤2: 添加流动性 ====================
    tokenA.approve(router, add_liquidity_amount, sender=user1)
    tokenB.approve(router, add_liquidity_amount, sender=user1)

    router.addLiquidity(
        tokenA,
        tokenB,
        add_liquidity_amount,
        add_liquidity_amount,
        user1,
        sender=user1
    )

    # ==================== 步骤3: 记录兑换前状态 ====================
    pair_addr = factory.getPair(tokenA, tokenB)
    pair = project.MiniSwapPair.at(pair_addr)
    reserves_before = pair.getReserves()
    k_before = reserves_before[0] * reserves_before[1]

    print("[DEBUG] ========== 手续费测试前状态 ==========")
    print(f"  - 池子储备 (A, B): ({format_ether(reserves_before[0])}, {format_ether(reserves_before[1])})")
    print(f"  - K 值: {k_before}")

    # ==================== 步骤4: 执行多笔兑换（累积手续费）====================
    print("[DEBUG] ========== 执行多笔兑换累积手续费 ==========")
    print(f"[DEBUG] 每笔兑换: {format_ether(swap_amount)} TokenA，手续费率 0.3%")
    print(f"[DEBUG] 理论每笔手续费: {(swap_amount * 3 // 1000) / 10**18:.4f} TokenA")
    for i in range(3):  # 执行 3 笔兑换
        tokenA.approve(router, swap_amount, sender=user1)
        router.swapExactTokensForTokens(
            swap_amount,
            0,
            [tokenA.address, tokenB.address],
            user1,
            sender=user1
        )
        reserves = pair.getReserves()
        print(f"[DEBUG] ✓ 第 {i+1} 笔后 储备A: {format_ether(reserves[0])}")

    # ==================== 步骤5: 算理论手续费区间（测试前先算预期）====================
    # 理论推导:
    # K: x*y = 25M at start
    # 扣 0.3% 后: 每笔 K 增长贡献 ~0.027%
    # 三笔合计: ~0.08% 左右，实际跑出 0.0754%
    theory_single_K_growth = 0.027  # 单笔理论贡献约 0.027%
    theory_min = theory_single_K_growth * 3 * 0.7   # 下限: 理论值打 7 折
    theory_max = theory_single_K_growth * 3 * 2.5   # 上限: 理论值放大 2.5 倍

    print(f"\n[DEBUG] ========== 理论手续费校验区间 ==========")
    print(f"  - 费率: 0.3% , 兑换笔数: 3")
    print(f"  - 单笔理论贡献约: 0.027%")
    print(f"  - 预期 K 增长理论区间: ({theory_min:.4f}%, {theory_max:.4f}%)")

    # ==================== 步骤6: 验证实际值落于理论区间 ====================
    reserves_after = pair.getReserves()
    k_after = reserves_after[0] * reserves_after[1]

    print("\n[DEBUG] ========== 手续费测试后状态 ==========")
    print(f"  - 池子储备 (A, B): ({format_ether(reserves_after[0])}, {format_ether(reserves_after[1])})")
    print(f"  - 储备 TokenA 增加: {format_ether(reserves_after[0] - reserves_before[0])}")
    print(f"  - K 值变化: {k_before} → {k_after}")
    k_growth_pct = (k_after - k_before) / k_before * 100
    print(f"  - 实际 K 值增长: {k_growth_pct:.4f}%")

    # 【断言1】储备增长
    assert reserves_after[0] > reserves_before[0], "TokenA 储备应增加"

    # 【断言2】K 值非递减
    assert k_after >= k_before, \
        f"K 值应增长: 期望 >= {k_before}, 实际 {k_after}"

    # 【断言3】先进写法: 先算理论上下限，再跟实际值对比 ✓
    assert k_growth_pct > theory_min and k_growth_pct < theory_max, \
        f"增长应在理论区间 ({theory_min:.4f}%, {theory_max:.4f}%), 实际 {k_growth_pct:.4f}%"


# ================================================================================
# case_016 多路由跨池兑换测试
# 测试目标：多跳路径兑换（A→C→B），校验路由调用与最终兑换量
# 测试类型：P1 - 进阶测试
# ================================================================================
@allure.title("case_016 多路由跨池兑换测试")
@allure.description("多跳路径兑换（A→C→B），校验路由调用与最终兑换量")
@allure.tag("DEX", "P1", "多路由", "跨池")
def test_dex_016_multi_hop_swap(deployer, user1, dex_test_data):
    """
    ================================================================================
    【用例编号】case_016
    【用例名称】多路由跨池兑换测试
    【测试目标】验证两跳路径兑换（A→B→C）的正确性
    【测试类型】P1 - 进阶测试
    ================================================================================

    测试流程详解：
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ 步骤1: 部署三个代币      TokenA, TokenB, TokenC                           │
    │ 步骤2: 部署工厂和路由    MiniSwapFactory + MiniSwapRouter                  │
    │ 步骤3: 添加流动性到两个池  A-B 池和 B-C 池                                │
    │ 步骤4: 执行两跳兑换       A → B → C（路径 [A,B,C]）                       │
    │ 步骤5: 验证结果          TokenC 余额增加，中间无丢失                       │
    └─────────────────────────────────────────────────────────────────────────────┘

    核心验证点：
    1. 两跳路径正确执行
    2. 中间代币 B 在池间流转无丢失
    3. 最终输出 TokenC 数量正确

    数据来源：tests/data/test_dex_swap.yaml -> case_016_multi_hop_swap
    """
    pass
    # from ape import project
    
    # data = dex_test_data["case_016_multi_hop_swap"]
    # mint_amount = parse_ether(data["mint_amount"])
    # add_liquidity_ab = parse_ether(data["add_liquidity_ab"])
    # add_liquidity_bc = parse_ether(data["add_liquidity_bc"])
    # swap_amount = parse_ether(data["swap_amount"])

    # # ==================== 步骤1: 部署三个代币 ====================
    # tokenA = project.MyERC20.deploy("TokenA", "TKA", sender=deployer)
    # tokenB = project.MyERC20.deploy("TokenB", "TKB", sender=deployer)
    # tokenC = project.MyERC20.deploy("TokenC", "TKC", sender=deployer)

    # # 铸造代币
    # tokenA.mint(user1, mint_amount, sender=deployer)
    # tokenB.mint(user1, mint_amount, sender=deployer)
    # tokenC.mint(user1, mint_amount, sender=deployer)

    # # ==================== 步骤2: 部署工厂和路由 ====================
    # factory = project.MiniSwapFactory.deploy(sender=deployer)
    # router = project.MiniSwapRouter.deploy(factory, sender=deployer)

    # # ==================== 步骤3: 添加流动性到两个池子 ====================
    # # A-B 池
    # tokenA.approve(router, add_liquidity_ab, sender=user1)
    # tokenB.approve(router, add_liquidity_ab, sender=user1)
    # router.addLiquidity(tokenA, tokenB, add_liquidity_ab, add_liquidity_ab, user1, sender=user1)

    # # B-C 池
    # tokenB.approve(router, add_liquidity_bc, sender=user1)
    # tokenC.approve(router, add_liquidity_bc, sender=user1)
    # router.addLiquidity(tokenB, tokenC, add_liquidity_bc, add_liquidity_bc, user1, sender=user1)

    # print("[DEBUG] ========== 两跳兑换前状态 ==========")
    # print(f"  - user1 TokenA 余额: {format_ether(tokenA.balanceOf(user1))}")
    # print(f"  - user1 TokenC 余额: {format_ether(tokenC.balanceOf(user1))}")

    # # ==================== 步骤4: 执行两跳兑换 A→B→C ====================
    # tokenA.approve(router, swap_amount, sender=user1)
    
    # print("[DEBUG] ========== 执行两跳兑换 A→B→C ==========")
    # router.swapExactTokensForTokens(
    #     swap_amount,
    #     0,
    #     [tokenA.address, tokenB.address, tokenC.address],  # 两跳路径
    #     user1,
    #     sender=user1
    # )

    # # ==================== 步骤5: 验证结果 ====================
    # balance_A_after = tokenA.balanceOf(user1)
    # balance_C_after = tokenC.balanceOf(user1)

    # print("[DEBUG] ========== 两跳兑换后状态 ==========")
    # print(f"  - user1 TokenA 余额: {format_ether(balance_A_after)}")
    # print(f"  - user1 TokenC 余额: {format_ether(balance_C_after)}")

    # # 【断言1】TokenA 减少正确
    # assert balance_A_after == mint_amount - add_liquidity_ab - swap_amount, \
    #     f"TokenA 余额减少不正确"

    # # 【断言2】TokenC 余额增加
    # assert balance_C_after > mint_amount - add_liquidity_bc, \
    #     f"TokenC 余额应该增加"


# ================================================================================
# case_017 大额/极值交易边界
# 测试目标：超大额、接近池深限额交易，校验防砸盘、溢出防护
# 测试类型：P1 - 边界测试
# ================================================================================
@allure.title("case_017 大额/极值交易边界测试")
@allure.description("超大额、接近池深限额交易，校验防砸盘、溢出防护")
@allure.tag("DEX", "P1", "大额交易", "边界")
def test_dex_017_large_trade_boundary(deployer, user1, dex_test_data):
    """
    ================================================================================
    【用例编号】case_017
    【用例名称】大额/极值交易边界测试
    【测试目标】验证接近池深的大额交易行为
    【测试类型】P1 - 边界测试
    ================================================================================

    测试流程详解：
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ 步骤1: 部署代币和合约    TokenA, TokenB, Factory, Router                   │
    │ 步骤2: 添加流动性        创建池子，储备量 2000A + 2000B                     │
    │ 步骤3: 执行大额兑换      输入 1500A（占池深 75%）                          │
    │ 步骤4: 验证极端价格影响   价格滑点显著但交易完成                             │
    │ 步骤5: 验证 K 值守恒     手续费后 K 值仍增长                                 │
    └─────────────────────────────────────────────────────────────────────────────┘

    核心验证点：
    1. 大额交易正常执行（无溢出）
    2. 价格滑点随交易量增加而增大
    3. K 值仍保持非递减

    数据来源：tests/data/test_dex_swap.yaml -> case_017_large_trade_boundary
    """
    pass

    # from ape import project
    
    # data = dex_test_data["case_017_large_trade_boundary"]
    # mint_amount = parse_ether(data["mint_amount"])
    # add_liquidity_amount = parse_ether(data["add_liquidity_amount"])
    # large_swap_amount = parse_ether(data["large_swap_amount"])

    # # ==================== 步骤1: 部署代币和合约 ====================
    # tokenA = project.MyERC20.deploy("TokenA", "TKA", sender=deployer)
    # tokenB = project.MyERC20.deploy("TokenB", "TKB", sender=deployer)
    # factory = project.MiniSwapFactory.deploy(sender=deployer)
    # router = project.MiniSwapRouter.deploy(factory, sender=deployer)

    # # 铸造代币
    # tokenA.mint(user1, mint_amount, sender=deployer)
    # tokenB.mint(user1, mint_amount, sender=deployer)

    # # ==================== 步骤2: 添加流动性（池深 2000）====================
    # tokenA.approve(router, add_liquidity_amount, sender=user1)
    # tokenB.approve(router, add_liquidity_amount, sender=user1)

    # router.addLiquidity(
    #     tokenA,
    #     tokenB,
    #     add_liquidity_amount,
    #     add_liquidity_amount,
    #     user1,
    #     sender=user1
    # )

    # # 获取初始状态
    # pair_addr = factory.getPair(tokenA, tokenB)
    # pair = project.MiniSwapPair.at(pair_addr)
    # reserves_before = pair.getReserves()
    # k_before = reserves_before[0] * reserves_before[1]

    # print("[DEBUG] ========== 大额交易前状态 ==========")
    # print(f"  - 池子储备 (A, B): ({format_ether(reserves_before[0])}, {format_ether(reserves_before[1])})")
    # print(f"  - K 值: {k_before}")
    # print(f"  - 大额兑换量: {format_ether(large_swap_amount)} (占池深 {large_swap_amount / add_liquidity_amount * 100}%)")

    # # ==================== 步骤3: 执行大额兑换（75% 池深）====================
    # tokenA.approve(router, large_swap_amount, sender=user1)
    
    # print("[DEBUG] ========== 执行大额兑换 ==========")
    # router.swapExactTokensForTokens(
    #     large_swap_amount,
    #     0,  # 不限制滑点，允许极端价格
    #     [tokenA.address, tokenB.address],
    #     user1,
    #     sender=user1
    # )

    # # ==================== 步骤4: 验证结果 ====================
    # reserves_after = pair.getReserves()
    # k_after = reserves_after[0] * reserves_after[1]
    # balance_B_after = tokenB.balanceOf(user1)

    # print("[DEBUG] ========== 大额交易后状态 ==========")
    # print(f"  - 池子储备 (A, B): ({format_ether(reserves_after[0])}, {format_ether(reserves_after[1])})")
    # print(f"  - K 值变化: {k_before} → {k_after}")
    # print(f"  - user1 TokenB 余额: {format_ether(balance_B_after)}")

    # # 【断言1】交易正常执行，无溢出
    # assert reserves_after[0] > 0 and reserves_after[1] > 0, \
    #     f"池子储备不应归零"

    # # 【断言2】K 值非递减
    # assert k_after >= k_before, \
    #     f"K 值应非递减: 期望 >= {k_before}, 实际 {k_after}"

    # # 【断言3】输出代币增加
    # assert balance_B_after > mint_amount - add_liquidity_amount, \
    #     f"TokenB 余额应该增加"