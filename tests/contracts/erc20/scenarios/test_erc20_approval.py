"""
==============================================================================
【ERC20 场景】授权功能测试
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
from framework.core.formatters import format_ether, parse_ether


@allure.title("case_004 授权功能测试")
@allure.description("验证 ERC20 approve 和 allowance 授权机制")
@allure.tag("ERC20", "P0", "功能测试", "授权")
def test_erc20_004_approve_authorization(erc20_token_with_balance, deployer, user1):
    """
    case_004 授权功能测试
    
    验证 ERC20 授权机制：
    - approve 设置授权额度
    - allowance 查询授权额度
    - transferFrom 使用授权额度转账
    - 授权额度正确扣减
    """
    erc20_api = erc20_token_with_balance
    
    log.step("case_004: 授权功能测试")
    
    log.info("步骤1: 查询初始授权额度")
    approve_amount = "200"
    initial_allowance = erc20_api.get_allowance(deployer, user1)
    log.debug(f"初始授权额度 (deployer->user1): {format_ether(initial_allowance)}")
    
    log.info("步骤2: 执行授权操作")
    tx = erc20_api.approve(user1, approve_amount, deployer)
    log.debug(f"授权操作完成，授权金额: {approve_amount}")
    
    log.info("步骤3: 验证授权结果")
    allowance_after = erc20_api.get_allowance(deployer, user1)
    log.debug(f"授权后额度: {format_ether(allowance_after)}")
    assert allowance_after == parse_ether(approve_amount), f"授权额度不符，预期: {format_ether(parse_ether(approve_amount))}, 实际: {format_ether(allowance_after)}"
    log.debug("授权验证通过")
    
    log.info("步骤4: 验证授权事件")
    approval_event = erc20_api.decode_approval_event(tx)
    log.debug(f"Approval 事件 - owner: {approval_event['owner']}, spender: {approval_event['spender']}, value: {format_ether(approval_event['value'])}")
    assert approval_event["owner"] == deployer, f"事件 owner 不符"
    assert approval_event["spender"] == user1, f"事件 spender 不符"
    assert approval_event["value"] == parse_ether(approve_amount), f"事件 value 不符"
    log.debug("授权事件验证通过")
    
    log.info("步骤5: 使用授权额度转账")
    transfer_amount = "100"
    balance_deployer_before = erc20_api.get_balance(deployer)
    balance_user1_before = erc20_api.get_balance(user1)
    log.debug(f"转账前 - deployer余额: {format_ether(balance_deployer_before)}, user1余额: {format_ether(balance_user1_before)}")
    
    erc20_api.transfer_from(deployer, user1, transfer_amount, user1)
    log.debug(f"转账操作完成，转账金额: {transfer_amount}")
    
    balance_deployer_after = erc20_api.get_balance(deployer)
    balance_user1_after = erc20_api.get_balance(user1)
    log.debug(f"转账后 - deployer余额: {format_ether(balance_deployer_after)}, user1余额: {format_ether(balance_user1_after)}")
    
    assert balance_deployer_after == balance_deployer_before - parse_ether(transfer_amount), f"deployer余额不符"
    assert balance_user1_after == balance_user1_before + parse_ether(transfer_amount), f"user1余额不符"
    log.debug("转账验证通过")
    
    log.info("步骤6: 验证授权额度扣减")
    remaining_allowance = erc20_api.get_allowance(deployer, user1)
    log.debug(f"剩余授权额度: {format_ether(remaining_allowance)}")
    expected_remaining = parse_ether(approve_amount) - parse_ether(transfer_amount)
    assert remaining_allowance == expected_remaining, f"剩余授权额度不符，预期: {format_ether(expected_remaining)}, 实际: {format_ether(remaining_allowance)}"
    log.debug("授权额度扣减验证通过")
    
    log.success("✅ case_004 授权功能测试通过")


@allure.title("case_005 超出授权额度转账测试")
@allure.description("验证超出授权额度时 transferFrom 失败")
@allure.tag("ERC20", "P0", "安全测试", "反向测试")
def test_erc20_005_transfer_from(erc20_token_with_balance, deployer, user1):
    """
    case_005 超出授权额度转账测试
    
    验证授权额度的安全保护：
    - 设置授权额度后，超出额度的转账被拒绝
    - 交易 revert
    """
    erc20_api = erc20_token_with_balance
    
    log.step("case_005: 超出授权额度转账测试")
    
    log.info("步骤1: 设置授权额度")
    approve_amount = "100"
    erc20_api.approve(user1, approve_amount, deployer)
    allowance = erc20_api.get_allowance(deployer, user1)
    log.debug(f"授权额度: {format_ether(allowance)}")
    
    log.info("步骤2: 尝试超出授权额度转账")
    transfer_amount = "150"
    log.debug(f"尝试转账金额: {transfer_amount} (超出授权额度 {approve_amount})")
    
    with reverts():
        erc20_api.transfer_from(deployer, user1, transfer_amount, user1)
    log.debug("超出授权额度转账被拒绝")
    
    log.info("步骤3: 验证授权额度未变化")
    allowance_after = erc20_api.get_allowance(deployer, user1)
    log.debug(f"授权额度未变化: {format_ether(allowance_after)}")
    assert allowance_after == parse_ether(approve_amount), f"授权额度不应变化"
    
    log.success("✅ case_005 超出授权额度转账测试通过")