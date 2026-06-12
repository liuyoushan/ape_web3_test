"""
==============================================================================
【模块概览】ERC20 代币标准测试用例
对应用例编号：case_001 ~ case_010
测试范围：ERC20 核心功能、权限控制、安全边界
==============================================================================
"""
from ape import project, reverts
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
from tests.helpers.logger import log
from tests.helpers.formatters import format_ether
from tests.fixtures.token_fixture import parse_ether


def test_verify_network():
    """验证网络配置（兼容主网 Fork 和本地测试链）"""
    from ape import chain
    
    chain_id = chain.chain_id
    
    # 定义支持的链 ID
    supported_chains = {
        1: "主网 Fork",
        1337: "本地测试链 (Ganache)",
        31337: "本地测试链 (Anvil)"
    }
    
    # 获取网络名称
    network_name = supported_chains.get(chain_id, f"未知链 (ID: {chain_id})")
    
    log.info(f"当前链 ID: {chain_id}")
    log.info(f"网络类型: {network_name}")
    
    # 验证链 ID 是有效的测试环境
    assert chain_id in supported_chains, f"不支持的链 ID: {chain_id}"
    
    # 检查区块高度（仅在主网 fork 时验证）
    if chain_id == 1:
        block_num = chain.blocks[-1].number
        log.info(f"当前区块高度: {block_num}")
        # 允许一定的区块差异（考虑到可能的链重组）
        assert abs(block_num - 19500000) < 100, f"区块号偏差过大: {block_num}"
        log.success("✅ 在主网 Fork 上运行")
    else:
        log.success(f"✅ 在 {network_name} 上运行")


# ==============================================================================
# case_001 代币基础信息校验
# 测试目标：MyERC20 合约的元数据（名称、符号、小数位数、初始总发行量）
# 测试类型：P0 - 功能测试 / 正向测试
# ==============================================================================
@allure.title("case_001 代币基础信息校验")
@allure.description("验证 MyERC20 合约的元数据：名称、符号、小数位数、初始总发行量")
@allure.tag("ERC20", "P0", "功能测试")
def test_erc20_001_metadata_verification(token):
    """
    【用例编号】case_001
    【用例名称】代币基础信息校验
    【测试目标】验证 ERC20 代币的基础元数据正确性
    【测试类型】P0 - 功能测试 / 正向测试
    
    核心验证点：
    1. 代币名称正确
    2. 代币符号正确
    3. 小数位数正确（18位）
    4. 初始总发行量正确
    """
    log.step("case_001: 代币基础信息校验")
    
    # 验证名称
    name = token.name()
    log.debug("代币名称: %s", name)
    assert name == "MyToken", f"名称不正确: {name}"
    
    # 验证符号
    symbol = token.symbol()
    log.debug("代币符号: %s", symbol)
    assert symbol == "MTK", f"符号不正确: {symbol}"
    
    # 验证小数位数
    decimals = token.decimals()
    log.debug("小数位数: %d", decimals)
    assert decimals == 18, f"小数位数不正确: {decimals}"
    
    # 验证初始总发行量（初始为0，通过 mint 增加）
    total_supply = token.totalSupply()
    log.debug("总发行量: %s", format_ether(total_supply))
    assert total_supply == 0, f"初始总发行量应为0: {total_supply}"
    
    log.success("✅ case_001 代币基础信息校验通过")


