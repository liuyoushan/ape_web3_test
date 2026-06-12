# from ape import project, accounts

# def test_dex_custom_functions(deployer, user1):
#     # ==================== 代币部署阶段 ====================
#     # 部署两个测试代币：TokenA(TKA) 和 TokenB(TKB)
#     tokenA = project.MyERC20.deploy("TokenA", "TKA", sender=deployer)
#     tokenB = project.MyERC20.deploy("TokenB", "TKB", sender=deployer)
#     print(f"代币部署完成: TokenA={tokenA.address}, TokenB={tokenB.address}")

#     # 铸造初始代币给用户（每个代币铸造 10000 个）
#     mint_amt = 10000 * 10**18
#     tokenA.mint(user1, mint_amt, sender=deployer)
#     tokenB.mint(user1, mint_amt, sender=deployer)
#     print(f"用户 {user1} 初始余额: TokenA={tokenA.balanceOf(user1)/10**18}, TokenB={tokenB.balanceOf(user1)/10**18}")

#     # ==================== DEX基础设施部署 ====================
#     # 部署 MiniSwap 工厂合约（用于创建交易对）
#     factory = project.MiniSwapFactory.deploy(sender=deployer)
#     # 部署路由合约（提供用户友好的接口）
#     router = project.MiniSwapRouter.deploy(factory, sender=deployer)
#     print(f"DEX部署完成: Factory={factory.address}, Router={router.address}")

#     # ==================== 添加流动性 ====================
#     # 用户授权路由合约操作代币（各授权 1000 个）
#     add_liquidity_amt = 1000 * 10**18
#     tokenA.approve(router, add_liquidity_amt, sender=user1)
#     tokenB.approve(router, add_liquidity_amt, sender=user1)

#     # 调用路由合约添加流动性到 TokenA-TokenB 交易对
#     router.addLiquidity(
#         tokenA,      # 代币A地址
#         tokenB,      # 代币B地址
#         add_liquidity_amt,  # TokenA投入数量
#         add_liquidity_amt,  # TokenB投入数量
#         user1,       # 流动性接收地址
#         sender=user1
#     )
#     print(f"添加流动性完成: 各投入 {add_liquidity_amt/10**18} TokenA和TokenB")
#     print(f"用户 {user1} 添加流动性后余额: TokenA={tokenA.balanceOf(user1)/10**18}, TokenB={tokenB.balanceOf(user1)/10**18}")

#     # ==================== 代币兑换测试 ====================
#     # 用户授权路由合约操作 TokenA（用于兑换）
#     swap_amt = 100 * 10**18  # 兑换金额：100 TokenA
#     tokenA.approve(router, swap_amt, sender=user1)

#     # 记录兑换前 TokenB 的余额
#     balance_before = tokenB.balanceOf(user1)
#     print(f"\n=== 代币兑换开始 ===")
#     print(f"兑换方向: TokenA -> TokenB")
#     print(f"兑换金额: {swap_amt/10**18} TokenA")
#     print(f"兑换前用户 TokenB 余额: {balance_before/10**18}")

#     # 调用路由合约执行代币兑换
#     # swapExactTokensForTokens(输入金额, 最小输出, [输入代币, 输出代币], 接收地址)
#     router.swapExactTokensForTokens(
#         swap_amt,                      # 输入 TokenA 的数量
#         0,                             # 最小期望输出（0表示接受任何数量）
#         [tokenA.address, tokenB.address],  # 兑换路径：TokenA -> TokenB
#         user1,                         # 兑换后代币接收地址
#         sender=user1
#     )

#     # 记录兑换后 TokenB 的余额
#     balance_after = tokenB.balanceOf(user1)
#     print(f"兑换后用户 TokenB 余额: {balance_after/10**18}")
#     print(f"获得 TokenB: {(balance_after - balance_before)/10**18}")

#     # 断言兑换成功，TokenB余额增加
#     assert balance_after > balance_before
#     print("✓ 代币兑换测试通过！")