"""
==============================================================================
ERC20 Fixture 工厂 & 工具函数
==============================================================================
"""
import yaml
from pathlib import Path
from ape import project
import pytest
from tests.helpers.formatters import parse_ether


# ==============================================================================
# 工具函数
# ==============================================================================
def mint_token(token, sender, recipient, amount_ether):
    """
    通用的 mint 工具函数

    :param token: Token 合约实例
    :param sender: 发送交易的账户（通常是 deployer）
    :param recipient: 接收 token 的账户
    :param amount_ether: 金额（字符串，如 "1000 ether"）
    :return: Token 合约实例（方便链式调用）
    """
    amount = parse_ether(amount_ether)
    token.mint(recipient, amount, sender=sender)
    return token


# ==============================================================================
# Fixtures
# ==============================================================================
@pytest.fixture(scope="module")
def erc20_test_data():
    """加载 ERC20 测试数据"""
    data_path = Path(__file__).parent.parent / "data" / "test_erc20.yaml"
    with open(data_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def token(deployer, erc20_test_data):
    """部署共享的 ERC20 代币（模块级别）"""
    data = erc20_test_data["common"]
    return project.MyERC20.deploy(
        data["token_name"],
        data["token_symbol"],
        sender=deployer
    )


@pytest.fixture(scope="module")
def eth_amount():
    """ETH 金额解析（wei 转换）"""
    def _eth(amount):
        return amount * 10**18
    return _eth


@pytest.fixture(scope="function")
def token_with_balance(token, deployer, erc20_test_data):
    """有初始余额的 token（每个函数重置）"""
    data = erc20_test_data["case_002_transfer"]
    mint_amount = int(float(data["mint_amount"].replace(" ether", "")) * 10**18)
    token.mint(deployer, mint_amount, sender=deployer)
    return token
