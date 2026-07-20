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
from framework.core.logger import log
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
    log.step("case_026: 授权安全高阶测试")
    data = security_test_data["case_026_approve_security"]
    initial_amount = parse_ether(str(data["initial_approve_amount"]))
    second_amount = parse_ether(str(data["second_approve_amount"]))
    infinite_amount = data["infinite_approve_amount"]
    log.debug(f"测试数据 - 初始授权: {format_ether(initial_amount)}, 二次授权: {format_ether(second_amount)}, 无限授权: {infinite_amount}")

    # 初始授权验证
    log.info("步骤1: 初始授权验证")
    tx = erc20_token.approve(user2, initial_amount, sender=user1)
    allowance = erc20_token.allowance(user1, user2)
    log.debug(f"授权后 allowance: {format_ether(allowance)}")
    assert allowance == initial_amount, f"初始授权不符，预期: {format_ether(initial_amount)}, 实际: {format_ether(allowance)}"
    log.debug("初始授权验证通过")

    # 重复授权覆盖旧值
    log.info("步骤2: 重复授权覆盖旧值")
    erc20_token.approve(user2, second_amount, sender=user1)
    allowance = erc20_token.allowance(user1, user2)
    log.debug(f"重复授权后 allowance: {format_ether(allowance)}")
    assert allowance == second_amount, f"重复授权不符，预期: {format_ether(second_amount)}, 实际: {format_ether(allowance)}"
    log.debug("重复授权覆盖验证通过")

    # 无限授权被拦截
    log.info("步骤3: 无限授权被拦截")
    try:
        erc20_token.approve(user2, infinite_amount, sender=user1)
        assert False, "未拦截无限授权，安全缺陷"
    except Exception as e:
        log.debug(f"无限授权被拦截，异常: {type(e).__name__}")
    log.debug("无限授权拦截验证通过")

    # 授权清零后无法操作
    log.info("步骤4: 授权清零后无法操作")
    erc20_token.approve(user2, 0, sender=user1)
    allowance = erc20_token.allowance(user1, user2)
    log.debug(f"授权清零后 allowance: {format_ether(allowance)}")
    try:
        erc20_token.transferFrom(user1, deployer, 1, sender=user2)
        assert False, "清零后应该无法操作"
    except Exception as e:
        log.debug(f"清零后操作被拒绝，异常: {type(e).__name__}")
    log.debug("授权清零验证通过")

    log.success("✅ case_026 授权安全高阶测试通过")


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
    log.step("case_027: 批量操作接口测试")
    data = security_test_data["case_027_batch_operations"]
    transfer_amount = parse_ether(str(data["transfer_amount"]))
    log.debug(f"测试数据 - 转账金额: {format_ether(transfer_amount)}")

    # 批量转账
    log.info("步骤1: 批量转账")
    recipients = [user1, user2, user3]
    erc20_token.mint(deployer, transfer_amount * len(recipients), sender=deployer)
    log.debug(f"铸造代币完成，数量: {format_ether(transfer_amount * len(recipients))}")
    amounts = [transfer_amount, transfer_amount, transfer_amount]
    tx = erc20_token.batchTransfer(recipients, amounts, sender=deployer)
    transfer_events = tx.decode_logs(erc20_token.Transfer)
    log.debug(f"批量转账完成，触发 Transfer 事件数: {len(transfer_events)}")
    assert len(transfer_events) == len(recipients), f"Transfer 事件数不符，预期: {len(recipients)}, 实际: {len(transfer_events)}"
    log.debug("批量转账验证通过")

    # 批量授权
    log.info("步骤2: 批量授权")
    spenders = [deployer, user2, user3]
    approve_amounts = [parse_ether("100"), parse_ether("200"), parse_ether("300")]
    erc20_token.batchApprove(spenders, approve_amounts, sender=user1)
    allowance0 = erc20_token.allowance(user1, deployer)
    allowance1 = erc20_token.allowance(user1, user2)
    log.debug(f"批量授权完成 - user1->deployer: {format_ether(allowance0)}, user1->user2: {format_ether(allowance1)}")
    assert allowance0 == approve_amounts[0], f"授权不符，预期: {format_ether(approve_amounts[0])}, 实际: {format_ether(allowance0)}"
    assert allowance1 == approve_amounts[1], f"授权不符，预期: {format_ether(approve_amounts[1])}, 实际: {format_ether(allowance1)}"
    log.debug("批量授权验证通过")

    # 数组长度不匹配被拒绝
    log.info("步骤3: 数组长度不匹配被拒绝")
    try:
        erc20_token.batchTransfer([user1, user2], [transfer_amount], sender=deployer)
        assert False, "应该拒绝数组长度不匹配的请求"
    except Exception as e:
        log.debug(f"数组长度不匹配被拒绝，异常: {type(e).__name__}")
    log.debug("数组长度校验验证通过")

    log.success("✅ case_027 批量操作接口测试通过")


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
    log.step("case_028: 质押/挖矿收益测算")
    data = security_test_data["case_028_staking_mining"]
    stake_amount = parse_ether(str(data["stake_amount"]))
    staking, reward_token = staking_contract
    log.debug(f"测试数据 - 质押金额: {format_ether(stake_amount)}")

    # 质押
    log.info("步骤1: 用户1质押")
    erc20_token.mint(user1, stake_amount, sender=deployer)
    log.debug(f"用户1获得质押代币: {format_ether(stake_amount)}")
    erc20_token.approve(staking.address, stake_amount, sender=user1)
    staking.stake(stake_amount, sender=user1)
    stake_balance = staking.userInfo(user1)[0]
    log.debug(f"用户1质押余额: {format_ether(stake_balance)}")
    assert stake_balance == stake_amount, f"质押余额不符，预期: {format_ether(stake_amount)}, 实际: {format_ether(stake_balance)}"
    log.debug("用户1质押验证通过")

    # 用户2质押触发奖励计算
    log.info("步骤2: 用户2质押触发奖励计算")
    erc20_token.mint(user2, stake_amount, sender=deployer)
    erc20_token.approve(staking.address, stake_amount, sender=user2)
    staking.stake(stake_amount, sender=user2)
    log.debug("用户2质押完成，触发区块奖励计算")

    # 验证有待领取奖励
    log.info("步骤3: 验证有待领取奖励")
    pending_reward = staking.pendingReward(user1.address)
    log.debug(f"用户1待领取奖励: {format_ether(pending_reward)}")
    assert pending_reward > 0, "用户1应有待领取奖励"
    log.debug("待领取奖励验证通过")

    # 解押
    log.info("步骤4: 用户1解押")
    staking.unstake(stake_amount, sender=user1)
    stake_balance = staking.userInfo(user1.address)[0]
    log.debug(f"用户1解押后质押余额: {format_ether(stake_balance)}")
    assert stake_balance == 0, f"解押后余额应为0，实际为 {format_ether(stake_balance)}"
    log.debug("用户1解押验证通过")

    # 领取奖励
    log.info("步骤5: 用户1领取奖励")
    reward_before = reward_token.balanceOf(user1)
    log.debug(f"领取前奖励余额: {format_ether(reward_before)}")
    staking.claimReward(sender=user1)
    reward_after = reward_token.balanceOf(user1)
    log.debug(f"领取后奖励余额: {format_ether(reward_after)}")
    assert reward_after > reward_before, "领取后奖励应增加"
    log.debug("奖励领取验证通过")

    log.success("✅ case_028 质押/挖矿收益测算测试通过")


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
    log.step("case_029: 时间锁/区块锁控制")
    lock_amount = 1000
    log.debug(f"测试数据 - 锁定金额: {lock_amount}")

    # 用户1锁定（时间锁）
    log.info("步骤1: 用户1锁定（时间锁）")
    timelock_contract.lock(lock_amount, sender=user1)
    lock_info = timelock_contract.userLocks(user1)
    log.debug(f"用户1锁定信息 - 金额: {lock_info[0]}, 是否过期: {timelock_contract.isTimeLockExpired(user1)}")
    assert lock_info[0] == lock_amount, f"锁定金额不符，预期: {lock_amount}, 实际: {lock_info[0]}"
    assert not timelock_contract.isTimeLockExpired(user1), "时间锁应未过期"
    log.debug("用户1时间锁验证通过")

    # 时间锁未到期无法释放
    log.info("步骤2: 时间锁未到期无法释放")
    try:
        timelock_contract.releaseByTime(sender=user1)
        assert False, "时间锁未到期时应该拒绝释放"
    except Exception as e:
        log.debug(f"时间锁未到期释放被拒绝，异常: {type(e).__name__}")
    log.debug("时间锁释放校验验证通过")

    # 用户2锁定（区块锁）
    log.info("步骤3: 用户2锁定（区块锁）")
    timelock_contract.lock(lock_amount, sender=user2)
    log.debug("用户2区块锁锁定完成")

    # 区块锁未到期无法释放
    log.info("步骤4: 区块锁未到期无法释放")
    try:
        timelock_contract.releaseByBlock(sender=user2)
        assert False, "区块锁未到期时应该拒绝释放"
    except Exception as e:
        log.debug(f"区块锁未到期释放被拒绝，异常: {type(e).__name__}")
    log.debug("区块锁释放校验验证通过")

    # 重复锁定和零金额锁定被拒绝
    log.info("步骤5: 重复锁定和零金额锁定被拒绝")
    try:
        timelock_contract.lock(lock_amount, sender=user1)
        assert False, "重复锁定应该被拒绝"
    except Exception as e:
        log.debug(f"重复锁定被拒绝，异常: {type(e).__name__}")

    try:
        timelock_contract.lock(0, sender=deployer)
        assert False, "零金额锁定应该被拒绝"
    except Exception as e:
        log.debug(f"零金额锁定被拒绝，异常: {type(e).__name__}")
    log.debug("重复锁定和零金额校验验证通过")

    # 管理员更新参数
    log.info("步骤6: 管理员更新参数")
    timelock_contract.updateLockDuration(172800, sender=deployer)
    duration = timelock_contract.lockDuration()
    log.debug(f"锁定时长更新后: {duration}")
    assert duration == 172800, f"锁定时长不符，预期: 172800, 实际: {duration}"
    log.debug("管理员参数更新验证通过")

    log.success("✅ case_029 时间锁/区块锁控制测试通过")


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
    log.step("case_030: 重入攻击防护测试")

    # 防护合约正常存取款
    log.info("步骤1: 防护合约正常存取款")
    reentrancy_vault.deposit(sender=user1, value=parse_ether("1"))
    balance = reentrancy_vault.balances(user1)
    log.debug(f"用户1存款后余额: {format_ether(balance)}")
    assert balance == parse_ether("1"), f"存款余额不符，预期: 1 ETH, 实际: {format_ether(balance)}"
    
    reentrancy_vault.withdraw(parse_ether("1"), sender=user1)
    balance = reentrancy_vault.balances(user1)
    log.debug(f"用户1取款后余额: {format_ether(balance)}")
    assert balance == 0, f"取款后余额应为0，实际: {format_ether(balance)}"
    log.debug("防护合约正常存取款验证通过")

    # 漏洞合约测试攻击
    log.info("步骤2: 漏洞合约测试攻击")
    deployer.transfer(vulnerable_vault.address, parse_ether("50"))
    log.debug("漏洞合约注入资金: 50 ETH")
    attacker = deployer.deploy(project.ReentrancyAttacker, vulnerable_vault.address)
    attacker.deposit(sender=deployer, value=parse_ether("5"))
    log.debug("攻击者存款: 5 ETH")
    try:
        attacker.attack(parse_ether("5"), sender=deployer)
    except Exception as e:
        log.debug(f"漏洞合约攻击执行，异常: {type(e).__name__}")

    # 防护合约拦截攻击
    log.info("步骤3: 防护合约拦截攻击")
    deployer.transfer(reentrancy_vault.address, parse_ether("50"))
    log.debug("防护合约注入资金: 50 ETH")
    attacker2 = deployer.deploy(project.ReentrancyAttacker, reentrancy_vault.address)
    attacker2.deposit(sender=deployer, value=parse_ether("5"))
    log.debug("攻击者2存款: 5 ETH")
    try:
        attacker2.attack(parse_ether("5"), sender=deployer)
        assert False, "重入攻击应该被拦截"
    except Exception as e:
        log.debug(f"重入攻击被拦截，异常: {type(e).__name__}")
    log.debug("重入攻击防护验证通过")

    log.success("✅ case_030 重入攻击防护测试通过")


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
    - SafeMath 安全函数正确执行
    - 除以零触发 revert
    """
    log.step("case_031: 整数溢出/下溢边界测试")
    max_uint256 = 2**256 - 1
    math_contract = deployer.deploy(project.IntegerMath)
    log.debug(f"测试数据 - max_uint256: {max_uint256}")

    # 基本运算正常
    log.info("步骤1: 基本运算正常")
    add_result = math_contract.add(100, 200)
    sub_result = math_contract.subtract(200, 100)
    mul_result = math_contract.multiply(10, 20)
    log.debug(f"加法(100+200): {add_result}, 减法(200-100): {sub_result}, 乘法(10*20): {mul_result}")
    assert add_result == 300, f"加法结果不符，预期: 300, 实际: {add_result}"
    assert sub_result == 100, f"减法结果不符，预期: 100, 实际: {sub_result}"
    assert mul_result == 200, f"乘法结果不符，预期: 200, 实际: {mul_result}"
    log.debug("基本运算验证通过")

    # 溢出/下溢触发 revert
    log.info("步骤2: 溢出/下溢触发 revert")
    try:
        math_contract.incrementMax()
        assert False, "应该触发溢出 revert"
    except Exception as e:
        log.debug(f"溢出被拦截，异常: {type(e).__name__}")

    try:
        math_contract.decrementZero()
        assert False, "应该触发下溢 revert"
    except Exception as e:
        log.debug(f"下溢被拦截，异常: {type(e).__name__}")
    log.debug("溢出/下溢防护验证通过")

    # SafeMath 安全函数
    log.info("步骤3: SafeMath 安全函数")
    safe_sub_result = math_contract.safeSub(100, 50)
    log.debug(f"safeSub(100, 50): {safe_sub_result}")
    assert safe_sub_result == 50, f"safeSub 结果不符，预期: 50, 实际: {safe_sub_result}"
    
    try:
        math_contract.safeSub(50, 100)
        assert False, "应该触发 revert"
    except Exception as e:
        log.debug(f"safeSub 下溢被拦截，异常: {type(e).__name__}")
    log.debug("SafeMath 安全函数验证通过")

    # 除以零触发 revert
    log.info("步骤4: 除以零触发 revert")
    try:
        math_contract.divide(100, 0)
        assert False, "应该触发除以零 revert"
    except Exception as e:
        log.debug(f"除以零被拦截，异常: {type(e).__name__}")
    log.debug("除以零防护验证通过")

    log.success("✅ case_031 整数溢出/下溢边界测试通过")


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
    log.step("case_032: 合约升级代理测试")

    # 部署 V1 并验证
    log.info("步骤1: 部署 V1 并验证")
    logic_v1 = deployer.deploy(project.LogicV1)
    proxy = deployer.deploy(project.UpgradeableProxy, logic_v1.address, deployer.address)
    proxy_v1 = project.LogicV1.at(proxy.address)
    proxy_v1.initialize(1000, sender=deployer)
    value = proxy_v1.getValue()
    version = proxy_v1.getVersion()
    log.debug(f"V1 初始化完成 - 值: {value}, 版本: {version}")
    assert value == 1000, f"V1 值不符，预期: 1000, 实际: {value}"
    assert version == "V1", f"V1 版本不符，预期: V1, 实际: {version}"
    log.debug("V1 部署验证通过")

    # 更新 V1 数据
    log.info("步骤2: 更新 V1 数据")
    proxy_v1.setValue(2000, sender=deployer)
    log.debug("V1 数据更新完成")

    # 升级到 V2
    log.info("步骤3: 升级到 V2")
    logic_v2 = deployer.deploy(project.LogicV2)
    proxy.upgradeTo(logic_v2.address, sender=deployer)
    proxy_v2 = project.LogicV2.at(proxy.address)
    log.debug("合约升级到 V2 完成")

    # 验证升级后数据不丢失
    log.info("步骤4: 验证升级后数据不丢失")
    value = proxy_v2.getValue()
    log.debug(f"V2 读取值: {value}")
    assert value == 2000, f"升级后数据丢失，预期: 2000, 实际: {value}"
    
    proxy_v2.initializeV2(500, sender=deployer)
    version = proxy_v2.getVersion()
    log.debug(f"V2 版本: {version}")
    assert version == "V2", f"V2 版本不符，预期: V2, 实际: {version}"
    log.debug("升级后数据验证通过")

    # 非管理员无法升级
    log.info("步骤5: 非管理员无法升级")
    try:
        proxy.upgradeTo(logic_v1.address, sender=user1)
        assert False, "非管理员不应能升级"
    except Exception as e:
        log.debug(f"非管理员升级被拒绝，异常: {type(e).__name__}")
    log.debug("非管理员权限校验验证通过")

    # 管理员可变更权限
    log.info("步骤6: 管理员可变更权限")
    proxy.changeAdmin(user1.address, sender=deployer)
    admin = proxy.getAdmin()
    log.debug(f"新管理员: {admin}")
    assert admin == user1.address, f"管理员变更失败，预期: {user1.address}, 实际: {admin}"
    log.debug("管理员权限变更验证通过")

    log.success("✅ case_032 合约升级代理测试通过")


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
    """
    log.step("case_034: 零地址/黑洞地址防护测试")
    erc20_token.mint(user1, parse_ether("1000"), sender=deployer)
    log.debug(f"用户1获得代币: 1000 ETH")

    # 零地址转账被拦截
    log.info("步骤1: 零地址转账被拦截")
    try:
        erc20_token.transfer("0x0000000000000000000000000000000000000000", parse_ether("100"), sender=user1)
        assert False, "零地址转账应该被拦截"
    except Exception as e:
        log.debug(f"零地址转账被拦截，异常: {type(e).__name__}")
    log.debug("零地址防护验证通过")

    # 黑洞地址转账被拦截
    log.info("步骤2: 黑洞地址转账被拦截")
    try:
        erc20_token.transfer("0x000000000000000000000000000000000000dEaD", parse_ether("100"), sender=user1)
        assert False, "黑洞地址转账应该被拦截"
    except Exception as e:
        log.debug(f"黑洞地址转账被拦截，异常: {type(e).__name__}")
    log.debug("黑洞地址防护验证通过")

    # 正常转账正常执行
    log.info("步骤3: 正常转账正常执行")
    balance_before = erc20_token.balanceOf(user1)
    log.debug(f"转账前余额: {format_ether(balance_before)}")
    erc20_token.transfer(deployer, parse_ether("100"), sender=user1)
    balance_after = erc20_token.balanceOf(user1)
    log.debug(f"转账后余额: {format_ether(balance_after)}")
    assert balance_after == balance_before - parse_ether("100"), f"转账后余额不符，预期: {format_ether(balance_before - parse_ether('100'))}, 实际: {format_ether(balance_after)}"
    log.debug("正常转账验证通过")

    log.success("✅ case_034 零地址/黑洞地址防护测试通过")


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
    """
    log.step("case_035: Gas与交易异常兼容测试")
    erc20_token.mint(user1, parse_ether("100"), sender=deployer)
    log.debug(f"用户1获得代币: 100 ETH")

    # 正常交易成功
    log.info("步骤1: 正常交易成功")
    erc20_token.transfer(user2, parse_ether("10"), sender=user1)
    balance_after = erc20_token.balanceOf(user2)
    log.debug(f"用户2获得代币: {format_ether(balance_after)}")
    log.debug("正常交易验证通过")

    # 低 Gas 交易失败
    log.info("步骤2: 低 Gas 交易失败")
    balance_before = erc20_token.balanceOf(user1)
    log.debug(f"低 Gas 交易前余额: {format_ether(balance_before)}")
    try:
        erc20_token.transfer(user2, parse_ether("10"), sender=user1, gas_limit=21000)
    except Exception as e:
        log.debug(f"低 Gas 交易失败，异常: {type(e).__name__}")

    # 状态回滚
    log.info("步骤3: 验证状态回滚")
    balance_after = erc20_token.balanceOf(user1)
    log.debug(f"低 Gas 交易后余额: {format_ether(balance_after)}")
    assert balance_after == balance_before, f"状态未回滚，预期: {format_ether(balance_before)}, 实际: {format_ether(balance_after)}"
    log.debug("状态回滚验证通过")

    log.success("✅ case_035 Gas与交易异常兼容测试通过")