# ==============================================================================
# case_002 正常转账功能测试
# 测试目标：普通地址间转账，校验余额变更、链上事件、交易状态
# 测试类型：P0 - 功能测试 / 正向测试
# ==============================================================================
@allure.title("case_002 正常转账功能测试")
@allure.description("普通地址间转账，校验余额变更、链上事件、交易状态")
@allure.tag("ERC20", "P0", "功能测试", "转账")
def test_erc20_002_normal_transfer(token_with_balance, deployer, user1, erc20_test_data):
    """
    【用例编号】case_002
    【用例名称】正常转账功能测试
    【测试目标】验证 ERC20 代币正常转账功能
    【测试类型】P0 - 功能测试 / 正向测试
    
    测试流程：
    1. 查询转账前余额
    2. 执行转账操作
    3. 验证余额变更
    4. 验证 Transfer 事件
    
    数据来源：tests/data/test_erc20.yaml -> case_002_transfer
    """
    data = erc20_test_data["case_002_transfer"]
    transfer_amount = parse_ether(data["transfer_amount"])
    
    log.step("case_002: 正常转账功能测试")
    log.debug("转账金额: %s", format_ether(transfer_amount))
    
    # 查询转账前余额
    log.step("阶段1：查询转账前初始余额")
    balance_deployer_before = token_with_balance.balanceOf(deployer)
    balance_user1_before = token_with_balance.balanceOf(user1)
    total_supply_before = token_with_balance.totalSupply()
    
    log.debug("deployer 余额: %s", format_ether(balance_deployer_before))
    log.debug("user1 余额: %s", format_ether(balance_user1_before))
    log.debug("totalSupply: %s", format_ether(total_supply_before))
    
    # 执行转账
    log.step("阶段2：执行转账操作")
    tx = token_with_balance.transfer(user1, transfer_amount, sender=deployer)
    
    # 验证转账结果
    log.step("阶段3：验证转账结果")
    balance_deployer_after = token_with_balance.balanceOf(deployer)
    balance_user1_after = token_with_balance.balanceOf(user1)
    total_supply_after = token_with_balance.totalSupply()
    
    log.debug("deployer 余额: %s", format_ether(balance_deployer_after))
    log.debug("user1 余额: %s", format_ether(balance_user1_after))
    log.debug("totalSupply: %s", format_ether(total_supply_after))
    
    # 断言余额变化
    assert balance_deployer_after == balance_deployer_before - transfer_amount, "deployer 余额减少不正确"
    assert balance_user1_after == balance_user1_before + transfer_amount, "user1 余额增加不正确"
    assert total_supply_after == total_supply_before, "总发行量不应变化"
    
    # 验证事件
    log.step("阶段4：验证 Transfer 事件")
    transfer_event = tx.decode_logs(token_with_balance.Transfer)[0]
    assert transfer_event["from"] == deployer, "事件 from 不正确"
    assert transfer_event["to"] == user1, "事件 to 不正确"
    assert transfer_event["value"] == transfer_amount, "事件 value 不正确"
    
    log.success("✅ case_002 正常转账测试通过")


# ==============================================================================
# case_002_002 用户自转账测试
# 测试目标：用户给自己转账的边界情况
# 测试类型：P1 - 边界测试 / 正向测试
# ==============================================================================
@allure.title("case_002_002 用户自转账测试")
@allure.description("验证用户给自己转账的边界情况")
@allure.tag("ERC20", "P1", "边界测试", "转账")
def test_erc20_002_normal_transfer_002(token_with_balance, deployer, user1):
    """
    【用例编号】case_002_002
    【用例名称】用户自转账测试
    【测试目标】验证用户给自己转账的边界情况
    【测试类型】P1 - 边界测试 / 正向测试
    """
    transfer_amount = parse_ether("50")
    
    log.step("case_002_002: 用户自转账测试")
    log.debug("转账金额: %s", format_ether(transfer_amount))
    
    # 先给 user1 mint 代币
    token_with_balance.mint(user1, transfer_amount, sender=deployer)
    
    # 查询转账前余额
    balance_before = token_with_balance.balanceOf(user1)
    log.debug("user1 转账前余额: %s", format_ether(balance_before))
    
    # 执行自转账
    tx = token_with_balance.transfer(user1, transfer_amount, sender=user1)
    
    # 验证余额不变
    balance_after = token_with_balance.balanceOf(user1)
    log.debug("user1 转账后余额: %s", format_ether(balance_after))
    
    assert balance_after == balance_before, "自转账后余额应不变"
    
    # 验证事件仍然触发
    transfer_event = tx.decode_logs(token_with_balance.Transfer)[0]
    assert transfer_event["from"] == user1
    assert transfer_event["to"] == user1
    assert transfer_event["value"] == transfer_amount
    
    log.success("✅ case_002_002 用户自转账测试通过")


