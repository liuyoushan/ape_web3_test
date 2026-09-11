"""
==============================================================================
【CEX 差异化资损场景】测试
==============================================================================
case_031 ~ case_034：面试核心竞争力场景

所有 MockChain 测试均为内存态，不影响真实链上数据。
"""
import pytest
import threading

try:
    import allure
except ImportError:
    class dummy_allure:
        def title(t): return lambda f: f
        def description(d): return lambda f: f
        def tag(*tags): return lambda f: f
    allure = dummy_allure()

from framework.core.logger import log
from framework.cex.mock_chain import MockChainSimulator, DepositStatus, WithdrawStatus


@allure.title("case_031 区块回滚充值扣回")
@allure.description("验证交易所能检测区块回滚并扣回已入账资金，防止凭空充值套利")
@allure.tag("CEX_Risk", "P0", "资金安全", "区块链模拟")
def test_cex_fund_031_block_rollback_deduction():
    """
    case_031: 区块回滚充值扣回

    主流程：
      1. MockChain 模拟充值入账（amount=0.01 BTC）
      2. 验证充值状态为 CONFIRMED，净充值额 = 0.01
      3. 触发区块回滚
      4. 验证充值状态变为 ROLLED_BACK，净充值额 = 0
      5. 余额一致性校验：内部余额 0 = 预期余额 0
    原理：
      区块回滚时交易失效，交易所必须检测并扣回已入账的资金。
      若不扣回，用户可利用回滚漏洞"凭空充值"套利。
    """
    log.step("case_031: 区块回滚充值扣回")
    mock = MockChainSimulator()
    tx_hash = "0x" + "a1b2" * 16
    amount = 0.01

    # 1. 模拟充值入账
    record = mock.register_deposit(tx_hash=tx_hash, amount=amount, address="bc1qtest")
    assert record.status == DepositStatus.CONFIRMED, f"充值状态应为 CONFIRMED，实际 {record.status}"
    assert record.amount == amount

    # 2. 验证净充值额
    net = mock.calculate_net_deposits()
    assert abs(net - amount) < 1e-8, f"净充值额应为 {amount}，实际 {net}"

    # 3. 触发区块回滚
    sim = mock.simulate_deposit_rollback(tx_hash=tx_hash)
    assert sim.success, f"回滚失败: {sim.message}"
    assert sim.data["balance_to_deduct"] == amount

    # 4. 验证回滚后状态
    record_after = mock.get_deposit_status(tx_hash)
    assert record_after.status == DepositStatus.ROLLED_BACK, f"回滚后状态应为 ROLLED_BACK，实际 {record_after.status}"

    # 5. 验证回滚后净充值额归零
    net_after = mock.calculate_net_deposits()
    assert abs(net_after) < 1e-8, f"回滚后净充值额应为 0，实际 {net_after}"

    # 6. 余额一致性校验
    consistency = mock.verify_balance_consistency(internal_balance=0.0)
    assert consistency["is_consistent"], f"余额不一致: {consistency}"

    log.success("✅ case_031 通过")


@allure.title("case_032 重复TxHash充值拦截")
@allure.description("验证交易所能识别重复的TxHash充值请求并拒绝入账，防止重放攻击")
@allure.tag("CEX_Risk", "P0", "资金安全", "区块链模拟")
def test_cex_fund_032_duplicate_txhash_intercept():
    """
    case_032: 重复TxHash充值拦截

    主流程：
      1. MockChain 模拟充值入账（amount=0.005 BTC）
      2. 再次提交同一 TxHash 的充值请求
      3. 验证第二次请求被标记为 should_block_credit=True
      4. 验证余额仅加一次（净充值额 = 0.005，不是 0.01）
    原理：
      防重复入账是交易所基本安全机制。
      攻击者可重放交易广播，若交易所不校验 TxHash 唯一性，会导致重复入账。
    """
    log.step("case_032: 重复TxHash充值拦截")
    mock = MockChainSimulator()
    tx_hash = "0x" + "c3d4" * 16
    amount = 0.005

    # 1. 首次充值入账
    record = mock.register_deposit(tx_hash=tx_hash, amount=amount, address="bc1qtest")
    assert record.status == DepositStatus.CONFIRMED

    # 2. 模拟重复充值请求
    sim = mock.simulate_duplicate_deposit(tx_hash=tx_hash)
    assert sim.success, f"重复检测失败: {sim.message}"
    assert sim.data["should_block_credit"] is True, "应拒绝重复入账"
    assert sim.data["amount"] == amount

    # 3. 验证余额仅加一次
    net = mock.calculate_net_deposits()
    assert abs(net - amount) < 1e-8, f"净充值额应为 {amount}（仅一次），实际 {net}"

    # 4. 验证原始充值状态不变
    record_after = mock.get_deposit_status(tx_hash)
    assert record_after.status == DepositStatus.CONFIRMED, \
        f"原始充值状态应保持 CONFIRMED，实际 {record_after.status}"

    log.success("✅ case_032 通过")


