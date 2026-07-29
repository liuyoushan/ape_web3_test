"""
==============================================================================
Contract Custom Fixtures 层 - 测试环境准备
==============================================================================
"""
import pytest
import yaml
from pathlib import Path
from ape import project


@pytest.fixture(scope="module")
def contract_custom_test_data():
    """
    加载自定义合约测试数据
    
    从 data/test_contract_custom.yaml 读取测试配置，包含：
    - case_018_admin_permission: 管理员权限测试参数
    - case_019_global_parameter_rw: 全局参数读写测试参数
    - case_020_custom_business_logic: 自定义业务逻辑测试参数
    
    Returns:
        dict: 测试数据字典
    """
    data_path = Path(__file__).parent.parent / "data" / "test_contract_custom.yaml"
    with open(data_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="function")
def myerc20_token(deployer, contract_custom_test_data):
    """
    部署自定义 ERC20 代币合约
    
    Args:
        deployer: 部署账户
        contract_custom_test_data: 自定义合约测试数据
        
    Returns:
        Contract: 已部署的 MyERC20 合约实例（支持角色权限控制）
    """
    data = contract_custom_test_data["case_018_admin_permission"]
    return deployer.deploy(project.MyERC20, data["token_name"], data["token_symbol"])


@pytest.fixture(scope="function")
def role_constants(myerc20_token):
    """
    获取角色常量值
    
    从 MyERC20 合约中读取各角色的字节码常量，用于权限校验测试。
    
    Args:
        myerc20_token: MyERC20 合约实例
        
    Returns:
        dict: 包含 MINTER_ROLE、PAUSER_ROLE、ADMIN_ROLE 的字典
    """
    return {
        "MINTER_ROLE": myerc20_token.MINTER_ROLE(),
        "PAUSER_ROLE": myerc20_token.PAUSER_ROLE(),
        "ADMIN_ROLE": myerc20_token.ADMIN_ROLE(),
    }