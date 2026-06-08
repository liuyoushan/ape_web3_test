// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../../contracts/MiniSwapRouter.sol";
import "../../contracts/MiniSwapFactory.sol";
import "../../contracts/MyERC20.sol";

/**
 * @title MultiUserConcurrent
 * @notice 多用户并发压测 - 模拟真实 mempool 竞争
 * @dev 生成多个独立用户钱包，每个用户独立执行 swap
 */
contract MultiUserConcurrent is Script {
    MiniSwapRouter public router;
    MyERC20 public tokenA;
    MyERC20 public tokenB;

    uint256 public constant USER_NUM = 20;
    uint256 public constant SWAP_AMOUNT = 10 ether;
    uint256 public constant MINT_PER_USER = 1000 ether;

    function run() external {
        uint256 deployerKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerKey);

        // 部署合约（本地测试）
        vm.startBroadcast(deployerKey);
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
            50000 ether,
            50000 ether,
            deployer
        );
        vm.stopBroadcast();

        // 生成用户并铸造代币
        address[] memory users = new address[](USER_NUM);
        uint256[] memory userKeys = new uint256[](USER_NUM);
        uint256 successCount = 0;

        for (uint256 i = 0; i < USER_NUM; i++) {
            userKeys[i] = uint256(keccak256(abi.encodePacked("user", i, block.timestamp)));
            users[i] = vm.addr(userKeys[i]);

            // deployer 给每个用户铸造代币
            vm.startBroadcast(deployerKey);
            tokenA.mint(users[i], MINT_PER_USER);
            vm.stopBroadcast();
        }

        address[] memory path = new address[](2);
        path[0] = address(tokenA);
        path[1] = address(tokenB);

        uint256 gasBefore = gasleft();

        // 每个用户独立发送 swap 交易
        for (uint256 i = 0; i < USER_NUM; i++) {
            vm.startBroadcast(userKeys[i]);

            // 用户授权 router
            tokenA.approve(address(router), SWAP_AMOUNT);

            try router.swapExactTokensForTokens(
                SWAP_AMOUNT,
                0,
                path,
                users[i]
            ) {
                successCount++;
            } catch {
                // 记录失败
            }

            vm.stopBroadcast();
        }

        uint256 totalGas = gasBefore - gasleft();

        console.log("\n========== Multi User Concurrent Report ==========");
        console.log("User count        :", USER_NUM);
        console.log("Success count     :", successCount);
        console.log("Total gas used    :", totalGas);
        console.log("Avg gas per tx    :", totalGas / USER_NUM);
        console.log("Success rate      :", (successCount * 100) / USER_NUM, "%");
        console.log("====================================================");
    }
}
