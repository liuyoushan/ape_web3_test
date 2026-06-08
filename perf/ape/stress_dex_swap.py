"""
==============================================================================
APE DEX Swap 并发压测脚本
==============================================================================
复用现有 tests/fixtures/ 的部署逻辑，对 DEX 进行多用户并发压测

运行方式:
    ape run perf/ape/stress_dex_swap

前置条件:
    - 本地 anvil 节点已启动: anvil --fork-url <RPC_URL> 或直接 anvil
    - 或连接 ape 配置的 local 网络
==============================================================================
"""

import time
import json
import os
from datetime import datetime
from ape import accounts, project, networks

from tests.helpers.formatters import parse_ether, format_ether


# ==============================================================================
# 配置参数
# ==============================================================================
CONFIG = {
    "user_count": 20,           # 并发用户数量
    "swap_amount": "10 ether",  # 每次兑换数量
    "mint_amount": "1000 ether", # 每个用户初始代币
    "liquidity_amount": "50000 ether",  # 初始流动性
    "report_dir": "perf/reports",
}


def deploy_environment(deployer):
    """部署 DEX 环境（复用 fixture 逻辑）"""
    print("[1/4] 部署代币...")
    tokenA = project.MyERC20.deploy("TokenA", "TKA", sender=deployer)
    tokenB = project.MyERC20.deploy("TokenB", "TKB", sender=deployer)
    print(f"      TokenA: {tokenA.address}")
    print(f"      TokenB: {tokenB.address}")

    print("[2/4] 部署 Factory & Router...")
    factory = project.MiniSwapFactory.deploy(sender=deployer)
    router = project.MiniSwapRouter.deploy(factory, sender=deployer)
    print(f"      Factory: {factory.address}")
    print(f"      Router: {router.address}")

    print("[3/4] 铸造代币并添加流动性...")
    tokenA.mint(deployer, parse_ether(CONFIG["liquidity_amount"]), sender=deployer)
    tokenB.mint(deployer, parse_ether(CONFIG["liquidity_amount"]), sender=deployer)

    tokenA.approve(router, parse_ether(CONFIG["liquidity_amount"]), sender=deployer)
    tokenB.approve(router, parse_ether(CONFIG["liquidity_amount"]), sender=deployer)

    router.addLiquidity(
        tokenA,
        tokenB,
        parse_ether(CONFIG["liquidity_amount"]),
        parse_ether(CONFIG["liquidity_amount"]),
        deployer,
        sender=deployer
    )
    print("      流动性添加完成")

    print("[4/4] 环境部署完成")
    return tokenA, tokenB, factory, router


def create_users(deployer, tokenA, count):
    """创建测试用户并铸造代币"""
    users = []
    for i in range(count):
        user = accounts.test_accounts[i + 1]  # deployer 是 test_accounts[0]
        tokenA.mint(user, parse_ether(CONFIG["mint_amount"]), sender=deployer)
        users.append(user)
    return users


def user_swap(user, tokenA, tokenB, router):
    """单个用户执行 swap"""
    swap_amount = parse_ether(CONFIG["swap_amount"])

    try:
        # 授权
        tokenA.approve(router, swap_amount, sender=user)

        # 执行兑换
        tx = router.swapExactTokensForTokens(
            swap_amount,
            0,
            [tokenA.address, tokenB.address],
            user,
            sender=user
        )
        return {
            "success": True,
            "gas_used": tx.gas_used,
            "tx_hash": tx.txn_hash,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def run_stress_test():
    """执行压测主流程"""
    print("=" * 60)
    print("APE DEX Swap 并发压测")
    print("=" * 60)

    deployer = accounts.test_accounts[0]
    print(f"Deployer: {deployer.address}")

    # 部署环境
    tokenA, tokenB, factory, router = deploy_environment(deployer)

    # 创建用户
    print(f"\n创建 {CONFIG['user_count']} 个测试用户...")
    users = create_users(deployer, tokenA, CONFIG["user_count"])

    # 执行并发 swap（串行模拟，ape test 账户不支持真正的并行签名）
    print(f"\n开始执行 {CONFIG['user_count']} 次 swap...")
    results = []
    start_time = time.time()

    for i, user in enumerate(users):
        result = user_swap(user, tokenA, tokenB, router)
        result["user_index"] = i
        results.append(result)

        if result["success"]:
            print(f"  User {i}: OK  gas={result['gas_used']}")
        else:
            print(f"  User {i}: FAIL  error={result['error']}")

    elapsed = time.time() - start_time

    # 统计结果
    success_count = sum(1 for r in results if r["success"])
    gas_list = [r["gas_used"] for r in results if r["success"]]
    avg_gas = sum(gas_list) // len(gas_list) if gas_list else 0

    report = {
        "timestamp": datetime.now().isoformat(),
        "test_type": "dex_swap_stress",
        "config": CONFIG,
        "summary": {
            "total_users": CONFIG["user_count"],
            "success_count": success_count,
            "fail_count": CONFIG["user_count"] - success_count,
            "success_rate": f"{success_count * 100 // CONFIG['user_count']}%",
            "total_time_sec": round(elapsed, 2),
            "avg_gas_used": avg_gas,
            "min_gas": min(gas_list) if gas_list else 0,
            "max_gas": max(gas_list) if gas_list else 0,
        },
        "details": results,
    }

    # 输出报告
    print("\n" + "=" * 60)
    print("压测报告")
    print("=" * 60)
    print(f"总用户数    : {report['summary']['total_users']}")
    print(f"成功数      : {report['summary']['success_count']}")
    print(f"失败数      : {report['summary']['fail_count']}")
    print(f"成功率      : {report['summary']['success_rate']}")
    print(f"总耗时      : {report['summary']['total_time_sec']}s")
    print(f"平均 Gas    : {report['summary']['avg_gas_used']}")
    print(f"最小 Gas    : {report['summary']['min_gas']}")
    print(f"最大 Gas    : {report['summary']['max_gas']}")
    print("=" * 60)

    # 保存报告
    os.makedirs(CONFIG["report_dir"], exist_ok=True)
    report_path = os.path.join(
        CONFIG["report_dir"],
        f"stress_dex_swap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n报告已保存: {report_path}")

    return report


def main():
    """ape run 入口"""
    run_stress_test()


if __name__ == "__main__":
    main()
