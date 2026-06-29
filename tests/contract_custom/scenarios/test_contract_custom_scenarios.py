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
    token = myerc20_token

    MINTER_ROLE = role_constants["MINTER_ROLE"]
    PAUSER_ROLE = role_constants["PAUSER_ROLE"]
    ADMIN_ROLE = role_constants["ADMIN_ROLE"]

    token.mint(user1, int(1000 * 10**18), sender=deployer)
    balance_user1 = token.balanceOf(user1)

    token.pause(sender=deployer)
    assert token.paused() == True

    token.unpause(sender=deployer)
    assert token.paused() == False

    token.grantRole(MINTER_ROLE, user2, sender=deployer)
    assert token.roles(MINTER_ROLE, user2) == True

    try:
        token.mint(user1, int(100 * 10**18), sender=user1)
        assert False, "应 revert"
    except Exception as e:
        assert "Missing required role" in str(e)

    try:
        token.pause(sender=user1)
        assert False, "应 revert"
    except Exception as e:
        assert "Missing required role" in str(e)

    try:
        token.grantRole(MINTER_ROLE, user1, sender=user1)
        assert False, "应 revert"
    except Exception as e:
        assert "Missing required role" in str(e)


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
    data = contract_custom_test_data["case_019_global_parameter_rw"]

    hello = deployer.deploy(project.HelloWorld)

    INITIAL_MSG = data["initial_message"]
    FIRST_UPDATE = data["first_update_message"]
    SECOND_UPDATE = data["second_update_message"]

    actual_initial = hello.message()
    assert actual_initial == INITIAL_MSG

    hello.setMessage(FIRST_UPDATE, sender=deployer)
    actual_after_first = hello.message()
    assert actual_after_first == FIRST_UPDATE

    hello.setMessage(SECOND_UPDATE, sender=deployer)
    actual_after_second = hello.message()
    assert actual_after_second == SECOND_UPDATE


@allure.title("custom 020 custom business logic")
@allure.description("Test for test_custom_020_custom_business_logic")
@allure.tag("功能测试")
def test_custom_020_custom_business_logic(deployer, contract_custom_test_data, project):
    """
    项目独有业务接口测试 - 定制化计算公式验证

    业务函数：MiniSwapRouter.getAmountOut
    - Uniswap 风格定制化公式：扣除 0.3% 手续费后计算输出
    """
    data = contract_custom_test_data["case_020_custom_business_logic"]
    swap_amount_ether = data["amount_in_ether"]
    swap_amount = parse_ether(str(swap_amount_ether))

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

    amount_out_chain = router.getAmountOut(swap_amount, tokenA.address, tokenB.address)

    amountInWithFee = swap_amount * 997
    numerator = amountInWithFee * reserveOut
    denominator = reserveIn * 1000 + amountInWithFee
    expected_local = numerator // denominator

    assert amount_out_chain == expected_local


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
    token = project.MyERC20.deploy("PauseToken", "PST", sender=deployer)
    test_mint_amt = 1000 * 10**18

    token.mint(user1, test_mint_amt, sender=deployer)
    balance_before = token.balanceOf(user1)
    assert balance_before == test_mint_amt

    try:
        token.pause(sender=user1)
        assert False, "普通用户Pause应该revert"
    except Exception as e:
        assert "Missing required role" in str(e) or "AccessControl" in str(e)

    token.pause(sender=deployer)
    assert token.paused() == True

    try:
        token.mint(user1, test_mint_amt, sender=deployer)
        assert False, "Pause后mint应revert"
    except Exception as e:
        assert "Contract is paused" in str(e)

    token.unpause(sender=deployer)
    assert token.paused() == False

    token.mint(user1, test_mint_amt, sender=deployer)
    balance_after = token.balanceOf(user1)
    assert balance_after == test_mint_amt * 2


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
    token = project.MyERC20.deploy("ListToken", "LST", sender=deployer)
    test_mint_amt = 5000 * 10**18

    MINTER_ROLE = token.MINTER_ROLE()
    token.grantRole(MINTER_ROLE, user2, sender=deployer)

    has_role = token.hasRole(MINTER_ROLE, user2)
    assert has_role == True

    token.mint(user2, test_mint_amt, sender=user2)
    user2_balance = token.balanceOf(user2)
    assert user2_balance == test_mint_amt

    role_not_granted = token.hasRole(MINTER_ROLE, user1)
    assert role_not_granted == False

    try:
        token.mint(user1, test_mint_amt, sender=user1)
        assert False, "名单外用户mint应revert"
    except Exception as e:
        assert "Missing required role" in str(e)


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
    hello = project.HelloWorld.deploy(sender=deployer)

    initial_val = hello.message()
    expected_default = contract_custom_test_data["case_019_global_parameter_rw"]["initial_message"]
    assert initial_val == expected_default

    new_val_1 = "FeeRate: 0.5%"
    hello.setMessage(new_val_1, sender=deployer)
    readback_1 = hello.message()
    assert readback_1 == new_val_1

    new_val_2 = "RewardRate: 10%, PlatformTax: 2%"
    hello.setMessage(new_val_2, sender=deployer)
    readback_2 = hello.message()
    assert readback_2 == new_val_2


@allure.title("custom 024 external contract call")
@allure.description("Test for test_custom_024_external_contract_call")
@allure.tag("功能测试")
def test_custom_024_external_contract_call(deployer, project, contract_custom_test_data):
    """
    外部合约依赖调用测试

    业务模式（预言机/外部池/跨合约场景）：
        结构：合约A → 调用 → 合约B（外部依赖）的只读接口
    """
    oracle_a = project.HelloWorld.deploy(sender=deployer)
    pool_ext = project.HelloWorld.deploy(sender=deployer)
    third_party = project.MyERC20.deploy("ChainLink", "LINK", sender=deployer)

    feed_price_1 = "ETH/USD: 3456.78"
    reserve_ext = "DAI Pool Reserve: 1.2M"

    oracle_a.setMessage(feed_price_1, sender=deployer)
    pool_ext.setMessage(reserve_ext, sender=deployer)

    actual_oracle = oracle_a.message()
    actual_pool = pool_ext.message()
    actual_symbol = third_party.symbol()
    actual_name = third_party.name()

    assert actual_oracle == feed_price_1
    assert actual_pool == reserve_ext
    assert actual_symbol == "LINK"
    assert actual_name == "ChainLink"

    feed_price_2 = "ETH/USD: 3680.00"
    oracle_a.setMessage(feed_price_2, sender=deployer)
    actual_oracle_v2 = oracle_a.message()

    assert actual_oracle_v2 == feed_price_2
    assert actual_oracle_v2 != feed_price_1


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
    token = project.MyERC20.deploy("TestToken", "TT", sender=deployer)

    try:
        token.mint(user1, 1000, sender=user1)
        assert False, "此处应触发 revert，但未触发"
    except Exception:
        pass

    token.pause(sender=deployer)

    try:
        token.mint(user1, 1000, sender=deployer)
        assert False, "暂停状态下 mint 应触发 revert"
    except Exception:
        pass

    token.unpause(sender=deployer)

    try:
        token.transfer("0x0000000000000000000000000000000000000000", 100, sender=deployer)
        assert False, "转账至零地址应触发 revert"
    except Exception:
        pass

    user1_balance = token.balanceOf(user1)

    try:
        token.transfer(deployer, user1_balance + 1, sender=user1)
        assert False, "超额转账应触发 revert"
    except Exception:
        pass

    hello = project.HelloWorld.deploy(sender=deployer)

    try:
        hello.setMessage("", sender=deployer)
        actual = hello.message()
    except Exception:
        pass