# ==============================================================================
# case_003 余额不足转账失败测试
# 测试目标：验证余额不足时转账失败
# 测试类型：P0 - 安全测试 / 反向测试
# ==============================================================================
@allure.title("case_003 余额不足转账失败测试")
@allure.description("验证余额不足时转账失败并抛出异常")
@allure.tag("ERC20", "P0", "安全测试", "反向测试")
def test_erc20_003_insufficient_balance_transfer(token_with_balance, deployer, user1):
    """
    【用例编号】case_003
    【用例名称】余额不足转账失败测试
    【测试目标】验证余额不足时转账失败
    【测试类型】P0 - 安全测试 / 反向测试
    
    核心验证点：
    1. 当转账金额大于账户余额时，交易失败
    2. 验证抛出的异常类型
    """
    log.step("case_003: 余额不足转账失败测试")
    
    # 获取当前余额
    balance_deployer = token_with_balance.balanceOf(deployer)
    log.debug("deployer 余额: %s", format_ether(balance_deployer))
    
    # 尝试转账超过余额的金额
    transfer_amount = balance_deployer + 1
    log.debug("尝试转账金额: %s (超过余额)", format_ether(transfer_amount))
    
    # 验证交易失败
    with reverts():
        token_with_balance.transfer(user1, transfer_amount, sender=deployer)
    
    log.success("✅ case_003 余额不足转账失败测试通过")


# ==============================================================================
# case_004 授权功能测试
# 测试目标：验证 approve 和 allowance 功能
# 测试类型：P0 - 功能测试 / 正向测试
# ==============================================================================
@allure.title("case_004 授权功能测试")
@allure.description("验证 ERC20 approve 和 allowance 授权机制")
@allure.tag("ERC20", "P0", "功能测试", "授权")
def test_erc20_004_approve_authorization(token_with_balance, deployer, user1):
    """
    【用例编号】case_004
    【用例名称】授权功能测试
    【测试目标】验证 ERC20 approve 和 allowance 授权机制
    【测试类型】P0 - 功能测试 / 正向测试
    
    测试流程：
    1. deployer 授权 user1 可花费代币
    2. 验证 allowance 正确设置
    3. user1 使用 transferFrom 转移代币
    4. 验证余额变化和事件
    """
    log.step("case_004: 授权功能测试")
    
    approve_amount = parse_ether("200")
    
    # 阶段1: 查询初始状态
    log.step("阶段1：查询初始授权状态")
    initial_allowance = token_with_balance.allowance(deployer, user1)
    log.debug("初始授权额度: %s", format_ether(initial_allowance))
    
    # 阶段2: 执行授权
    log.step("阶段2：执行授权操作")
    tx = token_with_balance.approve(user1, approve_amount, sender=deployer)
    
    # 验证授权结果
    allowance_after = token_with_balance.allowance(deployer, user1)
    log.debug("授权后额度: %s", format_ether(allowance_after))
    assert allowance_after == approve_amount, "授权额度不正确"
    
    # 验证 Approval 事件
    approval_event = tx.decode_logs(token_with_balance.Approval)[0]
    assert approval_event["owner"] == deployer
    assert approval_event["spender"] == user1
    assert approval_event["value"] == approve_amount
    
    # 阶段3: 使用授权转移代币
    log.step("阶段3：使用授权转移代币")
    transfer_amount = parse_ether("100")
    
    balance_deployer_before = token_with_balance.balanceOf(deployer)
    balance_user1_before = token_with_balance.balanceOf(user1)
    
    token_with_balance.transferFrom(deployer, user1, transfer_amount, sender=user1)
    
    # 验证余额变化
    balance_deployer_after = token_with_balance.balanceOf(deployer)
    balance_user1_after = token_with_balance.balanceOf(user1)
    
    log.debug("deployer 余额变化: %s -> %s", 
              format_ether(balance_deployer_before), 
              format_ether(balance_deployer_after))
    log.debug("user1 余额变化: %s -> %s", 
              format_ether(balance_user1_before), 
              format_ether(balance_user1_after))
    
    assert balance_deployer_after == balance_deployer_before - transfer_amount
    assert balance_user1_after == balance_user1_before + transfer_amount
    
    # 验证授权额度减少
    remaining_allowance = token_with_balance.allowance(deployer, user1)
    log.debug("剩余授权额度: %s", format_ether(remaining_allowance))
    assert remaining_allowance == approve_amount - transfer_amount
    
    log.success("✅ case_004 授权功能测试通过")


