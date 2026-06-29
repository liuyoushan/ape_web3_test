"""
==============================================================================
Security Fixtures 层 - 测试环境准备
==============================================================================
"""
import pytest
import yaml
from pathlib import Path
from ape import project
from tests.security.apis import ReentrancyVaultAPI, VulnerableVaultAPI, StakingAPI, TimeLockAPI


@pytest.fixture(scope="session")
def security_test_data():
    """
    加载安全测试数据
    
    从 data/test_security_advanced.yaml 读取测试配置，包含：
    - case_026_approve_security: 授权安全测试参数
    - case_027_batch_operations: 批量操作测试参数
    - case_028_staking_mining: 质押挖矿测试参数
    - case_029_timelock_blocklock: 时间锁测试参数
    - case_030_reentrancy_guard: 重入防护测试参数
    - case_031_integer_overflow_underflow: 整数溢出测试参数
    - case_032_proxy_upgrade: 代理升级测试参数
    
    Returns:
        dict: 测试数据字典
    """
    data_path = Path(__file__).parent.parent / "data" / "test_security_advanced.yaml"
    with open(data_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="function")
def erc20_token(deployer):
    """
    部署安全测试用 ERC20 代币合约
    
    Args:
        deployer: 部署账户
        
    Returns:
        Contract: 已部署的 MyERC20 合约实例（名称: Security Token，符号: SEC）
    """
    return project.MyERC20.deploy("Security Token", "SEC", sender=deployer)


@pytest.fixture(scope="function")
def reentrancy_vault(deployer):
    """
    部署重入防护金库合约（未封装）
    
    Args:
        deployer: 部署账户
        
    Returns:
        Contract: 已部署的 ReentrancyVault 合约实例
    """
    return project.ReentrancyVault.deploy(sender=deployer)


@pytest.fixture(scope="function")
def reentrancy_vault_api(deployer):
    """
    部署重入防护金库合约并封装 API
    
    Args:
        deployer: 部署账户
        
    Returns:
        ReentrancyVaultAPI: 重入防护金库交互封装对象
    """
    vault = project.ReentrancyVault.deploy(sender=deployer)
    return ReentrancyVaultAPI(vault)


@pytest.fixture(scope="function")
def vulnerable_vault(deployer):
    """
    部署存在重入漏洞的金库合约（未封装）
    
    Args:
        deployer: 部署账户
        
    Returns:
        Contract: 已部署的 VulnerableVault 合约实例
    """
    return project.VulnerableVault.deploy(sender=deployer)


@pytest.fixture(scope="function")
def vulnerable_vault_api(deployer):
    """
    部署存在重入漏洞的金库合约并封装 API
    
    Args:
        deployer: 部署账户
        
    Returns:
        VulnerableVaultAPI: 漏洞金库交互封装对象
    """
    vault = project.VulnerableVault.deploy(sender=deployer)
    return VulnerableVaultAPI(vault)


@pytest.fixture(scope="function")
def staking_contract(deployer):
    """
    部署质押合约（未封装）并准备奖励代币
    
    完整流程：
    1. 部署奖励代币合约
    2. 部署质押合约（配置奖励代币和奖励速率）
    3. 为质押合约 mint 足够的奖励代币
    
    Args:
        deployer: 部署账户
        
    Returns:
        tuple: (staking_contract, reward_token)
    """
    reward_token = project.MyERC20.deploy("Reward Token", "RWT", sender=deployer)
    reward_per_block = 10**18
    staking = project.StakingContract.deploy(
        reward_token.address, reward_token.address, reward_per_block, sender=deployer
    )
    reward_token.mint(staking.address, 1000000 * 10**18, sender=deployer)
    return (staking, reward_token)


@pytest.fixture(scope="function")
def staking_api(deployer):
    """
    部署质押合约并封装 API
    
    Args:
        deployer: 部署账户
        
    Returns:
        StakingAPI: 质押合约交互封装对象
    """
    reward_token = project.MyERC20.deploy("Reward Token", "RWT", sender=deployer)
    reward_per_block = 10**18
    staking = project.StakingContract.deploy(
        reward_token.address, reward_token.address, reward_per_block, sender=deployer
    )
    reward_token.mint(staking.address, 1000000 * 10**18, sender=deployer)
    return StakingAPI(staking)


@pytest.fixture(scope="function")
def timelock_contract(deployer, security_test_data):
    """
    部署时间锁合约（未封装）
    
    Args:
        deployer: 部署账户
        security_test_data: 安全测试数据
        
    Returns:
        Contract: 已部署的 TimeLockContract 合约实例
    """
    data = security_test_data.get("case_029_timelock_blocklock", {})
    lock_duration = data.get("lock_duration", 86400)
    lock_blocks = data.get("lock_blocks", 100)
    return project.TimeLockContract.deploy(lock_duration, lock_blocks, sender=deployer)


@pytest.fixture(scope="function")
def timelock_api(deployer, security_test_data):
    """
    部署时间锁合约并封装 API
    
    Args:
        deployer: 部署账户
        security_test_data: 安全测试数据
        
    Returns:
        TimeLockAPI: 时间锁合约交互封装对象
    """
    data = security_test_data.get("case_029_timelock_blocklock", {})
    lock_duration = data.get("lock_duration", 86400)
    lock_blocks = data.get("lock_blocks", 100)
    
    timelock = project.TimeLockContract.deploy(lock_duration, lock_blocks, sender=deployer)
    return TimeLockAPI(timelock)