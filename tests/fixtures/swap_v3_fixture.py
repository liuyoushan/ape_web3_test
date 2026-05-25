"""Uniswap V3 测试 Fixture"""
import yaml
from pathlib import Path
import pytest
from tests.helpers.formatters import parse_ether


@pytest.fixture(scope="session")
def swap_v3_test_data():
    """加载 V3 测试数据配置"""
    yaml_path = Path(__file__).parent.parent / "data" / "test_dex_swap_v3.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="function")
def v3_tokens(project, deployer):
    """部署测试用代币"""
    token_a = project.MyERC20.deploy("TokenA", "TKA", sender=deployer)
    token_b = project.MyERC20.deploy("TokenB", "TKB", sender=deployer)
    return token_a, token_b


@pytest.fixture(scope="function")
def v3_factory_and_router(project, deployer):
    """部署 V3 用的 Factory 和 Router（复用 V2 架构模拟）"""
    factory = project.MiniSwapFactory.deploy(sender=deployer)
    router = project.MiniSwapRouter.deploy(factory, sender=deployer)
    return factory, router


@pytest.fixture(scope="function")
def v3_liquidity_environment(project, deployer, user1, v3_tokens, v3_factory_and_router, swap_v3_test_data):
    """V3 流动性测试环境：代币 + Factory/Router + 用户初始余额"""
    data = swap_v3_test_data["case_055_concentrated_liquidity_add"]
    mint_amount = parse_ether(data["mint_amount"])
    token_a, token_b = v3_tokens
    factory, router = v3_factory_and_router
    
    token_a.mint(user1, mint_amount, sender=deployer)
    token_b.mint(user1, mint_amount, sender=deployer)
    
    return {
        "token_a": token_a,
        "token_b": token_b,
        "factory": factory,
        "router": router,
        "user1": user1,
        "deployer": deployer
    }


@pytest.fixture(scope="function")
def v3_pool(project, deployer, v3_tokens, swap_v3_test_data):
    """部署 V3 Pool（预留接口）"""
    token_a, token_b = v3_tokens
    fee_tier = swap_v3_test_data["fee_tiers"]["tier_0_3"]
    return None


@pytest.fixture(scope="function")
def v3_router(project, deployer, v3_pool):
    """部署 V3 Router（预留接口）"""
    return None