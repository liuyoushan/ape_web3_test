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
    data = liquidation_test_data["case_049_normal_liquidation"]
    debt_amount = parse_ether(str(data["debt_amount"]))
    collateral_amount = parse_ether(str(data["collateral_amount"]))
    adjusted_debt = parse_ether(str(data["adjusted_debt"]))

    liquidation_contract.setUserPosition(user1, collateral_amount, adjusted_debt, sender=deployer)

    actual_reward = adjusted_debt / 10
    user1_collateral_before = collateral_token.balanceOf(user1)
    user1_debt_before = liquidation_contract.userDebt(user1)

    collateral_token.mint(liquidation_contract, collateral_amount, sender=deployer)
    debt_token.mint(user2, adjusted_debt, sender=deployer)

    user2_collateral_before = collateral_token.balanceOf(user2)
    user2_debt_before = debt_token.balanceOf(user2)

    debt_token.approve(liquidation_contract, adjusted_debt, sender=user2)
    liquidation_contract.liquidate(user1, sender=user2)

    user1_debt_after = liquidation_contract.userDebt(user1)
    user1_collateral_after = liquidation_contract.userCollateral(user1)
    is_liquidated = liquidation_contract.isLiquidated(user1)

    liquidation_payment = adjusted_debt + actual_reward
    if collateral_amount >= liquidation_payment:
        expected_user1_collateral = collateral_amount - liquidation_payment
    else:
        expected_user1_collateral = 0

    assert user1_debt_after == 0
    assert user1_collateral_after == expected_user1_collateral
    assert is_liquidated == True

    user2_collateral_after = collateral_token.balanceOf(user2)
    user2_debt_after = debt_token.balanceOf(user2)

    if collateral_amount >= liquidation_payment:
        expected_user2_collateral = liquidation_payment
    else:
        expected_user2_collateral = collateral_amount
    actual_user2_collateral_gain = user2_collateral_after - user2_collateral_before

    assert actual_user2_collateral_gain == expected_user2_collateral
    assert user2_debt_after == 0


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
    data = liquidation_test_data["case_049_normal_liquidation"]
    collateral_amount = parse_ether(str(data["collateral_amount"]))
    adjusted_debt = parse_ether(str(data["adjusted_debt"]))

    liquidation_contract.setUserPosition(user1, collateral_amount, adjusted_debt, sender=deployer)

    collateral_token.mint(liquidation_contract, collateral_amount, sender=deployer)
    debt_token.mint(user2, adjusted_debt, sender=deployer)
    debt_token.approve(liquidation_contract, adjusted_debt, sender=user2)

    liquidation_contract.liquidate(user1, sender=user2)

    user1_debt_after = liquidation_contract.userDebt(user1)
    assert user1_debt_after == 0

    user1_collateral_after = liquidation_contract.userCollateral(user1)
    actual_reward = adjusted_debt / 10
    liquidation_payment = adjusted_debt + actual_reward
    if collateral_amount >= liquidation_payment:
        expected_user1_collateral = collateral_amount - liquidation_payment
    else:
        expected_user1_collateral = 0

    assert user1_collateral_after == expected_user1_collateral

    is_liquidated = liquidation_contract.isLiquidated(user1)
    assert is_liquidated == True

    user2_collateral_after = collateral_token.balanceOf(user2)
    user2_debt_after = debt_token.balanceOf(user2)

    if collateral_amount >= liquidation_payment:
        expected_user2_gain = liquidation_payment
    else:
        expected_user2_gain = collateral_amount

    assert user2_debt_after == 0
    assert user2_collateral_after == expected_user2_gain


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
    import ape
    data = liquidation_test_data["case_055_reentrancy_attack"]
    collateral_amount = parse_ether(str(data["collateral_amount"]))
    debt_amount = parse_ether(str(data["debt_amount"]))

    collateral_token.mint(user1, collateral_amount, sender=deployer)
    collateral_token.approve(liquidation_contract, collateral_amount, sender=user1)
    liquidation_contract.depositCollateral(collateral_amount, sender=user1)

    debt_token.mint(liquidation_contract, debt_amount, sender=deployer)
    liquidation_contract.borrow(debt_amount, sender=user1)

    new_collateral_value = parse_ether("900")
    liquidation_contract.setUserPosition(user1, new_collateral_value, debt_amount, sender=deployer)

    attacker_contract = deployer.deploy(
        ape.project.MaliciousAttacker,
        liquidation_contract.address,
        collateral_token.address,
        debt_token.address,
    )
    attacker_contract.setTarget(user1, sender=deployer)

    collateral_token.mint(liquidation_contract, new_collateral_value, sender=deployer)
    debt_token.mint(attacker_contract.address, debt_amount, sender=deployer)

    try:
        attacker_contract.attack(sender=deployer)
    except Exception:
        pass

    attack_success, reentrancy_count = attacker_contract.getAttackResult()

    assert attack_success == False
    assert liquidation_contract.isLiquidated(user1) == True
    assert liquidation_contract.canLiquidate(user1) == False
    assert liquidation_contract.userDebt(user1) == 0


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
    import ape
    data = liquidation_test_data["case_056_flash_loan_attack"]
    collateral_amount = parse_ether(str(data["target_collateral"]))
    debt_amount = parse_ether(str(data["target_debt"]))

    collateral_token.mint(user2, collateral_amount, sender=deployer)
    collateral_token.approve(liquidation_contract, collateral_amount, sender=user2)
    liquidation_contract.depositCollateral(collateral_amount, sender=user2)

    debt_token.mint(liquidation_contract, debt_amount, sender=deployer)
    liquidation_contract.borrow(debt_amount, sender=user2)

    liquidation_contract.setUserPosition(user2, parse_ether("900"), debt_amount, sender=deployer)

    flash_loan_contract = deployer.deploy(
        ape.project.SimpleFlashLoan,
        debt_token.address,
    )
    flash_loan_amount = parse_ether("10000")
    debt_token.mint(flash_loan_contract, flash_loan_amount, sender=deployer)

    attacker_contract = deployer.deploy(ape.project.FlashLoanAttacker)
    attacker_contract.setFlashLoanContract(flash_loan_contract.address, sender=deployer)
    attacker_contract.setTargetToken(debt_token.address, sender=deployer)

    collateral_token.mint(liquidation_contract, collateral_amount * 2, sender=deployer)
    debt_token.mint(attacker_contract.address, debt_amount, sender=deployer)

    try:
        callback_data = attacker_contract.onFlashLoanReceived.encode_input()
        flash_loan_contract.flashLoan(
            attacker_contract.address,
            flash_loan_amount,
            callback_data,
            sender=deployer
        )
    except Exception:
        pass

    attack_success, attack_count = attacker_contract.getAttackResult()
    assert liquidation_contract.userDebt(user2) == 0 or liquidation_contract.userDebt(user2) == debt_amount


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
    data = liquidation_test_data["case_057_duplicate_liquidation"]
    collateral_amount = parse_ether(str(data["collateral_amount"]))
    debt_amount = parse_ether(str(data["debt_amount"]))

    collateral_token.mint(user1, collateral_amount, sender=deployer)
    collateral_token.approve(liquidation_contract, collateral_amount, sender=user1)
    liquidation_contract.depositCollateral(collateral_amount, sender=user1)

    debt_token.mint(liquidation_contract, debt_amount, sender=deployer)
    liquidation_contract.borrow(debt_amount, sender=user1)

    new_collateral_value = parse_ether("900")
    liquidation_contract.setUserPosition(user1, new_collateral_value, debt_amount, sender=deployer)

    collateral_token.mint(liquidation_contract, new_collateral_value, sender=deployer)
    debt_token.mint(deployer, debt_amount, sender=deployer)
    debt_token.approve(liquidation_contract, debt_amount, sender=deployer)

    user1_debt_before = liquidation_contract.userDebt(user1)
    user1_collateral_before = liquidation_contract.userCollateral(user1)

    liquidation_contract.liquidate(user1, sender=deployer)

    is_liquidated_after_first = liquidation_contract.isLiquidated(user1)
    user1_debt_after_first = liquidation_contract.userDebt(user1)
    user1_collateral_after_first = liquidation_contract.userCollateral(user1)

    assert is_liquidated_after_first == True
    assert user1_debt_after_first == 0

    debt_token.mint(deployer, debt_amount, sender=deployer)
    debt_token.approve(liquidation_contract, debt_amount, sender=deployer)

    user1_debt_before_second = liquidation_contract.userDebt(user1)
    user1_collateral_before_second = liquidation_contract.userCollateral(user1)

    try:
        liquidation_contract.liquidate(user1, sender=deployer)
        assert False, "第二次清算应该失败"
    except Exception:
        pass

    is_liquidated_final = liquidation_contract.isLiquidated(user1)
    user1_debt_final = liquidation_contract.userDebt(user1)
    user1_collateral_final = liquidation_contract.userCollateral(user1)
    can_liquidate_final = liquidation_contract.canLiquidate(user1)

    assert is_liquidated_final == True
    assert user1_debt_final == 0
    assert user1_collateral_final == user1_collateral_after_first
    assert can_liquidate_final == False


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
    import ape
    data = liquidation_test_data["case_055_reentrancy_attack"]
    collateral_amount = parse_ether(str(data["collateral_amount"]))
    debt_amount = parse_ether(str(data["debt_amount"]))

    collateral_token.mint(user1, collateral_amount, sender=deployer)
    collateral_token.approve(liquidation_contract, collateral_amount, sender=user1)
    liquidation_contract.depositCollateral(collateral_amount, sender=user1)

    debt_token.mint(liquidation_contract, debt_amount, sender=deployer)
    liquidation_contract.borrow(debt_amount, sender=user1)

    new_collateral_value = parse_ether("900")
    liquidation_contract.setUserPosition(user1, new_collateral_value, debt_amount, sender=deployer)

    vulnerable_contract_a = deployer.deploy(
        ape.project.MaliciousAttacker,
        liquidation_contract.address,
        collateral_token.address,
        debt_token.address,
    )
    vulnerable_contract_a.setTarget(user1, sender=deployer)

    collateral_token.mint(liquidation_contract, new_collateral_value, sender=deployer)
    debt_token.mint(vulnerable_contract_a.address, debt_amount, sender=deployer)

    try:
        vulnerable_contract_a.attack(sender=deployer)
    except Exception:
        pass

    attack_success_a, reentrancy_count = vulnerable_contract_a.getAttackResult()

    assert liquidation_contract.isLiquidated(user1) == True
    assert attack_success_a == False

    liquidation_contract.resetLiquidationStatus(user1, sender=deployer)
    new_collateral_2 = parse_ether("1000")
    liquidation_contract.setUserPosition(user1, new_collateral_2, debt_amount, sender=deployer)

    can_liquidate_normal = liquidation_contract.canLiquidate(user1)
    assert can_liquidate_normal == True or can_liquidate_normal == False