"""
==============================================================================
【ERC20 场景】case_001 代币基础信息校验
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
from framework.core.formatters import format_ether


@allure.title("case_001 代币基础信息校验")
@allure.description("验证 MyERC20 合约的元数据：名称、符号、小数位数、初始总发行量")
@allure.tag("ERC20", "P0", "功能测试")
def test_erc20_001_metadata_verification(erc20_api, erc20_test_data):
    """
    case_001 代币基础信息校验
    
    验证 ERC20 合约的标准元数据接口：
    - name: 代币名称
    - symbol: 代币符号
    - decimals: 小数位数
    - totalSupply: 总发行量
    """
    log.step("case_001: 代币基础信息校验")
    
    data = erc20_test_data["common"]
    
    name = erc20_api.get_name()
    log.debug("代币名称: %s", name)
    assert name == data["token_name"], f"名称不正确: {name}"
    
    symbol = erc20_api.get_symbol()
    log.debug("代币符号: %s", symbol)
    assert symbol == data["token_symbol"], f"符号不正确: {symbol}"
    
    decimals = erc20_api.get_decimals()
    log.debug("小数位数: %d", decimals)
    assert decimals == data["expected_decimals"], f"小数位数不正确: {decimals}"
    
    total_supply = erc20_api.get_total_supply()
    log.debug("总发行量: %s", format_ether(total_supply))
    assert total_supply == data["expected_initial_supply"], f"初始总发行量不正确"
    
    log.success("✅ case_001 代币基础信息校验通过")