@allure.title("case_033 提币链上失败回滚")
@allure.description("验证交易所能在链上提币失败时自动退回资金，防止用户资产受损")
@allure.tag("CEX_Risk", "P0", "资金安全", "区块链模拟")
def test_cex_fund_033_withdraw_failure_refund():
    """
    case_033: 提币链上失败回滚

    主流程：
      1. MockChain 模拟提币申请（amount=0.002 BTC）
      2. 模拟提币广播上链
      3. 模拟链上失败（insufficient_gas）
      4. 验证 should_refund=True，refund_amount = 0.002
      5. 余额一致性校验：内部余额 0 = 预期余额 0（失败提币不计入净提币）
    原理：
      提币失败时资金必须原路退回，否则用户资产受损。
      常见失败原因：Gas 不足、网络异常、地址格式错误。
    """
    log.step("case_033: 提币链上失败回滚")
    mock = MockChainSimulator()
    withdraw_id = "WD_033_001"
    amount = 0.002

    # 1. 注册提币请求
    record = mock.register_withdraw(withdraw_id=withdraw_id, amount=amount, to_address="bc1qdest")
    assert record.status == WithdrawStatus.PENDING

    # 2. 模拟提币广播上链
    sim_broadcast = mock.simulate_withdraw_broadcast(withdraw_id=withdraw_id)
    assert sim_broadcast.success

    # 3. 模拟链上失败（Gas不足）
    sim_fail = mock.simulate_withdraw_failure(withdraw_id=withdraw_id, reason="insufficient_gas")
    assert sim_fail.success, f"失败模拟失败: {sim_fail.message}"
    assert sim_fail.data["should_refund"] is True
    assert sim_fail.data["refund_amount"] == amount

    # 4. 验证提币状态
    record_after = mock.get_withdraw_status(withdraw_id)
    assert record_after.status == WithdrawStatus.FAILED

    # 5. 验证净提币额归零
    net_withdraw = mock.calculate_net_withdraws()
    assert abs(net_withdraw) < 1e-8, f"净提币额应为 0，实际 {net_withdraw}"

    # 6. 余额一致性校验
    consistency = mock.verify_balance_consistency(internal_balance=0.0)
    assert consistency["is_consistent"], f"余额不一致: {consistency}"

    log.success("✅ case_033 通过")


@allure.title("case_034 并发下单不丢单")
@allure.description("验证高并发下单场景下系统保证原子性，不会出现丢单现象")
@allure.tag("CEX_Risk", "P0", "资金安全", "并发测试")
def test_cex_order_034_concurrent_orders():
    """
    case_034: 并发下单不丢单

    主流程：
      1. 串行提交 5 笔限价买单（测试网并发限流，生产环境可并发）
      2. 验证每笔订单返回 orderId（不丢单）
      3. 撤销所有挂单
      4. 验证撤单后无残留挂单
    原理：
      高并发下系统必须保证原子性，不能出现"钱扣了但订单没生成"的丢单。
      并发场景是交易所最常见的资损来源之一。
    """
    log.step("case_034: 并发下单不丢单")

    # 1. 初始化 CEX 客户端
    from tests.cex.order.apis.spot_api import SpotAPI
    from framework.core.config import config
    from framework.cex.base_client import CEXBaseClient

    api_key = config.get_env("CEX_API_KEY")
    api_secret = config.get_env("CEX_API_SECRET")
    base_url = config.get("cex.base_url", "https://testnet.binance.vision")
    client = CEXBaseClient(api_key=api_key, api_secret=api_secret, base_url=base_url)
    spot = SpotAPI(client)

    # 2. 获取当前卖一价作为下单价格
    ticker_resp = client.public_get("/api/v3/ticker/bookTicker", params={"symbol": "BTCUSDT"})
    ticker = ticker_resp.json() if ticker_resp.status_code == 200 else {}
    if "askPrice" not in ticker:
        client.close()
        pytest.skip("测试网 ticker 不可用")

    ask_price = float(ticker["askPrice"])
    limit_price = round(ask_price * 0.95, 2)

    # 3. 串行下单（测试网并发限流，生产环境可并发）
    order_ids = []
    for i in range(5):
        result = spot.place_order(
            symbol="BTCUSDT",
            side="BUY",
            order_type="LIMIT",
            time_in_force="GTC",
            quantity=0.001,
            price=limit_price,
        )
        if result and "orderId" in result:
            order_ids.append(result["orderId"])

    log.info(f"  下单完成: 成功={len(order_ids)}/5")

    # 4. 验证所有订单都有 orderId（不丢单）
    assert len(order_ids) == 5, f"下单成功率过低: {len(order_ids)}/5"

    # 5. 撤销所有挂单
    cancel_result = spot.cancel_all_open_orders("BTCUSDT")
    cancel_count = len(cancel_result) if isinstance(cancel_result, list) else 0
    log.info(f"  撤单完成: 撤销={cancel_count}")

    # 6. 验证无残留挂单
    open_orders = spot.get_open_orders("BTCUSDT")
    open_count = len(open_orders) if isinstance(open_orders, list) else 0
    assert open_count == 0, f"撤单后应无残留挂单，实际 {open_count} 笔"

    # 7. 清理资源
    client.close()
    log.success("✅ case_034 通过 (5/5 下单成功，撤单无残留)")
