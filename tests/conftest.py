"""
==============================================================================
共享 Fixture 配置
==============================================================================
"""
import pytest
from ape import project

# 直接导入 fixtures
from tests.fixtures.token_fixture import (
    erc20_test_data,
    token,
    eth_amount
)

# DEX 测试 fixtures
from tests.fixtures.dex_fixture import (
    dex_test_data,
    tokenA,
    tokenB,
    factory,
    router,
    tokens_with_balance,
    pair_with_liquidity
)

# Contract Custom 测试 fixtures
from tests.fixtures.contract_custom_fixture import (
    contract_custom_test_data,
    myerc20_token,
    role_constants
)


@pytest.fixture(scope="session")
def deployer(accounts):
    """部署者账户"""
    return accounts[0]


@pytest.fixture(scope="session")
def user1(accounts):
    """测试用户1"""
    return accounts[1]


@pytest.fixture(scope="session")
def user2(accounts):
    """测试用户2"""
    return accounts[2]


@pytest.fixture(scope="session")
def user3(accounts):
    """测试用户3"""
    return accounts[3]