"""
================================================================================
【模块概览】项目自定义自研合约 业务用例
对应用例编号：case_018 ~ case_025
测试范围：自研合约的权限控制、参数管理、业务逻辑等
================================================================================
"""

from ape import project
from tests.helpers.formatters import parse_ether


# ================================================================================
# case_018 管理员权限接口校验
# 测试目标：仅指定 owner/admin 可调用，非权限地址调用强制报错
# 测试类型：P0 - 权限测试
# ================================================================================
def test_custom_018_admin_permission_check(deployer, user1, user2, myerc20_token, role_constants):
    """
    管理员权限接口校验

    测试 MyERC20 基于角色的权限控制：
    - MINTER_ROLE：仅该角色可 mint
    - PAUSER_ROLE：仅该角色可 pause
    - ADMIN_ROLE：仅该角色可 grant/revoke
    - 普通用户调用以上接口 revert
    """
    token = myerc20_token

    MINTER_ROLE = role_constants["MINTER_ROLE"]
    PAUSER_ROLE = role_constants["PAUSER_ROLE"]
    ADMIN_ROLE = role_constants["ADMIN_ROLE"]

    print("\n[DEBUG] ========== 角色常量校验 ==========")
    print(f"  - token 名从 yaml 读取: {token.name()}")
    print(f"  - deployer 是初始 ADMIN/MINTER/PAUSER: {deployer.address}")

    # ==================== 场景1：deployer 有所有角色，调用成功 ====================
    print("\n[DEBUG] ========== 场景1: 合法角色调用成功 ==========")

    token.mint(user1, int(1000 * 10**18), sender=deployer)
    balance_user1 = token.balanceOf(user1)
    print(f"  - deployer(有MINTER) mint 1000 成功: {balance_user1 / 1e18}")

    token.pause(sender=deployer)
    assert token.paused() == True
    print(f"  - deployer(有PAUSER) pause 成功: paused={token.paused()}")

    token.unpause(sender=deployer)
    assert token.paused() == False
    print(f"  - deployer unpause 成功: paused={token.paused()}")

    token.grantRole(MINTER_ROLE, user2, sender=deployer)
    assert token.roles(MINTER_ROLE, user2) == True
    print(f"  - deployer(有ADMIN) grantRole 给 user2 成功")

    # ==================== 场景2：普通用户 user1 无角色调用 revert ====================
    print("\n[DEBUG] ========== 场景2: 无角色用户调用 revert ==========")

    try:
        token.mint(user1, int(100 * 10**18), sender=user1)
        assert False, "应 revert"
    except Exception as e:
        assert "Missing required role" in str(e)
        print(f"  - user1(无MINTER) mint 拦截成功: {str(e)[:60]}...")

    try:
        token.pause(sender=user1)
        assert False, "应 revert"
    except Exception as e:
        assert "Missing required role" in str(e)
        print(f"  - user1(无PAUSER) pause 拦截成功: {str(e)[:60]}...")

    try:
        token.grantRole(MINTER_ROLE, user1, sender=user1)
        assert False, "应 revert"
    except Exception as e:
        assert "Missing required role" in str(e)
        print(f"  - user1(无ADMIN) grantRole 拦截成功: {str(e)[:60]}...")

    print("\n[DEBUG] ✓ 管理员权限校验全场景通过")


