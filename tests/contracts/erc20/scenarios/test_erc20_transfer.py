"""
==============================================================================
【ERC20 场景】转账功能测试
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


@allure.title("case_002 正常转账功能测试")
@allure.description("普通地址间转账，校验余额变更、链上事件、交易状态")
@allure.tag("ERC20", "P0", "功能测试", "转账")
def test_erc20_002_normal_transfer(erc20_token_with_balance, deployer, user1, erc20_test_data):
    """
    case_002 正常转账功能测试
    
    验证普通地址间的代币转账功能：
    - 发送方余额减少
    - 接收方余额增加
    - 总供应量不变
    - Transfer 事件正确触发
    """
    erc20_api = erc20_token_with_balance
    data = erc20_test_data["case_002_transfer"]
    transfer_amount = data["transfer_amount"]
    
    log.step("case_002: 正常转账功能测试")
    log.debug("转账金额: %s", transfer_amount)
    
    balance_deployer_before = erc20_api.get_balance(deployer)
    balance_user1_before = erc20_api.get_balance(user1)
    total_supply_before = erc20_api.get_total_supply()
    
    log.debug("deployer 余额: %s", format_ether(balance_deployer_before))
    log.debug("user1 余额: %s", format_ether(balance_user1_before))
    
    tx = erc20_api.transfer(user1, transfer_amount, deployer)
    
    balance_deployer_after = erc20_api.get_balance(deployer)
    balance_user1_after = erc20_api.get_balance(user1)
    total_supply_after = erc20_api.get_total_supply()
    
    log.debug("deployer 余额: %s", format_ether(balance_deployer_after))
    log.debug("user1 余额: %s", format_ether(balance_user1_after))
    
    expected_transfer = parse_ether(transfer_amount)
    assert balance_deployer_after == balance_deployer_before - expected_transfer
    assert balance_user1_after == balance_user1_before + expected_transfer
    assert total_supply_after == total_supply_before
    
    transfer_event = erc20_api.decode_transfer_event(tx)
    assert transfer_event["from"] == deployer
    assert transfer_event["to"] == user1
    assert transfer_event["value"] == expected_transfer
    
    log.success("✅ case_002 正常转账测试通过")


@allure.title("case_002_002 用户自转账测试")
@allure.description("验证用户给自己转账的边界情况")
@allure.tag("ERC20", "P1", "边界测试", "转账")
def test_erc20_002_normal_transfer_002(erc20_api, deployer, user1):
    """
    case_002_002 用户自转账测试
    
    验证用户给自己转账的边界场景：
    - 余额保持不变
    - Transfer 事件正常触发（from=to）
    """
    transfer_amount = "50"
    
    log.step("case_002_002: 用户自转账测试")
    
    erc20_api.mint(user1, transfer_amount, deployer)
    
    balance_before = erc20_api.get_balance(user1)
    log.debug("user1 转账前余额: %s", format_ether(balance_before))
    
    tx = erc20_api.transfer(user1, transfer_amount, user1)
    
    balance_after = erc20_api.get_balance(user1)
    log.debug("user1 转账后余额: %s", format_ether(balance_after))
    
    assert balance_after == balance_before
    
    transfer_event = erc20_api.decode_transfer_event(tx)
    assert transfer_event["from"] == user1
    assert transfer_event["to"] == user1
    assert transfer_event["value"] == parse_ether(transfer_amount)
    
    log.success("✅ case_002_002 用户自转账测试通过")


@allure.title("case_003 余额不足转账失败测试")
@allure.description("验证余额不足时转账失败并抛出异常")
@allure.tag("ERC20", "P0", "安全测试", "反向测试")
def test_erc20_003_insufficient_balance_transfer(erc20_token_with_balance, deployer, user1):
    """
    case_003 余额不足转账失败测试
    
    验证余额不足时转账被拒绝：
    - 尝试转账金额超过账户余额
    - 交易 revert，状态回滚
    """
    erc20_api = erc20_token_with_balance
    
    log.step("case_003: 余额不足转账失败测试")
    
    balance_deployer = erc20_api.get_balance(deployer)
    log.debug("deployer 余额: %s", format_ether(balance_deployer))
    
    transfer_amount = balance_deployer + 1
    
    with reverts():
        erc20_api.contract.transfer(user1, transfer_amount, sender=deployer)
    
    log.success("✅ case_003 余额不足转账失败测试通过")