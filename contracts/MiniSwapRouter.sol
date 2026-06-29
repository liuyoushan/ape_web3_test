// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./MyERC20.sol";
import "./MiniSwapFactory.sol";

contract MiniSwapRouter {
    address public immutable factory;

    constructor(address _factory) {
        factory = _factory;
    }

    function addLiquidity(
        address tokenA,
        address tokenB,
        uint256 amountADesired,
        uint256 amountBDesired,
        address to
    ) external returns (uint256 amountA, uint256 amountB, uint256 liquidity) {
        address pair = MiniSwapFactory(factory).getPair(tokenA, tokenB);
        if (pair == address(0)) {
            pair = MiniSwapFactory(factory).createPair(tokenA, tokenB);
        }
        (amountA, amountB) = (amountADesired, amountBDesired);
        MyERC20(tokenA).transferFrom(msg.sender, pair, amountA);
        MyERC20(tokenB).transferFrom(msg.sender, pair, amountB);
        liquidity = MiniSwapPair(pair).mint(to);
    }

    function swapExactTokensForTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to
    ) external {
        require(path.length >= 2, "invalid path length");
        
        uint256 amount = amountIn;
        
        for (uint256 i = 0; i < path.length - 1; i++) {
            address tokenIn = path[i];
            address tokenOut = path[i + 1];
            address pair = MiniSwapFactory(factory).getPair(tokenIn, tokenOut);
            
            if (i == 0) {
                MyERC20(tokenIn).transferFrom(msg.sender, pair, amount);
            } else {
                MyERC20(tokenIn).transfer(pair, amount);
            }
            
            amount = getAmountOut(amount, tokenIn, tokenOut);
            
            address token0 = MiniSwapPair(pair).token0();
            (uint256 amount0Out, uint256 amount1Out) = tokenOut == token0 ? (amount, uint256(0)) : (uint256(0), amount);
            
            address recipient = (i == path.length - 2) ? to : address(this);
            MiniSwapPair(pair).swap(amount0Out, amount1Out, recipient);
        }
        
        require(amount >= amountOutMin, "insufficient output amount");
    }

    function getAmountOut(uint256 amountIn, address tokenIn, address tokenOut) public view returns (uint256) {
        address pair = MiniSwapFactory(factory).getPair(tokenIn, tokenOut);
        (uint112 reserve0, uint112 reserve1) = MiniSwapPair(pair).getReserves();
        address token0 = MiniSwapPair(pair).token0();
        (uint112 reserveIn, uint112 reserveOut) = tokenIn == token0 ? (reserve0, reserve1) : (reserve1, reserve0);
        uint256 amountInWithFee = amountIn * 997;
        uint256 numerator = amountInWithFee * reserveOut;
        uint256 denominator = reserveIn * 1000 + amountInWithFee;
        return numerator / denominator;
    }

    function removeLiquidity(
        address tokenA,
        address tokenB,
        uint256 liquidity,
        address to
    ) external returns (uint256 amountA, uint256 amountB) {
        address pair = MiniSwapFactory(factory).getPair(tokenA, tokenB);
        require(pair != address(0), "pair does not exist");

        MiniSwapPair(pair).transferFrom(msg.sender, pair, liquidity);
        (uint256 amount0, uint256 amount1) = MiniSwapPair(pair).burn(to);
        (amountA, amountB) = tokenA < tokenB ? (amount0, amount1) : (amount1, amount0);
    }
}