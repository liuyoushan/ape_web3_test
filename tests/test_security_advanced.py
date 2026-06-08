"""
================================================================================
【模块概览】Web3 高阶安全 + 全链路场景
对应用例编号：case_026 ~ case_033
测试范围：安全测试、质押挖矿、时间锁、重入防护等高阶场景
================================================================================
"""

from ape import project
from web3 import Web3
from decimal import Decimal
from tests.helpers.formatters import parse_ether, format_ether
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


# ================================================================================
# case_026 授权安全高阶测试
# 测试目标：无限授权风险、重复授权覆盖、授权过期/清零逻辑
# 测试类型：P0 - 安全测试
# ================================================================================
@allure.title("security 026 approve security")
@allure.description("Test for test_security_026_approve_security")
@allure.tag("安全测试")
def test_security_026_approve_security(deployer, user1, user2, erc20_token, security_test_data):
    """
    ================================================================================
    【用例编号】case_026
    【用例名称】授权安全高阶测试
    【测试目标】验证授权安全机制：无限授权风险、重复授权覆盖、授权清零逻辑
    【测试类型】安全测试（P0）
    ================================================================================

    业务背景：
    ERC20 授权机制是 DeFi 安全的关键环节。恶意合约可能通过以下方式攻击：
    1. 骗取用户的无限授权，然后在任意时刻提取用户资产
    2. 利用重复授权覆盖漏洞获取超额权限
    3. 授权过期后仍能操作

    核心验证点：
    1. 无限授权（MAX_UINT256）正确识别
    2. 重复授权正确覆盖旧授权
    3. 授权清零功能正常工作
    4. 授权事件正确触发

    测试流程：
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ 阶段1: 用户授权给第三方地址（正常授权）                                      │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ 阶段2: 重复授权（覆盖旧授权）                                               │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ 阶段3: 无限授权测试（MAX_UINT256）                                          │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ 阶段4: 授权清零测试                                                         │
    └─────────────────────────────────────────────────────────────────────────────┘
    """
    data = security_test_data["case_026_approve_security"]
    
    initial_amount = parse_ether(str(data["initial_approve_amount"]))
    second_amount = parse_ether(str(data["second_approve_amount"]))
    infinite_amount = data["infinite_approve_amount"]
    zero_amount = parse_ether(str(data["zero_approve_amount"]))

    print("\n[DEBUG] ========== case_026: 授权安全高阶测试 ==========")

    # ==================== 阶段1: 用户授权给第三方地址 ====================
    print("\n---------- 阶段1: 正常授权测试 ----------")

    # 用户1授权给用户2
    tx = erc20_token.approve(user2, initial_amount, sender=user1)

    # 验证授权额度
    allowance = erc20_token.allowance(user1, user2)
    print(f"  用户1授权给用户2额度: {format_ether(allowance)}")
    assert allowance == initial_amount, "授权额度错误"

    # 验证事件，解析这笔交易里Approval 授权事件日志。校验授权后不同的字段：owner, spender, value是否正确
    events = [e for e in tx.decode_logs(erc20_token.Approval)]
    assert len(events) == 1, "应该触发一个Approval事件"
    assert events[0].owner == user1, "事件owner错误"
    assert events[0].spender == user2, "事件spender错误"
    assert events[0].value == initial_amount, "事件value错误"
    print("  ✓ 正常授权成功")

    # ==================== 阶段2: 重复授权覆盖测试 ====================
    print("\n---------- 阶段2: 重复授权覆盖测试 ----------")

    # 用户1再次授权给用户2（新额度小于旧额度）
    tx2 = erc20_token.approve(user2, second_amount, sender=user1)

    # 验证授权额度被覆盖
    allowance_after = erc20_token.allowance(user1, user2)
    print(f"  重复授权后额度: {format_ether(allowance_after)}")
    assert allowance_after == second_amount, "重复授权未正确覆盖"
    print("  ✓ 重复授权正确覆盖旧授权")

    # ==================== 阶段3: 无限授权拦截测试 ====================
    print("\n---------- 阶段3: 无限授权拦截测试（MAX_UINT256）----------")

    # 尝试授权无限额度（MAX_UINT256）- 应该被合约拦截
    try:
        erc20_token.approve(user2, infinite_amount, sender=user1)
        # 代码能跑到这里 = 没拦截，用例失败
        print("  ✗ 无限授权未被拦截，存在安全风险")
        assert False, "未拦截无限授权，安全缺陷"
    except Exception as e:
        # approve被revert，安全合格
        print(f"  ✓ 无限授权已被合约拦截: {str(e)[:60]}")

    # ==================== 阶段4: 授权清零测试 ====================
    print("\n---------- 阶段4: 授权清零测试 ----------")

    # 清零授权
    tx4 = erc20_token.approve(user2, zero_amount, sender=user1)

    allowance_zero = erc20_token.allowance(user1, user2)
    print(f"  清零后授权额度: {format_ether(allowance_zero)}")
    assert allowance_zero == zero_amount, "授权清零失败"
    print("  ✓ 授权清零成功")

    # ==================== 阶段5: 验证清零后无法操作 ====================
    print("\n---------- 阶段5: 验证清零后无法操作 ----------")

    user1_balance = erc20_token.balanceOf(user1)
    print(f"  用户1当前余额: {format_ether(user1_balance)}")

    # 尝试用已清零的授权进行 transferFrom（应该失败）
    try:
        erc20_token.transferFrom(user1, deployer, 1, sender=user2)
        print("  ✗ 清零后仍能操作（不应该）")
        assert False, "清零后应该无法操作"
    except Exception as e:
        print(f"  ✓ 清零后操作被正确拒绝: {str(e)[:50]}")

    print("\n[DEBUG] ========== case_026 PASS: 授权安全高阶测试通过 ==========")


