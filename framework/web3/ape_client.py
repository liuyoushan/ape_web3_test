"""
==============================================================================
Ape Framework 客户端封装
==============================================================================
支持特性：
  - 合约部署和调用
  - 账户管理
  - 网络切换
  - 快照和回滚
  - 事件监听
==============================================================================
"""

from typing import Any, Optional, List, Dict
from framework.core.logger import log


class ApeClient:
    """
    Ape Framework 客户端
    
    使用方式：
        client = ApeClient()
        
        # 合约部署
        contract = client.deploy(project.MyERC20, "Token", "TKN")
        
        # 合约调用
        balance = client.call(contract.balanceOf, user_address)
        
        # 交易发送
        tx = client.transact(contract.transfer, recipient, amount, sender=user)
        
        # 快照和回滚
        snapshot_id = client.snapshot()
        client.rollback(snapshot_id)
    """
    
    def __init__(self, network: Optional[str] = None):
        """
        初始化 Ape 客户端
        
        Args:
            network: 网络名称（如 "ethereum:local"）
        """
        self.network = network
        
        # 导入 Ape 模块（延迟导入，避免未安装时报错）
        try:
            from ape import project, accounts, networks, chain
            self.project = project
            self.accounts = accounts
            self.networks = networks
            self.chain = chain
        except ImportError as e:
            log.error(f"Ape Framework 未安装: {e}")
            raise
    
    def deploy(
        self,
        contract_type: Any,
        *args,
        sender: Optional[Any] = None,
        **kwargs
    ) -> Any:
        """
        部署合约
        
        Args:
            contract_type: 合约类型
            *args: 构造函数参数
            sender: 发送者账户
            **kwargs: 其他参数
            
        Returns:
            合约实例
        """
        log.debug(f"部署合约: {contract_type.__name__}")
        
        if sender is None:
            sender = self.accounts.test_accounts[0]
        
        contract = contract_type.deploy(*args, sender=sender, **kwargs)
        
        log.success(f"合约部署成功: {contract.address}")
        return contract
    
    def call(
        self,
        method: Any,
        *args,
        **kwargs
    ) -> Any:
        """
        调用合约方法（只读）
        
        Args:
            method: 合约方法
            *args: 方法参数
            **kwargs: 其他参数
            
        Returns:
            方法返回值
        """
        log.debug(f"调用合约方法: {method.__name__}")
        
        result = method(*args, **kwargs)
        
        log.success(f"方法调用成功")
        return result
    
    def transact(
        self,
        method: Any,
        *args,
        sender: Optional[Any] = None,
        value: Optional[int] = None,
        **kwargs
    ) -> Any:
        """
        发送交易
        
        Args:
            method: 合约方法
            *args: 方法参数
            sender: 发送者账户
            value: 发送的 ETH 数量（wei）
            **kwargs: 其他参数
            
        Returns:
            交易收据
        """
        log.debug(f"发送交易: {method.__name__}")
        
        if sender is None:
            sender = self.accounts.test_accounts[0]
        
        if value is not None:
            kwargs["value"] = value
        
        receipt = method(*args, sender=sender, **kwargs)
        
        log.success(f"交易成功: {receipt.txn_hash}")
        return receipt
    
    def snapshot(self) -> int:
        """
        创建快照
        
        Returns:
            快照 ID
        """
        snapshot_id = self.chain.snapshot()
        log.debug(f"创建快照: {snapshot_id}")
        return snapshot_id
    
    def rollback(self, snapshot_id: int):
        """
        回滚到快照
        
        Args:
            snapshot_id: 快照 ID
        """
        self.chain.restore(snapshot_id)
        log.debug(f"回滚到快照: {snapshot_id}")
    
    def get_account(self, index: int = 0) -> Any:
        """
        获取测试账户
        
        Args:
            index: 账户索引
            
        Returns:
            账户对象
        """
        return self.accounts.test_accounts[index]
    
    def get_accounts(self, count: int = 10) -> List[Any]:
        """
        获取多个测试账户
        
        Args:
            count: 账户数量
            
        Returns:
            账户列表
        """
        return self.accounts.test_accounts[:count]
    
    def get_balance(self, account: Any) -> int:
        """
        获取账户余额
        
        Args:
            account: 账户对象或地址
            
        Returns:
            余额（wei）
        """
        return account.balance
    
    def get_block_number(self) -> int:
        """
        获取当前区块号
        
        Returns:
            区块号
        """
        return self.chain.blocks.head.number
    
    def mine(self, num_blocks: int = 1):
        """
        挖矿
        
        Args:
            num_blocks: 区块数量
        """
        self.chain.mine(num_blocks)
        log.debug(f"挖矿 {num_blocks} 个区块")
    
    def set_balance(self, account: Any, amount: int):
        """
        设置账户余额
        
        Args:
            account: 账户对象
            amount: 余额（wei）
        """
        # 使用 Anvil 的 setBalance 功能
        provider = self.chain.provider
        if hasattr(provider, "set_balance"):
            provider.set_balance(account.address, amount)
            log.debug(f"设置账户余额: {account.address} -> {amount}")
    
    def get_events(
        self,
        receipt: Any,
        event_name: str
    ) -> List[Dict]:
        """
        获取交易事件
        
        Args:
            receipt: 交易收据
            event_name: 事件名称
            
        Returns:
            事件列表
        """
        events = []
        
        for event in receipt.events:
            if event.event_name == event_name:
                events.append(event.event_arguments)
        
        return events


# 全局 Ape 客户端
ape_client = ApeClient()