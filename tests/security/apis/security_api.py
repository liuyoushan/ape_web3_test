"""
==============================================================================
Security API 层 - 封装安全测试合约交互
==============================================================================
"""
from ape import Contract
from framework.core.formatters import parse_ether, format_ether


class ReentrancyVaultAPI:
    """
    重入防护金库合约交互封装类
    
    提供带有重入锁保护的金库操作，用于测试重入攻击防护机制。
    """

    def __init__(self, contract: Contract):
        """
        初始化重入防护金库 API
        
        Args:
            contract: Ape Contract 对象，已部署的 ReentrancyVault 合约实例
        """
        self.contract = contract

    def deposit(self, amount_ether: str, sender):
        """
        存款操作
        
        Args:
            amount_ether: 存款金额（ether字符串）
            sender: 存款账户
        """
        amount = parse_ether(amount_ether)
        return self.contract.deposit(sender=sender, value=amount)

    def withdraw(self, sender):
        """
        取款操作
        
        Args:
            sender: 取款账户
        """
        return self.contract.withdraw(sender=sender)

    def get_balance(self, address) -> int:
        """
        获取指定地址的存款余额
        
        Args:
            address: 用户地址
            
        Returns:
            int: 存款余额（wei）
        """
        return self.contract.balances(address)


class VulnerableVaultAPI:
    """
    存在重入漏洞的金库合约交互封装类
    
    提供未受保护的金库操作，用于模拟重入攻击场景。
    """

    def __init__(self, contract: Contract):
        """
        初始化漏洞金库 API
        
        Args:
            contract: Ape Contract 对象，已部署的 VulnerableVault 合约实例
        """
        self.contract = contract

    def deposit(self, amount_ether: str, sender):
        """
        存款操作
        
        Args:
            amount_ether: 存款金额（ether字符串）
            sender: 存款账户
        """
        amount = parse_ether(amount_ether)
        return self.contract.deposit(sender=sender, value=amount)

    def withdraw(self, sender):
        """
        取款操作（存在重入漏洞）
        
        Args:
            sender: 取款账户
        """
        return self.contract.withdraw(sender=sender)

    def get_balance(self, address) -> int:
        """
        获取指定地址的存款余额
        
        Args:
            address: 用户地址
            
        Returns:
            int: 存款余额（wei）
        """
        return self.contract.balances(address)


class StakingAPI:
    """
    质押合约交互封装类
    
    提供质押、解押、领取奖励等操作的原子封装。
    """

    def __init__(self, contract: Contract):
        """
        初始化质押 API
        
        Args:
            contract: Ape Contract 对象，已部署的 StakingContract 合约实例
        """
        self.contract = contract

    def stake(self, amount_ether: str, sender):
        """
        质押操作
        
        Args:
            amount_ether: 质押金额（ether字符串）
            sender: 质押账户
        """
        amount = parse_ether(amount_ether)
        return self.contract.stake(amount, sender=sender)

    def withdraw(self, amount_ether: str, sender):
        """
        解押操作
        
        Args:
            amount_ether: 解押金额（ether字符串）
            sender: 解押账户
        """
        amount = parse_ether(amount_ether)
        return self.contract.withdraw(amount, sender=sender)

    def get_reward(self, sender):
        """
        领取质押奖励
        
        Args:
            sender: 领取奖励的账户
        """
        return self.contract.getReward(sender=sender)

    def get_staked_balance(self, address) -> int:
        """
        获取指定地址的质押余额
        
        Args:
            address: 用户地址
            
        Returns:
            int: 质押余额（wei）
        """
        return self.contract.balances(address)


class TimeLockAPI:
    """
    时间锁合约交互封装类
    
    提供基于时间/区块的锁定机制操作封装。
    """

    def __init__(self, contract: Contract):
        """
        初始化时间锁 API
        
        Args:
            contract: Ape Contract 对象，已部署的 TimeLockContract 合约实例
        """
        self.contract = contract

    def deposit(self, amount_ether: str, sender):
        """
        锁定存款操作
        
        Args:
            amount_ether: 锁定金额（ether字符串）
            sender: 锁定账户
        """
        amount = parse_ether(amount_ether)
        return self.contract.deposit(sender=sender, value=amount)

    def withdraw(self, sender):
        """
        解锁取款操作
        
        Args:
            sender: 取款账户
        """
        return self.contract.withdraw(sender=sender)

    def get_lock_time(self, user) -> int:
        """
        获取用户的锁定时间
        
        Args:
            user: 用户地址
            
        Returns:
            int: 锁定时间戳
        """
        return self.contract.lockTime(user)