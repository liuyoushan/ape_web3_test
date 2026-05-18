"""
==============================================================================
测试格式化工具
==============================================================================
"""

DECIMALS = 18


def format_ether(amount_wei, decimals=4):
    """
    将 wei 格式化为 ether 字符串（带单位）

    Args:
        amount_wei: 以 wei 为单位的金额
        decimals: 保留小数位数，默认4位

    Returns:
        str: 格式化后的字符串，如 "100.0000 ETH"

    Example:
        >>> format_ether(100000000000000000000)
        '100.0000 ETH'
    """
    return f"{amount_wei / 10**DECIMALS:.{decimals}f} ETH"


def format_token_amount(amount_wei, symbol="Token", decimals=4):
    """
    将 wei 格式化为代币数量字符串

    Args:
        amount_wei: 以 wei 为单位的金额
        symbol: 代币符号，默认 "Token"
        decimals: 保留小数位数，默认4位

    Returns:
        str: 格式化后的字符串，如 "100.0000 Token"

    Example:
        >>> format_token_amount(100000000000000000000)
        '100.0000 Token'
    """
    return f"{amount_wei / 10**DECIMALS:.{decimals}f} {symbol}"


def parse_ether(amount_ether):
    """
    解析 ether 字符串为 wei 整数

    Args:
        amount_ether: 金额（字符串，如 "1000 ether"）

    Returns:
        int: wei 整数

    Example:
        >>> parse_ether("1000 ether")
        1000000000000000000000
    """
    return int(float(amount_ether.replace(" ether", "")) * 10**18)
