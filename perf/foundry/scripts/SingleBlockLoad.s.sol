// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../../contracts/MiniSwapRouter.sol";
import "../../contracts/MiniSwapFactory.sol";
import "../../contracts/MyERC20.sol";

/**
 * @title SingleBlockLoad
 * @notice 单区块批量交易压测 - 填满区块
 * @dev 在单个区块内发送大量 swap 交易，测试区块 gas 限制下的吞吐量
 */
contract SingleBlockLoad is Script {
    MiniSwapRouter public router;
    MyERC20 public tokenA;
    MyERC20 public tokenB;

    // 单块交易数量（根据 gas 限制调整，Mantle 约 30M gas）
    uint256 public constant BATCH_COUNT = 50;
    uint256 public constant SWAP_AMOUNT = 1 ether;

    function run() external {
        uint256 deployerKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerKey);
        vm.startBroadcast(deployerKey);

        // 使用已部署的合约地址（或通过环境变量传入）
        address routerAddr = vm.envOr("ROUTER_ADDRESS", address(0));
        address tokenAAddr = vm.envOr("TOKENA_ADDRESS", address(0));
        address tokenBAddr = vm.envOr("TOKENB_ADDRESS", address(0));

        if (routerAddr == address(0)) {
            // 本地测试：重新部署
            MiniSwapFactory factory = new MiniSwapFactory();
            router = new MiniSwapRouter(address(factory));
            tokenA = new MyERC20("TokenA", "TKA");
            tokenB = new MyERC20("TokenB", "TKB");

            tokenA.mint(deployer, 100000 ether);
            tokenB.mint(deployer, 100000 ether);

            tokenA.approve(address(router), type(uint256).max);
            tokenB.approve(address(router), type(uint256).max);

            router.addLiquidity(
                address(tokenA),
                address(tokenB),
                10000 ether,
                10000 ether,
                deployer
            );
        } else {
            router = MiniSwapRouter(routerAddr);
            tokenA = MyERC20(tokenAAddr);
            tokenB = MyERC20(tokenBAddr);
        }

        // 预先授权
        tokenA.approve(address(router), type(uint256).max);

        address[] memory path = new address[](2);
        path[0] = address(tokenA);
        path[1] = address(tokenB);

        uint256 gasBefore = gasleft();
        uint256 successCount = 0;

        // 批量发送 swap 交易填满区块
        for (uint256 i = 0; i < BATCH_COUNT; i++) {
            try router.swapExactTokensForTokens(
                SWAP_AMOUNT,
                0,
                path,
                deployer
            ) {
                successCount++;
            } catch {
                // 记录失败但不中断
            }
        }

        uint256 totalGas = gasBefore - gasleft();
        vm.stopBroadcast();

        console.log("\n========== Single Block Load Report ==========");
        console.log("Batch count       :", BATCH_COUNT);
        console.log("Success count     :", successCount);
        console.log("Total gas used    :", totalGas);
        console.log("Avg gas per tx    :", totalGas / BATCH_COUNT);
        console.log("Success rate      :", (successCount * 100) / BATCH_COUNT, "%");
        console.log("================================================");
    }
}