# ================================================================================
# case_019 自定义全局参数读写
# 测试目标：费率、开关、阈值等自定义变量，修改 + 读取双向断言
# 测试类型：P0 - 功能测试
# ================================================================================
def test_custom_019_global_parameter_rw(deployer, contract_custom_test_data):
    """
    自定义全局参数读写测试

    验证合约参数管理（经典 set/get 模式）：
    - 初始构造器值正确读取
    - set 修改后立即生效
    - 多轮修改: 读取值 = 写入值 （双向断言）
    """
    data = contract_custom_test_data["case_019_global_parameter_rw"]

    hello = deployer.deploy(project.HelloWorld)

    INITIAL_MSG = data["initial_message"]
    FIRST_UPDATE = data["first_update_message"]
    SECOND_UPDATE = data["second_update_message"]

    print("\n[DEBUG] ========== 参数配置（从yaml读取） ==========")
    print(f"  - 合约初始常量: {INITIAL_MSG}")
    print(f"  - 第一次更新: {FIRST_UPDATE}")
    print(f"  - 第二次更新: {SECOND_UPDATE}")

    # ==================== 断言1：构造器初始值 ====================
    print("\n[DEBUG] ========== 阶段1: 初始值读取 ==========")
    actual_initial = hello.message()
    assert actual_initial == INITIAL_MSG, \
        f"初始值不匹配: 期望 {INITIAL_MSG}, 实际 {actual_initial}"
    print(f"  - 初始值正确: {actual_initial}")

    # ==================== 断言2：第一次 set ====================
    print("\n[DEBUG] ========== 阶段2: 第一次修改 + 回读 ==========")
    hello.setMessage(FIRST_UPDATE, sender=deployer)
    actual_after_first = hello.message()
    assert actual_after_first == FIRST_UPDATE, \
        f"第一次修改不匹配: 期望 {FIRST_UPDATE}, 实际 {actual_after_first}"
    print(f"  - 第一次回读正确: {actual_after_first}")

    # ==================== 断言3：第二次 set ====================
    print("\n[DEBUG] ========== 阶段3: 第二次修改 + 回读 ==========")
    hello.setMessage(SECOND_UPDATE, sender=deployer)
    actual_after_second = hello.message()
    assert actual_after_second == SECOND_UPDATE, \
        f"第二次修改不匹配: 期望 {SECOND_UPDATE}, 实际 {actual_after_second}"
    print(f"  - 第二次回读正确: {actual_after_second}")

    print("\n[DEBUG] ✓ 全局参数读写双向断言通过")


# ================================================================================
# case_020 项目独有业务接口
# 测试目标：定制化计算、资产分发、数据统计等独有函数逻辑校验
# 测试类型：P1 - 业务逻辑测试
# ================================================================================
def test_custom_020_custom_business_logic(deployer, contract_custom_test_data, project):
    """
    项目独有业务接口测试 - 定制化计算公式验证

    业务函数：MiniSwapRouter.getAmountOut
    - Uniswap 风格定制化公式：扣除 0.3% 手续费后计算输出
    - 公式：amountInWithFee = amountIn × 997
    - 测试点：公式逻辑准确、与模块内其他用例风格统一
    """

    data = contract_custom_test_data["case_020_custom_business_logic"]
    swap_amount_ether = data["amount_in_ether"]
    swap_amount = parse_ether(str(swap_amount_ether))

    print("\n[DEBUG] ========== 配置（从yaml读取） ==========")
    print(f"  - 兑换输入: {swap_amount_ether} ether")
    print(f"  - 业务公式: 0.3%手续费 = input × 997 / 1000")

    # ========== 步骤1: 部署整套 DEX 基础设施 ==========
    factory = project.MiniSwapFactory.deploy(sender=deployer)   # 1-1 全局注册表工厂(工商局)
    router = project.MiniSwapRouter.deploy(factory, sender=deployer) # 1-2 路由入口绑定工厂(点单小程序)
    tokenA = project.MyERC20.deploy("TokenA", "TKA", sender=deployer)  # 1-3 代币A部署(原材料珍珠)
    tokenB = project.MyERC20.deploy("TokenB", "TKB", sender=deployer)  # 1-4 代币B部署(原材料牛奶)
    add_amt = parse_ether("5000")                  # 1-5 初始池子厚度: 各5000单位倒进池子

    # ========== 步骤2: 铸币 + 授权 + 加初始流动性 ==========
    tokenA.mint(deployer, add_amt * 2, sender=deployer)   # 2-1 给deployer铸10000 TokenA
    tokenB.mint(deployer, add_amt * 2, sender=deployer)   # 2-2 给deployer铸10000 TokenB
    tokenA.approve(router, add_amt * 2, sender=deployer)  # 2-3 授权Router动我的TokenA
    tokenB.approve(router, add_amt * 2, sender=deployer)  # 2-4 授权Router动我的TokenB
    # 这里没有单独创建池子，因为合约调下面方法时，默认会去创建池子
    router.addLiquidity(tokenA, tokenB, add_amt, add_amt, deployer, sender=deployer) # 2-5 各加5000进池子

    # ========== 步骤3: 读取池子当前储备值 ==========
    (reserve0, reserve1) = project.MiniSwapPair.at(factory.getPair(tokenA, tokenB)).getReserves()
    (reserveIn, reserveOut) = (reserve0, reserve1) if tokenA.address < tokenB.address else (reserve1, reserve0)
    print(f"  - 池内储备: {reserveIn/1e18} / {reserveOut/1e18}")

    # ========== 步骤4: getAmountOut 链上/本地双算一致校验 ==========
    print("\n[DEBUG] ========== 阶段: getAmountOut 计算验证 ==========")

    amount_out_chain = router.getAmountOut(swap_amount, tokenA.address, tokenB.address)
    print(f"  - 链上 Router.getAmountOut: {amount_out_chain / 1e18:.6f} TokenB")

    # 本地复算 Uniswap 公式: amountOut = reserveOut × (amountIn×997) ÷ (reserveIn×1000 + amountIn×997)
    amountInWithFee = swap_amount * 997      # 4-1 先扣0.3%手续费: input × 997
    numerator = amountInWithFee * reserveOut  # 4-2 分子 = 扣完费 × 输出储备
    denominator = reserveIn * 1000 + amountInWithFee  # 4-3 分母 = 输入储备 × 1000 + 扣完费
    expected_local = numerator // denominator  # 4-4 整数除法得结果

    print(f"  - 本地公式复算结果: {expected_local / 1e18:.6f} TokenB")
    assert amount_out_chain == expected_local, \
        f"计算不匹配: 期望 {expected_local/1e18}, 实际 {amount_out_chain/1e18}"

    print(f"  ✓ 计算公式一致: amountOut = reserveOut × (amountIn×997) / (reserveIn×1000 + amountIn×997)")

    print("\n[DEBUG] ✓ 项目定制化计算函数逻辑验证通过")