# ==============================================================================
# case_005 超出授权额度转账测试
# 测试目标：验证超出授权额度时转账失败
# 测试类型：P0 - 安全测试 / 反向测试
# ==============================================================================
@allure.title("case_005 超出授权额度转账测试")
@allure.description("验证超出授权额度时 transferFrom 失败")
@allure.tag("ERC20", "P0", "安全测试", "反向测试")
def test_erc20_005_transfer_from(token_with_balance, deployer, user1):
    """
    【用例编号】case_005
    【用例名称】超出授权额度转账测试
    【测试目标】验证超出授权额度时转账失败
    【测试类型】P0 - 安全测试 / 反向测试
    """
    log.step("case_005: 超出授权额度转账测试")
    
    approve_amount = parse_ether("100")
    
    # 授权 user1 花费 100 代币
    token_with_balance.approve(user1, approve_amount, sender=deployer)
    
    # 尝试转移超过授权额度的代币
    transfer_amount = parse_ether("150")
    log.debug("授权额度: %s, 尝试转移: %s", 
              format_ether(approve_amount), 
              format_ether(transfer_amount))
    
    # 验证交易失败
    with reverts():
        token_with_balance.transferFrom(deployer, user1, transfer_amount, sender=user1)
    
    log.success("✅ case_005 超出授权额度转账测试通过")


# ==============================================================================
# case_006 铸币功能测试
# 测试目标：验证 minter 角色可以铸造代币
# 测试类型：P0 - 功能测试 / 正向测试
# ==============================================================================
@allure.title("case_006 铸币功能测试")
@allure.description("验证拥有 MINTER_ROLE 的账户可以铸造代币")
@allure.tag("ERC20", "P0", "功能测试", "铸币")
def test_erc20_006_mint_tokens(token, deployer, user1, erc20_test_data):
    """
    【用例编号】case_006
    【用例名称】铸币功能测试
    【测试目标】验证拥有 MINTER_ROLE 的账户可以铸造代币
    【测试类型】P0 - 功能测试 / 正向测试
    
    测试流程：
    1. 部署者（拥有 MINTER_ROLE）铸造代币给 user1
    2. 验证余额变化
    3. 验证总发行量增加
    4. 验证 Transfer 事件
    
    数据来源：tests/data/test_erc20.yaml -> case_006_mint
    """
    data = erc20_test_data["case_006_mint"]
    mint_amount = parse_ether(data["mint_amount"])
    
    log.step("case_006: 铸币功能测试")
    log.debug("铸造金额: %s", format_ether(mint_amount))
    
    # 查询铸造前状态
    log.step("阶段1：查询铸造前状态")
    balance_user1_before = token.balanceOf(user1)
    total_supply_before = token.totalSupply()
    
    log.debug("user1 铸造前余额: %s", format_ether(balance_user1_before))
    log.debug("铸造前总发行量: %s", format_ether(total_supply_before))
    
    # 执行铸造
    log.step("阶段2：执行铸造操作")
    tx = token.mint(user1, mint_amount, sender=deployer)
    
    # 验证铸造结果
    log.step("阶段3：验证铸造结果")
    balance_user1_after = token.balanceOf(user1)
    total_supply_after = token.totalSupply()
    
    log.debug("user1 铸造后余额: %s", format_ether(balance_user1_after))
    log.debug("铸造后总发行量: %s", format_ether(total_supply_after))
    
    # 断言余额变化
    assert balance_user1_after == balance_user1_before + mint_amount, "user1 余额增加不正确"
    assert total_supply_after == total_supply_before + mint_amount, "总发行量增加不正确"
    
    # 验证 Transfer 事件（铸币时 from 地址为 0x0）
    transfer_event = tx.decode_logs(token.Transfer)[0]
    assert transfer_event["from"] == "0x" + "0" * 40, "铸币事件 from 应为零地址"
    assert transfer_event["to"] == user1, "铸币事件 to 不正确"
    assert transfer_event["value"] == mint_amount, "铸币事件 value 不正确"
    
    log.success("✅ case_006 铸币功能测试通过")


