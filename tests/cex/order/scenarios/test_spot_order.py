"""
==============================================================================
【CEX 现货交易模块】接口测试（对齐币安测试网 testnet.binance.vision）
==============================================================================
case_005 ~ case_012：现货核心交易接口
case_032：差异化并发场景（简历亮点）

⚠️ 说明：本模块会真实下单/撤单。所有限价单价格远离市价，保证不成交，
用例末尾统一撤单清理，不残留挂单、不消耗资产。
"""
import pytest
from framework.core.logger import log


SYMBOL = "BTCUSDT"


@pytest.mark.CEX_Order
@pytest.mark.Trade
@pytest.mark.P0
def test_cex_order_005_place_limit_order(spot_api, market_api, get_balance, cex_order_test_data):
    """case_005: 限价挂单(BUY) - place_order(side=BUY, type=LIMIT)，取盘口买一×0.99动态定价，校验USDT冻结(free->locked)
    就是挂限价买单，买单只买低于市价，没人卖所以不会吃盘成交"""
    log.step("case_005: 限价挂单测试")
    data = cex_order_test_data["spot"]["case_005"]

    # 1. 取盘口买一价，买单挂在略低于市价位置（保证不成交，只看冻结）
    depth = market_api.get_order_book(SYMBOL, 1)
    best_bid = float(depth["bids"][0][0])
    limit_price = round(best_bid * 0.99, 2)
    log.info(f"当前盘口买一: {best_bid}, 挂单价格: {limit_price}（低于市价，不会成交）")

    # 2. 下单前记录 USDT 余额
    before = get_balance("USDT")
    log.info(f"下单前 USDT: free={before['free']}, locked={before['locked']}")

    # 3. 动态价买单
    order = spot_api.place_order(
        symbol=SYMBOL, side=data["side"], order_type=data["type"],
        quantity=data["quantity"], price=limit_price,
        time_in_force=data["time_in_force"],
    )
    order_id = order["orderId"]
    try:
        # 4. 校验订单状态为 NEW（已挂单未成交）
        assert order["status"] == "NEW", f"新挂单状态应为 NEW，实际 {order['status']}"
        assert order["side"] == "BUY"
        assert order["type"] == "LIMIT"

        # 5. 校验资产冻结：应冻结 limit_price*quantity USDT
        after = get_balance("USDT")
        log.info(f"下单后 USDT: free={after['free']}, locked={after['locked']}")
        frozen = round(after["locked"] - before["locked"], 2)
        expected = round(limit_price * data["quantity"], 2)
        assert frozen == expected, f"冻结金额应为 {expected}，实际 {frozen}"
        log.success(f"✅ case_005 通过：挂单成功，冻结 {frozen} USDT")
    finally:
        # 6. 清理：撤单
        spot_api.cancel_order(SYMBOL, order_id)


@pytest.mark.CEX_Order
@pytest.mark.Trade
@pytest.mark.P0
def test_cex_order_006_place_market_order(spot_api, get_balance, cex_order_test_data):
    """case_006: 市价挂单(BUY) - place_order(side=BUY, type=MARKET, quote_order_qty=20)，花20USDT市价买入BTC，校验成交金额
    市价单MARKET，一般不需要挂单，而是直接吃卖1价，当然取决于盘口深度，如果没有单则不会成交或部分成交
    """
    log.step("case_006: 市价挂单测试")

    # 用 quoteOrderQty 花 20 USDT 市价买 BTC（够 minNotional=5）
    before_btc = get_balance("BTC")
    order = spot_api.place_order(
        symbol=SYMBOL, side="BUY", order_type="MARKET", quote_order_qty=20,
    )
    # 市价单立即成交，状态应为 FILLED
    assert order["status"] == "FILLED", f"市价单应立即成交，实际 {order['status']}"
    assert float(order["executedQty"]) > 0, "应有成交数量"
    assert len(order.get("fills", [])) > 0, "应有成交明细 fills"

    # 校验实际花费的 USDT ≈ 20
    spent = float(order["cummulativeQuoteQty"])
    log.info(f"市价买入成交: 花费 {spent} USDT, 买到 {order['executedQty']} BTC")
    assert abs(spent - 20) < 1, f"花费应接近 20 USDT，实际 {spent}"

    # 校验 BTC 余额增加
    after_btc = get_balance("BTC")
    assert after_btc["free"] > before_btc["free"], "买入后 BTC 可用余额应增加"
    log.success(f"✅ case_006 通过：市价单即时成交，BTC +{round(after_btc['free']-before_btc['free'],8)}")