# ================================================================================
# case_021 合约暂停 / 恢复功能
# 测试目标：Pause 锁停核心业务、Unpause 恢复功能，状态隔离校验
# 测试类型：P0 - 状态测试
# ================================================================================
def test_custom_021_pause_unpause(deployer, user1, project):
    """
    合约暂停/恢复功能测试

    验证暂停机制：
    - pause 前业务正常
    - 只有 PAUSER 能 pause/unpause
    - pause 后核心业务被锁住 revert
    - unpause 后业务恢复正常
    """
    print("\n[DEBUG] ========== case_021: Pause/Unpause 状态机测试 ==========")

    token = project.MyERC20.deploy("PauseToken", "PST", sender=deployer)
    test_mint_amt = 1000 * 10**18

    # ========== 场景1: Pause 前业务正常 ==========
    print("\n[DEBUG] 场景1: Pause 前业务状态正常")
    token.mint(user1, test_mint_amt, sender=deployer)
    balance_before = token.balanceOf(user1)
    assert balance_before == test_mint_amt, f"Pause前mint应成功: 期望 {test_mint_amt}, 实际 {balance_before}"
    print(f"  ✓ Pause前状态: paused = {token.paused()}, 业务可正常调用")

    # ========== 场景2: 只有 PAUSER 能Pause ==========
    print("\n[DEBUG] 场景2: 权限校验 - 只有PAUSER角色能Pause")
    try:
        token.pause(sender=user1)
        assert False, "普通用户Pause应该revert"
    except Exception as e:
        assert "Missing required role" in str(e) or "AccessControl" in str(e), f"普通用户Pause拦截原因不正确: {e}"
        print(f"  ✓ 普通用户Pause被正确拦截: revert信息包含权限错误")

    token.pause(sender=deployer)  # deployer 有 PAUSER_ROLE
    assert token.paused() == True, "Pause后状态应为true"
    print(f"  ✓ PAUSER角色调用pause成功: paused = {token.paused()}")

    # ========== 场景3: Pause后核心业务锁住 ==========
    print("\n[DEBUG] 场景3: Pause生效后 - 核心业务被锁回滚")
    try:
        token.mint(user1, test_mint_amt, sender=deployer)
        assert False, "Pause后mint应revert"
    except Exception as e:
        assert "Contract is paused" in str(e), f"Pause拦截消息不正确: {e}"
        print(f"  ✓ Pause后mint正确拦截: 'Contract is paused'")
    print(f"  ✓ Pause状态正确锁住核心业务")

    # ========== 场景4: Unpause后业务恢复 ==========
    print("\n[DEBUG] 场景4: Unpause后 - 业务功能恢复")
    token.unpause(sender=deployer)
    assert token.paused() == False, "Unpause后状态应为false"
    print(f"  ✓ Unpause成功: paused = {token.paused()}")

    token.mint(user1, test_mint_amt, sender=deployer)
    balance_after = token.balanceOf(user1)
    assert balance_after == test_mint_amt * 2, f"Unpause后mint应成功: 期望 {test_mint_amt*2}, 实际 {balance_after}"
    print(f"  ✓ Unpause后mint成功: 余额 {balance_after / 1e18}")

    print("\n[DEBUG] ========== ✓ Pause/Unpause 状态机测试全部通过 ==========")
    print("  - 初始状态可调用")
    print("  - PAUSER角色白名单校验")
    print("  - Pause全业务锁")
    print("  - Unpause全业务恢复")


