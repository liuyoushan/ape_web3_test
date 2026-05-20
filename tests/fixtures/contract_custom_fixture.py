"""
==============================================================================
Contract Custom Fixture 工厂 & 工具函数
==============================================================================
"""
import yaml
from pathlib import Path
from ape import project
import pytest


# ==============================================================================
# Fixtures
# ==============================================================================
@pytest.fixture(scope="module")
def contract_custom_test_data():
    """加载 contract_custom 测试数据"""
    data_path = Path(__file__).parent.parent / "data" / "test_contract_custom.yaml"
    with open(data_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="function")
def myerc20_token(deployer, project, contract_custom_test_data):
    """
    case_018~case_025 通用测试 token fixture
    """
    data = contract_custom_test_data["case_018_admin_permission"]
    return deployer.deploy(project.MyERC20, data["token_name"], data["token_symbol"])


@pytest.fixture(scope="function")
def role_constants(myerc20_token):
    """
    统一导出 MyERC20 的角色常量
    """
    return {
        "MINTER_ROLE": myerc20_token.MINTER_ROLE(),
        "PAUSER_ROLE": myerc20_token.PAUSER_ROLE(),
        "ADMIN_ROLE": myerc20_token.ADMIN_ROLE(),
    }
