"""
==============================================================================
DEX 测试 Fixtures
==============================================================================
"""

import pytest
from ape import project
from tests.helpers.formatters import parse_ether


@pytest.fixture(scope="function")
def dex_test_data():
    """DEX 测试数据"""
    import yaml
    import os
    
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "test_dex_swap.yaml")
    with open(data_path, "r") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="function")
def tokenA(deployer, dex_test_data):
    """部署 TokenA"""
    data = dex_test_data["common"]
    return project.MyERC20.deploy(data["tokenA_name"], data["tokenA_symbol"], sender=deployer)


@pytest.fixture(scope="function")
def tokenB(deployer, dex_test_data):
    """部署 TokenB"""
    data = dex_test_data["common"]
    return project.MyERC20.deploy(data["tokenB_name"], data["tokenB_symbol"], sender=deployer)


@pytest.fixture(scope="function")
def factory(deployer):
    """部署 MiniSwapFactory"""
    return project.MiniSwapFactory.deploy(sender=deployer)


@pytest.fixture(scope="function")
def router(deployer, factory):
    """部署 MiniSwapRouter"""
    return project.MiniSwapRouter.deploy(factory, sender=deployer)


@pytest.fixture(scope="function")
def tokens_with_balance(tokenA, tokenB, deployer, user1, dex_test_data):
    """为用户铸造代币"""
    data = dex_test_data["common"]
    mint_amount = parse_ether("10000")
    
    tokenA.mint(user1, mint_amount, sender=deployer)
    tokenB.mint(user1, mint_amount, sender=deployer)
    
    return tokenA, tokenB


@pytest.fixture(scope="function")
def pair_with_liquidity(tokenA, tokenB, factory, router, deployer, user1):
    """创建交易对并添加流动性"""
    add_liquidity_amount = parse_ether("1000")
    
    tokenA.approve(router, add_liquidity_amount, sender=user1)
    tokenB.approve(router, add_liquidity_amount, sender=user1)
    
    router.addLiquidity(
        tokenA,
        tokenB,
        add_liquidity_amount,
        add_liquidity_amount,
        user1,
        sender=user1
    )
    
    pair_addr = factory.getPair(tokenA, tokenB)
    return project.MiniSwapPair.at(pair_addr)