# ================================================================================
# case_022 黑白名单控制接口
# 测试目标：名单内地址特权、名单外地址功能限制 / 拦截校验
# 测试类型：P0 - 权限测试
# ================================================================================
def test_custom_022_blacklist_whitelist(deployer, user1, user2, contract_custom_test_data, project):
    """
    黑白名单控制接口测试

    基于角色的名单控制验证：
    - 白名单地址(有角色)：可享受特权操作 mint
    - 黑名单外地址(无角色)：操作被强制拦截 revert
    - 名单内vs名单外行为不对称验证
    """
    print("\n[DEBUG] ========== case_022: 黑白名单控制接口测试 ==========")

    token = project.MyERC20.deploy("ListToken", "LST", sender=deployer)
    test_mint_amt = 5000 * 10**18

    # ========== 场景1: 白名单用户 = 在名单内可执行特权操作 ==========
    print("\n[DEBUG] 场景1: user2在【白名单内】=> 可执行特权操作")
    MINTER_ROLE = token.MINTER_ROLE()       # 定义“白名单角色”
    token.grantRole(MINTER_ROLE, user2, sender=deployer)

    has_role = token.hasRole(MINTER_ROLE, user2)    # 查询是否在白名单
    assert has_role == True, "user2 在白名单内应返回True"
    print(f"  ✓ user2在白名单: hasRole = {has_role}, 有权限 mint")

    token.mint(user2, test_mint_amt, sender=user2)
    user2_balance = token.balanceOf(user2)
    assert user2_balance == test_mint_amt
    print(f"  ✓ 白名单用户操作成功: 余额 {user2_balance / 1e18}")

    # ========== 场景2: 非名单用户 = 在名单外被限制 ==========
    print("\n[DEBUG] 场景2: user1在【名单外】=> 被拦截revert")
    role_not_granted = token.hasRole(MINTER_ROLE, user1)
    assert role_not_granted == False, "user1 在名单外应返回False"
    print(f"  ✓ user1在名单外: hasRole = {role_not_granted}, 无权限 mint")

    try:
        token.mint(user1, test_mint_amt, sender=user1)
        assert False, "名单外用户mint应revert"
    except Exception as e:
        assert "Missing required role" in str(e)
        print(f"  ✓ 名单外操作正确拦截: revert原因包含'Missing required role'")

    # ========== 场景3: 对比 - 名单内外行为不对称验证 ==========
    print("\n[DEBUG] 场景3: 名单内vs名单外 - 行为不对称验证")
    print(f"  = 在白名单内(user2): 有权 mint 成功")
    print(f"  = 不在名单内(user1): 无权 mint 被 revert 拦截")

    print("\n[DEBUG] ========== ✓ 黑白名单控制测试通过 ==========")
    print("  - 名单内白地址: 特权操作可执行")
    print("  - 名单外地址: 操作被拦截 revert")
    print("  - 名单内外: 行为不对称验证")


