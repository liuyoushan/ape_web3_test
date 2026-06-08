// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../../contracts/MiniSwapRouter.sol";
import "../../contracts/MiniSwapFactory.sol";
import "../../contracts/MyERC20.sol";

/**
 * @title GasBenchmark
 * @notice DEX 核心操作 Gas 基准测试
 * @dev 部署合约 -> 添加流动性 -> 执行兑换 -> 记录各步骤 gas 消耗
 */
contract GasBenchmark is Script {
    MiniSwapFactory public factory;
    MiniSwapRouter public router;
    MyERC20 public tokenA;
    MyERC20 public tokenB;

    // 测试参数
    uint256 constant INITIAL_MINT = 10000 ether;
    uint256 constant LIQUIDITY_AMOUNT = 1000 ether;
    uint256 constant SWAP_AMOUNT = 100 ether;

    function run() external {
        uint256 deployerKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerKey);
        vm.startBroadcast(deployerKey);

        // 1. 部署代币
        tokenA = new MyERC20("TokenA", "TKA");
        tokenB = new MyERC20("TokenB", "TKB");
        console.log("TokenA deployed at:", address(tokenA));
        console.log("TokenB deployed at:", address(tokenB));

        // 2. 部署 Factory 和 Router
        factory = new MiniSwapFactory();
        router = new MiniSwapRouter(address(factory));
        console.log("Factory deployed at:", address(factory));
        console.log("Router deployed at:", address(router));

        // 3. 铸造代币给 deployer
        tokenA.mint(deployer, INITIAL_MINT);
        tokenB.mint(deployer, INITIAL_MINT);

        // 4. 授权 Router
        tokenA.approve(address(router), type(uint256).max);
        tokenB.approve(address(router), type(uint256).max);

        // 5. 添加流动性（记录 gas）
        uint256 gasBefore = gasleft();
        router.addLiquidity(
            address(tokenA),
            address(tokenB),
            LIQUIDITY_AMOUNT,
            LIQUIDITY_AMOUNT,
            deployer
        );
        uint256 gasAddLiquidity = gasBefore - gasleft();
        console.log("Gas used - addLiquidity:", gasAddLiquidity);

        // 6. 执行兑换（记录 gas）
        address[] memory path = new address[](2);
        path[0] = address(tokenA);
        path[1] = address(tokenB);

        gasBefore = gasleft();
        router.swapExactTokensForTokens(
            SWAP_AMOUNT,
            0,
            path,
            deployer
        );
        uint256 gasSwap = gasBefore - gasleft();
        console.log("Gas used - swapExactTokensForTokens:", gasSwap);

        // 7. 移除流动性（记录 gas）
        address pairAddr = factory.getPair(address(tokenA), address(tokenB));
        MiniSwapPair pair = MiniSwapPair(pairAddr);
        uint256 lpBalance = pair.balanceOf(deployer);
        pair.approve(address(router), lpBalance);

        gasBefore = gasleft();
        router.removeLiquidity(
            address(tokenA),
            address(tokenB),
            lpBalance,
            deployer
        );
        uint256 gasRemoveLiquidity = gasBefore - gasleft();
        console.log("Gas used - removeLiquidity:", gasRemoveLiquidity);

        vm.stopBroadcast();

        // 输出汇总报告
        console.log("\n========== Gas Benchmark Report ==========");
        console.log("addLiquidity      :", gasAddLiquidity);
        console.log("swap              :", gasSwap);
        console.log("removeLiquidity   :", gasRemoveLiquidity);
        console.log("==========================================");
    }
}