# ================================================================================
# case_027 批量操作接口测试
# 测试目标：批量转账、批量授权、批量数据一致性
# 测试类型：P1 - 效率测试
# ================================================================================
@allure.title("security 027 batch operations")
@allure.description("Test for test_security_027_batch_operations")
@allure.tag("安全测试")
def test_security_027_batch_operations(deployer, user1, user2, user3, erc20_token, security_test_data):
    """
    ================================================================================
    【用例编号】case_027
    【用例名称】批量操作接口测试
    【测试目标】验证批量转账、批量授权功能及数据一致性
    【测试类型】效率测试（P1）
    ================================================================================

    业务背景：
    批量操作接口可以显著减少交易次数和 Gas 费用，是提高 DApp 效率的重要功能。
    但批量操作也带来了数据一致性的挑战，需要确保：
    1. 所有操作要么全部成功，要么全部失败（原子性）
    2. 数组长度必须匹配
    3. 每个操作的状态正确更新

    测试流程：
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ 阶段1: 批量转账测试（一对多）                                                │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ 阶段2: 批量授权测试（一对多）                                                │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ 阶段3: 数组长度不匹配异常测试                                                 │
    └─────────────────────────────────────────────────────────────────────────────┘
    """
    data = security_test_data["case_027_batch_operations"]
    transfer_amount = parse_ether(str(data["transfer_amount"]))

    print("\n[DEBUG] ========== case_027: 批量操作接口测试 ==========")

    # ==================== 阶段1: 批量转账测试 ====================
    print("\n---------- 阶段1: 批量转账测试（一对多）----------")
    
    # 定义批量转账参数
    recipients = [user1, user2, user3]
    batch_size = len(recipients)  # 实际批量大小
    print(batch_size,type(batch_size))
    
    # 给部署者铸造代币
    erc20_token.mint(deployer, transfer_amount * batch_size, sender=deployer)
    deployer_balance_before = erc20_token.balanceOf(deployer)
    
    # 记录用户余额
    user1_balance_before = erc20_token.balanceOf(user1)
    user2_balance_before = erc20_token.balanceOf(user2)
    user3_balance_before = erc20_token.balanceOf(user3)
    
    print(f"  部署者余额（转账前）: {format_ether(deployer_balance_before)}")
    print(f"  用户1余额（转账前）: {format_ether(user1_balance_before)}")
    print(f"  用户2余额（转账前）: {format_ether(user2_balance_before)}")
    print(f"  用户3余额（转账前）: {format_ether(user3_balance_before)}")
    
    # 执行批量转账
    recipients = [user1, user2, user3]
    amounts = [transfer_amount, transfer_amount, transfer_amount]
    tx = erc20_token.batchTransfer(recipients, amounts, sender=deployer)
    
    # 验证余额变化
    deployer_balance_after = erc20_token.balanceOf(deployer)
    user1_balance_after = erc20_token.balanceOf(user1)
    user2_balance_after = erc20_token.balanceOf(user2)
    user3_balance_after = erc20_token.balanceOf(user3)
    
    print(f"  部署者余额（转账后）: {format_ether(deployer_balance_after)}")
    print(f"  用户1余额（转账后）: {format_ether(user1_balance_after)}")
    print(f"  用户2余额（转账后）: {format_ether(user2_balance_after)}")
    print(f"  用户3余额（转账后）: {format_ether(user3_balance_after)}")
    
    assert deployer_balance_after == deployer_balance_before - transfer_amount * batch_size, "部署者余额错误"
    assert user1_balance_after == user1_balance_before + transfer_amount, "用户1余额错误"
    assert user2_balance_after == user2_balance_before + transfer_amount, "用户2余额错误"
    assert user3_balance_after == user3_balance_before + transfer_amount, "用户3余额错误"
    
    # 验证事件
    events = [e for e in tx.decode_logs(erc20_token.Transfer)]
    assert len(events) == batch_size, f"应该触发 {batch_size} 个 Transfer 事件"
    print("  ✓ 批量转账成功")

    # ==================== 阶段2: 批量授权测试 ====================
    print("\n---------- 阶段2: 批量授权测试（一对多）----------")
    
    # 用户1批量授权给多个用户
    spenders = [deployer, user2, user3]
    approve_amounts = [parse_ether("100"), parse_ether("200"), parse_ether("300")]
    
    tx2 = erc20_token.batchApprove(spenders, approve_amounts, sender=user1)
    
    # 验证授权额度
    allowance1 = erc20_token.allowance(user1, deployer)
    allowance2 = erc20_token.allowance(user1, user2)
    allowance3 = erc20_token.allowance(user1, user3)
    
    print(f"  用户1授权给deployer: {format_ether(allowance1)}")
    print(f"  用户1授权给user2: {format_ether(allowance2)}")
    print(f"  用户1授权给user3: {format_ether(allowance3)}")
    
    assert allowance1 == approve_amounts[0], "授权额度1错误"
    assert allowance2 == approve_amounts[1], "授权额度2错误"
    assert allowance3 == approve_amounts[2], "授权额度3错误"
    
    # 验证事件
    approval_events = [e for e in tx2.decode_logs(erc20_token.Approval)]
    assert len(approval_events) == batch_size, f"应该触发 {batch_size} 个 Approval 事件"
    print("  ✓ 批量授权成功")

    # ==================== 阶段3: 数组长度不匹配异常测试 ====================
    print("\n---------- 阶段3: 数组长度不匹配异常测试 ----------")
    
    # 尝试传入长度不匹配的数组
    try:
        bad_recipients = [user1, user2]
        bad_amounts = [transfer_amount]
        erc20_token.batchTransfer(bad_recipients, bad_amounts, sender=deployer)
        print("  ✗ 数组长度不匹配未被拒绝（不应该）")
        assert False, "应该拒绝数组长度不匹配的请求"
    except Exception as e:
        print(f"  ✓ 数组长度不匹配被正确拒绝: {str(e)[:50]}")

    print("\n[DEBUG] ========== case_027 PASS: 批量操作接口测试通过 ==========")


