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
    
    approve_amount = "200"
    initial_allowance = erc20_api.get_allowance(deployer, user1)
    log.debug("初始授权额度: %s", format_ether(initial_allowance))
    
    tx = erc20_api.approve(user1, approve_amount, deployer)
    
    allowance_after = erc20_api.get_allowance(deployer, user1)
    log.debug("授权后额度: %s", format_ether(allowance_after))
    assert allowance_after == parse_ether(approve_amount)
    
    approval_event = erc20_api.decode_approval_event(tx)
    assert approval_event["owner"] == deployer
    assert approval_event["spender"] == user1
    assert approval_event["value"] == parse_ether(approve_amount)
    
    transfer_amount = "100"
    
    balance_deployer_before = erc20_api.get_balance(deployer)
    balance_user1_before = erc20_api.get_balance(user1)
    
    erc20_api.transfer_from(deployer, user1, transfer_amount, user1)
    
    balance_deployer_after = erc20_api.get_balance(deployer)
    balance_user1_after = erc20_api.get_balance(user1)
    
    assert balance_deployer_after == balance_deployer_before - parse_ether(transfer_amount)
    assert balance_user1_after == balance_user1_before + parse_ether(transfer_amount)
    
    remaining_allowance = erc20_api.get_allowance(deployer, user1)
    log.debug("剩余授权额度: %s", format_ether(remaining_allowance))
    assert remaining_allowance == parse_ether(approve_amount) - parse_ether(transfer_amount)
    
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
    
    approve_amount = "100"
    erc20_api.approve(user1, approve_amount, deployer)
    
    transfer_amount = "150"
    log.debug("授权额度: %s, 尝试转移: %s", approve_amount, transfer_amount)
    
    with reverts():
        erc20_api.transfer_from(deployer, user1, transfer_amount, user1)
    
    log.success("✅ case_005 超出授权额度转账测试通过")