"""
==============================================================================
DEX API 层 - 封装 DEX 合约交互
==============================================================================
"""
from ape import Contract
from framework.core.formatters import parse_ether, format_ether


class MiniSwapPairAPI:
    """
    MiniSwap 交易对合约交互封装类
    
    提供交易对（Pair）合约的原子操作封装，
    用于查询储备金、LP 代币余额和授权操作。
    """

    def __init__(self, contract: Contract):
        """
        初始化 Pair API
        
        Args:
            contract: Ape Contract 对象，已部署的 MiniSwapPair 合约实例
        """
        self.contract = contract

    def get_reserves(self):
        """
        获取交易对储备金
        
        Returns:
            tuple: (reserveA, reserveB, blockTimestampLast)
        """
        return self.contract.getReserves()

    def get_balance(self, address):
        """
        获取指定地址的 LP 代币余额
        
        Args:
            address: 钱包地址
            
        Returns:
            int: LP 代币余额（wei）
        """
        return self.contract.balanceOf(address)

    def get_total_supply(self):
        """
        获取 LP 代币总供应量
        
        Returns:
            int: LP 代币总供应量（wei）
        """
        return self.contract.totalSupply()

    def approve(self, spender, amount_ether: str, sender):
        """
        授权操作
        
        Args:
            spender: 被授权地址
            amount_ether: 授权金额（ether字符串）
            sender: 授权方账户
        """
        amount = parse_ether(amount_ether)
        return self.contract.approve(spender, amount, sender=sender)


class MiniSwapRouterAPI:
    """
    MiniSwap 路由合约交互封装类
    
    提供 DEX 核心交易功能的原子操作封装，
    包括添加/移除流动性、代币兑换、金额计算等。
    """

    def __init__(self, contract: Contract):
        """
        初始化 Router API
        
        Args:
            contract: Ape Contract 对象，已部署的 MiniSwapRouter 合约实例
        """
        self.contract = contract

    def add_liquidity(
        self, token_a, token_b, amount_a_ether: str, amount_b_ether: str, to, sender
    ):
        """
        添加流动性
        
        Args:
            token_a: TokenA 合约地址或实例
            token_b: TokenB 合约地址或实例
            amount_a_ether: TokenA 存入金额（ether字符串）
            amount_b_ether: TokenB 存入金额（ether字符串）
            to: LP 代币接收地址
            sender: 执行交易的账户
        """
        amount_a = parse_ether(amount_a_ether)
        amount_b = parse_ether(amount_b_ether)
        return self.contract.addLiquidity(
            token_a, token_b, amount_a, amount_b, to, sender=sender
        )

    def remove_liquidity(self, token_a, token_b, lp_amount, to, sender):
        """
        移除流动性
        
        Args:
            token_a: TokenA 合约地址或实例
            token_b: TokenB 合约地址或实例
            lp_amount: 要销毁的 LP 代币数量（wei）
            to: 赎回资产接收地址
            sender: 执行交易的账户
        """
        return self.contract.removeLiquidity(token_a, token_b, lp_amount, to, sender=sender)

    def swap_exact_tokens_for_tokens(
        self, amount_in_ether: str, amount_out_min, path, to, sender
    ):
        """
        精确输入代币兑换
        
        Args:
            amount_in_ether: 输入代币金额（ether字符串）
            amount_out_min: 最小输出金额（wei），用于滑点控制
            path: 兑换路径列表，如 [tokenA, tokenB] 或 [tokenA, tokenB, tokenC]
            to: 输出代币接收地址
            sender: 执行交易的账户
        """
        amount_in = parse_ether(amount_in_ether)
        return self.contract.swapExactTokensForTokens(
            amount_in, amount_out_min, path, to, sender=sender
        )

    def get_amount_out(self, amount_in_ether: str, token_a, token_b):
        """
        计算预期输出金额
        
        Args:
            amount_in_ether: 输入金额（ether字符串）
            token_a: 输入代币合约地址或实例
            token_b: 输出代币合约地址或实例
            
        Returns:
            int: 预期输出金额（wei）
        """
        amount_in = parse_ether(amount_in_ether)
        return self.contract.getAmountOut(amount_in, token_a, token_b)


class MiniSwapFactoryAPI:
    """
    MiniSwap 工厂合约交互封装类
    
    提供交易对创建和查询功能的原子操作封装。
    """

    def __init__(self, contract: Contract):
        """
        初始化 Factory API
        
        Args:
            contract: Ape Contract 对象，已部署的 MiniSwapFactory 合约实例
        """
        self.contract = contract

    def get_pair(self, token_a, token_b):
        """
        查询交易对地址
        
        Args:
            token_a: TokenA 合约地址或实例
            token_b: TokenB 合约地址或实例
            
        Returns:
            str: 交易对合约地址，不存在则返回 0x0
        """
        return self.contract.getPair(token_a, token_b)