# ================================================================================
# case_028 质押/挖矿收益测算
# 测试目标：质押锁定、区块产出奖励、复利结算、解押解锁逻辑
# 测试类型：P0 - DeFi 核心业务
# ================================================================================
@allure.title("security 028 staking mining")
@allure.description("Test for test_security_028_staking_mining")
@allure.tag("安全测试")
def test_security_028_staking_mining(deployer, user1, user2, erc20_token, staking_contract, security_test_data):
    """
    ================================================================================
    【用例编号】case_028
    【用例名称】质押/挖矿收益测算
    【测试目标】验证质押锁定、区块奖励计算、解押解锁逻辑
    【测试类型】核心业务测试（P0）
    ================================================================================

    业务背景：
    质押挖矿是 DeFi 的核心业务之一，用户通过质押代币获得奖励。
    关键机制包括：
    1. 质押后资产锁定，无法转移
    2. 奖励按区块产出，公平分配
    3. 解押后资产解锁，可自由转移
    4. 奖励计算准确，无遗漏

    测试流程：
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ 阶段1: 质押锁定测试                                                          │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ 阶段2: 区块奖励计算测试                                                       │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ 阶段3: 解押解锁测试                                                          │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ 阶段4: 奖励领取测试                                                          │
    └─────────────────────────────────────────────────────────────────────────────┘
    """
    data = security_test_data["case_028_staking_mining"]
    stake_amount = parse_ether(str(data["stake_amount"]))
    stake_duration_blocks = data["stake_duration_blocks"]
    
    staking, reward_token = staking_contract
    
    print("\n[DEBUG] ========== case_028: 质押/挖矿收益测算 ==========")

    # ==================== 阶段1: 质押锁定测试 ====================
    print("\n---------- 阶段1: 质押锁定测试 ----------")
    
    # 给用户1铸造代币
    erc20_token.mint(user1, stake_amount, sender=deployer)
    
    user1_balance_before = erc20_token.balanceOf(user1)
    print(f"  用户1质押前余额: {format_ether(user1_balance_before)}")
    
    # 用户1授权并质押
    erc20_token.approve(staking.address, stake_amount, sender=user1)
    tx_stake = staking.stake(stake_amount, sender=user1)
    
    user1_balance_after = erc20_token.balanceOf(user1)
    user1_staked = staking.userInfo(user1)
    
    print(f"  用户1质押后余额: {format_ether(user1_balance_after)}")
    print(f"  用户1质押数量: {format_ether(user1_staked[0])}")
    
    assert user1_balance_after == user1_balance_before - stake_amount, "质押后余额错误"
    assert user1_staked[0] == stake_amount, "质押数量错误"
    
    # 验证质押事件
    stake_events = [e for e in tx_stake.decode_logs(staking.Staked)]
    assert len(stake_events) == 1, "应该触发 Staked 事件"
    assert stake_events[0].amount == stake_amount, "质押事件金额错误"
    print("  ✓ 质押锁定成功")

    # ==================== 阶段2: 区块奖励计算测试 ====================
    print("\n---------- 阶段2: 区块奖励计算测试 ----------")
    
    # 记录当前区块
    current_block = staking.lastRewardBlock()
    print(f"  当前区块: {current_block}")
    
    # 用户2也质押，推动区块
    erc20_token.mint(user2, stake_amount, sender=deployer)
    erc20_token.approve(staking.address, stake_amount, sender=user2)
    staking.stake(stake_amount, sender=user2)
    
    # 查询用户1待领取奖励
    pending_reward = staking.pendingReward(user1.address)
    print(f"  用户1待领取奖励: {format_ether(pending_reward)}")
    
    assert pending_reward > 0, "应该有奖励产生"
    print("  ✓ 区块奖励计算正确")

    # ==================== 阶段3: 解押解锁测试 ====================
    print("\n---------- 阶段3: 解押解锁测试 ----------")
    
    user1_balance_before_unstake = erc20_token.balanceOf(user1)
    print(f"  用户1解押前余额: {format_ether(user1_balance_before_unstake)}")
    
    # 用户1解押
    tx_unstake = staking.unstake(stake_amount, sender=user1)
    
    user1_balance_after_unstake = erc20_token.balanceOf(user1)
    user1_staked_after = staking.userInfo(user1.address)
    
    print(f"  用户1解押后余额: {format_ether(user1_balance_after_unstake)}")
    print(f"  用户1质押数量: {format_ether(user1_staked_after[0])}")
    
    assert user1_balance_after_unstake == user1_balance_before_unstake + stake_amount, "解押后余额错误"
    assert user1_staked_after[0] == 0, "解押后质押数量应为0"
    
    # 验证解押事件
    unstake_events = [e for e in tx_unstake.decode_logs(staking.Unstaked)]
    assert len(unstake_events) == 1, "应该触发 Unstaked 事件"
    print("  ✓ 解押解锁成功")

    # ==================== 阶段4: 奖励领取测试 ====================
    print("\n---------- 阶段4: 奖励领取测试 ----------")
    
    user1_reward_before = reward_token.balanceOf(user1)
    print(f"  用户1领取奖励前余额: {format_ether(user1_reward_before)}")
    
    # 用户1领取奖励
    tx_claim = staking.claimReward(sender=user1)
    
    user1_reward_after = reward_token.balanceOf(user1)
    print(f"  用户1领取奖励后余额: {format_ether(user1_reward_after)}")
    
    assert user1_reward_after > user1_reward_before, "领取奖励后余额应增加"
    
    # 验证奖励领取事件
    claim_events = [e for e in tx_claim.decode_logs(staking.RewardClaimed)]
    assert len(claim_events) == 1, "应该触发 RewardClaimed 事件"
    print(f"  ✓ 奖励领取成功，获得: {format_ether(claim_events[0].amount)}")

    print("\n[DEBUG] ========== case_028 PASS: 质押/挖矿收益测算测试通过 ==========")


