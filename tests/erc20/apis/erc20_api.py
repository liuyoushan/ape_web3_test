"""
==============================================================================
ERC20 API 层 - 封装 ERC20 合约交互
==============================================================================
"""
from ape import Contract
from framework.core.formatters import parse_ether, format_ether


class ERC20API:
    """
    ERC20 代币合约交互封装类
    
    提供 ERC20 标准接口及扩展功能的原子操作封装，
    统一处理单位转换（ether字符串 -> wei）和合约调用。
    """

    def __init__(self, contract: Contract):
        """
        初始化 ERC20 API
        
        Args:
            contract: Ape Contract 对象，已部署的 ERC20 合约实例
        """
        self.contract = contract

    def get_name(self) -> str:
        """获取代币名称"""
        return self.contract.name()

    def get_symbol(self) -> str:
        """获取代币符号"""
        return self.contract.symbol()

    def get_decimals(self) -> int:
        """获取代币小数位数"""
        return self.contract.decimals()

    def get_total_supply(self) -> int:
        """获取代币总供应量（wei）"""
        return self.contract.totalSupply()

    def get_balance(self, address) -> int:
        """
        获取指定地址的代币余额
        
        Args:
            address: 钱包地址
        
        Returns:
            余额（wei）
        """
        return self.contract.balanceOf(address)

    def get_allowance(self, owner, spender) -> int:
        """
        获取授权额度
        
        Args:
            owner: 授权方地址
            spender: 被授权方地址
        
        Returns:
            授权额度（wei）
        """
        return self.contract.allowance(owner, spender)

    def transfer(self, to, amount_ether: str, sender):
        """
        代币转账
        
        Args:
            to: 接收方地址
            amount_ether: 转账金额（ether字符串，如 "100"）
            sender: 发送方账户
        """
        amount = parse_ether(amount_ether)
        return self.contract.transfer(to, amount, sender=sender)

    def transfer_from(self, from_addr, to, amount_ether: str, sender):
        """
        授权转账
        
        Args:
            from_addr: 资金来源地址
            to: 接收方地址
            amount_ether: 转账金额（ether字符串）
            sender: 执行交易的账户（需有授权）
        """
        amount = parse_ether(amount_ether)
        return self.contract.transferFrom(from_addr, to, amount, sender=sender)

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

    def mint(self, to, amount_ether: str, sender):
        """
        铸造代币（需 MINTER_ROLE）
        
        Args:
            to: 接收铸造代币的地址
            amount_ether: 铸造金额（ether字符串）
            sender: 执行账户（需有 MINTER_ROLE）
        """
        amount = parse_ether(amount_ether)
        return self.contract.mint(to, amount, sender=sender)

    def burn(self, amount_ether: str, sender):
        """
        销毁自己的代币
        
        Args:
            amount_ether: 销毁金额（ether字符串）
            sender: 执行账户
        """
        amount = parse_ether(amount_ether)
        return self.contract.burn(amount, sender=sender)

    def burn_from(self, from_addr, amount_ether: str, sender):
        """
        销毁指定地址的代币（需授权）
        
        Args:
            from_addr: 代币来源地址
            amount_ether: 销毁金额（ether字符串）
            sender: 执行账户（需有授权）
        """
        amount = parse_ether(amount_ether)
        return self.contract.burnFrom(from_addr, amount, sender=sender)

    def pause(self, sender):
        """
        暂停合约（需 PAUSER_ROLE）
        
        Args:
            sender: 执行账户（需有 PAUSER_ROLE）
        """
        return self.contract.pause(sender=sender)

    def unpause(self, sender):
        """
        恢复合约（需 PAUSER_ROLE）
        
        Args:
            sender: 执行账户（需有 PAUSER_ROLE）
        """
        return self.contract.unpause(sender=sender)

    def is_paused(self) -> bool:
        """检查合约是否暂停"""
        return self.contract.paused()

    def grant_role(self, role, account, sender):
        """
        授予角色（需 ADMIN_ROLE）
        
        Args:
            role: 角色标识（如 MINTER_ROLE）
            account: 被授予角色的地址
            sender: 执行账户（需有 ADMIN_ROLE）
        """
        return self.contract.grantRole(role, account, sender=sender)

    def revoke_role(self, role, account, sender):
        """
        撤销角色（需 ADMIN_ROLE）
        
        Args:
            role: 角色标识
            account: 被撤销角色的地址
            sender: 执行账户（需有 ADMIN_ROLE）
        """
        return self.contract.revokeRole(role, account, sender=sender)

    def has_role(self, role, account) -> bool:
        """
        检查地址是否拥有指定角色
        
        Args:
            role: 角色标识
            account: 待检查地址
        
        Returns:
            是否拥有角色
        """
        return self.contract.hasRole(role, account)

    def get_minter_role(self) -> bytes:
        """获取 MINTER_ROLE 角色标识"""
        return self.contract.MINTER_ROLE()

    def get_pauser_role(self) -> bytes:
        """获取 PAUSER_ROLE 角色标识"""
        return self.contract.PAUSER_ROLE()

    def get_admin_role(self) -> bytes:
        """获取 ADMIN_ROLE 角色标识"""
        return self.contract.ADMIN_ROLE()

    def decode_transfer_event(self, tx):
        """
        解析交易中的 Transfer 事件
        
        Args:
            tx: 交易对象
        
        Returns:
            Transfer 事件对象，包含 from, to, value
        """
        events = tx.decode_logs(self.contract.Transfer)
        return events[0] if events else None

    def decode_approval_event(self, tx):
        """
        解析交易中的 Approval 事件
        
        Args:
            tx: 交易对象
        
        Returns:
            Approval 事件对象，包含 owner, spender, value
        """
        events = tx.decode_logs(self.contract.Approval)
        return events[0] if events else None