@pytest.mark.CEX_Order
@pytest.mark.Trade
@pytest.mark.P0
def test_cex_order_007_cancel_order(spot_api, market_api, get_balance, cex_order_test_data):
    """case_007: 撤销订单(SELL) - place_order(side=SELL, type=LIMIT)，取盘口卖一×1.01动态定价，撤单后校验BTC冻结返还
    卖的比市价高，不会成交。然后手动撤单
    """
    log.step("case_007: 撤销订单测试")
    data = cex_order_test_data["spot"]["case_007"]

    # 1. 取盘口卖一价，卖单挂在略高于市价位置（保证不成交，只看冻结/返还）
    depth = market_api.get_order_book(SYMBOL, 1)
    best_ask = float(depth["asks"][0][0])
    limit_price = round(best_ask * 1.01, 2)
    log.info(f"当前盘口卖一: {best_ask}, 挂单价格: {limit_price}（高于市价，不会成交）")

    # 2. 下单前记录 BTC 余额
    before = get_balance("BTC")

    # 3. 动态价卖单（卖单冻结的是 BTC）
    order = spot_api.place_order(
        symbol=SYMBOL, side="SELL", order_type="LIMIT",
        quantity=data["quantity"], price=limit_price, time_in_force="GTC",
    )
    order_id = order["orderId"]
    assert order["status"] == "NEW", "卖单应挂单成功"

    frozen = get_balance("BTC")
    assert frozen["locked"] > before["locked"], "卖单应冻结 BTC"

    # 4. 撤单
    result = spot_api.cancel_order(SYMBOL, order_id)
    assert result["status"] == "CANCELED", f"撤单后状态应为 CANCELED，实际 {result['status']}"

    # 5. 校验冻结返还
    after = get_balance("BTC")
    assert abs(after["free"] - before["free"]) < 1e-8, "撤单后 BTC 可用余额应恢复"
    log.success("✅ case_007 通过：撤单成功，冻结资产已返还")


@pytest.mark.CEX_Order
@pytest.mark.Trade
@pytest.mark.P0
def test_cex_order_008_query_order_detail(spot_api, cex_order_test_data):
    """case_008: 订单详情查询 - 先place_order(side=BUY, type=LIMIT, price=50000)挂单，再get_order_status(orderId)查详情"""
    log.step("case_008: 订单详情查询测试")

    # 先挂一个不成交的单，拿到 orderId
    order = spot_api.place_order(
        symbol=SYMBOL, side="BUY", order_type="LIMIT",
        quantity=0.001, price=50000.00, time_in_force="GTC",
    )
    order_id = order["orderId"]
    try:
        # 查询订单详情
        detail = spot_api.get_order_status(SYMBOL, order_id)
        print('===---')
        print(detail)
        for field in ["orderId", "symbol", "status", "executedQty", "price", "origQty"]:
            assert field in detail, f"订单详情应含字段 {field}"
        assert detail["orderId"] == order_id, "orderId 应一致"
        assert detail["symbol"] == SYMBOL
        assert detail["status"] == "NEW"
        log.info(f"订单详情: status={detail['status']}, 已成交={detail['executedQty']}")
        log.success("✅ case_008 通过：订单详情查询正常")
    finally:
        spot_api.cancel_order(SYMBOL, order_id)


@pytest.mark.CEX_Order
@pytest.mark.Trade
@pytest.mark.P0
def test_cex_order_009_query_trade_history(spot_api, cex_order_test_data):
    """case_009: 历史成交查询 - get_trade_history(symbol=BTCUSDT)，不挂单，依赖case_006产生的成交数据"""
    log.step("case_009: 历史成交查询测试")
    data = cex_order_test_data["spot"]["case_009"]

    trades = spot_api.get_trade_history(symbol=data["symbol"], limit=data["limit"])
    print('成交历史',trades)
    assert isinstance(trades, list), "成交历史应为列表"
    # 前面 case_006 已产生过成交，这里应有记录（若无则说明账户无历史，也允许空）
    if trades:
        t = trades[0]
        for field in ["id", "orderId", "price", "qty", "commission", "isBuyer"]:
            assert field in t, f"成交记录应含字段 {field}"
        log.info(f"最近成交: price={t['price']}, qty={t['qty']}, 手续费={t['commission']}{t.get('commissionAsset','')}")
    log.success(f"✅ case_009 通过：查询到 {len(trades)} 条成交记录")


