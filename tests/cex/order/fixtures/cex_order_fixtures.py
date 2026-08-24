"""
==============================================================================
CEX 订单系统 Fixtures - 测试环境准备
==============================================================================
"""
import pytest
import yaml
from pathlib import Path
from framework.cex.base_client import CEXBaseClient
from framework.core.config import config
from tests.cex.order.apis.spot_api import SpotAPI
from tests.cex.order.apis.market_api import MarketAPI


@pytest.fixture(scope="function")
def cex_order_test_data():
    """加载订单系统测试数据"""
    data_path = Path(__file__).parent.parent / "data" / "test_cex_order.yaml"
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
def spot_api(cex_client):
    """现货交易 API 实例"""
    return SpotAPI(cex_client)


@pytest.fixture(scope="function")
def market_api(cex_client):
    """行情 API 实例"""
    return MarketAPI(cex_client)


@pytest.fixture(scope="function")
def get_balance(cex_client):
    """
    查询单币种余额的辅助函数（返回 {free, locked}）
    订单用例校验资产冻结/释放时用。
    """
    def _get(asset: str) -> dict:
        resp = cex_client.private_get("/api/v3/account")
        for b in resp.json().get("balances", []):
            if b["asset"] == asset.upper():
                return {"free": float(b["free"]), "locked": float(b["locked"])}
        return {"free": 0.0, "locked": 0.0}
    return _get
