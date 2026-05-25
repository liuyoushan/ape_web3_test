"""
==============================================================================
清算业务 Fixtures
==============================================================================
"""
import pytest
from pathlib import Path
import yaml


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
        "HEALTH_FACTOR_WARNING": liquidation_test_data["case_048_liquidation_trigger"]["health_factor_warning"],
        "HEALTH_FACTOR_LIQUIDATION": liquidation_test_data["case_048_liquidation_trigger"]["health_factor_liquidation"],
        "LIQUIDATOR_REWARD_PCT": liquidation_test_data["case_049_normal_liquidation"]["liquidator_reward_pct"],
        "PLATFORM_FEE_PCT": liquidation_test_data["case_049_normal_liquidation"]["platform_fee_pct"],
    }
