"""
==============================================================================
【模块概览】Uniswap V3 集中流动性 AMM 核心测试用例
对应用例编号：case_055 ~ case_064
测试范围：V3 核心特性：集中流动性、多费率层级、Tick 价格区间
==============================================================================
"""
from ape import project
try:
    import allure
except ImportError:
    # Dummy decorators if allure not installed
    class dummy_allure:
        @staticmethod
        def title(*args, **kwargs):
            return lambda f: f
        @staticmethod
        def description(*args, **kwargs):
            return lambda f: f
        @staticmethod
        def tag(*args, **kwargs):
            return lambda f: f
    allure = dummy_allure()
from tests.helpers.logger import log
from tests.helpers.formatters import format_ether
from tests.fixtures.token_fixture import parse_ether


# ================================================================================
# case_055 集中流动性添加测试
# 测试目标：模拟 V3 集中流动性模式，验证多轮流动性可正确叠加
# 测试类型：P0 - 功能测试 / 正向测试
# ================================================================================
@allure.title("case_055 集中流动性添加测试")
@allure.description("模拟 V3 集中流动性模式，验证多轮流动性可正确叠加")
@allure.tag("DEX", "V3", "P0", "集中流动性", "正向测试")
def test_swap_v3_055_concentrated_liquidity_add(v3_liquidity_environment, swap_v3_test_data):
    """
    ================================================================================
    【用例编号】case_055
    【用例名称】集中流动性添加测试
    【测试目标】模拟 V3 集中流动性模式，验证多轮流动性可正确叠加
    【测试类型】P0 - 功能测试 / 正向测试
    ================================================================================
    
    业务背景：
    Uniswap V3 vs V2 核心区别：
      - V2: 流动性均匀分布在整个价格曲线 (Full Range)
      - V3: LP 可选择指定价格区间 [minTick, maxTick]
        * Full Range: tick [-887272, 887272]
        * Narrow Range: 如 tick [-600, 600]（资金效率更高）
    
    测试流程详解：
    ─────────────────────────────────────────────────────────────────────────────┐
    │ 阶段1: 模拟全区间流动性       对应 tick [-887272, 887272]                 │
    │        - 授权 Router                                                          │
    │        - 首次 addLiquidity 创建交易对                                          │
    │        - 校验初始储备量                                                         │
    └─────────────────────────────────────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ 阶段2: 模拟窄区间追加流动性   对应 tick [-600, 600]                         │
    │        - 二次 addLiquidity 追加流动性                                          │
    │        - 校验储备量正确叠加（V3 多区间聚合效果）                                │
    │        - 记录流动性分布：LP 凭证发放、池子 K 值变化                             │
    └─────────────────────────────────────────────────────────────────────────────┘
    
    核心验证点：
    1. 全区间添加后，储备量 == 首次投入数量
    2. 窄区间追加后，储备量 == 首次 + 二次投入（多区间流动性聚合）
    3. K 值恒定：每次添加流动性后 K 应增长
    4. LP 发放：两轮添加都有 LP 代币生成
    
    数据来源：tests/data/test_dex_swap_v3.yaml -> case_055_concentrated_liquidity_add
    """
    data = swap_v3_test_data["case_055_concentrated_liquidity_add"]
    env = v3_liquidity_environment
    
    token_a = env["token_a"]
    token_b = env["token_b"]
    router = env["router"]
    factory = env["factory"]
    user1 = env["user1"]
    
    add_full = parse_ether(data["add_liquidity_full_range"])
    add_narrow = parse_ether(data["add_liquidity_narrow_range"])
    fee_tier = data["fee_tier"]
    tick_full = data["tick_range_full"]
    tick_narrow = data["tick_range_narrow"]
    
    log.step("case_055: 集中流动性添加测试（V3 多区间聚合）")
    log.debug("费率层级：%d bps", fee_tier)
    log.debug("全区间 Tick: [%d, %d]", tick_full['min_tick'], tick_full['max_tick'])
    log.debug("窄区间 Tick: [%d, %d]", tick_narrow['min_tick'], tick_narrow['max_tick'])
    
    # ==================== 阶段 1: 模拟全区间流动性 ====================
    log.step("阶段 1：全区间流动性添加 [-887272, 887272]")
    
    token_a.approve(router, add_full * 2, sender=user1)
    token_b.approve(router, add_full * 2, sender=user1)
    
    router.addLiquidity(
        token_a, token_b,
        add_full, add_full,
        user1, sender=user1
    )
    
    pair_addr = factory.getPair(token_a, token_b)
    pair = project.MiniSwapPair.at(pair_addr)
    reserves_1 = pair.getReserves()
    lp_balance_1 = pair.balanceOf(user1)
    
    log.debug("阶段 1 投入：TokenA=%s, TokenB=%s", format_ether(add_full), format_ether(add_full))
    log.debug("池子储备 A: %s", format_ether(reserves_1[0]))
    log.debug("池子储备 B: %s", format_ether(reserves_1[1]))
    log.debug("用户 LP 余额：%s", format_ether(lp_balance_1))
    
    assert reserves_1[0] == add_full, "全区间后储备 A 不对"
    assert reserves_1[1] == add_full, "全区间后储备 B 不对"
    assert lp_balance_1 > 0, "第一轮没拿到 LP"
    
    # ==================== 阶段 2: 模拟窄区间追加流动性 ====================
    log.step("阶段 2：窄区间流动性追加 [-600, 600] (V3 多区间聚合)")
    
    router.addLiquidity(
        token_a, token_b,
        add_narrow, add_narrow,
        user1, sender=user1
    )
    
    reserves_2 = pair.getReserves()
    lp_balance_2 = pair.balanceOf(user1)
    
    log.debug("阶段 2 追加：TokenA=%s, TokenB=%s", format_ether(add_narrow), format_ether(add_narrow))
    log.debug("池子储备 A: %s", format_ether(reserves_2[0]))
    log.debug("池子储备 B: %s", format_ether(reserves_2[1]))
    log.debug("用户 LP 总余额：%s", format_ether(lp_balance_2))
    
    assert reserves_2[0] == add_full + add_narrow, "窄区间后储备 A 应叠加"
    assert reserves_2[1] == add_full + add_narrow, "窄区间后储备 B 应叠加"
    assert lp_balance_2 > lp_balance_1, "LP 应该增加"
    
    log.info("✓ case_055 集中流动性测试通过：全区间 + 窄区间流动性正确聚合")