@pytest.mark.CEX_Order
@pytest.mark.Trade
@pytest.mark.P0
def test_cex_order_010_get_open_orders(spot_api, cex_order_test_data):
    """case_010: 当前挂单查询 - 先place_order连挂2笔BUY LIMIT(price=50000/49000)，再get_open_orders查列表"""
    log.step("case_010: 当前挂单查询测试")

    # 挂 2 个不成交的单
    o1 = spot_api.place_order(SYMBOL, "BUY", "LIMIT", quantity=0.001, price=50000.00)
    o2 = spot_api.place_order(SYMBOL, "BUY", "LIMIT", quantity=0.001, price=49000.00)
    try:
        open_orders = spot_api.get_open_orders(SYMBOL)
        assert isinstance(open_orders, list), "挂单列表应为 list"
        order_ids = [o["orderId"] for o in open_orders]
        assert o1["orderId"] in order_ids, "挂单1应在列表中"
        assert o2["orderId"] in order_ids, "挂单2应在列表中"
        for o in open_orders:
            assert o["status"] == "NEW", "挂单状态应为 NEW"
        log.info(f"当前挂单数: {len(open_orders)}")
        log.success("✅ case_010 通过：当前挂单查询正常")
    finally:
        spot_api.cancel_all_open_orders(SYMBOL)


@pytest.mark.CEX_Order
@pytest.mark.Trade
@pytest.mark.P0
def test_cex_order_011_cancel_all_orders(spot_api, cex_order_test_data):
    """case_011: 全撤挂单 - 先place_order连挂3笔BUY LIMIT(price=50000/49000/48000)，再cancel_all_open_orders一次性全撤"""
    log.step("case_011: 全撤挂单测试")

    # 挂 3 个不成交的单
    for price in [50000.00, 49000.00, 48000.00]:
        spot_api.place_order(SYMBOL, "BUY", "LIMIT", quantity=0.001, price=price)

    # 全撤
    result = spot_api.cancel_all_open_orders(SYMBOL)
    assert isinstance(result, list), "全撤应返回被撤订单列表"
    assert len(result) >= 3, f"应撤销至少 3 个订单，实际 {len(result)}"
    for r in result:
        assert r["status"] == "CANCELED", "被撤订单状态应为 CANCELED"

    # 校验挂单清空
    remaining = spot_api.get_open_orders(SYMBOL)
    assert len(remaining) == 0, "全撤后应无剩余挂单"
    log.success(f"✅ case_011 通过：一次性撤销 {len(result)} 个挂单")


@pytest.mark.CEX_Order
@pytest.mark.Trade
@pytest.mark.P0
def test_cex_order_012_market_order_boundary(spot_api, market_api, cex_order_test_data):
    """case_012: 市价单边界 - place_test_order(side=BUY, type=MARKET)不下真实单，校验minNotional边界
    看接口名称把，就是个预校验接口，不产生任何实际单
    """
    log.step("case_012: 市价单成交边界测试")

    # 边界1：低于 minNotional(5 USDT) 的单应被拒
    tiny = spot_api.place_test_order(
        symbol=SYMBOL, side="BUY", order_type="MARKET", quote_order_qty=1,
    )
    # 币安测试下单：金额太小会返回错误码 -1013 (NOTIONAL)
    assert tiny.get("code") is not None, "低于最小名义价值的单应被拒"
    log.info(f"小额单被拒: code={tiny.get('code')}, msg={tiny.get('msg')}")

    # 边界2：合法市价单参数校验通过（返回空 {}）
    valid = spot_api.place_test_order(
        symbol=SYMBOL, side="BUY", order_type="MARKET", quote_order_qty=50,
    )
    assert valid == {}, f"合法参数应校验通过（空dict），实际 {valid}"
    log.success("✅ case_012 通过：市价单边界校验正常（小额拒绝、合法通过）")