# ==============================================================================
# case_007 销毁代币功能测试
# 测试目标：验证用户可以销毁自己的代币
# 测试类型：P0 - 功能测试 / 正向测试
# ==============================================================================
@allure.title("case_007 销毁代币功能测试")
@allure.description("验证用户可以销毁自己持有的代币")
@allure.tag("ERC20", "P0", "功能测试", "销毁")
def test_erc20_007_burn_tokens(token_with_balance, deployer, user1):
    """
    【用例编号】case_007
    【用例名称】销毁代币功能测试
    【测试目标】验证用户可以销毁自己持有的代币
    【测试类型】P0 - 功能测试 / 正向测试
    
    测试流程：
    1. 先给 user1 mint 代币
    2. user1 销毁部分代币
    3. 验证余额减少
    4. 验证总发行量减少
    5. 验证 Transfer 事件
    """
    mint_amount = parse_ether("200")
    burn_amount = parse_ether("100")
    
    log.step("case_007: 销毁代币功能测试")
    log.debug("铸造金额: %s, 销毁金额: %s", format_ether(mint_amount), format_ether(burn_amount))
    
    # 先给 user1 mint 代币
    token_with_balance.mint(user1, mint_amount, sender=deployer)
    
    # 查询销毁前状态
    log.step("阶段1：查询销毁前状态")
    balance_user1_before = token_with_balance.balanceOf(user1)
    total_supply_before = token_with_balance.totalSupply()
    
    log.debug("user1 销毁前余额: %s", format_ether(balance_user1_before))
    log.debug("销毁前总发行量: %s", format_ether(total_supply_before))
    
    # 执行销毁
    log.step("阶段2：执行销毁操作")
    tx = token_with_balance.burn(burn_amount, sender=user1)
    
    # 验证销毁结果
    log.step("阶段3：验证销毁结果")
    balance_user1_after = token_with_balance.balanceOf(user1)
    total_supply_after = token_with_balance.totalSupply()
    
    log.debug("user1 销毁后余额: %s", format_ether(balance_user1_after))
    log.debug("销毁后总发行量: %s", format_ether(total_supply_after))
    
    # 断言余额变化
    assert balance_user1_after == balance_user1_before - burn_amount, "user1 余额减少不正确"
    assert total_supply_after == total_supply_before - burn_amount, "总发行量减少不正确"
    
    # 验证 Transfer 事件（销毁时 to 地址为 0x0）
    transfer_event = tx.decode_logs(token_with_balance.Transfer)[0]
    assert transfer_event["from"] == user1, "销毁事件 from 不正确"
    assert transfer_event["to"] == "0x" + "0" * 40, "销毁事件 to 应为零地址"
    assert transfer_event["value"] == burn_amount, "销毁事件 value 不正确"
    
    log.success("✅ case_007 销毁代币功能测试通过")


