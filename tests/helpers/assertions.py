"""
==============================================================================
测试断言助手
==============================================================================
"""

def assert_token_metadata(token, expected_name, expected_symbol, expected_decimals, expected_supply):
    """
    验证代币元数据
    
    Args:
        token: 合约实例
        expected_name: 预期名称
        expected_symbol: 预期符号
        expected_decimals: 预期小数位
        expected_supply: 预期初始总供应量
    """
    assert token.name() == expected_name, f"代币名称不匹配"
    assert token.symbol() == expected_symbol, f"代币符号不匹配"
    assert token.decimals() == expected_decimals, f"代币小数位不匹配"
    assert token.totalSupply() == expected_supply, f"初始总供应量不匹配"


def assert_balance(token, account, expected):
    """
    验证账户余额
    
    Args:
        token: 合约实例
        account: 账户地址/对象
        expected: 预期余额
    """
    assert token.balanceOf(account) == expected, f"账户余额不匹配"


def assert_transfer_event(receipt, from_, to, value):
    """
    验证 Transfer 事件
    
    Args:
        receipt: 交易收据
        from_: 发送方地址
        to: 接收方地址
        value: 转移金额
    """
    events = [e for e in receipt.events if e.event_name == "Transfer"]
    assert len(events) == 1, f"应该触发1个Transfer事件"
    event = events[0]
    assert event.event_arguments["from"] == from_, f"Transfer事件的from地址不匹配"
    assert event.event_arguments["to"] == to, f"Transfer事件的to地址不匹配"
    assert event.event_arguments["value"] == value, f"Transfer事件的value不匹配"


def assert_address_format(address):
    """
    验证地址格式
    
    Args:
        address: 待验证的地址
    """
    assert address != "", "地址不能为空"
    assert address.startswith("0x"), "地址应该以0x开头"
    assert len(address) == 42, "以太坊地址长度应该是42个字符"


def assert_approval_event(receipt, owner, spender, value):
    """
    验证 Approval 事件
    
    Args:
        receipt: 交易收据
        owner: 授权方地址
        spender: 被授权方地址
        value: 授权金额
    """
    events = [e for e in receipt.events if e.event_name == "Approval"]
    assert len(events) == 1, f"应该触发1个Approval事件"
    event = events[0]
    assert event.event_arguments["owner"] == owner, f"Approval事件的owner地址不匹配"
    assert event.event_arguments["spender"] == spender, f"Approval事件的spender地址不匹配"
    assert event.event_arguments["value"] == value, f"Approval事件的value不匹配"
