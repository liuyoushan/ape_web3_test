"""
================================================================================
【模块概览】项目自定义自研合约 业务用例
对应用例编号：case_018 ~ case_025
测试范围：自研合约的权限控制、参数管理、业务逻辑等
================================================================================
"""

from ape import project


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
    from tests.helpers.formatters import parse_ether

    data = contract_custom_test_data["case_020_custom_business_logic"]
    swap_amount_ether = data["amount_in_ether"]
    swap_amount = parse_ether(str(swap_amount_ether))

    print("\n[DEBUG] ========== 配置（从yaml读取） ==========")
    print(f"  - 兑换输入: {swap_amount_ether} ether")
    print(f"  - 业务公式: 0.3%手续费 = input × 997 / 1000")

    factory = project.MiniSwapFactory.deploy(sender=deployer)
    router = project.MiniSwapRouter.deploy(factory, sender=deployer)
    tokenA = project.MyERC20.deploy("TokenA", "TKA", sender=deployer)
    tokenB = project.MyERC20.deploy("TokenB", "TKB", sender=deployer)
    add_amt = parse_ether("5000")

    tokenA.mint(deployer, add_amt * 2, sender=deployer)
    tokenB.mint(deployer, add_amt * 2, sender=deployer)
    tokenA.approve(router, add_amt * 2, sender=deployer)
    tokenB.approve(router, add_amt * 2, sender=deployer)
    router.addLiquidity(tokenA, tokenB, add_amt, add_amt, deployer, sender=deployer)

    (reserve0, reserve1) = project.MiniSwapPair.at(factory.getPair(tokenA, tokenB)).getReserves()
    (reserveIn, reserveOut) = (reserve0, reserve1) if tokenA.address < tokenB.address else (reserve1, reserve0)
    print(f"  - 池内储备: {reserveIn/1e18} / {reserveOut/1e18}")

    # ==================== 阶段：getAmountOut 公式逻辑验证 ====================
    print("\n[DEBUG] ========== 阶段: getAmountOut 计算验证 ==========")

    amount_out_chain = router.getAmountOut(swap_amount, tokenA.address, tokenB.address)
    print(f"  - 链上 Router.getAmountOut: {amount_out_chain / 1e18:.6f} TokenB")

    amountInWithFee = swap_amount * 997
    numerator = amountInWithFee * reserveOut
    denominator = reserveIn * 1000 + amountInWithFee
    expected_local = numerator // denominator

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
def test_custom_021_pause_unpause(deployer, user1):
    """
    合约暂停/恢复功能测试

    验证暂停机制：
    - pause 后核心业务无法调用
    - unpause 后业务恢复正常
    - 状态切换事件正确触发
    """
    raise NotImplementedError("用例待实现")


# ================================================================================
# case_022 黑白名单控制接口
# 测试目标：名单内地址特权、名单外地址功能限制 / 拦截校验
# 测试类型：P0 - 权限测试
# ================================================================================
def test_custom_022_blacklist_whitelist(deployer, user1):
    """
    黑白名单控制接口测试

    验证名单控制机制：
    - 白名单地址享受特权
    - 黑名单地址被限制
    - 名单更新权限正确
    """
    raise NotImplementedError("用例待实现")


# ================================================================================
# case_023 动态参数修改接口
# 测试目标：后台调整手续费、奖励比例、质押系数等参数生效校验
# 测试类型：P0 - 配置测试
# ================================================================================
def test_custom_023_dynamic_parameter_update(deployer):
    """
    动态参数修改接口测试

    验证参数动态调整：
    - 手续费率可调整
    - 奖励比例可修改
    - 修改后立即生效
    """
    raise NotImplementedError("用例待实现")


# ================================================================================
# case_024 外部合约依赖调用
# 测试目标：预言机、外部池、跨合约读取数据的返回值容错校验
# 测试类型：P1 - 集成测试
# ================================================================================
def test_custom_024_external_contract_call(deployer):
    """
    外部合约依赖调用测试

    验证外部依赖处理：
    - 预言机数据读取
    - 外部池数据查询
    - 异常情况容错处理
    """
    raise NotImplementedError("用例待实现")


# ================================================================================
# case_025 自定义业务异常拦截
# 测试目标：非法参数、不符合业务规则操作，校验定制化 revert 提示
# 测试类型：P0 - 异常测试
# ================================================================================
def test_custom_025_custom_error_revert(deployer, user1):
    """
    自定义业务异常拦截测试

    验证业务规则校验：
    - 非法参数触发 revert
    - 错误消息清晰可辨
    - 边界条件正确处理
    """
    raise NotImplementedError("用例待实现")
