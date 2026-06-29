"""
==============================================================================
【ERC20 场景】铸币与销毁功能测试
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

from framework.core.logger import log
from framework.core.formatters import format_ether, parse_ether


@allure.title("case_006 铸币功能测试")
@allure.description("验证拥有 MINTER_ROLE 的账户可以铸造代币")
@allure.tag("ERC20", "P0", "功能测试", "铸币")
def test_erc20_006_mint_tokens(erc20_api, deployer, user1, erc20_test_data):
    """
    case_006 铸币功能测试
    
    验证代币铸造功能：
    - 铸造后接收方余额增加
    - 总供应量增加
    - Transfer 事件 from=0x0
    """
    data = erc20_test_data["case_006_mint"]
    mint_amount = data["mint_amount"]
    
    log.step("case_006: 铸币功能测试")
    log.debug("铸造金额: %s", mint_amount)
    
    balance_user1_before = erc20_api.get_balance(user1)
    total_supply_before = erc20_api.get_total_supply()
    
    tx = erc20_api.mint(user1, mint_amount, deployer)
    
    balance_user1_after = erc20_api.get_balance(user1)
    total_supply_after = erc20_api.get_total_supply()
    
    expected_mint = parse_ether(mint_amount)
    assert balance_user1_after == balance_user1_before + expected_mint
    assert total_supply_after == total_supply_before + expected_mint
    
    transfer_event = erc20_api.decode_transfer_event(tx)
    assert transfer_event["from"] == "0x" + "0" * 40
    assert transfer_event["to"] == user1
    assert transfer_event["value"] == expected_mint
    
    log.success("✅ case_006 铸币功能测试通过")


@allure.title("case_007 销毁代币功能测试")
@allure.description("验证用户可以销毁自己持有的代币")
@allure.tag("ERC20", "P0", "功能测试", "销毁")
def test_erc20_007_burn_tokens(erc20_api, deployer, user1):
    """
    case_007 销毁代币功能测试
    
    验证代币销毁功能：
    - 销毁后账户余额减少
    - 总供应量减少
    - Transfer 事件 to=0x0
    """
    mint_amount = "200"
    burn_amount = "100"
    
    log.step("case_007: 销毁代币功能测试")
    
    erc20_api.mint(user1, mint_amount, deployer)
    
    balance_user1_before = erc20_api.get_balance(user1)
    total_supply_before = erc20_api.get_total_supply()
    
    tx = erc20_api.burn(burn_amount, user1)
    
    balance_user1_after = erc20_api.get_balance(user1)
    total_supply_after = erc20_api.get_total_supply()
    
    expected_burn = parse_ether(burn_amount)
    assert balance_user1_after == balance_user1_before - expected_burn
    assert total_supply_after == total_supply_before - expected_burn
    
    transfer_event = erc20_api.decode_transfer_event(tx)
    assert transfer_event["from"] == user1
    assert transfer_event["to"] == "0x" + "0" * 40
    assert transfer_event["value"] == expected_burn
    
    log.success("✅ case_007 销毁代币功能测试通过")