"""Uniswap V3 测试 Fixture"""
import yaml
from pathlib import Path
import pytest


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
def v3_pool(project, deployer, v3_tokens, swap_v3_test_data):
    """部署 V3 Pool（预留接口）"""
    token_a, token_b = v3_tokens
    fee_tier = swap_v3_test_data["fee_tiers"]["tier_0_3"]
    # TODO: 部署 V3 Pool 合约
    # pool = project.MiniSwapV3Pool.deploy(token_a, token_b, fee_tier, sender=deployer)
    # return pool
    return None


@pytest.fixture(scope="function")
def v3_router(project, deployer, v3_pool):
    """部署 V3 Router（预留接口）"""
    # TODO: 部署 V3 Router 合约
    # router = project.MiniSwapV3Router.deploy(sender=deployer)
    # return router
    return None