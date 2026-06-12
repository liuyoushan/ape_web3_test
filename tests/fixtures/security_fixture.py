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


@pytest.fixture(scope="session")
def staking_contract(deployer, erc20_token):
    """部署质押合约用于测试"""
    # 部署奖励代币
    reward_token = deployer.deploy(project.MyERC20, "Reward Token", "RWT")
    
    # 部署质押合约
    reward_per_block = 1000000000000000000  # 1 token per block
    staking = deployer.deploy(
        project.StakingContract,
        erc20_token.address,
        reward_token.address,
        reward_per_block
    )
    
    # 给质押合约铸造奖励代币
    reward_token.mint(staking.address, 1000000 * 10**18, sender=deployer)
    
    return staking, reward_token


@pytest.fixture(scope="session")
def timelock_contract(deployer, security_test_data):
    """部署时间锁合约用于测试"""
    data = security_test_data.get("case_029_timelock_blocklock", {})
    lock_duration = data.get("lock_duration", 86400)
    lock_blocks = data.get("lock_blocks", 100)
    
    timelock = deployer.deploy(
        project.TimeLockContract,
        lock_duration,
        lock_blocks
    )
    
    return timelock


@pytest.fixture(scope="session")
def reentrancy_vault(deployer):
    """部署带防重入锁的合约用于测试"""
    vault = deployer.deploy(project.ReentrancyVault)
    return vault


@pytest.fixture(scope="session")
def vulnerable_vault(deployer):
    """部署不带防重入锁的合约用于测试（演示漏洞）"""
    vault = deployer.deploy(project.VulnerableVault)
    return vault