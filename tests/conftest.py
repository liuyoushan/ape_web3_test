"""
==============================================================================
共享 Fixture 配置
==============================================================================

注意：各模块的 fixtures 已迁移到对应模块的 fixtures 目录中，
通过各模块的 conftest.py 自动加载。

本文件仅保留全局共享的基础 fixtures（如账户）。
==============================================================================
"""
import pytest
from ape import project


@pytest.fixture(scope="session")
def deployer(accounts):
    """部署者账户"""
    return accounts[0]


@pytest.fixture(scope="session")
def user1(accounts):
    """测试用户1"""
    return accounts[1]


@pytest.fixture(scope="session")
def user2(accounts):
    """测试用户2"""
    return accounts[2]


@pytest.fixture(scope="session")
def user3(accounts):
    """测试用户3"""
    return accounts[3]