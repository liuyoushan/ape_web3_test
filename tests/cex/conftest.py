"""
==============================================================================
CEX 模块全局配置
==============================================================================
CI 默认不提供币安测试网密钥，若未配置 CEX_API_KEY / CEX_API_SECRET，
自动跳过全部 CEX 用例，避免因外网鉴权失败导致流水线失败。
本地 .env 配置了密钥时不受影响。
==============================================================================
"""
import os
import pytest

from framework.core.config import config as app_config


def _has_cex_credentials() -> bool:
    """是否配置了 CEX 测试网密钥（.env 或环境变量）"""
    key = (app_config.get_env("CEX_API_KEY") or "").strip()
    secret = (app_config.get_env("CEX_API_SECRET") or "").strip()
    return bool(key and secret)


def pytest_collection_modifyitems(session, config, items):
    if _has_cex_credentials():
        return

    skip_marker = pytest.mark.skip(
        reason="未配置 CEX_API_KEY/CEX_API_SECRET，跳过 CEX 用例（CI 默认跳过）"
    )
    cex_root = os.path.dirname(os.path.abspath(__file__))

    for item in items:
        fspath = os.path.abspath(str(item.fspath))
        if fspath.startswith(cex_root + os.sep):
            item.add_marker(skip_marker)
