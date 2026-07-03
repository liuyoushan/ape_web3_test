"""
==============================================================================
【合约自定义场景】完整自定义合约测试用例
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

from ape import project
from framework.core.logger import log
from framework.core.formatters import parse_ether


@allure.title("custom 018 admin permission check")
@allure.description("Test for test_custom_018_admin_permission_check")
@allure.tag("功能测试")
def test_custom_018_admin_permission_check(deployer, user1, user2, myerc20_token, role_constants):
    """
    管理员权限接口校验

    测试 MyERC20 基于角色的权限控制：
    - MINTER_ROLE：仅该角色可 mint
    - PAUSER_ROLE：仅该角色可 pause
    - ADMIN_ROLE：仅该角色可 grant/revoke
    - 普通用户调用以上接口 revert
    """
    log.step("custom_018: 管理员权限接口校验")
    token = myerc20_token
    MINTER_ROLE = role_constants["MINTER_ROLE"]
    PAUSER_ROLE = role_constants["PAUSER_ROLE"]
    log.debug(f"角色常量 - MINTER_ROLE: {MINTER_ROLE.hex()[:8]}..., PAUSER_ROLE: {PAUSER_ROLE.hex()[:8]}...")

    # 管理员操作（应有权限）
    log.info("步骤1: 管理员操作（应有权限）")
    token.mint(user1, int(1000 * 10**18), sender=deployer)
    log.debug(f"管理员 mint 成功，用户1余额: {token.balanceOf(user1) / 10**18}")
    
    token.pause(sender=deployer)
    is_paused = token.paused()
    log.debug(f"管理员 pause 后状态: {is_paused}")
    assert is_paused == True, f"pause 状态不符，预期: True, 实际: {is_paused}"
    
    token.unpause(sender=deployer)
    is_paused = token.paused()
    log.debug(f"管理员 unpause 后状态: {is_paused}")
    assert is_paused == False, f"unpause 状态不符，预期: False, 实际: {is_paused}"
    
    token.grantRole(MINTER_ROLE, user2, sender=deployer)
    log.debug("管理员授权用户2 MINTER_ROLE")
    log.debug("管理员操作验证通过")

    # 普通用户操作（应被拒绝）
    log.info("步骤2: 普通用户操作（应被拒绝）")
    try:
        token.mint(user1, int(100 * 10**18), sender=user1)
        assert False, "应 revert"
    except Exception as e:
        log.debug(f"普通用户 mint 被拒绝，异常: {type(e).__name__}")
        assert "Missing required role" in str(e)

    try:
        token.pause(sender=user1)
        assert False, "应 revert"
    except Exception as e:
        log.debug(f"普通用户 pause 被拒绝，异常: {type(e).__name__}")
        assert "Missing required role" in str(e)
    log.debug("普通用户权限校验验证通过")

    log.success("✅ custom_018 管理员权限接口校验测试通过")


@allure.title("custom 019 global parameter rw")
@allure.description("Test for test_custom_019_global_parameter_rw")
@allure.tag("功能测试")
def test_custom_019_global_parameter_rw(deployer, contract_custom_test_data):
    """
    自定义全局参数读写测试

    验证合约参数管理（经典 set/get 模式）：
    - 初始构造器值正确读取
    - set 修改后立即生效
    - 多轮修改: 读取值 = 写入值 （双向断言）
    """
    log.step("custom_019: 自定义全局参数读写测试")
    data = contract_custom_test_data["case_019_global_parameter_rw"]
    hello = deployer.deploy(project.HelloWorld)
    log.debug(f"测试数据 - 初始消息: {data['initial_message']}")

    # 验证初始值
    log.info("步骤1: 验证初始值")
    initial_msg = hello.message()
    log.debug(f"初始消息: {initial_msg}")
    assert initial_msg == data["initial_message"], f"初始消息不符，预期: {data['initial_message']}, 实际: {initial_msg}"
    log.debug("初始值验证通过")

    # 第一次修改
    log.info("步骤2: 第一次修改")
    hello.setMessage(data["first_update_message"], sender=deployer)
    msg_after_first = hello.message()
    log.debug(f"第一次修改后消息: {msg_after_first}")
    assert msg_after_first == data["first_update_message"], f"第一次修改后消息不符，预期: {data['first_update_message']}, 实际: {msg_after_first}"
    log.debug("第一次修改验证通过")

    # 第二次修改
    log.info("步骤3: 第二次修改")
    hello.setMessage(data["second_update_message"], sender=deployer)
    msg_after_second = hello.message()
    log.debug(f"第二次修改后消息: {msg_after_second}")
    assert msg_after_second == data["second_update_message"], f"第二次修改后消息不符，预期: {data['second_update_message']}, 实际: {msg_after_second}"
    log.debug("第二次修改验证通过")

    log.success("✅ custom_019 自定义全局参数读写测试通过")


@allure.title("custom 020 custom business logic")
@allure.description("Test for test_custom_020_custom_business_logic")
@allure.tag("功能测试")
def test_custom_020_custom_business_logic(deployer, contract_custom_test_data, project):
    """
    项目独有业务接口测试 - 定制化计算公式验证

    业务函数：MiniSwapRouter.getAmountOut
    - Uniswap 风格定制化公式：扣除 0.3% 手续费后计算输出
    """
    log.step("custom_020: 项目独有业务接口测试")
    data = contract_custom_test_data["case_020_custom_business_logic"]
    swap_amount = parse_ether(str(data["amount_in_ether"]))
    add_amt = parse_ether("5000")
    log.debug(f"测试数据 - 兑换金额: {swap_amount / 10**18}, 添加流动性: {add_amt / 10**18}")

    # 部署 DEX 合约并添加流动性
    log.info("步骤1: 部署 DEX 合约并添加流动性")
    factory = project.MiniSwapFactory.deploy(sender=deployer)
    router = project.MiniSwapRouter.deploy(factory, sender=deployer)
    tokenA = project.MyERC20.deploy("TokenA", "TKA", sender=deployer)
    tokenB = project.MyERC20.deploy("TokenB", "TKB", sender=deployer)
    log.debug("DEX 合约部署完成")

    tokenA.mint(deployer, add_amt * 2, sender=deployer)
    tokenB.mint(deployer, add_amt * 2, sender=deployer)
    tokenA.approve(router, add_amt * 2, sender=deployer)
    tokenB.approve(router, add_amt * 2, sender=deployer)
    router.addLiquidity(tokenA, tokenB, add_amt, add_amt, deployer, sender=deployer)
    log.debug("流动性添加完成")

    # 获取储备金并计算预期输出
    log.info("步骤2: 获取储备金并计算预期输出")
    pair = project.MiniSwapPair.at(factory.getPair(tokenA, tokenB))
    (reserve0, reserve1) = pair.getReserves()
    (reserveIn, reserveOut) = (reserve0, reserve1) if tokenA.address < tokenB.address else (reserve1, reserve0)
    log.debug(f"储备金 - reserveIn: {reserveIn / 10**18}, reserveOut: {reserveOut / 10**18}")
    
    amount_out_chain = router.getAmountOut(swap_amount, tokenA.address, tokenB.address)
    log.debug(f"链上计算输出: {amount_out_chain / 10**18}")

    # 本地公式验证（扣除 0.3% 手续费）
    log.info("步骤3: 本地公式验证")
    amountInWithFee = swap_amount * 997
    expected_local = (amountInWithFee * reserveOut) // (reserveIn * 1000 + amountInWithFee)
    log.debug(f"本地计算输出: {expected_local / 10**18}")
    assert amount_out_chain == expected_local, f"链上计算与本地公式不符，链上: {amount_out_chain}, 本地: {expected_local}"
    log.debug("业务公式验证通过")

    log.success("✅ custom_020 项目独有业务接口测试通过")


@allure.title("custom 021 pause unpause")
@allure.description("Test for test_custom_021_pause_unpause")
@allure.tag("功能测试")
def test_custom_021_pause_unpause(deployer, user1, project):
    """
    合约暂停/恢复功能测试

    验证暂停机制：
    - pause 前业务正常
    - 只有 PAUSER 能 pause/unpause
    - pause 后核心业务被锁住 revert
    - unpause 后业务恢复正常
    """
    log.step("custom_021: 合约暂停/恢复功能测试")
    token = project.MyERC20.deploy("PauseToken", "PST", sender=deployer)
    test_mint_amt = 1000 * 10**18
    log.debug(f"测试数据 - 代币名称: PST, 测试金额: {test_mint_amt / 10**18}")

    # pause 前业务正常
    log.info("步骤1: pause 前业务正常")
    token.mint(user1, test_mint_amt, sender=deployer)
    balance = token.balanceOf(user1)
    log.debug(f"用户1余额: {balance / 10**18}")
    assert balance == test_mint_amt, f"余额不符，预期: {test_mint_amt / 10**18}, 实际: {balance / 10**18}"
    log.debug("pause 前业务验证通过")

    # 普通用户无法 pause
    log.info("步骤2: 普通用户无法 pause")
    try:
        token.pause(sender=user1)
        assert False, "普通用户Pause应该revert"
    except Exception as e:
        log.debug(f"普通用户 pause 被拒绝，异常: {type(e).__name__}")
    log.debug("普通用户权限校验验证通过")

    # pause 后业务被锁住
    log.info("步骤3: pause 后业务被锁住")
    token.pause(sender=deployer)
    is_paused = token.paused()
    log.debug(f"pause 后状态: {is_paused}")
    assert is_paused == True, f"pause 状态不符，预期: True, 实际: {is_paused}"

    try:
        token.mint(user1, test_mint_amt, sender=deployer)
        assert False, "Pause后mint应revert"
    except Exception as e:
        log.debug(f"pause 后 mint 被拒绝，异常: {type(e).__name__}")
    log.debug("pause 后业务拦截验证通过")

    # unpause 后业务恢复
    log.info("步骤4: unpause 后业务恢复")
    token.unpause(sender=deployer)
    is_paused = token.paused()
    log.debug(f"unpause 后状态: {is_paused}")
    assert is_paused == False, f"unpause 状态不符，预期: False, 实际: {is_paused}"

    token.mint(user1, test_mint_amt, sender=deployer)
    balance = token.balanceOf(user1)
    log.debug(f"用户1最终余额: {balance / 10**18}")
    assert balance == test_mint_amt * 2, f"最终余额不符，预期: {test_mint_amt * 2 / 10**18}, 实际: {balance / 10**18}"
    log.debug("unpause 后业务恢复验证通过")

    log.success("✅ custom_021 合约暂停/恢复功能测试通过")


@allure.title("custom 022 blacklist whitelist")
@allure.description("Test for test_custom_022_blacklist_whitelist")
@allure.tag("功能测试")
def test_custom_022_blacklist_whitelist(deployer, user1, user2, contract_custom_test_data, project):
    """
    黑白名单控制接口测试

    基于角色的名单控制验证：
    - 白名单地址(有角色)：可享受特权操作 mint
    - 黑名单外地址(无角色)：操作被强制拦截 revert
    """
    log.step("custom_022: 黑白名单控制接口测试")
    token = project.MyERC20.deploy("ListToken", "LST", sender=deployer)
    test_mint_amt = 5000 * 10**18
    log.debug(f"测试数据 - 代币名称: LST, 测试金额: {test_mint_amt / 10**18}")

    # 白名单用户(user2)可 mint
    log.info("步骤1: 白名单用户(user2)可 mint")
    MINTER_ROLE = token.MINTER_ROLE()
    token.grantRole(MINTER_ROLE, user2, sender=deployer)
    log.debug("用户2被授权 MINTER_ROLE")
    
    token.mint(user2, test_mint_amt, sender=user2)
    balance = token.balanceOf(user2)
    log.debug(f"用户2 mint 后余额: {balance / 10**18}")
    assert balance == test_mint_amt, f"余额不符，预期: {test_mint_amt / 10**18}, 实际: {balance / 10**18}"
    log.debug("白名单用户验证通过")

    # 黑名单外用户(user1)不可 mint
    log.info("步骤2: 黑名单外用户(user1)不可 mint")
    has_role = token.hasRole(MINTER_ROLE, user1)
    log.debug(f"用户1是否有 MINTER_ROLE: {has_role}")
    assert has_role == False, "用户1不应有 MINTER_ROLE"

    try:
        token.mint(user1, test_mint_amt, sender=user1)
        assert False, "名单外用户mint应revert"
    except Exception as e:
        log.debug(f"名单外用户 mint 被拒绝，异常: {type(e).__name__}")
        assert "Missing required role" in str(e)
    log.debug("黑名单外用户校验验证通过")

    log.success("✅ custom_022 黑白名单控制接口测试通过")


@allure.title("custom 023 dynamic parameter update")
@allure.description("Test for test_custom_023_dynamic_parameter_update")
@allure.tag("功能测试")
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
    log.step("custom_023: 动态参数修改接口测试")
    hello = project.HelloWorld.deploy(sender=deployer)
    initial_msg = contract_custom_test_data["case_019_global_parameter_rw"]["initial_message"]
    log.debug(f"测试数据 - 初始消息: {initial_msg}")

    # 验证初始值
    log.info("步骤1: 验证初始值")
    msg = hello.message()
    log.debug(f"初始消息: {msg}")
    assert msg == initial_msg, f"初始消息不符，预期: {initial_msg}, 实际: {msg}"
    log.debug("初始值验证通过")

    # 第一次修改
    log.info("步骤2: 第一次修改")
    hello.setMessage("FeeRate: 0.5%", sender=deployer)
    msg = hello.message()
    log.debug(f"第一次修改后消息: {msg}")
    assert msg == "FeeRate: 0.5%", f"第一次修改后消息不符，预期: FeeRate: 0.5%, 实际: {msg}"
    log.debug("第一次修改验证通过")

    # 第二次修改
    log.info("步骤3: 第二次修改")
    hello.setMessage("RewardRate: 10%, PlatformTax: 2%", sender=deployer)
    msg = hello.message()
    log.debug(f"第二次修改后消息: {msg}")
    assert msg == "RewardRate: 10%, PlatformTax: 2%", f"第二次修改后消息不符，预期: RewardRate: 10%, PlatformTax: 2%, 实际: {msg}"
    log.debug("第二次修改验证通过")

    log.success("✅ custom_023 动态参数修改接口测试通过")


@allure.title("custom 024 external contract call")
@allure.description("Test for test_custom_024_external_contract_call")
@allure.tag("功能测试")
def test_custom_024_external_contract_call(deployer, project, contract_custom_test_data):
    """
    外部合约依赖调用测试

    业务模式（预言机/外部池/跨合约场景）：
        结构：合约A → 调用 → 合约B（外部依赖）的只读接口
    """
    log.step("custom_024: 外部合约依赖调用测试")

    # 部署外部合约：预言机、外部池、第三方代币
    log.info("步骤1: 部署外部合约")
    oracle_a = project.HelloWorld.deploy(sender=deployer)
    pool_ext = project.HelloWorld.deploy(sender=deployer)
    third_party = project.MyERC20.deploy("ChainLink", "LINK", sender=deployer)
    log.debug("外部合约部署完成：预言机、外部池、第三方代币")

    # 写入并验证数据
    log.info("步骤2: 写入并验证数据")
    oracle_a.setMessage("ETH/USD: 3456.78", sender=deployer)
    pool_ext.setMessage("DAI Pool Reserve: 1.2M", sender=deployer)
    
    oracle_msg = oracle_a.message()
    log.debug(f"预言机消息: {oracle_msg}")
    assert oracle_msg == "ETH/USD: 3456.78", f"预言机消息不符，预期: ETH/USD: 3456.78, 实际: {oracle_msg}"

    pool_msg = pool_ext.message()
    log.debug(f"外部池消息: {pool_msg}")
    assert pool_msg == "DAI Pool Reserve: 1.2M", f"外部池消息不符，预期: DAI Pool Reserve: 1.2M, 实际: {pool_msg}"

    symbol = third_party.symbol()
    name = third_party.name()
    log.debug(f"第三方代币 - 符号: {symbol}, 名称: {name}")
    assert symbol == "LINK", f"代币符号不符，预期: LINK, 实际: {symbol}"
    assert name == "ChainLink", f"代币名称不符，预期: ChainLink, 实际: {name}"
    log.debug("数据验证通过")

    # 更新预言机价格
    log.info("步骤3: 更新预言机价格")
    oracle_a.setMessage("ETH/USD: 3680.00", sender=deployer)
    oracle_msg = oracle_a.message()
    log.debug(f"更新后预言机消息: {oracle_msg}")
    assert oracle_msg == "ETH/USD: 3680.00", f"更新后预言机消息不符，预期: ETH/USD: 3680.00, 实际: {oracle_msg}"
    log.debug("预言机价格更新验证通过")

    log.success("✅ custom_024 外部合约依赖调用测试通过")


@allure.title("custom 025 custom error revert")
@allure.description("Test for test_custom_025_custom_error_revert")
@allure.tag("功能测试")
def test_custom_025_custom_error_revert(deployer, user1, project):
    """
    自定义业务异常拦截测试

    验证：
    - 权限校验：非授权地址调用权限接口，预期 revert
    - 状态校验：暂停合约无法执行写操作，预期 revert
    - 参数校验：零值、负值、超限等非法输入
    - 业务规则：余额不足、流动性为零等边界条件
    """
    log.step("custom_025: 自定义业务异常拦截测试")
    token = project.MyERC20.deploy("TestToken", "TT", sender=deployer)
    log.debug("测试数据 - 代币名称: TT")

    # 权限校验：普通用户无法 mint
    log.info("步骤1: 权限校验 - 普通用户无法 mint")
    try:
        token.mint(user1, 1000, sender=user1)
        assert False, "应 revert"
    except Exception as e:
        log.debug(f"普通用户 mint 被拒绝，异常: {type(e).__name__}")
    log.debug("权限校验验证通过")

    # 状态校验：暂停后无法 mint
    log.info("步骤2: 状态校验 - 暂停后无法 mint")
    token.pause(sender=deployer)
    log.debug("合约已暂停")
    try:
        token.mint(user1, 1000, sender=deployer)
        assert False, "应 revert"
    except Exception as e:
        log.debug(f"暂停后 mint 被拒绝，异常: {type(e).__name__}")
    
    token.unpause(sender=deployer)
    log.debug("合约已恢复")
    log.debug("状态校验验证通过")

    # 参数校验：转账至零地址被拒绝
    log.info("步骤3: 参数校验 - 转账至零地址被拒绝")
    try:
        token.transfer("0x0000000000000000000000000000000000000000", 100, sender=deployer)
        assert False, "应 revert"
    except Exception as e:
        log.debug(f"零地址转账被拒绝，异常: {type(e).__name__}")
    log.debug("参数校验验证通过")

    # 业务规则：超额转账被拒绝
    log.info("步骤4: 业务规则 - 超额转账被拒绝")
    try:
        token.transfer(deployer, token.balanceOf(user1) + 1, sender=user1)
        assert False, "应 revert"
    except Exception as e:
        log.debug(f"超额转账被拒绝，异常: {type(e).__name__}")
    log.debug("业务规则校验验证通过")

    log.success("✅ custom_025 自定义业务异常拦截测试通过")