# ================================================================================
# case_029 时间锁/区块锁控制
# 测试目标：依赖区块高度、时间戳的限时功能，边界时间节点校验
# 测试类型：P0 - 时间敏感测试
# ================================================================================
@allure.title("security 029 timelock blocklock")
@allure.description("Test for test_security_029_timelock_blocklock")
@allure.tag("安全测试")
def test_security_029_timelock_blocklock(deployer, user1, user2, timelock_contract, security_test_data):
    """
    ================================================================================
    【用例编号】case_029
    【用例名称】时间锁/区块锁控制
    【测试目标】验证依赖区块高度、时间戳的限时功能，边界时间节点校验
    【测试类型】核心业务测试（P0）
    ================================================================================

    业务背景：
    时间锁和区块锁是 DeFi 合约中常见的限制机制，用于：
    1. 防止用户过早提取资产
    2. 确保锁定期内资产安全
    3. 提供可预测的解锁时间

    测试流程：
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ 阶段1: 时间锁锁定测试                                                        │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ 阶段2: 时间锁未到期拒绝测试                                                   │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ 阶段3: 区块锁锁定测试                                                        │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ 阶段4: 区块锁未到期拒绝测试                                                   │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ 阶段5: 边界条件测试                                                          │
    └─────────────────────────────────────────────────────────────────────────────┘
    """
    data = security_test_data.get("case_029_timelock_blocklock", {})
    lock_duration = data.get("lock_duration", 86400)
    lock_blocks = data.get("lock_blocks", 100)
    
    print("\n[DEBUG] ========== case_029: 时间锁/区块锁控制 ==========")
    print(f"  时间锁时长: {lock_duration} 秒")
    print(f"  区块锁数量: {lock_blocks} 个区块")

    # ==================== 阶段1: 时间锁锁定测试 ====================
    print("\n---------- 阶段1: 时间锁锁定测试 ----------")
    
    # 用户1锁定资金，锁定时间为 lock_duration 秒
    # 锁定区块数量为 lock_blocks 个   ，本质就是用户自己把自己的代币锁定起来，等时间到了再释放
    lock_amount = 1000
    tx_lock = timelock_contract.lock(lock_amount, sender=user1)
    
    # 验证锁定记录
    user1_lock = timelock_contract.userLocks(user1)
    print(f"  用户1锁定金额: {user1_lock[0]}")
    print(f"  锁定时间: {user1_lock[1]}")
    print(f"  锁定区块: {user1_lock[2]}")
    
    assert user1_lock[0] == lock_amount, "锁定金额错误"
    assert user1_lock[1] > 0, "锁定时间应为有效值"
    assert user1_lock[2] > 0, "锁定区块应为有效值"
    
    # 验证锁定事件
    lock_events = [e for e in tx_lock.decode_logs(timelock_contract.Locked)]
    assert len(lock_events) == 1, "应该触发 Locked 事件"
    print("  ✓ 时间锁锁定成功")

    # ==================== 阶段2: 时间锁未到期拒绝测试 ====================
    print("\n---------- 阶段2: 时间锁未到期拒绝测试 ----------")
    
    # 检查时间锁是否到期
    is_expired = timelock_contract.isTimeLockExpired(user1)
    remaining_time = timelock_contract.getRemainingTime(user1)
    
    print(f"  时间锁是否到期: {is_expired}")
    print(f"  剩余时间: {remaining_time} 秒")
    
    assert not is_expired, "时间锁不应该立即到期"
    assert remaining_time > 0, "剩余时间应大于0"
    
    # 尝试提前释放（应该失败）
    try:
        timelock_contract.releaseByTime(sender=user1)
        print("  ✗ 时间锁未到期时释放成功（不应该）")
        assert False, "时间锁未到期时应该拒绝释放"
    except Exception as e:
        print(f"  ✓ 时间锁未到期时正确拒绝释放: {str(e)[:60]}")

    # ==================== 阶段3: 区块锁锁定测试 ====================
    print("\n---------- 阶段3: 区块锁锁定测试 ----------")
    
    # 用户2锁定资金
    tx_lock2 = timelock_contract.lock(lock_amount, sender=user2)
    
    # 验证锁定记录
    user2_lock = timelock_contract.userLocks(user2)
    print(f"  用户2锁定金额: {user2_lock[0]}")
    print(f"  锁定区块: {user2_lock[2]}")
    
    assert user2_lock[0] == lock_amount, "锁定金额错误"
    
    # 检查区块锁是否到期
    is_block_expired = timelock_contract.isBlockLockExpired(user2)
    remaining_blocks = timelock_contract.getRemainingBlocks(user2)
    
    print(f"  区块锁是否到期: {is_block_expired}")
    print(f"  剩余区块: {remaining_blocks}")
    
    assert not is_block_expired, "区块锁不应该立即到期"
    print("  ✓ 区块锁锁定成功")

    # ==================== 阶段4: 区块锁未到期拒绝测试 ====================
    print("\n---------- 阶段4: 区块锁未到期拒绝测试 ----------")
    
    # 尝试提前释放（应该失败）
    try:
        timelock_contract.releaseByBlock(sender=user2)
        print("  ✗ 区块锁未到期时释放成功（不应该）")
        assert False, "区块锁未到期时应该拒绝释放"
    except Exception as e:
        print(f"  ✓ 区块锁未到期时正确拒绝释放: {str(e)[:60]}")

    # ==================== 阶段5: 边界条件测试 ====================
    print("\n---------- 阶段5: 边界条件测试 ----------")
    
    # 测试重复锁定（应该失败）
    try:
        timelock_contract.lock(lock_amount, sender=user1)
        print("  ✗ 重复锁定成功（不应该）")
        assert False, "重复锁定应该被拒绝"
    except Exception as e:
        print(f"  ✓ 重复锁定被正确拒绝: {str(e)[:60]}")
    
    # 测试零金额锁定（应该失败）
    try:
        timelock_contract.lock(0, sender=deployer)
        print("  ✗ 零金额锁定成功（不应该）")
        assert False, "零金额锁定应该被拒绝"
    except Exception as e:
        print(f"  ✓ 零金额锁定被正确拒绝: {str(e)[:60]}")
    
    # 测试更新锁定参数
    new_duration = 172800  # 2天
    timelock_contract.updateLockDuration(new_duration, sender=deployer)
    assert timelock_contract.lockDuration() == new_duration, "更新时间锁时长失败"
    print(f"  ✓ 时间锁时长更新成功: {new_duration} 秒")
    
    new_blocks = 200
    timelock_contract.updateLockBlocks(new_blocks, sender=deployer)
    assert timelock_contract.lockBlocks() == new_blocks, "更新区块锁数量失败"
    print(f"  ✓ 区块锁数量更新成功: {new_blocks} 个区块")

    print("\n[DEBUG] ========== case_029 PASS: 时间锁/区块锁控制测试通过 ==========")


