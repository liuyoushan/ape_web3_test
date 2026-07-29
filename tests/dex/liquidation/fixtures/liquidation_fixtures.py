"""
==============================================================================
Liquidation Fixtures 层 - 测试环境准备
==============================================================================
"""
import pytest
import yaml
from pathlib import Path
from ape import project
from tests.dex.liquidation.apis import LiquidationAPI
from framework.core.formatters import parse_ether, format_ether


@pytest.fixture(scope="session")
def liquidation_test_data():
    """
    加载清算测试数据
    
    从 data/test_liquidation.yaml 读取测试配置，包含：
    - case_*: 各测试用例的参数（抵押金额、债务金额等）
    
    Returns:
        dict: 测试数据字典
    """
    data_path = Path(__file__).parent.parent / "data" / "test_liquidation.yaml"
    with open(data_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="function")
def collateral_token(deployer):
    """
    部署抵押代币合约
    
    Args:
        deployer: 部署账户
        
    Returns:
        Contract: 已部署的 Collateral 代币合约实例
    """
    return project.MyERC20.deploy("Collateral", "COL", sender=deployer)


@pytest.fixture(scope="function")
def debt_token(deployer):
    """
    部署债务代币合约
    
    Args:
        deployer: 部署账户
        
    Returns:
        Contract: 已部署的 Debt 代币合约实例
    """
    return project.MyERC20.deploy("Debt", "DEBT", sender=deployer)


@pytest.fixture(scope="function")
def liquidation_contract(deployer, collateral_token, debt_token):
    """
    部署清算合约（未封装）
    
    Args:
        deployer: 部署账户
        collateral_token: 抵押代币合约
        debt_token: 债务代币合约
        
    Returns:
        Contract: 已部署的 Liquidation 合约实例
    """
    return project.Liquidation.deploy(collateral_token, debt_token, sender=deployer)


@pytest.fixture(scope="function")
def liquidation_contract_api(deployer, collateral_token, debt_token):
    """
    部署清算合约并封装 API
    
    Args:
        deployer: 部署账户
        collateral_token: 抵押代币合约
        debt_token: 债务代币合约
        
    Returns:
        LiquidationAPI: 清算合约交互封装对象
    """
    contract = project.Liquidation.deploy(collateral_token, debt_token, sender=deployer)
    return LiquidationAPI(contract)


@pytest.fixture(scope="function")
def liquidation_environment(deployer, user1, liquidation_test_data, collateral_token, debt_token, liquidation_contract):
    """
    创建完整的清算测试环境
    
    准备工作：
    1. 为用户 mint 抵押资产
    2. 为合约准备债务资产
    3. 设置用户初始借贷状态
    
    Args:
        deployer: 部署账户
        user1: 测试用户账户
        liquidation_test_data: 清算测试数据
        collateral_token: 抵押代币合约
        debt_token: 债务代币合约
        liquidation_contract: 清算合约
        
    Returns:
        dict: 包含测试环境的字典
    """
    data = liquidation_test_data["case_048_liquidation_trigger"]
    
    collateral_amount = parse_ether(str(data["collateral_amount"]))
    debt_amount = parse_ether(str(data["debt_amount"]))
    
    collateral_token.mint(user1, collateral_amount, sender=deployer)
    debt_token.mint(deployer, debt_amount * 10, sender=deployer)
    debt_token.transfer(liquidation_contract, debt_amount * 5, sender=deployer)
    
    return {
        "collateral_token": collateral_token,
        "debt_token": debt_token,
        "liquidation_contract": liquidation_contract,
        "collateral_amount": collateral_amount,
        "debt_amount": debt_amount,
    }


@pytest.fixture(scope="function")
def liquidation_env(
    deployer, user1, liquidation_test_data,
    collateral_token, debt_token, liquidation_contract_api
):
    """
    创建封装 API 的清算测试环境
    
    与 liquidation_environment 类似，但使用封装后的 API 对象
    
    Args:
        deployer: 部署账户
        user1: 测试用户账户
        liquidation_test_data: 清算测试数据
        collateral_token: 抵押代币合约
        debt_token: 债务代币合约
        liquidation_contract_api: 封装后的清算 API
        
    Returns:
        dict: 包含测试环境的字典
    """
    data = liquidation_test_data["case_048_liquidation_trigger"]
    
    collateral_amount = int(float(data["collateral_amount"]) * 10**18)
    debt_amount = int(float(data["debt_amount"]) * 10**18)
    
    collateral_token.mint(user1, collateral_amount, sender=deployer)
    debt_token.mint(deployer, debt_amount * 10, sender=deployer)
    debt_token.transfer(liquidation_contract_api.contract, debt_amount * 5, sender=deployer)
    
    return {
        "collateral_token": collateral_token,
        "debt_token": debt_token,
        "liquidation_api": liquidation_contract_api,
        "collateral_amount": collateral_amount,
        "debt_amount": debt_amount,
    }