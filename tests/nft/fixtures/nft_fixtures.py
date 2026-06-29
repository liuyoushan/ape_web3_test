"""
==============================================================================
NFT Fixtures 层 - 测试环境准备
==============================================================================
"""
import pytest
import yaml
from pathlib import Path
from ape import project


@pytest.fixture(scope="module")
def nft_test_data():
    """
    加载 NFT 测试数据
    
    从 data/test_nft.yaml 读取测试配置，包含：
    - common: 通用配置（集合名称、符号等）
    - case_*: 各测试用例的参数
    
    Returns:
        dict: 测试数据字典
    """
    data_path = Path(__file__).parent.parent / "data" / "test_nft.yaml"
    with open(data_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="function")
def nft_contract(deployer, nft_test_data):
    """
    部署 ERC721 NFT 合约
    
    Args:
        deployer: 部署账户
        nft_test_data: NFT 测试数据
        
    Returns:
        Contract: 已部署的 MyERC721 合约实例
    """
    data = nft_test_data["common"]
    return project.MyERC721.deploy(data["collection_name"], data["collection_symbol"], sender=deployer)