# ==============================================================================
# case_008 RBAC 角色控制测试（异常流程）
# 测试目标：验证没有权限的账户无法执行受限操作
# 测试类型：P0 - 安全测试 / 反向测试
# ==============================================================================
@allure.title("case_008 RBAC 角色控制测试")
@allure.description("验证没有权限的账户无法执行受限操作（铸币、暂停）")
@allure.tag("ERC20", "P0", "安全测试", "RBAC", "反向测试")
def test_erc20_008_rbac_role_control(token, user1, user2):
    """
    【用例编号】case_008
    【用例名称】RBAC 角色控制测试（异常流程）
    【测试目标】验证没有权限的账户无法执行受限操作
    【测试类型】P0 - 安全测试 / 反向测试
    
    测试流程：
    1. 验证普通用户无法铸币（无 MINTER_ROLE）
    2. 验证普通用户无法暂停合约（无 PAUSER_ROLE）
    """
    log.step("case_008: RBAC 角色控制测试（异常流程）")
    
    # 测试1: 普通用户无法铸币
    log.step("阶段1：验证普通用户无法铸币")
    with reverts():
        token.mint(user1, parse_ether("100"), sender=user1)
    log.debug("✓ 普通用户铸币失败（预期行为）")
    
    # 测试2: 普通用户无法暂停合约
    log.step("阶段2：验证普通用户无法暂停合约")
    with reverts():
        token.pause(sender=user1)
    log.debug("✓ 普通用户暂停失败（预期行为）")
    
    # 测试3: 无权限用户无法授权其他用户铸币权限
    log.step("阶段3：验证无权限用户无法授权")
    MINTER_ROLE = token.MINTER_ROLE()
    with reverts():
        token.grantRole(MINTER_ROLE, user2, sender=user1)
    log.debug("✓ 无权限用户授权失败（预期行为）")
    
    log.success("✅ case_008 RBAC 角色控制测试通过")


# ==============================================================================
# case_009 RBAC 角色正常操作测试
# 测试目标：验证拥有权限的账户可以执行受限操作
# 测试类型：P0 - 功能测试 / 正向测试
# ==============================================================================
@allure.title("case_009 RBAC 角色正常操作测试")
@allure.description("验证拥有权限的账户可以执行受限操作")
@allure.tag("ERC20", "P0", "功能测试", "RBAC", "正向测试")
def test_erc20_009_role_normal_operations(token, deployer, user1, user2):
    """
    【用例编号】case_009
    【用例名称】RBAC 角色正常操作测试
    【测试目标】验证拥有权限的账户可以执行受限操作
    【测试类型】P0 - 功能测试 / 正向测试
    
    测试流程：
    1. 部署者授权 user1 为 MINTER_ROLE
    2. user1 执行铸币操作
    3. 部署者授权 user2 为 PAUSER_ROLE
    4. user2 执行暂停操作
    5. 验证暂停后转账失败
    6. 部署者恢复合约
    """
    log.step("case_009: RBAC 角色正常操作测试")
    
    MINTER_ROLE = token.MINTER_ROLE()
    PAUSER_ROLE = token.PAUSER_ROLE()
    
    # 阶段1: 授权 user1 为 MINTER
    log.step("阶段1：授权 user1 为 MINTER_ROLE")
    token.grantRole(MINTER_ROLE, user1, sender=deployer)
    assert token.hasRole(MINTER_ROLE, user1), "user1 应拥有 MINTER_ROLE"
    log.debug("✓ user1 已获得 MINTER_ROLE")
    
    # 阶段2: user1 执行铸币
    log.step("阶段2：user1 执行铸币操作")
    mint_amount = parse_ether("500")
    token.mint(user1, mint_amount, sender=user1)
    balance = token.balanceOf(user1)
    assert balance == mint_amount, "铸币后余额不正确"
    log.debug("✓ user1 铸币成功，余额: %s", format_ether(balance))
    
    # 阶段3: 授权 user2 为 PAUSER
    log.step("阶段3：授权 user2 为 PAUSER_ROLE")
    token.grantRole(PAUSER_ROLE, user2, sender=deployer)
    assert token.hasRole(PAUSER_ROLE, user2), "user2 应拥有 PAUSER_ROLE"
    log.debug("✓ user2 已获得 PAUSER_ROLE")
    
    # 阶段4: user2 执行暂停
    log.step("阶段4：user2 执行暂停操作")
    token.pause(sender=user2)
    assert token.paused(), "合约应处于暂停状态"
    log.debug("✓ 合约已暂停")
    
    # 阶段5: 验证暂停后转账失败
    log.step("阶段5：验证暂停后转账失败")
    with reverts():
        token.transfer(user2, parse_ether("10"), sender=user1)
    log.debug("✓ 暂停期间转账失败（预期行为）")
    
    # 阶段6: 部署者恢复合约
    log.step("阶段6：部署者恢复合约")
    token.unpause(sender=deployer)
    assert not token.paused(), "合约应处于正常状态"
    log.debug("✓ 合约已恢复")
    
    log.success("✅ case_009 RBAC 角色正常操作测试通过")