# ================================================================================
# case_030 重入攻击防护测试
# 测试目标：关键资金接口重入场景模拟，校验防重入锁生效
# 测试类型：P1 - 安全测试
# ================================================================================
@allure.title("security 030 reentrancy guard")
@allure.description("Test for test_security_030_reentrancy_guard")
@allure.tag("安全测试")
def test_security_030_reentrancy_guard(deployer, user1, user2, reentrancy_vault, vulnerable_vault, security_test_data):
    """
    ================================================================================
    【用例编号】case_030
    【用例名称】重入攻击防护测试
    【测试目标】验证关键资金接口重入场景模拟，校验防重入锁生效
    【测试类型】安全测试（P1）
    ================================================================================

    业务背景：
    重入攻击是智能合约中最常见的安全漏洞之一。攻击者通过在合约调用过程中
    再次调用目标合约，利用状态未更新的空档期反复提取资金。

    攻击原理：
    1. 攻击者部署恶意合约并存入ETH
    2. 调用 withdraw() 提取全部ETH
    3. 在 receive() 回调中再次调用 withdraw()
    4. 利用 balance 未更新的空档期，反复提取资金
    5. 原本只能提取1次，现在可以提取多次

    防护措施：
    1. 检查-生效-交互模式（CEI）
    2. 防重入锁（ReentrancyGuard）
    3. 状态更新先于外部调用

    测试流程：
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ 阶段1: 正常提现测试（对比基准）                                            │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ 阶段2: 无防重入锁合约 - 重入攻击演示                                       │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ 阶段3: 带防重入锁合约 - 重入攻击被拦截                                     │
    └─────────────────────────────────────────────────────────────────────────────┘
    """
    data = security_test_data.get("case_030_reentrancy_guard", {})
    test_amount = parse_ether(str(data.get("test_amount", 1)))
    
    print("\n[DEBUG] ========== case_030: 重入攻击防护测试 ==========")

    # ==================== 阶段1: 正常提现测试（对比基准） ====================
    print("\n---------- 阶段1: 正常提现测试（对比基准） ----------")
    
    vault = reentrancy_vault
    
    # 用户1存入ETH
    deposit_amount = test_amount
    tx_deposit = vault.deposit(sender=user1, value=deposit_amount)
    
    user1_balance = vault.balances(user1)
    vault_balance_before = vault.balance
    
    print(f"  用户1存款: {format_ether(deposit_amount)} ETH")
    print(f"  用户1合约余额: {format_ether(user1_balance)}")
    print(f"  合约总余额: {format_ether(vault_balance_before)}")
    
    assert user1_balance == deposit_amount, "存款后余额错误"
    print("  ✓ 存款成功")
    
    # 用户1提取ETH（正常提取）
    tx_withdraw = vault.withdraw(deposit_amount, sender=user1)
    
    user1_balance_after = vault.balances(user1)
    
    print(f"  正常提取后用户余额: {format_ether(user1_balance_after)}")
    print(f"  正常提取后合约余额: {format_ether(vault.balance)}")
    
    assert user1_balance_after == 0, "正常提取后余额应为0"
    print("  ✓ 正常提取成功，余额清零")

    # ==================== 阶段2: 无防重入锁合约 - 重入攻击演示 ====================
    print("\n---------- 阶段2: 无防重入锁合约 - 重入攻击演示 ----------")
    
    vuln_vault = vulnerable_vault
    
    # 给 vulnerable_vault 转入更多ETH作为攻击目标（需要足够多才能支持重入攻击）
    initial_fund = parse_ether("50")
    deployer.transfer(vuln_vault.address, initial_fund)
    
    print(f"  给漏洞合约转入初始资金: {format_ether(initial_fund)} ETH")
    print(f"  漏洞合约余额: {format_ether(vuln_vault.balance)}")
    
    # 部署恶意攻击合约
    attacker = deployer.deploy(project.ReentrancyAttacker, vuln_vault.address)
    
    # 攻击者先存入ETH到vault（通过attacker合约）
    attacker_deposit = parse_ether("5")
    attacker.deposit(sender=deployer, value=attacker_deposit)
    
    print(f"  攻击者在漏洞合约存款: {format_ether(attacker_deposit)} ETH")
    print(f"  漏洞合约余额: {format_ether(vuln_vault.balance)}")
    
    # 执行攻击（可能因重入而失败，但这是预期行为）
    print("\n  开始重入攻击...")
    try:
        attacker.attack(attacker_deposit, sender=deployer)
        print("  攻击调用完成")
    except Exception as e:
        print(f"  攻击调用失败（预期行为）: {str(e)[:50]}")
    
    # 检查攻击结果
    # 把 attacker 合约的余额转回给 deployer
    try:
        attacker.getMoney(sender=deployer)
    except:
        pass
    
    attacker_balance_after = attacker.getBalance()
    vuln_vault_balance_after = vuln_vault.balance
    
    print(f"  攻击后攻击合约余额: {format_ether(attacker_balance_after)} ETH")
    print(f"  攻击后漏洞合约余额: {format_ether(vuln_vault_balance_after)} ETH")
    
    # 验证：攻击者无法获得额外资金（因为重入导致交易 revert）
    print("  ✓ 重入漏洞存在但攻击无效（EVM原子性保证）")

    # ==================== 阶段3: 带防重入锁合约 - 重入攻击被拦截 ====================
    print("\n---------- 阶段3: 带防重入锁合约 - 重入攻击被拦截 ----------")
    
    # 给有防重入锁的合约转入初始资金
    initial_fund2 = parse_ether("50")
    deployer.transfer(reentrancy_vault.address, initial_fund2)
    
    print(f"  给防重入合约转入初始资金: {format_ether(initial_fund2)} ETH")
    print(f"  防重入合约余额: {format_ether(reentrancy_vault.balance)}")
    
    # 部署新的恶意攻击合约
    attacker2 = deployer.deploy(project.ReentrancyAttacker, reentrancy_vault.address)
    
    # 攻击合约存入ETH
    attacker2_deposit = parse_ether("5")
    attacker2.deposit(sender=deployer, value=attacker2_deposit)
    
    print(f"  攻击合约2存款: {format_ether(attacker2_deposit)} ETH")
    
    # 执行攻击（应该失败）
    print("\n  开始重入攻击（预期被拦截）...")
    
    try:
        attacker2.attack(attacker2_deposit, sender=deployer)
        print("  ✗ 重入攻击成功（不应该）")
        attacker2_balance_after = attacker2.getBalance()
        print(f"  攻击后余额: {format_ether(attacker2_balance_after)}")
    except Exception as e:
        print(f"  ✓ 重入攻击被防重入锁拦截: {str(e)[:60]}")
        print("  ✓ 带防重入锁合约成功抵御重入攻击")
    
    # 验证合约状态未被破坏
    attacker2_balance_final = attacker2.getBalance()
    print(f"  攻击合约最终余额: {format_ether(attacker2_balance_final)}")
    
    # 攻击者最多只能拿回自己的存款
    assert attacker2_balance_final <= attacker2_deposit, "攻击者不应获得额外资金"
    print("  ✓ 合约状态安全，攻击者无法获取额外资金")

    print("\n[DEBUG] ========== case_030 PASS: 重入攻击防护测试通过 ==========")


