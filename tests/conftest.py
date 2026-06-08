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
    eth_amount,
    token_with_balance
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

# 清算业务测试 fixtures
from tests.fixtures.liquidation_fixture import (
    liquidation_test_data,
    liquidation_constants,
    collateral_token,
    debt_token,
    liquidation_contract,
    malicious_attacker,
    liquidation_environment
)

# Swap V3 测试 fixtures
from tests.fixtures.swap_v3_fixture import (
    swap_v3_test_data,
    v3_tokens,
    v3_factory_and_router,
    v3_liquidity_environment
)

# 安全高级测试 fixtures
from tests.fixtures.security_fixture import (
    security_test_data,
    erc20_token,
    staking_contract,
    timelock_contract,
    reentrancy_vault,
    vulnerable_vault
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