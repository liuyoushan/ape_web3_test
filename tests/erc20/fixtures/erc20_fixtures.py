"""
==============================================================================
ERC20 Fixtures 层 - 测试环境准备
==============================================================================
"""
import pytest
import yaml
from pathlib import Path
from ape import project
from tests.erc20.apis import ERC20API


@pytest.fixture(scope="module")
def erc20_test_data():
    """
    加载 ERC20 测试数据
    
    从 data/test_erc20.yaml 读取测试配置，包含：
    - common: 通用配置（代币名称、符号）
    - case_*: 各测试用例的参数
    
    Returns:
        dict: 测试数据字典
    """
    data_path = Path(__file__).parent.parent / "data" / "test_erc20.yaml"
    with open(data_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def erc20_contract(deployer, erc20_test_data):
    """
    部署 ERC20 合约
    
    使用测试数据中的通用配置部署 MyERC20 合约实例
    
    Args:
        deployer: 部署账户
        erc20_test_data: 测试数据
    
    Returns:
        Contract: 已部署的 ERC20 合约实例
    """
    data = erc20_test_data["common"]
    return project.MyERC20.deploy(
        data["token_name"],
        data["token_symbol"],
        sender=deployer
    )


@pytest.fixture(scope="module")
def erc20_api(erc20_contract):
    """
    创建 ERC20 API 封装实例
    
    Args:
        erc20_contract: 已部署的 ERC20 合约
    
    Returns:
        ERC20API: ERC20 合约交互封装对象
    """
    return ERC20API(erc20_contract)


@pytest.fixture(scope="function")
def erc20_token_with_balance(erc20_api, deployer, erc20_test_data):
    """
    创建带有余额的 ERC20 代币环境
    
    在 deployer 账户中 mint 指定数量的代币，
    用于需要初始余额的测试场景（如转账测试）
    
    Args:
        erc20_api: ERC20 API 实例
        deployer: 部署账户
        erc20_test_data: 测试数据
    
    Returns:
        ERC20API: 带有初始余额的 ERC20 API 实例
    """
    data = erc20_test_data["case_002_transfer"]
    mint_amount = data["mint_amount"]
    erc20_api.mint(deployer, mint_amount, deployer)
    return erc20_api