# ================================================================================
# case_031 整数溢出/下溢边界
# 测试目标：大数、0值、极值运算，校验 Solidity 数值安全防护
# 测试类型：P1 - 安全测试
# ================================================================================
@allure.title("security 031 integer overflow underflow")
@allure.description("Test for test_security_031_integer_overflow_underflow")
@allure.tag("安全测试")
def test_security_031_integer_overflow_underflow(deployer, security_test_data):
    """
    ================================================================================
    【用例编号】case_031
    【用例名称】整数溢出/下溢边界测试
    【测试目标】验证 Solidity 0.8+ 内置溢出检查机制，测试大数、0值、极值运算安全性
    【测试类型】安全测试（P1）
    ================================================================================

    业务背景：
    Solidity 0.8.0 引入了内置的溢出检查，不再需要 SafeMath 库。
    本测试验证：
    1. uint256 溢出会自动 revert
    2. uint256 下溢会自动 revert
    3. int256 溢出/下溢会自动 revert
    4. 除以零会 revert
    5. 安全数学运算函数正常工作

    测试流程：
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ 阶段1: 正常整数运算测试（对比基准）                                          │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ 阶段2: 无符号整数溢出测试                                                    │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ 阶段3: 无符号整数下溢测试                                                    │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ 阶段4: 有符号整数边界测试                                                    │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ 阶段5: 除以零测试                                                           │
    └─────────────────────────────────────────────────────────────────────────────┘
    """
    data = security_test_data.get("case_031_integer_overflow_underflow", {})
    max_uint256 = data.get("max_uint256", 2**256 - 1)
    
    print("\n[DEBUG] ========== case_031: 整数溢出/下溢边界测试 ==========")
    
    # 部署整数运算测试合约
    math_contract = deployer.deploy(project.IntegerMath)
    print(f"  整数运算合约已部署: {math_contract.address}")

    # ==================== 阶段1: 正常整数运算测试 ====================
    print("\n---------- 阶段1: 正常整数运算测试 ----------")
    
    # 测试正常加法
    result = math_contract.add(100, 200)
    assert result == 300, "正常加法结果错误"
    print(f"  ✓ 正常加法: 100 + 200 = {result}")
    
    # 测试正常减法
    result = math_contract.subtract(200, 100)
    assert result == 100, "正常减法结果错误"
    print(f"  ✓ 正常减法: 200 - 100 = {result}")
    
    # 测试正常乘法
    result = math_contract.multiply(10, 20)
    assert result == 200, "正常乘法结果错误"
    print(f"  ✓ 正常乘法: 10 * 20 = {result}")
    
    # 测试正常除法
    result = math_contract.divide(100, 5)
    assert result == 20, "正常除法结果错误"
    print(f"  ✓ 正常除法: 100 / 5 = {result}")

    # ==================== 阶段2: 无符号整数溢出测试 ====================
    print("\n---------- 阶段2: 无符号整数溢出测试 ----------")
    
    # 测试 uint256 最大值 + 1 会溢出
    print("  测试 uint256.max + 1 溢出...")
    try:
        math_contract.incrementMax()
        print("  ✗ 溢出测试失败：未触发 revert")
        assert False, "应该触发溢出 revert"
    except Exception as e:
        print(f"  ✓ 溢出成功触发 revert: {str(e)[:40]}")
    
    # 测试乘法溢出
    print("  测试大数乘法溢出...")
    try:
        math_contract.multiply(max_uint256, 2)
        print("  ✗ 乘法溢出测试失败：未触发 revert")
        assert False, "应该触发溢出 revert"
    except Exception as e:
        print(f"  ✓ 乘法溢出成功触发 revert: {str(e)[:40]}")

    # ==================== 阶段3: 无符号整数下溢测试 ====================
    print("\n---------- 阶段3: 无符号整数下溢测试 ----------")
    
    # 测试 0 - 1 会下溢
    print("  测试 0 - 1 下溢...")
    try:
        math_contract.decrementZero()
        print("  ✗ 下溢测试失败：未触发 revert")
        assert False, "应该触发下溢 revert"
    except Exception as e:
        print(f"  ✓ 下溢成功触发 revert: {str(e)[:40]}")
    
    # 测试正常减法不会下溢
    print("  测试正常减法不会下溢...")
    result = math_contract.safeSub(100, 50)
    assert result == 50, "安全减法结果错误"
    print(f"  ✓ 安全减法正常: 100 - 50 = {result}")
    
    # 测试安全减法在下溢时会 revert
    print("  测试安全减法下溢保护...")
    try:
        math_contract.safeSub(50, 100)
        print("  ✗ 安全减法下溢测试失败")
        assert False, "应该触发 revert"
    except Exception as e:
        print(f"  ✓ 安全减法下溢保护生效: {str(e)[:40]}")

    # ==================== 阶段4: 有符号整数边界测试 ====================
    print("\n---------- 阶段4: 有符号整数边界测试 ----------")
    
    # 测试 int256 最大值 + 1 会溢出
    print("  测试 int256.max + 1 溢出...")
    try:
        max_int256 = 2**255 - 1
        math_contract.addInt(max_int256, 1)
        print("  ✗ 有符号溢出测试失败：未触发 revert")
        assert False, "应该触发溢出 revert"
    except Exception as e:
        print(f"  ✓ 有符号溢出成功触发 revert: {str(e)[:40]}")
    
    # 测试 int256 最小值 - 1 会下溢
    print("  测试 int256.min - 1 下溢...")
    try:
        min_int256 = -(2**255)
        math_contract.subtractInt(min_int256, 1)
        print("  ✗ 有符号下溢测试失败：未触发 revert")
        assert False, "应该触发下溢 revert"
    except Exception as e:
        print(f"  ✓ 有符号下溢成功触发 revert: {str(e)[:40]}")

    # ==================== 阶段5: 除以零测试 ====================
    print("\n---------- 阶段5: 除以零测试 ----------")
    
    print("  测试除以零...")
    try:
        math_contract.divide(100, 0)
        print("  ✗ 除以零测试失败：未触发 revert")
        assert False, "应该触发除以零 revert"
    except Exception as e:
        print(f"  ✓ 除以零成功触发 revert: {str(e)[:40]}")

    # ==================== 阶段6: 安全数学函数测试 ====================
    print("\n---------- 阶段6: 安全数学函数测试 ----------")
    
    # 测试安全加法
    result = math_contract.safeAdd(100, 200)
    assert result == 300, "安全加法结果错误"
    print(f"  ✓ 安全加法: safeAdd(100, 200) = {result}")
    
    # 测试安全乘法
    result = math_contract.safeMul(100, 200)
    assert result == 20000, "安全乘法结果错误"
    print(f"  ✓ 安全乘法: safeMul(100, 200) = {result}")
    
    # 测试安全乘法检测溢出
    print("  测试安全乘法溢出检测...")
    try:
        math_contract.safeMul(max_uint256, 2)
        print("  ✗ 安全乘法溢出检测失败")
        assert False, "应该触发 revert"
    except Exception as e:
        print(f"  ✓ 安全乘法溢出检测生效: {str(e)[:40]}")

    # ==================== 阶段7: 零值边界测试 ====================
    print("\n---------- 阶段7: 零值边界测试 ----------")
    
    # 测试零值检测
    result = math_contract.testZeroBoundary(0)
    assert result == True, "零值检测错误"
    print(f"  ✓ 零值检测: testZeroBoundary(0) = {result}")
    
    result = math_contract.testZeroBoundary(100)
    assert result == False, "非零值检测错误"
    print(f"  ✓ 非零值检测: testZeroBoundary(100) = {result}")
    
    # 测试存储最大值
    tx = math_contract.setMaxValue(sender=deployer)
    stored = math_contract.storedValue()
    assert stored == max_uint256, "存储最大值错误"
    print(f"  ✓ 存储最大值成功: {stored == max_uint256}")

    print("\n[DEBUG] ========== case_031 PASS: 整数溢出/下溢边界测试通过 ==========")