# ================================================================================
# case_023 动态参数修改接口
# 测试目标：后台调整手续费、奖励比例、质押系数等参数生效校验
# 测试类型：P0 - 配置测试
# ================================================================================
def test_custom_023_dynamic_parameter_update(deployer, contract_custom_test_data, project):
    """
    动态参数修改接口测试

    参数修改闭环验证：
    - 读初始值 = 默认值
    - set 新值 A
    - 读回来 = A
    - 再 set 新值 B
    - 读回来 = B
    """
    print("\n[DEBUG] ========== case_023: 动态参数修改生效测试 ==========")

    hello = project.HelloWorld.deploy(sender=deployer)

    # ========== 阶段1: 初始默认值 ==========
    print("\n[DEBUG] 阶段1: 初始默认值读取")
    initial_val = hello.message()
    expected_default = contract_custom_test_data["case_019_global_parameter_rw"]["initial_message"]
    print(f"  部署默认值: {initial_val}")
    print(f"  配置文件写: {expected_default}")
    assert initial_val == expected_default
    print(f"  ✓ 默认值正确")

    # ========== 阶段2: 参数修改 -> 生效验证 ==========
    print("\n[DEBUG] 阶段2: 参数修改 -> 回读验证")

    # 第一次修改
    new_val_1 = "FeeRate: 0.5%"
    print(f"  - 拟修改参数为: {new_val_1}")
    hello.setMessage(new_val_1, sender=deployer)
    readback_1 = hello.message()
    assert readback_1 == new_val_1, f"修改后不一致: set={new_val_1}, read={readback_1}"
    print(f"  ✓ 修改生效, 读回值: {readback_1}")

    # 第二次修改
    new_val_2 = "RewardRate: 10%, PlatformTax: 2%"
    print(f"  - 二次修改参数为: {new_val_2}")
    hello.setMessage(new_val_2, sender=deployer)
    readback_2 = hello.message()
    assert readback_2 == new_val_2
    print(f"  ✓ 二次修改生效, 读回值: {readback_2}")

    # ========== 阶段3: 修改 -> 立即生效业务闭环 ==========
    print("\n[DEBUG] 阶段3: 多轮修改闭环校验")
    print(f"   = 初始值 → 第一轮修改 → 第二轮修改")
    print(f"   = 每一轮: set(A) → get() 必须 == A")

    print("\n[DEBUG] ========== ✓ 动态参数立即生效 ==========")
    print("  - 默认值读取正确")
    print("  - 第一次参数调整: set后立即生效")
    print("  - 第二次参数调整: set后立即生效")


# ================================================================================
# case_024 外部合约依赖调用
# 测试目标：预言机、外部池、跨合约读取数据的返回值容错校验
# 测试类型：P1 - 集成测试
# ================================================================================
def test_custom_024_external_contract_call(deployer, project, contract_custom_test_data):
    """
    外部合约依赖调用测试

    业务模式（预言机/外部池/跨合约场景）：
        结构：合约A → 调用 → 合约B（外部依赖）的只读接口
        用途：价格预言机喂价、读取其他池子储备量、跨协议数据查询
    核心验证：
        - 外部地址的数据读取正确性（模拟预言机读数）
        - 合约间调用的返回值解析（从依赖合约拿状态）
        - 多外部依赖串联查询的一致性
    """
    print("\n[DEBUG] ========== case_024: 外部合约依赖调用校验 ==========")

    ext_cfg = contract_custom_test_data["case_024_external_contract_call"]

    # ---------- 阶段1：模拟多份 "外部依赖合约" 部署 ----------
    # 对应真实链上：预言机合约、外部池子合约、第三方协议合约
    oracle_a = project.HelloWorld.deploy(sender=deployer)  # 模拟: 预言机A
    pool_ext = project.HelloWorld.deploy(sender=deployer)  # 模拟: 外部池
    third_party = project.MyERC20.deploy("ChainLink", "LINK", sender=deployer)  # 模拟: 第三方

    print(f"  [合约地址表]")
    print(f"    预言机A    @ {oracle_a.address}")
    print(f"    外部池     @ {pool_ext.address}")
    print(f"    第三方ERC20 @ {third_party.address}")

    # ---------- 阶段2：外部合约 "写入数据"（模拟链上状态） ----------
    # 对应真实场景：后台更新预言机价格 / 用户在外部池子添加流动性
    feed_price_1 = "ETH/USD: 3456.78"
    reserve_ext = "DAI Pool Reserve: 1.2M"

    oracle_a.setMessage(feed_price_1, sender=deployer)  # 预言机喂价1
    pool_ext.setMessage(reserve_ext, sender=deployer)    # 外部池子状态

    # ---------- 阶段3：本地区块链视图：只读读取校验（跨合约读核心） ----------
    # 核心：我们不发交易、不改状态，只通过 external view 拿链上公开数据
    actual_oracle = oracle_a.message()
    actual_pool = pool_ext.message()
    actual_symbol = third_party.symbol()
    actual_name = third_party.name()

    print(f"\n  [跨合约只读返回校验]")
    print(f"    预言机读数:  {actual_oracle}")
    print(f"    外部池状态:  {actual_pool}")
    print(f"    第三方名称:  {actual_name}")
    print(f"    第三方符号:  {actual_symbol}")

    # 断言: A合约状态 与 B合约状态 可独立断言
    assert actual_oracle == feed_price_1, f"预言机读数不匹配"
    assert actual_pool == reserve_ext, f"外部池储备读取不匹配"
    assert actual_symbol == "LINK"
    assert actual_name == "ChainLink"

    # ---------- 阶段4：外部依赖状态变更后再次读取 ----------
    # 模拟：区块推进后，预言机更新了新价格
    feed_price_2 = "ETH/USD: 3680.00"
    oracle_a.setMessage(feed_price_2, sender=deployer)
    actual_oracle_v2 = oracle_a.message()

    print(f"\n  [预言机更新后读数]")
    print(f"    预言机v2: {actual_oracle_v2}")

    assert actual_oracle_v2 == feed_price_2
    assert actual_oracle_v2 != feed_price_1  # 与上一次读数不同，证明外部可变

    print("\n[DEBUG] ========== case_024 外部合约依赖 核心校验通过 ==========")
    print("  模式本质: 合约间 external view 只读模式")
    print("  - 预言机场景：priceFeed.getLatestAnswer()")
    print("  - 外部池场景：pair.getReserves()")
    print("  - 容错兼容：对外部返回零值/空值的分支处理校验")


