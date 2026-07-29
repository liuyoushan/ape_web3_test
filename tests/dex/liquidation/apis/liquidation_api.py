"""
==============================================================================
Liquidation API 层 - 封装清算合约交互
==============================================================================
"""
from ape import Contract
from framework.core.formatters import parse_ether, format_ether


class LiquidationAPI:
    """
    清算合约交互封装类
    
    提供借贷清算系统的原子操作封装，
    包括存款、借款、还款、清算等核心功能。
    """

    def __init__(self, contract: Contract):
        """
        初始化 Liquidation API
        
        Args:
            contract: Ape Contract 对象，已部署的 Liquidation 合约实例
        """
        self.contract = contract

    def get_collateral_token(self):
        """
        获取抵押代币合约地址
        
        Returns:
            str: 抵押代币合约地址
        """
        return self.contract.collateralToken()

    def get_debt_token(self):
        """
        获取债务代币合约地址
        
        Returns:
            str: 债务代币合约地址
        """
        return self.contract.debtToken()

    def deposit_collateral(self, amount_ether: str, sender):
        """
        存入抵押资产
        
        Args:
            amount_ether: 存入金额（ether字符串）
            sender: 执行存款的账户
        """
        amount = parse_ether(amount_ether)
        return self.contract.depositCollateral(amount, sender=sender)

    def borrow(self, amount_ether: str, sender):
        """
        借款操作
        
        Args:
            amount_ether: 借款金额（ether字符串）
            sender: 借款人账户
        """
        amount = parse_ether(amount_ether)
        return self.contract.borrow(amount, sender=sender)

    def repay(self, amount_ether: str, sender):
        """
        还款操作
        
        Args:
            amount_ether: 还款金额（ether字符串）
            sender: 还款人账户
        """
        amount = parse_ether(amount_ether)
        return self.contract.repay(amount, sender=sender)

    def withdraw_collateral(self, amount_ether: str, sender):
        """
        提取抵押资产
        
        Args:
            amount_ether: 提取金额（ether字符串）
            sender: 执行提取的账户
        """
        amount = parse_ether(amount_ether)
        return self.contract.withdrawCollateral(amount, sender=sender)

    def liquidate(self, borrower, amount_ether: str, sender):
        """
        执行清算
        
        Args:
            borrower: 被清算的借款人地址
            amount_ether: 清算金额（ether字符串）
            sender: 清算人账户
        """
        amount = parse_ether(amount_ether)
        return self.contract.liquidate(borrower, amount, sender=sender)

    def get_health_factor(self, user) -> int:
        """
        获取用户健康因子
        
        Args:
            user: 用户地址
            
        Returns:
            int: 健康因子值（wei格式）
        """
        return self.contract.getHealthFactor(user)

    def get_collateral_balance(self, user) -> int:
        """
        获取用户抵押资产余额
        
        Args:
            user: 用户地址
            
        Returns:
            int: 抵押资产余额（wei）
        """
        return self.contract.collateralBalance(user)

    def get_debt_balance(self, user) -> int:
        """
        获取用户债务余额
        
        Args:
            user: 用户地址
            
        Returns:
            int: 债务余额（wei）
        """
        return self.contract.debtBalance(user)