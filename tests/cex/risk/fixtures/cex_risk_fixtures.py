"""
==============================================================================
CEX 风控体系 Fixtures - 测试环境准备
==============================================================================
"""
import pytest
import yaml
from pathlib import Path
from framework.cex.base_client import CEXBaseClient
from framework.core.config import config
from tests.cex.risk.apis.risk_api import RiskAPI


@pytest.fixture(scope="function")
def cex_risk_test_data():
    """加载风控体系测试数据"""
    data_path = Path(__file__).parent.parent / "data" / "test_cex_risk.yaml"
    with open(data_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="function")
def cex_client():
    """创建 CEX 基础客户端"""
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
def risk_api(cex_client):
    """风控 API 实例"""
    return RiskAPI(cex_client)