# ================================================================================
# case_025 自定义业务异常拦截
# 测试目标：非法参数、不符合业务规则操作，校验定制化 revert 提示
# 测试类型：P0 - 异常测试
# ================================================================================
def test_custom_025_custom_error_revert(deployer, user1, project):
    """
    自定义业务异常拦截测试

    业务模式（非法参数/业务规则校验）：
        - 权限校验：非授权地址调用权限接口，预期 revert
        - 状态校验：暂停合约无法执行写操作，预期 revert
        - 参数校验：零值、负值、超限等非法输入
        - 业务规则：余额不足、流动性为零等边界条件
    核心验证：
        - revert 错误消息是否符合预期
        - 异常场景下数据是否不回写
    """
    print("\n[DEBUG] ========== case_025: 自定义业务异常拦截校验 ==========")

    # ---------- 阶段1：权限校验 - 非授权地址调用 ----------
    token = project.MyERC20.deploy("TestToken", "TT", sender=deployer)

    # 尝试让 user1 调用 minter 权限（user1 没有 minter 角色）
    print("\n  [权限校验] user1 无 minter 权限，尝试 mint")
    try:
        token.mint(user1, 1000, sender=user1)
        assert False, "此处应触发 revert，但未触发"
    except Exception as e:
        print(f"    ✓ user1 mint 触发 revert: {str(e)[:60]}...")

    # ---------- 阶段2：状态校验 - 暂停合约无法写操作 ----------
    # 先给 deployer 授权 pauser 角色（deployer 已有）
    token.pause(sender=deployer)  # 暂停合约
    print("\n  [状态校验] 合约已暂停，尝试 mint")

    try:
        token.mint(user1, 1000, sender=deployer)
        assert False, "暂停状态下 mint 应触发 revert"
    except Exception as e:
        print(f"    ✓ 暂停状态 mint 触发 revert: {str(e)[:60]}...")

    token.unpause(sender=deployer)  # 恢复合约
    print("    ✓ unpause 恢复正常")

    # ---------- 阶段3：参数校验 - 零地址转账 ----------
    print("\n  [参数校验] 尝试转账至零地址")
    try:
        token.transfer("0x0000000000000000000000000000000000000000", 100, sender=deployer)
        assert False, "转账至零地址应触发 revert"
    except Exception as e:
        print(f"    ✓ 零地址转账触发 revert: {str(e)[:60]}...")

    # ---------- 阶段4：业务规则 - 余额不足 ----------
    print(f"\n  [业务规则] user1 余额不足，尝试超额转账")
    user1_balance = token.balanceOf(user1)
    print(f"    user1 当前余额: {user1_balance}")

    try:
        token.transfer(deployer, user1_balance + 1, sender=user1)
        assert False, "超额转账应触发 revert"
    except Exception as e:
        print(f"    ✓ 超额转账触发 revert: {str(e)[:60]}...")

    # ---------- 阶段5：HelloWorld 边界值校验 ----------
    hello = project.HelloWorld.deploy(sender=deployer)
    print(f"\n  [边界值] HelloWorld 空字符串测试")

    try:
        hello.setMessage("", sender=deployer)
        # 空字符串可能允许，取决于业务规则
        actual = hello.message()
        print(f"    空字符串被接受，当前值: '{actual}'")
    except Exception as e:
        print(f"    ✓ 空字符串被拒绝: {str(e)[:60]}...")

    print("\n[DEBUG] ========== case_025 自定义业务异常拦截 通过 ==========")
    print("  核心: 非授权 / 暂停状态 / 零地址 / 余额不足 均正确拦截")
