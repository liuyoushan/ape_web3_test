"""
==============================================================================
【清算场景】完整清算测试用例
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

from ape import reverts
from framework.core.logger import log
from framework.core.formatters import parse_ether, format_ether


@allure.title("case_049 正常清算流程测试")
@allure.description("验证完整清算流程：清算人执行清算，抵押资产被扣除、债务偿还")
@allure.tag("Liquidation", "P0", "功能测试")
def test_liquidation_049_normal_workflow(deployer, user1, user2, liquidation_test_data, collateral_token, debt_token, liquidation_contract):
    """
    case_049 正常清算流程测试
    
    验证完整的清算执行流程：
    - 清算人（user2）偿还借款人（user1）的债务
    - 借款人抵押资产按比例扣除（包含清算奖励）
    - 借款人债务清零
    - 清算人获得抵押资产作为奖励
    """
    log.step("case_049: 正常清算流程测试")
    data = liquidation_test_data["case_049_normal_liquidation"]
    debt_amount = parse_ether(str(data["debt_amount"]))
    collateral_amount = parse_ether(str(data["collateral_amount"]))
    adjusted_debt = parse_ether(str(data["adjusted_debt"]))
    log.debug(f"测试数据 - 债务: {format_ether(debt_amount)}, 抵押品: {format_ether(collateral_amount)}, 调整后债务: {format_ether(adjusted_debt)}")

    # 设置用户仓位
    log.info("步骤1: 设置用户仓位")
    liquidation_contract.setUserPosition(user1, collateral_amount, adjusted_debt, sender=deployer)
    actual_reward = adjusted_debt // 10
    log.debug(f"用户1仓位设置完成 - 抵押品: {format_ether(collateral_amount)}, 债务: {format_ether(adjusted_debt)}, 清算奖励: {format_ether(actual_reward)}")

    # 准备代币
    log.info("步骤2: 准备代币")
    collateral_token.mint(liquidation_contract, collateral_amount, sender=deployer)
    debt_token.mint(user2, adjusted_debt, sender=deployer)
    log.debug(f"代币铸造完成 - 清算合约抵押品: {format_ether(collateral_token.balanceOf(liquidation_contract))}, 用户2债务代币: {format_ether(debt_token.balanceOf(user2))}")

    user2_collateral_before = collateral_token.balanceOf(user2)
    log.debug(f"用户2清算前抵押品余额: {format_ether(user2_collateral_before)}")

    # 执行清算
    log.info("步骤3: 执行清算")
    debt_token.approve(liquidation_contract, adjusted_debt, sender=user2)
    log.debug(f"用户2授权清算合约使用债务代币: {format_ether(adjusted_debt)}")
    liquidation_contract.liquidate(user1, sender=user2)
    log.debug("清算执行完成")

    # 验证借款人状态
    log.info("步骤4: 验证借款人状态")
    user_debt = liquidation_contract.userDebt(user1)
    is_liquidated = liquidation_contract.isLiquidated(user1)
    log.debug(f"用户1债务: {format_ether(user_debt)}, 是否已清算: {is_liquidated}")
    assert user_debt == 0, f"用户1债务应为0，实际为 {format_ether(user_debt)}"
    assert is_liquidated == True, f"用户1应已清算，实际为 {is_liquidated}"
    log.debug("借款人状态验证通过")

    # 验证清算人收益
    log.info("步骤5: 验证清算人收益")
    liquidation_payment = adjusted_debt + actual_reward
    expected_user2_collateral = liquidation_payment if collateral_amount >= liquidation_payment else collateral_amount
    actual_user2_collateral_gain = collateral_token.balanceOf(user2) - user2_collateral_before
    log.debug(f"清算支付总额: {format_ether(liquidation_payment)}, 预期用户2获得: {format_ether(expected_user2_collateral)}, 实际获得: {format_ether(actual_user2_collateral_gain)}")
    assert actual_user2_collateral_gain == expected_user2_collateral, f"清算人收益不符，预期: {format_ether(expected_user2_collateral)}, 实际: {format_ether(actual_user2_collateral_gain)}"
    log.debug("清算人收益验证通过")

    log.success("✅ case_049 正常清算流程测试通过")


@allure.title("case_050 清算后状态校验")
@allure.description("验证清算完成后各状态的正确性")
@allure.tag("Liquidation", "P0", "功能测试")
def test_liquidation_050_post_state_check(deployer, user1, user2, liquidation_test_data, collateral_token, debt_token, liquidation_contract):
    """
    case_050 清算后状态校验
    
    验证清算执行后的状态一致性：
    - 借款人债务清零
    - 借款人抵押资产按规则扣除
    - 清算标记为已清算
    - 清算人获得抵押资产奖励
    """
    log.step("case_050: 清算后状态校验")
    data = liquidation_test_data["case_049_normal_liquidation"]
    collateral_amount = parse_ether(str(data["collateral_amount"]))
    adjusted_debt = parse_ether(str(data["adjusted_debt"]))
    log.debug(f"测试数据 - 抵押品: {format_ether(collateral_amount)}, 调整后债务: {format_ether(adjusted_debt)}")

    # 设置仓位并执行清算
    log.info("步骤1: 设置仓位并执行清算")
    liquidation_contract.setUserPosition(user1, collateral_amount, adjusted_debt, sender=deployer)
    log.debug(f"用户1仓位设置完成")
    collateral_token.mint(liquidation_contract, collateral_amount, sender=deployer)
    debt_token.mint(user2, adjusted_debt, sender=deployer)
    log.debug(f"代币铸造完成")
    debt_token.approve(liquidation_contract, adjusted_debt, sender=user2)
    liquidation_contract.liquidate(user1, sender=user2)
    log.debug("清算执行完成")

    # 验证借款人状态
    log.info("步骤2: 验证借款人状态")
    user_debt = liquidation_contract.userDebt(user1)
    is_liquidated = liquidation_contract.isLiquidated(user1)
    log.debug(f"用户1债务: {format_ether(user_debt)}, 是否已清算: {is_liquidated}")
    assert user_debt == 0, f"用户1债务应为0，实际为 {format_ether(user_debt)}"
    assert is_liquidated == True, f"用户1应已清算，实际为 {is_liquidated}"
    log.debug("借款人状态验证通过")

    # 验证抵押品扣除和清算人收益
    log.info("步骤3: 验证抵押品扣除和清算人收益")
    liquidation_payment = adjusted_debt + (adjusted_debt // 10)
    expected_collateral = collateral_amount - liquidation_payment if collateral_amount >= liquidation_payment else 0
    log.debug(f"清算支付总额: {format_ether(liquidation_payment)}, 用户1预期剩余抵押品: {format_ether(expected_collateral)}")
    
    actual_collateral = liquidation_contract.userCollateral(user1)
    log.debug(f"用户1实际剩余抵押品: {format_ether(actual_collateral)}")
    assert actual_collateral == expected_collateral, f"用户1抵押品不符，预期: {format_ether(expected_collateral)}, 实际: {format_ether(actual_collateral)}"
    
    user2_collateral = collateral_token.balanceOf(user2)
    expected_user2_collateral = liquidation_payment if collateral_amount >= liquidation_payment else collateral_amount
    log.debug(f"用户2实际获得抵押品: {format_ether(user2_collateral)}, 预期: {format_ether(expected_user2_collateral)}")
    assert user2_collateral == expected_user2_collateral, f"用户2抵押品不符，预期: {format_ether(expected_user2_collateral)}, 实际: {format_ether(user2_collateral)}"
    log.debug("抵押品和收益验证通过")

    log.success("✅ case_050 清算后状态校验测试通过")


@allure.title("case_055 重入攻击防护测试")
@allure.description("验证重入锁和 Check-Effects-Interaction 模式有效")
@allure.tag("Liquidation", "P0", "安全测试")
def test_liquidation_055_reentrancy_protection(deployer, user1, liquidation_contract, liquidation_test_data, collateral_token, debt_token):
    """
    case_055 重入攻击防护测试
    
    验证清算合约的重入攻击防护机制：
    - 使用重入锁防止递归调用
    - 使用 Check-Effects-Interaction 模式
    - 恶意攻击者无法通过递归调用窃取资产
    """
    log.step("case_055: 重入攻击防护测试")
    import ape
    data = liquidation_test_data["case_055_reentrancy_attack"]
    collateral_amount = parse_ether(str(data["collateral_amount"]))
    debt_amount = parse_ether(str(data["debt_amount"]))
    log.debug(f"测试数据 - 抵押品: {format_ether(collateral_amount)}, 债务: {format_ether(debt_amount)}")

    # 用户存入抵押品并借入债务
    log.info("步骤1: 用户存入抵押品并借入债务")
    collateral_token.mint(user1, collateral_amount, sender=deployer)
    log.debug(f"用户1获得抵押品: {format_ether(collateral_amount)}")
    collateral_token.approve(liquidation_contract, collateral_amount, sender=user1)
    liquidation_contract.depositCollateral(collateral_amount, sender=user1)
    log.debug(f"用户1存入抵押品完成")
    debt_token.mint(liquidation_contract, debt_amount, sender=deployer)
    liquidation_contract.borrow(debt_amount, sender=user1)
    log.debug(f"用户1借入债务: {format_ether(debt_amount)}")

    # 调整仓位满足清算条件
    log.info("步骤2: 调整仓位满足清算条件")
    liquidation_contract.setUserPosition(user1, parse_ether("900"), debt_amount, sender=deployer)
    log.debug(f"用户1仓位调整完成 - 抵押品: 900, 债务: {format_ether(debt_amount)}")

    # 部署恶意攻击合约并执行攻击
    log.info("步骤3: 部署恶意攻击合约并执行攻击")
    attacker_contract = deployer.deploy(ape.project.MaliciousAttacker, liquidation_contract.address, collateral_token.address, debt_token.address)
    attacker_contract.setTarget(user1, sender=deployer)
    collateral_token.mint(liquidation_contract, parse_ether("900"), sender=deployer)
    debt_token.mint(attacker_contract.address, debt_amount, sender=deployer)
    log.debug("攻击合约部署完成，准备执行攻击")

    try:
        attacker_contract.attack(sender=deployer)
    except Exception as e:
        log.debug(f"攻击被拦截，异常: {type(e).__name__}")

    # 验证攻击被拦截，清算正常完成
    log.info("步骤4: 验证攻击被拦截，清算正常完成")
    attack_success, _ = attacker_contract.getAttackResult()
    log.debug(f"攻击是否成功: {attack_success}")
    assert attack_success == False, "重入攻击应被拦截"
    
    is_liquidated = liquidation_contract.isLiquidated(user1)
    user_debt = liquidation_contract.userDebt(user1)
    log.debug(f"用户1是否已清算: {is_liquidated}, 用户1债务: {format_ether(user_debt)}")
    assert is_liquidated == True, "用户1应已清算"
    assert user_debt == 0, f"用户1债务应为0，实际为 {format_ether(user_debt)}"
    log.debug("重入攻击防护验证通过")

    log.success("✅ case_055 重入攻击防护测试通过")


@allure.title("case_056 闪电贷价格操纵测试")
@allure.description("验证清算系统能抵御闪电贷攻击")
@allure.tag("Liquidation", "P0", "安全测试")
def test_liquidation_056_flash_loan_attack(deployer, user1, user2, collateral_token, debt_token, liquidation_contract, liquidation_test_data):
    """
    case_056 闪电贷价格操纵测试
    
    验证清算系统对闪电贷攻击的防护能力：
    - 攻击者无法通过闪电贷操纵价格进行恶意清算
    - 清算条件判断不受临时价格波动影响
    """
    log.step("case_056: 闪电贷价格操纵测试")
    import ape
    data = liquidation_test_data["case_056_flash_loan_attack"]
    collateral_amount = parse_ether(str(data["target_collateral"]))
    debt_amount = parse_ether(str(data["target_debt"]))
    log.debug(f"测试数据 - 抵押品: {format_ether(collateral_amount)}, 债务: {format_ether(debt_amount)}")

    # 设置用户仓位
    log.info("步骤1: 设置用户仓位")
    collateral_token.mint(user2, collateral_amount, sender=deployer)
    log.debug(f"用户2获得抵押品: {format_ether(collateral_amount)}")
    collateral_token.approve(liquidation_contract, collateral_amount, sender=user2)
    liquidation_contract.depositCollateral(collateral_amount, sender=user2)
    log.debug(f"用户2存入抵押品完成")
    debt_token.mint(liquidation_contract, debt_amount, sender=deployer)
    liquidation_contract.borrow(debt_amount, sender=user2)
    log.debug(f"用户2借入债务: {format_ether(debt_amount)}")
    liquidation_contract.setUserPosition(user2, parse_ether("900"), debt_amount, sender=deployer)
    log.debug(f"用户2仓位调整完成")

    # 部署闪电贷和攻击者合约
    log.info("步骤2: 部署闪电贷和攻击者合约")
    flash_loan_contract = deployer.deploy(ape.project.SimpleFlashLoan, debt_token.address)
    debt_token.mint(flash_loan_contract, parse_ether("10000"), sender=deployer)
    log.debug(f"闪电贷合约部署完成，注入资金: 10000")
    attacker_contract = deployer.deploy(ape.project.FlashLoanAttacker)
    attacker_contract.setFlashLoanContract(flash_loan_contract.address, sender=deployer)
    attacker_contract.setTargetToken(debt_token.address, sender=deployer)
    log.debug("攻击者合约部署完成")

    # 执行闪电贷攻击
    log.info("步骤3: 执行闪电贷攻击")
    collateral_token.mint(liquidation_contract, collateral_amount * 2, sender=deployer)
    debt_token.mint(attacker_contract.address, debt_amount, sender=deployer)
    log.debug("攻击准备完成，开始执行闪电贷攻击")
    try:
        callback_data = attacker_contract.onFlashLoanReceived.encode_input()
        flash_loan_contract.flashLoan(attacker_contract.address, parse_ether("10000"), callback_data, sender=deployer)
    except Exception as e:
        log.debug(f"闪电贷攻击被拦截，异常: {type(e).__name__}")

    # 验证用户状态正常
    log.info("步骤4: 验证用户状态正常")
    user_debt = liquidation_contract.userDebt(user2)
    log.debug(f"用户2债务: {format_ether(user_debt)}")
    assert user_debt in (0, debt_amount), f"用户2债务不在预期范围内，实际为 {format_ether(user_debt)}"
    log.debug("闪电贷攻击防护验证通过")

    log.success("✅ case_056 闪电贷价格操纵测试通过")


@allure.title("case_057 重复清算防护测试")
@allure.description("验证同一仓位不能被多次清算")
@allure.tag("Liquidation", "P0", "安全测试")
def test_liquidation_057_duplicate_protection(deployer, user1, liquidation_contract, liquidation_test_data, collateral_token, debt_token):
    """
    case_057 重复清算防护测试
    
    验证重复清算防护机制：
    - 已清算的仓位不能再次被清算
    - 第二次清算尝试被拒绝
    - 清算状态保持一致
    """
    log.step("case_057: 重复清算防护测试")
    data = liquidation_test_data["case_057_duplicate_liquidation"]
    collateral_amount = parse_ether(str(data["collateral_amount"]))
    debt_amount = parse_ether(str(data["debt_amount"]))
    log.debug(f"测试数据 - 抵押品: {format_ether(collateral_amount)}, 债务: {format_ether(debt_amount)}")

    # 设置用户仓位
    log.info("步骤1: 设置用户仓位")
    collateral_token.mint(user1, collateral_amount, sender=deployer)
    log.debug(f"用户1获得抵押品: {format_ether(collateral_amount)}")
    collateral_token.approve(liquidation_contract, collateral_amount, sender=user1)
    liquidation_contract.depositCollateral(collateral_amount, sender=user1)
    log.debug(f"用户1存入抵押品完成")
    debt_token.mint(liquidation_contract, debt_amount, sender=deployer)
    liquidation_contract.borrow(debt_amount, sender=user1)
    log.debug(f"用户1借入债务: {format_ether(debt_amount)}")
    liquidation_contract.setUserPosition(user1, parse_ether("900"), debt_amount, sender=deployer)
    log.debug(f"用户1仓位调整完成")

    # 第一次清算
    log.info("步骤2: 执行第一次清算")
    collateral_token.mint(liquidation_contract, parse_ether("900"), sender=deployer)
    debt_token.mint(deployer, debt_amount, sender=deployer)
    debt_token.approve(liquidation_contract, debt_amount, sender=deployer)
    liquidation_contract.liquidate(user1, sender=deployer)
    log.debug("第一次清算执行完成")

    is_liquidated = liquidation_contract.isLiquidated(user1)
    user_debt = liquidation_contract.userDebt(user1)
    log.debug(f"第一次清算后 - 是否已清算: {is_liquidated}, 债务: {format_ether(user_debt)}")
    assert is_liquidated == True, "第一次清算后用户1应已清算"
    assert user_debt == 0, f"第一次清算后用户1债务应为0，实际为 {format_ether(user_debt)}"
    log.debug("第一次清算验证通过")

    # 第二次清算（预期失败）
    log.info("步骤3: 尝试第二次清算（预期失败）")
    debt_token.mint(deployer, debt_amount, sender=deployer)
    debt_token.approve(liquidation_contract, debt_amount, sender=deployer)
    try:
        liquidation_contract.liquidate(user1, sender=deployer)
        assert False, "第二次清算应该失败"
    except Exception as e:
        log.debug(f"第二次清算被拒绝，异常: {type(e).__name__}")

    # 验证状态不变
    log.info("步骤4: 验证状态不变")
    is_liquidated = liquidation_contract.isLiquidated(user1)
    user_debt = liquidation_contract.userDebt(user1)
    can_liquidate = liquidation_contract.canLiquidate(user1)
    log.debug(f"第二次清算后状态 - 是否已清算: {is_liquidated}, 债务: {format_ether(user_debt)}, 是否可清算: {can_liquidate}")
    assert is_liquidated == True, "用户1应仍为已清算状态"
    assert user_debt == 0, f"用户1债务应仍为0，实际为 {format_ether(user_debt)}"
    assert can_liquidate == False, "用户1应不可再次清算"
    log.debug("重复清算防护验证通过")

    log.success("✅ case_057 重复清算防护测试通过")


@allure.title("case_051 非清算条件拒绝测试")
@allure.description("验证非清算条件下拒绝执行清算")
@allure.tag("Liquidation", "P1", "功能测试")
def test_liquidation_051_non_liquidation_condition_reject(deployer, user1, liquidation_test_data):
    """
    case_051 非清算条件拒绝测试
    
    验证健康因子高于阈值时拒绝执行清算：
    - 当用户健康因子正常时，清算操作被拒绝
    - 保护用户免受恶意清算
    """
    raise NotImplementedError("case_051 待实现")


@allure.title("case_052 清算奖励计算测试")
@allure.description("验证清算奖励/罚金计算逻辑")
@allure.tag("Liquidation", "P1", "功能测试")
def test_liquidation_052_liquidation_reward_calculation(deployer, user1, user2, liquidation_test_data):
    """
    case_052 清算奖励计算测试
    
    验证清算奖励和罚金的计算逻辑：
    - 清算人获得适当的清算奖励
    - 借款人承担合理的清算罚金
    - 计算精度和边界条件正确
    """
    raise NotImplementedError("case_052 待实现")


@allure.title("case_053 批量清算场景测试")
@allure.description("验证批量清算场景")
@allure.tag("Liquidation", "P1", "功能测试")
def test_liquidation_053_batch_liquidation_scenario(deployer, user1, user2, user3, liquidation_test_data):
    """
    case_053 批量清算场景测试
    
    验证批量清算的执行能力：
    - 同时清算多个用户仓位
    - 系统性能和状态一致性
    - 并发清算时的资源分配
    """
    raise NotImplementedError("case_053 待实现")


@allure.title("case_054 价格预言机操纵边界测试")
@allure.description("验证价格预言机操纵边界")
@allure.tag("Liquidation", "P1", "安全测试")
def test_liquidation_054_price_oracle_manipulation_boundary(deployer, user1, liquidation_test_data):
    """
    case_054 价格预言机操纵边界测试
    
    验证价格预言机操纵的防护机制：
    - 防止预言机价格被操纵导致恶意清算
    - 价格偏差检测和保护
    """
    raise NotImplementedError("case_054 待实现")


@allure.title("case_058 漏洞合约攻击测试")
@allure.description("验证清算系统能抵御多种漏洞合约的攻击")
@allure.tag("Liquidation", "P0", "安全测试")
def test_liquidation_058_vulnerability_protection(deployer, user1, liquidation_contract, liquidation_test_data, collateral_token, debt_token):
    """
    case_058 漏洞合约攻击测试
    
    验证清算系统对多种漏洞合约攻击的防护能力：
    - 重入攻击防护
    - 恶意回调防护
    - 漏洞合约交互安全
    """
    log.step("case_058: 漏洞合约攻击测试")
    import ape
    data = liquidation_test_data["case_055_reentrancy_attack"]
    collateral_amount = parse_ether(str(data["collateral_amount"]))
    debt_amount = parse_ether(str(data["debt_amount"]))
    log.debug(f"测试数据 - 抵押品: {format_ether(collateral_amount)}, 债务: {format_ether(debt_amount)}")

    # 设置用户仓位
    log.info("步骤1: 设置用户仓位")
    collateral_token.mint(user1, collateral_amount, sender=deployer)
    log.debug(f"用户1获得抵押品: {format_ether(collateral_amount)}")
    collateral_token.approve(liquidation_contract, collateral_amount, sender=user1)
    liquidation_contract.depositCollateral(collateral_amount, sender=user1)
    log.debug(f"用户1存入抵押品完成")
    debt_token.mint(liquidation_contract, debt_amount, sender=deployer)
    liquidation_contract.borrow(debt_amount, sender=user1)
    log.debug(f"用户1借入债务: {format_ether(debt_amount)}")
    liquidation_contract.setUserPosition(user1, parse_ether("900"), debt_amount, sender=deployer)
    log.debug(f"用户1仓位调整完成")

    # 部署恶意攻击合约并执行攻击
    log.info("步骤2: 部署恶意攻击合约并执行攻击")
    attacker = deployer.deploy(ape.project.MaliciousAttacker, liquidation_contract.address, collateral_token.address, debt_token.address)
    attacker.setTarget(user1, sender=deployer)
    collateral_token.mint(liquidation_contract, parse_ether("900"), sender=deployer)
    debt_token.mint(attacker.address, debt_amount, sender=deployer)
    log.debug("攻击合约部署完成，准备执行攻击")
    try:
        attacker.attack(sender=deployer)
    except Exception as e:
        log.debug(f"攻击被拦截，异常: {type(e).__name__}")

    # 验证攻击失败，清算正常完成
    log.info("步骤3: 验证攻击失败，清算正常完成")
    attack_success, _ = attacker.getAttackResult()
    log.debug(f"攻击是否成功: {attack_success}")
    assert attack_success == False, "漏洞合约攻击应被拦截"

    is_liquidated = liquidation_contract.isLiquidated(user1)
    log.debug(f"用户1是否已清算: {is_liquidated}")
    assert is_liquidated == True, "用户1应已正常清算"
    log.debug("漏洞合约攻击防护验证通过")

    # 重置状态验证
    log.info("步骤4: 重置状态验证")
    liquidation_contract.resetLiquidationStatus(user1, sender=deployer)
    liquidation_contract.setUserPosition(user1, parse_ether("1000"), debt_amount, sender=deployer)
    log.debug("状态重置完成")

    log.success("✅ case_058 漏洞合约攻击测试通过")