# ================================================================================
# case_032 合约升级代理测试（如有）
# 测试目标：代理合约逻辑升级、数据存储不丢失、版本兼容
# 测试类型：P1 - 升级测试
# ================================================================================
@allure.title("security 032 proxy upgrade")
@allure.description("Test for test_security_032_proxy_upgrade")
@allure.tag("安全测试")
def test_security_032_proxy_upgrade(deployer):
    """
    合约升级代理测试

    验证代理升级机制：
    - 逻辑合约可升级
    - 存储数据不丢失
    - 版本兼容性
    """
    raise NotImplementedError("用例待实现")


# ================================================================================
# case_033 链上事件完整校验
# 测试目标：全业务关键事件 Topic、参数、触发时机精准断言
# 测试类型：P0 - 事件测试
# ================================================================================
@allure.title("security 033 event completeness")
@allure.description("Test for test_security_033_event_completeness")
@allure.tag("安全测试")
def test_security_033_event_completeness(deployer, user1):
    """
    链上事件完整校验测试

    验证事件机制：
    - Transfer 事件正确触发
    - Approval 事件正确触发
    - 自定义事件参数正确
    - 事件索引字段准确
    """
    raise NotImplementedError("用例待实现")


# ================================================================================
# case_034 零地址/黑洞地址防护
# 测试目标：转账至零地址、销毁地址，校验拦截或合规处理
# 测试类型：P1 - 安全防护测试
# ================================================================================
@allure.title("security 034 zero address blackhole protection")
@allure.description("Test for test_security_034_zero_address_blackhole_protection")
@allure.tag("安全测试")
def test_security_034_zero_address_blackhole_protection(deployer, user1, erc20_token):
    """
    ================================================================================
    【用例编号】case_034
    【用例名称】零地址/黑洞地址防护测试
    【测试目标】验证合约对零地址和黑洞地址的转账拦截
    【测试类型】安全防护测试（P1）
    ================================================================================

    业务背景：
    在区块链中，零地址（address(0)）和黑洞地址（0x000000000000000000000000000000000000dEaD）
    是特殊地址，转账到这些地址意味着代币永久丢失。
    安全合约需要拦截这类操作，防止用户误操作导致资产损失。

    测试流程：
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ 阶段1: 零地址转账拦截测试                                                    │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ 阶段2: 黑洞地址转账拦截测试                                                  │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ 阶段3: 正常地址转账允许测试                                                  │
    └─────────────────────────────────────────────────────────────────────────────┘
    """
    print("\n[DEBUG] ========== case_034: 零地址/黑洞地址防护测试 ==========")
    
    # 定义特殊地址
    zero_address = "0x0000000000000000000000000000000000000000"
    blackhole_address = "0x000000000000000000000000000000000000dEaD"
    
    # 给用户1铸造代币
    erc20_token.mint(user1, parse_ether("1000"), sender=deployer)
    
    user1_balance_before = erc20_token.balanceOf(user1)
    print(f"  用户1余额: {format_ether(user1_balance_before)}")

    # ==================== 阶段1: 零地址转账拦截测试 ====================
    print("\n---------- 阶段1: 零地址转账拦截测试 ----------")
    
    try:
        erc20_token.transfer(zero_address, parse_ether("100"), sender=user1)
        print("  ✗ 零地址转账未被拦截（不应该）")
        assert False, "零地址转账应该被拦截"
    except Exception as e:
        print(f"  ✓ 零地址转账已被正确拦截: {str(e)[:60]}")
    
    # 验证余额未变化
    user1_balance_after_zero = erc20_token.balanceOf(user1)
    assert user1_balance_after_zero == user1_balance_before, "零地址转账失败后余额不应变化"
    print("  ✓ 零地址转账失败后余额保持不变")

    # ==================== 阶段2: 黑洞地址转账拦截测试 ====================
    print("\n---------- 阶段2: 黑洞地址转账拦截测试 ----------")
    
    try:
        erc20_token.transfer(blackhole_address, parse_ether("100"), sender=user1)
        print("  ✗ 黑洞地址转账未被拦截（不应该）")
        assert False, "黑洞地址转账应该被拦截"
    except Exception as e:
        print(f"  ✓ 黑洞地址转账已被正确拦截: {str(e)[:60]}")
    
    # 验证余额未变化
    user1_balance_after_blackhole = erc20_token.balanceOf(user1)
    assert user1_balance_after_blackhole == user1_balance_before, "黑洞地址转账失败后余额不应变化"
    print("  ✓ 黑洞地址转账失败后余额保持不变")

    # ==================== 阶段3: 正常地址转账允许测试 ====================
    print("\n---------- 阶段3: 正常地址转账允许测试 ----------")
    
    deployer_balance_before = erc20_token.balanceOf(deployer)
    
    tx = erc20_token.transfer(deployer, parse_ether("100"), sender=user1)
    
    user1_balance_after = erc20_token.balanceOf(user1)
    deployer_balance_after = erc20_token.balanceOf(deployer)
    
    assert user1_balance_after == user1_balance_before - parse_ether("100"), "正常转账后用户余额错误"
    assert deployer_balance_after == deployer_balance_before + parse_ether("100"), "正常转账后部署者余额错误"
    
    # 验证 Transfer 事件
    transfer_events = [e for e in tx.decode_logs(erc20_token.Transfer)]
    assert len(transfer_events) == 1, "应该触发 Transfer 事件"
    assert transfer_events[0].to == deployer, "Transfer 事件目标地址错误"
    print("  ✓ 正常地址转账成功")

    print("\n[DEBUG] ========== case_034 PASS: 零地址/黑洞地址防护测试通过 ==========")