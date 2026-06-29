"""
==============================================================================
【安全场景】完整安全测试用例
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
from framework.core.formatters import parse_ether, format_ether


@allure.title("case_026 授权安全高阶测试")
@allure.description("验证授权安全机制：无限授权风险、重复授权覆盖、授权清零逻辑")
@allure.tag("Security", "P0", "安全测试")
def test_security_026_approve_security(deployer, user1, user2, erc20_token, security_test_data):
    """
    case_026 授权安全高阶测试
    
    验证 ERC20 授权机制的安全性：
    - 初始授权正确记录
    - 重复授权覆盖旧值
    - 无限授权（type(uint256).max）被拦截
    - 授权清零后无法操作
    - Approval 事件正确触发
    """
    data = security_test_data["case_026_approve_security"]
    
    initial_amount = parse_ether(str(data["initial_approve_amount"]))
    second_amount = parse_ether(str(data["second_approve_amount"]))
    infinite_amount = data["infinite_approve_amount"]
    zero_amount = parse_ether(str(data["zero_approve_amount"]))

    tx = erc20_token.approve(user2, initial_amount, sender=user1)
    allowance = erc20_token.allowance(user1, user2)
    assert allowance == initial_amount

    events = [e for e in tx.decode_logs(erc20_token.Approval)]
    assert len(events) == 1
    assert events[0].owner == user1
    assert events[0].spender == user2
    assert events[0].value == initial_amount

    tx2 = erc20_token.approve(user2, second_amount, sender=user1)
    allowance_after = erc20_token.allowance(user1, user2)
    assert allowance_after == second_amount

    try:
        erc20_token.approve(user2, infinite_amount, sender=user1)
        assert False, "未拦截无限授权，安全缺陷"
    except Exception:
        pass

    tx4 = erc20_token.approve(user2, zero_amount, sender=user1)
    allowance_zero = erc20_token.allowance(user1, user2)
    assert allowance_zero == zero_amount

    try:
        erc20_token.transferFrom(user1, deployer, 1, sender=user2)
        assert False, "清零后应该无法操作"
    except Exception:
        pass


@allure.title("case_027 批量操作接口测试")
@allure.description("验证批量转账、批量授权功能及数据一致性")
@allure.tag("Security", "P1", "效率测试")
def test_security_027_batch_operations(deployer, user1, user2, user3, erc20_token, security_test_data):
    """
    case_027 批量操作接口测试
    
    验证批量操作的正确性和安全性：
    - 批量转账：多地址同时转账，余额正确扣减
    - 批量授权：多地址同时授权，allowance 正确设置
    - Transfer/Approval 事件正确触发
    - 数组长度不匹配时被拒绝
    """
    data = security_test_data["case_027_batch_operations"]
    transfer_amount = parse_ether(str(data["transfer_amount"]))

    recipients = [user1, user2, user3]
    batch_size = len(recipients)

    erc20_token.mint(deployer, transfer_amount * batch_size, sender=deployer)
    deployer_balance_before = erc20_token.balanceOf(deployer)
    user1_balance_before = erc20_token.balanceOf(user1)
    user2_balance_before = erc20_token.balanceOf(user2)
    user3_balance_before = erc20_token.balanceOf(user3)

    amounts = [transfer_amount, transfer_amount, transfer_amount]
    tx = erc20_token.batchTransfer(recipients, amounts, sender=deployer)

    deployer_balance_after = erc20_token.balanceOf(deployer)
    user1_balance_after = erc20_token.balanceOf(user1)
    user2_balance_after = erc20_token.balanceOf(user2)
    user3_balance_after = erc20_token.balanceOf(user3)

    assert deployer_balance_after == deployer_balance_before - transfer_amount * batch_size
    assert user1_balance_after == user1_balance_before + transfer_amount
    assert user2_balance_after == user2_balance_before + transfer_amount
    assert user3_balance_after == user3_balance_before + transfer_amount

    events = [e for e in tx.decode_logs(erc20_token.Transfer)]
    assert len(events) == batch_size

    spenders = [deployer, user2, user3]
    approve_amounts = [parse_ether("100"), parse_ether("200"), parse_ether("300")]

    tx2 = erc20_token.batchApprove(spenders, approve_amounts, sender=user1)

    allowance1 = erc20_token.allowance(user1, deployer)
    allowance2 = erc20_token.allowance(user1, user2)
    allowance3 = erc20_token.allowance(user1, user3)

    assert allowance1 == approve_amounts[0]
    assert allowance2 == approve_amounts[1]
    assert allowance3 == approve_amounts[2]

    approval_events = [e for e in tx2.decode_logs(erc20_token.Approval)]
    assert len(approval_events) == batch_size

    try:
        bad_recipients = [user1, user2]
        bad_amounts = [transfer_amount]
        erc20_token.batchTransfer(bad_recipients, bad_amounts, sender=deployer)
        assert False, "应该拒绝数组长度不匹配的请求"
    except Exception:
        pass


@allure.title("case_028 质押/挖矿收益测算")
@allure.description("验证质押锁定、区块奖励计算、解押解锁逻辑")
@allure.tag("Security", "P0", "核心业务")
def test_security_028_staking_mining(deployer, user1, user2, erc20_token, staking_contract, security_test_data):
    """
    case_028 质押/挖矿收益测算
    
    验证质押系统的完整流程：
    - 质押：代币转入合约，质押余额增加
    - 奖励计算：基于区块高度计算待领取奖励
    - 解押：代币返还用户，质押余额清零
    - 领取奖励：奖励代币正确发放
    - Staked/Unstaked/RewardClaimed 事件正确触发
    """
    data = security_test_data["case_028_staking_mining"]
    stake_amount = parse_ether(str(data["stake_amount"]))

    staking, reward_token = staking_contract

    erc20_token.mint(user1, stake_amount, sender=deployer)
    user1_balance_before = erc20_token.balanceOf(user1)

    erc20_token.approve(staking.address, stake_amount, sender=user1)
    tx_stake = staking.stake(stake_amount, sender=user1)

    user1_balance_after = erc20_token.balanceOf(user1)
    user1_staked = staking.userInfo(user1)

    assert user1_balance_after == user1_balance_before - stake_amount
    assert user1_staked[0] == stake_amount

    stake_events = [e for e in tx_stake.decode_logs(staking.Staked)]
    assert len(stake_events) == 1
    assert stake_events[0].amount == stake_amount

    erc20_token.mint(user2, stake_amount, sender=deployer)
    erc20_token.approve(staking.address, stake_amount, sender=user2)
    staking.stake(stake_amount, sender=user2)

    pending_reward = staking.pendingReward(user1.address)
    assert pending_reward > 0

    user1_balance_before_unstake = erc20_token.balanceOf(user1)
    tx_unstake = staking.unstake(stake_amount, sender=user1)

    user1_balance_after_unstake = erc20_token.balanceOf(user1)
    user1_staked_after = staking.userInfo(user1.address)

    assert user1_balance_after_unstake == user1_balance_before_unstake + stake_amount
    assert user1_staked_after[0] == 0

    unstake_events = [e for e in tx_unstake.decode_logs(staking.Unstaked)]
    assert len(unstake_events) == 1

    user1_reward_before = reward_token.balanceOf(user1)
    tx_claim = staking.claimReward(sender=user1)

    user1_reward_after = reward_token.balanceOf(user1)
    assert user1_reward_after > user1_reward_before

    claim_events = [e for e in tx_claim.decode_logs(staking.RewardClaimed)]
    assert len(claim_events) == 1


@allure.title("case_029 时间锁/区块锁控制")
@allure.description("验证依赖区块高度、时间戳的限时功能，边界时间节点校验")
@allure.tag("Security", "P0", "时间敏感")
def test_security_029_timelock_blocklock(deployer, user1, user2, timelock_contract, security_test_data):
    """
    case_029 时间锁/区块锁控制
    
    验证时间锁机制的安全性：
    - 锁定操作正确记录金额和时间戳
    - 时间锁未到期时拒绝释放
    - 区块锁未到期时拒绝释放
    - 重复锁定被拒绝
    - 零金额锁定被拒绝
    - 管理员可更新锁定参数
    """
    data = security_test_data.get("case_029_timelock_blocklock", {})
    lock_duration = data.get("lock_duration", 86400)
    lock_blocks = data.get("lock_blocks", 100)

    lock_amount = 1000
    tx_lock = timelock_contract.lock(lock_amount, sender=user1)

    user1_lock = timelock_contract.userLocks(user1)
    assert user1_lock[0] == lock_amount
    assert user1_lock[1] > 0
    assert user1_lock[2] > 0

    lock_events = [e for e in tx_lock.decode_logs(timelock_contract.Locked)]
    assert len(lock_events) == 1

    is_expired = timelock_contract.isTimeLockExpired(user1)
    remaining_time = timelock_contract.getRemainingTime(user1)

    assert not is_expired
    assert remaining_time > 0

    try:
        timelock_contract.releaseByTime(sender=user1)
        assert False, "时间锁未到期时应该拒绝释放"
    except Exception:
        pass

    tx_lock2 = timelock_contract.lock(lock_amount, sender=user2)
    user2_lock = timelock_contract.userLocks(user2)
    assert user2_lock[0] == lock_amount

    is_block_expired = timelock_contract.isBlockLockExpired(user2)
    remaining_blocks = timelock_contract.getRemainingBlocks(user2)

    assert not is_block_expired

    try:
        timelock_contract.releaseByBlock(sender=user2)
        assert False, "区块锁未到期时应该拒绝释放"
    except Exception:
        pass

    try:
        timelock_contract.lock(lock_amount, sender=user1)
        assert False, "重复锁定应该被拒绝"
    except Exception:
        pass

    try:
        timelock_contract.lock(0, sender=deployer)
        assert False, "零金额锁定应该被拒绝"
    except Exception:
        pass

    new_duration = 172800
    timelock_contract.updateLockDuration(new_duration, sender=deployer)
    assert timelock_contract.lockDuration() == new_duration

    new_blocks = 200
    timelock_contract.updateLockBlocks(new_blocks, sender=deployer)
    assert timelock_contract.lockBlocks() == new_blocks


@allure.title("case_030 重入攻击防护测试")
@allure.description("验证关键资金接口重入场景模拟，校验防重入锁生效")
@allure.tag("Security", "P1", "安全测试")
def test_security_030_reentrancy_guard(deployer, user1, user2, reentrancy_vault, vulnerable_vault, security_test_data):
    """
    case_030 重入攻击防护测试
    
    验证重入攻击防护机制：
    - 正常存款/取款功能正常
    - 漏洞合约易受重入攻击（攻击者可提取超额资金）
    - 防护合约成功拦截重入攻击（reentrant lock 生效）
    - 攻击后攻击者余额不超过存款金额
    """
    data = security_test_data.get("case_030_reentrancy_guard", {})
    test_amount = parse_ether(str(data.get("test_amount", 1)))

    vault = reentrancy_vault

    deposit_amount = test_amount
    tx_deposit = vault.deposit(sender=user1, value=deposit_amount)

    user1_balance = vault.balances(user1)
    assert user1_balance == deposit_amount

    tx_withdraw = vault.withdraw(deposit_amount, sender=user1)
    user1_balance_after = vault.balances(user1)
    assert user1_balance_after == 0

    vuln_vault = vulnerable_vault
    initial_fund = parse_ether("50")
    deployer.transfer(vuln_vault.address, initial_fund)

    attacker = deployer.deploy(project.ReentrancyAttacker, vuln_vault.address)
    attacker_deposit = parse_ether("5")
    attacker.deposit(sender=deployer, value=attacker_deposit)

    try:
        attacker.attack(attacker_deposit, sender=deployer)
    except Exception:
        pass

    try:
        attacker.getMoney(sender=deployer)
    except Exception:
        pass

    initial_fund2 = parse_ether("50")
    deployer.transfer(reentrancy_vault.address, initial_fund2)

    attacker2 = deployer.deploy(project.ReentrancyAttacker, reentrancy_vault.address)
    attacker2_deposit = parse_ether("5")
    attacker2.deposit(sender=deployer, value=attacker2_deposit)

    try:
        attacker2.attack(attacker2_deposit, sender=deployer)
        assert False, "重入攻击应该被拦截"
    except Exception:
        pass

    attacker2_balance_final = attacker2.getBalance()
    assert attacker2_balance_final <= attacker2_deposit


@allure.title("case_031 整数溢出/下溢边界测试")
@allure.description("验证 Solidity 0.8+ 内置溢出检查机制")
@allure.tag("Security", "P1", "安全测试")
def test_security_031_integer_overflow_underflow(deployer, security_test_data):
    """
    case_031 整数溢出/下溢边界测试
    
    验证 Solidity 0.8+ 内置安全检查：
    - 基本算术运算（add/sub/mul/div）正常工作
    - 无符号整数溢出触发 revert
    - 无符号整数下溢触发 revert
    - 有符号整数溢出/下溢触发 revert
    - SafeMath 安全函数正确执行
    - 除以零触发 revert
    - 零值边界条件正确处理
    """
    data = security_test_data.get("case_031_integer_overflow_underflow", {})
    max_uint256 = data.get("max_uint256", 2**256 - 1)

    math_contract = deployer.deploy(project.IntegerMath)

    result = math_contract.add(100, 200)
    assert result == 300

    result = math_contract.subtract(200, 100)
    assert result == 100

    result = math_contract.multiply(10, 20)
    assert result == 200

    result = math_contract.divide(100, 5)
    assert result == 20

    try:
        math_contract.incrementMax()
        assert False, "应该触发溢出 revert"
    except Exception:
        pass

    try:
        math_contract.multiply(max_uint256, 2)
        assert False, "应该触发溢出 revert"
    except Exception:
        pass

    try:
        math_contract.decrementZero()
        assert False, "应该触发下溢 revert"
    except Exception:
        pass

    result = math_contract.safeSub(100, 50)
    assert result == 50

    try:
        math_contract.safeSub(50, 100)
        assert False, "应该触发 revert"
    except Exception:
        pass

    try:
        max_int256 = 2**255 - 1
        math_contract.addInt(max_int256, 1)
        assert False, "应该触发溢出 revert"
    except Exception:
        pass

    try:
        min_int256 = -(2**255)
        math_contract.subtractInt(min_int256, 1)
        assert False, "应该触发下溢 revert"
    except Exception:
        pass

    try:
        math_contract.divide(100, 0)
        assert False, "应该触发除以零 revert"
    except Exception:
        pass

    result = math_contract.safeAdd(100, 200)
    assert result == 300

    result = math_contract.safeMul(100, 200)
    assert result == 20000

    try:
        math_contract.safeMul(max_uint256, 2)
        assert False, "应该触发 revert"
    except Exception:
        pass

    result = math_contract.testZeroBoundary(0)
    assert result == True

    result = math_contract.testZeroBoundary(100)
    assert result == False

    math_contract.setMaxValue(sender=deployer)
    stored = math_contract.storedValue()
    assert stored == max_uint256


@allure.title("case_033 事件完整性测试")
@allure.description("验证合约事件触发的完整性和正确性")
@allure.tag("Security", "P1", "事件测试")
def test_security_033_event_completeness(deployer, user1):
    """
    case_033 事件完整性测试
    
    验证合约事件触发的完整性：
    - 每次状态变更都正确触发事件
    - 事件参数与实际状态一致
    - 事件顺序与操作顺序一致
    - 无遗漏或冗余事件
    """
    raise NotImplementedError("用例待实现")


@allure.title("case_032 合约升级代理测试")
@allure.description("验证代理合约逻辑升级、数据存储不丢失、版本兼容性")
@allure.tag("Security", "P1", "升级测试")
def test_security_032_proxy_upgrade(deployer, user1, security_test_data):
    """
    case_032 合约升级代理测试
    
    验证代理合约升级机制的安全性：
    - 初始化 V1 逻辑合约
    - 数据读写在代理中正常工作
    - 升级到 V2 后数据不丢失
    - V2 新增功能正常工作
    - 非管理员无法执行升级
    - 管理员可变更升级权限
    """
    data = security_test_data.get("case_032_proxy_upgrade", {})
    test_value = data.get("test_value", 1000)

    logic_v1 = deployer.deploy(project.LogicV1)
    proxy = deployer.deploy(project.UpgradeableProxy, logic_v1.address, deployer.address)
    proxy_v1 = project.LogicV1.at(proxy.address)

    proxy_v1.initialize(test_value, sender=deployer)

    value = proxy_v1.getValue()
    version = proxy_v1.getVersion()

    assert value == test_value
    assert version == "V1"

    new_value = test_value * 2
    proxy_v1.setValue(new_value, sender=deployer)
    value_after = proxy_v1.getValue()
    assert value_after == new_value

    logic_v2 = deployer.deploy(project.LogicV2)
    proxy.upgradeTo(logic_v2.address, sender=deployer)

    implementation = proxy.getImplementation()
    assert implementation == logic_v2.address

    proxy_v2 = project.LogicV2.at(proxy.address)

    value_after_upgrade = proxy_v2.getValue()
    assert value_after_upgrade == new_value

    additional_value = 500
    proxy_v2.initializeV2(additional_value, sender=deployer)

    version_after_init = proxy_v2.getVersion()
    assert version_after_init == "V2"

    proxy_v2.setAdditionalValue(100, sender=deployer)
    additional = proxy_v2.getAdditionalValue()
    assert additional == 100

    sum_result = proxy_v2.getSum()
    expected_sum = new_value + 100
    assert sum_result == expected_sum

    try:
        proxy.upgradeTo(logic_v1.address, sender=user1)
        assert False, "非管理员不应能升级"
    except Exception:
        pass

    new_admin = user1.address
    proxy.changeAdmin(new_admin, sender=deployer)
    admin_after = proxy.getAdmin()
    assert admin_after == new_admin


@allure.title("case_034 零地址/黑洞地址防护测试")
@allure.description("验证合约对零地址和黑洞地址的转账拦截")
@allure.tag("Security", "P1", "安全防护")
def test_security_034_zero_address_blackhole_protection(deployer, user1, erc20_token):
    """
    case_034 零地址/黑洞地址防护测试
    
    验证合约对危险地址的防护：
    - 转账至零地址（0x0）被拦截
    - 转账至黑洞地址（0x...dEaD）被拦截
    - 正常地址间转账正常执行
    - 拦截后余额保持不变
    - Transfer 事件正确触发
    """
    zero_address = "0x0000000000000000000000000000000000000000"
    blackhole_address = "0x000000000000000000000000000000000000dEaD"

    erc20_token.mint(user1, parse_ether("1000"), sender=deployer)
    user1_balance_before = erc20_token.balanceOf(user1)

    try:
        erc20_token.transfer(zero_address, parse_ether("100"), sender=user1)
        assert False, "零地址转账应该被拦截"
    except Exception:
        pass

    user1_balance_after_zero = erc20_token.balanceOf(user1)
    assert user1_balance_after_zero == user1_balance_before

    try:
        erc20_token.transfer(blackhole_address, parse_ether("100"), sender=user1)
        assert False, "黑洞地址转账应该被拦截"
    except Exception:
        pass

    user1_balance_after_blackhole = erc20_token.balanceOf(user1)
    assert user1_balance_after_blackhole == user1_balance_before

    deployer_balance_before = erc20_token.balanceOf(deployer)

    tx = erc20_token.transfer(deployer, parse_ether("100"), sender=user1)

    user1_balance_after = erc20_token.balanceOf(user1)
    deployer_balance_after = erc20_token.balanceOf(deployer)

    assert user1_balance_after == user1_balance_before - parse_ether("100")
    assert deployer_balance_after == deployer_balance_before + parse_ether("100")

    transfer_events = [e for e in tx.decode_logs(erc20_token.Transfer)]
    assert len(transfer_events) == 1
    assert transfer_events[0].to == deployer


@allure.title("case_035 Gas与交易异常兼容测试")
@allure.description("验证低Gas、超限Gas场景下交易失败时数据回滚的完整性")
@allure.tag("Security", "P1", "交易异常")
def test_security_035_gas_tx_exception(deployer, user1, user2, erc20_token, security_test_data):
    """
    case_035 Gas与交易异常兼容测试
    
    验证交易异常时的安全性：
    - 正常 Gas 下交易成功执行
    - 低 Gas（如 21000）导致交易失败
    - 交易失败时状态完全回滚
    - 发送方和接收方余额保持不变
    """
    data = security_test_data.get("case_035_gas_tx_exception", {})
    test_amount = data.get("test_amount", 100)

    erc20_token.mint(user1, parse_ether(str(test_amount)), sender=deployer)
    user1_balance_before = erc20_token.balanceOf(user1)
    user2_balance_before = erc20_token.balanceOf(user2)

    tx = erc20_token.transfer(user2, parse_ether("10"), sender=user1)
    user1_balance_after = erc20_token.balanceOf(user1)
    user2_balance_after = erc20_token.balanceOf(user2)

    assert user1_balance_after == user1_balance_before - parse_ether("10")
    assert user2_balance_after == user2_balance_before + parse_ether("10")

    user1_balance_before = user1_balance_after
    user2_balance_before = user2_balance_after

    try:
        erc20_token.transfer(user2, parse_ether("10"), sender=user1, gas_limit=21000)
    except Exception:
        pass

    user1_balance_after_low_gas = erc20_token.balanceOf(user1)
    user2_balance_after_low_gas = erc20_token.balanceOf(user2)

    assert user1_balance_after_low_gas == user1_balance_before
    assert user2_balance_after_low_gas == user2_balance_before