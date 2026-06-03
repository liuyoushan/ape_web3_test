"""
==============================================================================
安全高级测试 Fixtures
==============================================================================
"""
import pytest
import yaml
from pathlib import Path
from ape import project

# 测试数据文件路径
TEST_DATA_PATH = Path(__file__).parent.parent / "data" / "test_security_advanced.yaml"


@pytest.fixture(scope="session")
def security_test_data():
    """安全高级测试数据"""
    with open(TEST_DATA_PATH, "r") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def erc20_token(deployer):
    """部署一个 ERC20 代币合约用于测试"""
    token = deployer.deploy(project.MyERC20, "Test Token", "TTK")
    return token