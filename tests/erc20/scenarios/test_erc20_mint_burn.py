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
    log.debug(f"铸造金额: {mint_amount}")
    
    log.info("步骤1: 记录铸造前状态")
    balance_user1_before = erc20_api.get_balance(user1)
    total_supply_before = erc20_api.get_total_supply()
    log.debug(f"铸造前 - user1余额: {format_ether(balance_user1_before)}, 总供应量: {format_ether(total_supply_before)}")
    
    log.info("步骤2: 执行铸造操作")
    tx = erc20_api.mint(user1, mint_amount, deployer)
    log.debug(f"铸造操作完成")
    
    log.info("步骤3: 验证余额和总供应量变化")
    balance_user1_after = erc20_api.get_balance(user1)
    total_supply_after = erc20_api.get_total_supply()
    log.debug(f"铸造后 - user1余额: {format_ether(balance_user1_after)}, 总供应量: {format_ether(total_supply_after)}")
    
    expected_mint = parse_ether(mint_amount)
    assert balance_user1_after == balance_user1_before + expected_mint, f"user1余额不符，预期: {format_ether(balance_user1_before + expected_mint)}, 实际: {format_ether(balance_user1_after)}"
    assert total_supply_after == total_supply_before + expected_mint, f"总供应量不符，预期: {format_ether(total_supply_before + expected_mint)}, 实际: {format_ether(total_supply_after)}"
    log.debug("余额和总供应量验证通过")
    
    log.info("步骤4: 验证 Transfer 事件")
    transfer_event = erc20_api.decode_transfer_event(tx)
    log.debug(f"Transfer 事件 - from: {transfer_event['from']}, to: {transfer_event['to']}, value: {format_ether(transfer_event['value'])}")
    assert transfer_event["from"] == "0x" + "0" * 40, f"事件 from 应为零地址"
    assert transfer_event["to"] == user1, f"事件 to 应为 user1"
    assert transfer_event["value"] == expected_mint, f"事件 value 不符"
    log.debug("Transfer 事件验证通过")
    
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
    log.debug(f"测试数据 - 铸造金额: {mint_amount}, 销毁金额: {burn_amount}")
    
    log.info("步骤1: 先铸造代币给用户")
    erc20_api.mint(user1, mint_amount, deployer)
    balance_after_mint = erc20_api.get_balance(user1)
    log.debug(f"铸造后 user1余额: {format_ether(balance_after_mint)}")
    
    log.info("步骤2: 记录销毁前状态")
    balance_user1_before = erc20_api.get_balance(user1)
    total_supply_before = erc20_api.get_total_supply()
    log.debug(f"销毁前 - user1余额: {format_ether(balance_user1_before)}, 总供应量: {format_ether(total_supply_before)}")
    
    log.info("步骤3: 执行销毁操作")
    tx = erc20_api.burn(burn_amount, user1)
    log.debug(f"销毁操作完成")
    
    log.info("步骤4: 验证余额和总供应量变化")
    balance_user1_after = erc20_api.get_balance(user1)
    total_supply_after = erc20_api.get_total_supply()
    log.debug(f"销毁后 - user1余额: {format_ether(balance_user1_after)}, 总供应量: {format_ether(total_supply_after)}")
    
    expected_burn = parse_ether(burn_amount)
    assert balance_user1_after == balance_user1_before - expected_burn, f"user1余额不符，预期: {format_ether(balance_user1_before - expected_burn)}, 实际: {format_ether(balance_user1_after)}"
    assert total_supply_after == total_supply_before - expected_burn, f"总供应量不符，预期: {format_ether(total_supply_before - expected_burn)}, 实际: {format_ether(total_supply_after)}"
    log.debug("余额和总供应量验证通过")
    
    log.info("步骤5: 验证 Transfer 事件")
    transfer_event = erc20_api.decode_transfer_event(tx)
    log.debug(f"Transfer 事件 - from: {transfer_event['from']}, to: {transfer_event['to']}, value: {format_ether(transfer_event['value'])}")
    assert transfer_event["from"] == user1, f"事件 from 应为 user1"
    assert transfer_event["to"] == "0x" + "0" * 40, f"事件 to 应为零地址"
    assert transfer_event["value"] == expected_burn, f"事件 value 不符"
    log.debug("Transfer 事件验证通过")
    
    log.success("✅ case_007 销毁代币功能测试通过")