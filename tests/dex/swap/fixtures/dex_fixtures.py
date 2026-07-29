"""
==============================================================================
DEX Fixtures 层 - 测试环境准备
==============================================================================
"""
import pytest
import yaml
from pathlib import Path
from ape import project
from tests.dex.swap.apis import MiniSwapFactoryAPI, MiniSwapRouterAPI, MiniSwapPairAPI


@pytest.fixture(scope="function")
def dex_test_data():
    """
    加载 DEX 测试数据
    
    从 data/test_dex_swap.yaml 读取测试配置，包含：
    - common: 通用配置（代币名称、符号）
    - case_*: 各测试用例的参数（mint_amount、swap_amount 等）
    
    Returns:
        dict: 测试数据字典
    """
    data_path = Path(__file__).parent.parent / "data" / "test_dex_swap.yaml"
    with open(data_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="function")
def dex_token_a(deployer, dex_test_data):
    """
    部署 TokenA 代币合约
    
    Args:
        deployer: 部署账户
        dex_test_data: DEX 测试数据
        
    Returns:
        Contract: 已部署的 TokenA 合约实例
    """
    data = dex_test_data["common"]
    return project.MyERC20.deploy(data["tokenA_name"], data["tokenA_symbol"], sender=deployer)


@pytest.fixture(scope="function")
def dex_token_b(deployer, dex_test_data):
    """
    部署 TokenB 代币合约
    
    Args:
        deployer: 部署账户
        dex_test_data: DEX 测试数据
        
    Returns:
        Contract: 已部署的 TokenB 合约实例
    """
    data = dex_test_data["common"]
    return project.MyERC20.deploy(data["tokenB_name"], data["tokenB_symbol"], sender=deployer)


@pytest.fixture(scope="function")
def dex_factory(deployer):
    """
    部署 MiniSwapFactory 合约并封装 API
    
    Args:
        deployer: 部署账户
        
    Returns:
        MiniSwapFactoryAPI: Factory 合约交互封装对象
    """
    factory = project.MiniSwapFactory.deploy(sender=deployer)
    return MiniSwapFactoryAPI(factory)


@pytest.fixture(scope="function")
def dex_router(deployer, dex_factory):
    """
    部署 MiniSwapRouter 合约并封装 API
    
    Args:
        deployer: 部署账户
        dex_factory: Factory API 实例
        
    Returns:
        MiniSwapRouterAPI: Router 合约交互封装对象
    """
    router = project.MiniSwapRouter.deploy(dex_factory.contract, sender=deployer)
    return MiniSwapRouterAPI(router)


@pytest.fixture(scope="function")
def dex_pair_api(dex_token_a, dex_token_b, dex_factory, dex_router, deployer, user1):
    """
    创建带有流动性的交易对环境
    
    完整流程：
    1. 为 user1 mint 初始代币
    2. 授权 Router 操作代币
    3. 添加流动性创建交易对
    4. 返回 Pair API 实例
    
    Args:
        dex_token_a: TokenA 合约实例
        dex_token_b: TokenB 合约实例
        dex_factory: Factory API 实例
        dex_router: Router API 实例
        deployer: 部署账户
        user1: 测试用户账户
        
    Returns:
        MiniSwapPairAPI: Pair 合约交互封装对象
    """
    from framework.core.formatters import parse_ether
    
    mint_amount = parse_ether("10000")
    dex_token_a.mint(user1, mint_amount, sender=deployer)
    dex_token_b.mint(user1, mint_amount, sender=deployer)
    
    add_liquidity_amount = parse_ether("1000")
    dex_token_a.approve(dex_router.contract, add_liquidity_amount, sender=user1)
    dex_token_b.approve(dex_router.contract, add_liquidity_amount, sender=user1)
    
    dex_router.add_liquidity(
        dex_token_a, dex_token_b, "1000", "1000", user1, user1
    )
    
    pair_addr = dex_factory.get_pair(dex_token_a, dex_token_b)
    pair = project.MiniSwapPair.at(pair_addr)
    return MiniSwapPairAPI(pair)


@pytest.fixture(scope="function")
def swap_v3_test_data():
    """
    加载 Swap V3 测试数据
    
    从 data/test_dex_swap_v3.yaml 读取测试配置
    
    Returns:
        dict: 测试数据字典
    """
    data_path = Path(__file__).parent.parent / "data" / "test_dex_swap_v3.yaml"
    with open(data_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="function")
def v3_liquidity_environment(deployer, user1, swap_v3_test_data):
    """
    创建 V3 集中流动性测试环境
    
    注意：当前使用 MiniSwap V2 合约模拟 V3 集中流动性测试
    
    Args:
        deployer: 部署账户
        user1: 测试用户账户
        swap_v3_test_data: V3 测试数据
        
    Returns:
        dict: 包含 token_a, token_b, router, factory, user1 的环境字典
    """
    from framework.core.formatters import parse_ether
    
    factory = project.MiniSwapFactory.deploy(sender=deployer)
    router = project.MiniSwapRouter.deploy(factory, sender=deployer)
    
    token_a = project.MyERC20.deploy("TokenA", "TKA", sender=deployer)
    token_b = project.MyERC20.deploy("TokenB", "TKB", sender=deployer)
    
    mint_amount = parse_ether("10000")
    token_a.mint(user1, mint_amount, sender=deployer)
    token_b.mint(user1, mint_amount, sender=deployer)
    
    return {
        "token_a": token_a,
        "token_b": token_b,
        "router": router,
        "factory": factory,
        "user1": user1,
    }