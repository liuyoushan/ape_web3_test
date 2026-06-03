"""
==============================================================================
清算业务 Fixtures
==============================================================================
"""
import pytest
from pathlib import Path
import yaml
from ape import project


@pytest.fixture(scope="session")
def liquidation_test_data():
    """加载清算测试配置"""
    yaml_path = Path(__file__).parent.parent / "data" / "test_liquidation.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="function")
def liquidation_constants(liquidation_test_data):
    """清算常量配置"""
    return {
        # 预警线阈值
        "HEALTH_FACTOR_WARNING": liquidation_test_data["case_048_liquidation_trigger"]["health_factor_warning"],
        # 强平线阈值
        "HEALTH_FACTOR_LIQUIDATION": liquidation_test_data["case_048_liquidation_trigger"]["health_factor_liquidation"],
        # 清算奖励比例
        "LIQUIDATOR_REWARD_PCT": liquidation_test_data["case_049_normal_liquidation"]["liquidator_reward_pct"],
        # 平台手续费比例
        "PLATFORM_FEE_PCT": liquidation_test_data["case_049_normal_liquidation"]["platform_fee_pct"],
    }


@pytest.fixture(scope="function")
def collateral_token(project, deployer):
    """抵押品代币，用户用这个代币抵押，就会被清算者清算"""
    return project.MyERC20.deploy("Collateral", "COL", sender=deployer)


@pytest.fixture(scope="function")
def debt_token(project, deployer):
    """债务代币，借这个代币，就会被清算者清算"""
    return project.MyERC20.deploy("Debt", "DEBT", sender=deployer)


@pytest.fixture(scope="function")
def liquidation_contract(deployer, collateral_token, debt_token):
    """部署清算合约"""
    return project.Liquidation.deploy(collateral_token, debt_token, sender=deployer)


@pytest.fixture(scope="function")
def malicious_attacker(deployer, liquidation_contract, collateral_token, debt_token):
    """部署恶意攻击合约（用于重入攻击测试）"""
    return project.MaliciousAttacker.deploy(
        liquidation_contract,
        collateral_token,
        debt_token,
        sender=deployer
    )


@pytest.fixture(scope="function")
def liquidation_environment(
    deployer, user1, liquidation_test_data, liquidation_constants,
    collateral_token, debt_token, liquidation_contract
):
    """
    清算测试环境：
    - 部署抵押品和债务代币
    - 部署清算合约
    - 设置初始余额
    - 返回测试所需的所有对象
    """
    data = liquidation_test_data["case_048_liquidation_trigger"]
    
    # 铸造初始代币给用户
    collateral_amount = int(float(data["collateral_amount"]) * 10**18)
    debt_amount = int(float(data["debt_amount"]) * 10**18)
    
    collateral_token.mint(user1, collateral_amount, sender=deployer)
    debt_token.mint(deployer, debt_amount * 10, sender=deployer)  # 部署者持有债务代币
    
    # 给清算合约转账债务代币（用于借贷）
    debt_token.transfer(liquidation_contract, debt_amount * 5, sender=deployer)
    
    return {
        # 抵押品代币
        "collateral_token": collateral_token,
        # 债务代币  
        "debt_token": debt_token,
        # 清算合约
        "liquidation_contract": liquidation_contract,
        # 清算常量
        "constants": liquidation_constants,
        # 清算测试数据
        "data": data,
        # 初始抵押品数量
        "collateral_amount": collateral_amount,
        # 初始债务数量
        "debt_amount": debt_amount
    }
