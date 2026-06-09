// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "./contracts/MiniSwapRouter.sol";
import "./contracts/MiniSwapFactory.sol";
import "./contracts/MyERC20.sol";

contract MultiUserConcurrent is Script {
    uint256 public constant USER_NUM = 20;
    uint256 public constant SWAP_AMOUNT = 10 ether;
    uint256 public constant MINT_PER_USER = 100 ether;
    uint256 constant APPROVAL_AMOUNT = type(uint256).max - 1;

    function run() external {
        uint256 deployerKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerKey);

        vm.startBroadcast(deployerKey);
        MyERC20 tokenA = new MyERC20("TokenA", "TKA");
        MyERC20 tokenB = new MyERC20("TokenB", "TKB");
        MiniSwapFactory factory = new MiniSwapFactory();
        MiniSwapRouter router = new MiniSwapRouter(address(factory));

        tokenA.mint(deployer, 100000 ether);
        tokenB.mint(deployer, 100000 ether);
        tokenA.approve(address(router), APPROVAL_AMOUNT);
        tokenB.approve(address(router), APPROVAL_AMOUNT);
        router.addLiquidity(address(tokenA), address(tokenB), 50000 ether, 50000 ether, deployer);
        vm.stopBroadcast();

        address[] memory users = new address[](USER_NUM);
        uint256[] memory userKeys = new uint256[](USER_NUM);

        for (uint256 i = 0; i < USER_NUM; i++) {
            userKeys[i] = uint256(keccak256(abi.encodePacked("user", i, block.timestamp)));
            users[i] = vm.addr(userKeys[i]);

            vm.startBroadcast(deployerKey);
            tokenA.mint(users[i], MINT_PER_USER);
            vm.stopBroadcast();
        }

        address[] memory path = new address[](2);
        path[0] = address(tokenA);
        path[1] = address(tokenB);

        uint256 gasBefore = gasleft();
        uint256 successCount = 0;

        for (uint256 i = 0; i < USER_NUM; i++) {
            vm.startBroadcast(userKeys[i]);
            tokenA.approve(address(router), SWAP_AMOUNT);

            try router.swapExactTokensForTokens(SWAP_AMOUNT, 0, path, users[i]) {
                successCount++;
            } catch {}

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