# ==============================================================================
# case_010 权限升级测试
# 测试目标：验证 ADMIN 可以管理角色权限
# 测试类型：P1 - 功能测试 / 正向测试
# ==============================================================================
@allure.title("case_010 权限升级测试")
@allure.description("验证 ADMIN 角色可以管理其他角色的权限")
@allure.tag("ERC20", "P1", "功能测试", "RBAC", "权限管理")
def test_erc20_010_permission_upgrade(token, deployer, user1):
    """
    【用例编号】case_010
    【用例名称】权限升级测试
    【测试目标】验证 ADMIN 角色可以管理其他角色的权限
    【测试类型】P1 - 功能测试 / 正向测试
    
    测试流程：
    1. 部署者（默认 ADMIN）授权 user1 为 MINTER
    2. 验证 user1 可以铸币
    3. 部署者撤销 user1 的 MINTER 权限
    4. 验证 user1 无法再铸币
    """
    log.step("case_010: 权限升级测试")
    
    MINTER_ROLE = token.MINTER_ROLE()
    ADMIN_ROLE = token.ADMIN_ROLE()
    
    # 验证部署者是 ADMIN
    assert token.hasRole(ADMIN_ROLE, deployer), "deployer 应拥有 ADMIN_ROLE"
    
    # 阶段1: 授权 user1 为 MINTER
    log.step("阶段1：授权 user1 为 MINTER_ROLE")
    token.grantRole(MINTER_ROLE, user1, sender=deployer)
    assert token.hasRole(MINTER_ROLE, user1), "user1 应拥有 MINTER_ROLE"
    
    # 阶段2: user1 可以铸币
    log.step("阶段2：user1 执行铸币")
    token.mint(user1, parse_ether("200"), sender=user1)
    log.debug("✓ user1 铸币成功")
    
    # 阶段3: 撤销 user1 的权限
    log.step("阶段3：撤销 user1 的 MINTER_ROLE")
    token.revokeRole(MINTER_ROLE, user1, sender=deployer)
    assert not token.hasRole(MINTER_ROLE, user1), "user1 不应再拥有 MINTER_ROLE"
    
    # 阶段4: user1 无法再铸币
    log.step("阶段4：验证 user1 无法再铸币")
    with reverts():
        token.mint(user1, parse_ether("100"), sender=user1)
    log.debug("✓ user1 铸币失败（预期行为）")
    
    log.success("✅ case_010 权限升级测试通过")
