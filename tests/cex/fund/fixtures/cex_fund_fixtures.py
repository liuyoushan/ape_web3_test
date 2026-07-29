"""
==============================================================================
CEX 资金链路 Fixtures - 测试环境准备
==============================================================================
"""
import pytest
import yaml
from pathlib import Path
from framework.cex.base_client import CEXBaseClient
from framework.cex.mock_chain import MockChainSimulator
from framework.core.config import config
from tests.cex.fund.apis.account_api import AccountAPI
from tests.cex.fund.apis.deposit_api import DepositAPI
from tests.cex.fund.apis.withdraw_api import WithdrawAPI
from tests.cex.fund.apis.transfer_api import TransferAPI


@pytest.fixture(scope="function")
def cex_fund_test_data():
    """加载资金链路测试数据"""
    data_path = Path(__file__).parent.parent / "data" / "test_cex_fund.yaml"
    with open(data_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="function")
def cex_client():
    """
    创建 CEX 基础客户端
    
    从配置读取 API Key/Secret，实际使用时替换为真实测试环境凭据。
    """
    api_key = config.get_env("CEX_API_KEY", "test_api_key")
    api_secret = config.get_env("CEX_API_SECRET", "test_api_secret")
    base_url = config.get("cex.base_url", "https://testnet.binance.vision")
    
    client = CEXBaseClient(
        api_key=api_key,
        api_secret=api_secret,
        base_url=base_url
    )
    yield client
    client.close()


@pytest.fixture(scope="function")
def mock_chain():
    """创建链上事件模拟器"""
    simulator = MockChainSimulator()
    yield simulator
    simulator.reset()


@pytest.fixture(scope="function")
def account_api(cex_client):
    """账户 API 实例"""
    return AccountAPI(cex_client)


@pytest.fixture(scope="function")
def deposit_api(cex_client):
    """充币 API 实例"""
    return DepositAPI(cex_client)


@pytest.fixture(scope="function")
def withdraw_api(cex_client):
    """提币 API 实例"""
    return WithdrawAPI(cex_client)


@pytest.fixture(scope="function")
def transfer_api(cex_client):
    """划转 API 实例"""
    return TransferAPI(cex_client)
