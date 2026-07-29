"""
==============================================================================
【CEX 资金划转模块】接口测试
==============================================================================
case_021 ~ case_024：划转核心接口与对账
"""
import pytest
from framework.core.logger import log


@pytest.mark.skip(reason="占位待实现")
@pytest.mark.CEX_Fund
@pytest.mark.Transfer
@pytest.mark.P0
def test_cex_fund_021_spot_to_futures(transfer_api, account_api, cex_fund_test_data):
    """case_021: 现货→合约划转 - 资产从现货划转至合约账户"""
    log.step("case_021: 现货→合约划转测试")
    # TODO: 调 spot_to_futures() → 验证现货减、合约增
    pass
    log.success("✅ case_021 通过 (占位)")


@pytest.mark.skip(reason="占位待实现")
@pytest.mark.CEX_Fund
@pytest.mark.Transfer
@pytest.mark.P0
def test_cex_fund_022_futures_to_spot(transfer_api, account_api, cex_fund_test_data):
    """case_022: 合约→现货划转 - 资产从合约划转至现货账户"""
    log.step("case_022: 合约→现货划转测试")
    # TODO: 调 spot_to_futures(type=TO_SPOT) → 验证合约减、现货增
    pass
    log.success("✅ case_022 通过 (占位)")


@pytest.mark.skip(reason="占位待实现")
@pytest.mark.CEX_Fund
@pytest.mark.Transfer
@pytest.mark.P0
def test_cex_fund_023_get_transfer_history(transfer_api, cex_fund_test_data):
    """case_023: 划转历史查询 - 查询跨账户划转历史"""
    log.step("case_023: 划转历史查询测试")
    # TODO: 调 get_transfer_history() → 验证记录完整性
    pass
    log.success("✅ case_023 通过 (占位)")


@pytest.mark.skip(reason="占位待实现")
@pytest.mark.CEX_Fund
@pytest.mark.Transfer
@pytest.mark.P0
def test_cex_fund_024_transfer_bilateral_recon(transfer_api, account_api, cex_fund_test_data):
    """case_024: 划转双边对账 - 双边余额同步校验，划转金额一致"""
    log.step("case_024: 划转双边对账测试")
    # TODO: 划转 → 查双边余额 → 验证 send_decrease == recv_increase == amount
    pass
    log.success("✅ case_024 通过 (占位)")