@pytest.mark.CEX_Order
@pytest.mark.CEX_Order
@pytest.mark.Trade
@pytest.mark.P0
def test_cex_order_013_ioc_limit(spot_api, market_api, get_balance, cex_order_test_data):
    """case_013: IOC限价单 - place_order(time_in_force=IOC)，立即成交或取消，不挂盘
     IOC：能吃多少吃多少，剩余撤销...意思是我定一个价格比如 100. 那么满足条件的全部成交，其他撤单。允许部分成功
    """
    log.step("case_013: IOC限价单测试")
    data = cex_order_test_data["spot"]["case_013"]

    # 1. 取盘口买一价，挂一个IOC买单，价格低于市价（不会立刻成交，整单取消）
    depth = market_api.get_order_book(SYMBOL, 1)
    best_bid = float(depth["bids"][0][0])
    safe_price = round(best_bid * 0.99, 2)
    log.info(f"盘口买一: {best_bid}, IOC挂单价: {safe_price}（低于市价，不会立刻成交）")

    before_usdt = get_balance("USDT")
    order = spot_api.place_order(
        symbol=SYMBOL, side=data["side"], order_type=data["type"],
        quantity=data["quantity"], price=safe_price,
        time_in_force=data["time_in_force"],
    )
    # 2. IOC不会立刻成交时应直接取消，状态为EXPIRED或CANCELED
    status = order.get("status")
    assert status in ("EXPIRED", "CANCELED", "FILLED"), \
        f"IOC未成交应取消，实际 status={status}"
    log.info(f"IOC结果: status={status}")

    # 3. 不应有挂单残留
    open_orders = spot_api.get_open_orders(SYMBOL)
    order_ids = [o["orderId"] for o in open_orders]
    assert order.get("orderId") not in order_ids, "IOC不应有挂单残留"

    # 4. 余额不变（未成交）
    after_usdt = get_balance("USDT")
    assert abs(after_usdt["free"] - before_usdt["free"]) < 1e-8, "IOC未成交余额应不变"
    log.success(f"✅ case_013 通过：IOC未成交自动取消，无挂单残留，余额不变")


@pytest.mark.CEX_Order
@pytest.mark.Trade
@pytest.mark.P0
def test_cex_order_014_fok_limit(spot_api, market_api, get_balance, cex_order_test_data):
    """case_014: FOK限价单 - place_order(time_in_force=FOK)，必须全部成交否则整单撤销
     FOK：必须全部成交，否则整单撤销。。。挂限价后去盘口找单，一定要够我期望交易的总量时才交易成功，否则交易失败一笔都不成功。不允许部分成功
     """
    log.step("case_014: FOK限价单测试")
    data = cex_order_test_data["spot"]["case_014"]

    # 1. 取盘口买一价，挂一个FOK买单，价格低于市价（盘口深度不够全部成交，整单撤销）
    depth = market_api.get_order_book(SYMBOL, 1)
    best_bid = float(depth["bids"][0][0])
    safe_price = round(best_bid * 0.99, 2)
    log.info(f"盘口买一: {best_bid}, FOK挂单价: {safe_price}（低于市价，不会立刻成交）")

    before_usdt = get_balance("USDT")
    order = spot_api.place_order(
        symbol=SYMBOL, side=data["side"], order_type=data["type"],
        quantity=data["quantity"], price=safe_price,
        time_in_force=data["time_in_force"],
    )
    # 2. FOK无法全部成交时应整单取消
    status = order.get("status")
    assert status in ("EXPIRED", "CANCELED"), \
        f"FOK无法全部成交应整单取消，实际 status={status}"
    assert float(order.get("executedQty", 0)) == 0, "FOK整单取消不应有部分成交"
    log.info(f"FOK结果: status={status}, executedQty={order.get('executedQty')}")

    # 3. 不应有挂单残留
    open_orders = spot_api.get_open_orders(SYMBOL)
    order_ids = [o["orderId"] for o in open_orders]
    assert order.get("orderId") not in order_ids, "FOK不应有挂单残留"

    # 4. 余额不变
    after_usdt = get_balance("USDT")
    assert abs(after_usdt["free"] - before_usdt["free"]) < 1e-8, "FOK取消后余额应不变"
    log.success(f"✅ case_014 通过：FOK无法全部成交整单取消，无残留，余额不变")


@pytest.mark.skip(reason="占位待实现 - 并发场景需多线程，阶段4统一实现")
@pytest.mark.CEX_Order
@pytest.mark.Trade
@pytest.mark.P1
def test_cex_order_032_concurrent_orders(spot_api, cex_order_test_data):
    """case_032: 并发下单不丢单 - 高并发下不丢单、资金安全"""
    log.step("case_032: 并发下单不丢单测试")
    # TODO: 多线程并发下单 → 验证不丢单、资金无错乱
    pass
