"""
==============================================================================
链上事件模拟器（Mock Chain）
==============================================================================
模拟 CEX 测试中的核心差异化场景，这些场景在真实环境中难以随意触发：
- 区块回滚模拟（充值入账后回滚）
- 重复 TxHash 注入（一笔充值多次到账测试）
- 提币链上转账失败模拟
- 网络延迟/打包超时
- Gas 费不足导致交易回滚

使用方式：
    from framework.cex.mock_chain import MockChainSimulator
    
    simulator = MockChainSimulator()
    
    # 模拟充值回滚
    simulator.simulate_deposit_rollback(tx_hash="0xabc...", amount=1000)
    
    # 模拟重复充值
    simulator.simulate_duplicate_deposit(tx_hash="0xabc...")
    
    # 模拟提币失败
    simulator.simulate_withdraw_failure(withdraw_id="12345", reason="insufficient_gas")
"""

import time
import random
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from framework.core.logger import log


class ChainEvent(Enum):
    """链上事件类型"""
    BLOCK_ROLLBACK = "block_rollback"          # 区块回滚
    DUPLICATE_TX = "duplicate_tx"              # 重复交易
    WITHDRAW_FAILED = "withdraw_failed"        # 提币失败
    NETWORK_DELAY = "network_delay"            # 网络延迟
    GAS_INSUFFICIENT = "gas_insufficient"      # Gas 费不足
    TX_TIMEOUT = "tx_timeout"                  # 交易超时


class DepositStatus(Enum):
    """充值状态"""
    PENDING = "pending"                # 等待确认
    CONFIRMED = "confirmed"            # 已确认
    ROLLED_BACK = "rolled_back"        # 已回滚
    DUPLICATE = "duplicate"            # 重复入账
    REJECTED = "rejected"              # 已拒绝


class WithdrawStatus(Enum):
    """提币状态"""
    PENDING = "pending"                # 待处理
    PROCESSING = "processing"          # 处理中
    BROADCASTED = "broadcasted"        # 已广播
    CONFIRMED = "confirmed"            # 已确认
    FAILED = "failed"                  # 失败
    ROLLED_BACK = "rolled_back"        # 已回滚


@dataclass
class DepositRecord:
    """充值记录"""
    tx_hash: str
    amount: float
    address: str
    status: DepositStatus = DepositStatus.PENDING
    block_height: int = 0
    confirmations: int = 0
    timestamp: float = field(default_factory=time.time)
    rollback_height: int = 0  # 回滚触发的区块高度


@dataclass
class WithdrawRecord:
    """提币记录"""
    withdraw_id: str
    amount: float
    to_address: str
    status: WithdrawStatus = WithdrawStatus.PENDING
    gas_price: float = 0
    tx_hash: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    failure_reason: str = ""


@dataclass
class ChainSimulation:
    """链上模拟结果"""
    event: ChainEvent
    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)


class MockChainSimulator:
    """
    链上事件模拟器
    
    用于测试 CEX 在各种链上异常场景下的账务一致性与风控机制。
    所有模拟均为内存态，不影响真实链上数据。
    """
    
    def __init__(self):
        self._deposits: Dict[str, DepositRecord] = {}       # tx_hash -> DepositRecord
        self._withdraws: Dict[str, WithdrawRecord] = {}     # withdraw_id -> WithdrawRecord
        self._duplicate_tx_hashes: set = set()              # 已触发重复检测的 tx_hash
        self._simulation_log: List[ChainSimulation] = []    # 模拟日志
        self._block_height: int = 100000                    # 模拟当前区块高度
        self._chain_state: Dict[str, Any] = {               # 模拟链上状态
            "total_deposits": 0,
            "total_withdraws": 0,
            "rolled_back_deposits": 0,
            "failed_withdraws": 0,
        }
    
    # ==================== 区块高度模拟 ====================
    
    def advance_block(self, blocks: int = 1):
        """推进模拟区块高度"""
        self._block_height += blocks
        log.debug(f"[MockChain] 区块高度推进至 #{self._block_height}")
        return self._block_height
    
    @property
    def current_block(self) -> int:
        """获取当前模拟区块高度"""
        return self._block_height
    
    # ==================== 充值模拟 ====================
    
    def register_deposit(
        self,
        tx_hash: str,
        amount: float,
        address: str,
        confirmations: int = 10
    ) -> DepositRecord:
        """
        注册一笔充值（模拟链上充值成功）
        
        Args:
            tx_hash: 交易哈希
            amount: 充值金额
            address: 收款地址
            confirmations: 初始确认数
        """
        record = DepositRecord(
            tx_hash=tx_hash,
            amount=amount,
            address=address,
            status=DepositStatus.CONFIRMED,
            block_height=self._block_height,
            confirmations=confirmations
        )
        self._deposits[tx_hash] = record
        self._chain_state["total_deposits"] += amount
        
        log.info(f"[MockChain] 充值注册成功: tx={tx_hash[:10]}... amount={amount} block=#{self._block_height}")
        return record
    
    def simulate_deposit_rollback(
        self,
        tx_hash: str,
        rollback_height: int = None
    ) -> ChainSimulation:
        """
        模拟充值区块回滚
        
        场景：充值已入账，但后续区块回滚导致交易失效
        测试点：交易所是否检测到回滚并扣回余额
        
        Args:
            tx_hash: 已充值的交易哈希
            rollback_height: 回滚发生的区块高度
        """
        if tx_hash not in self._deposits:
            return ChainSimulation(
                event=ChainEvent.BLOCK_ROLLBACK,
                success=False,
                message=f"充值记录不存在: {tx_hash}"
            )
        
        record = self._deposits[tx_hash]
        
        if record.status != DepositStatus.CONFIRMED:
            return ChainSimulation(
                event=ChainEvent.BLOCK_ROLLBACK,
                success=False,
                message=f"当前状态 {record.status.value} 无法回滚"
            )
        
        # 执行回滚
        record.status = DepositStatus.ROLLED_BACK
        record.rollback_height = rollback_height or self._block_height + 50
        self._chain_state["total_deposits"] -= record.amount
        self._chain_state["rolled_back_deposits"] += 1
        
        simulation = ChainSimulation(
            event=ChainEvent.BLOCK_ROLLBACK,
            success=True,
            message=f"充值回滚成功: tx={tx_hash[:10]}... amount={record.amount} block=#{record.rollback_height}",
            data={
                "tx_hash": tx_hash,
                "amount": record.amount,
                "original_block": record.block_height,
                "rollback_block": record.rollback_height,
                "balance_to_deduct": record.amount,  # 交易所需扣回的金额
            }
        )
        
        self._simulation_log.append(simulation)
        log.warning(f"[MockChain] 充值回滚: {simulation.message} ⚠️ 交易所需扣回 {record.amount}")
        return simulation
    
    def simulate_duplicate_deposit(self, tx_hash: str) -> ChainSimulation:
        """
        模拟同一 TxHash 重复充值请求
        
        场景：用户/攻击者重复提交同一笔充值请求
        测试点：交易所防重复入账机制是否生效
        
        Args:
            tx_hash: 已充值的交易哈希
        """
        if tx_hash not in self._deposits:
            return ChainSimulation(
                event=ChainEvent.DUPLICATE_TX,
                success=False,
                message=f"充值记录不存在: {tx_hash}"
            )
        
        record = self._deposits[tx_hash]
        
        if record.status == DepositStatus.ROLLED_BACK:
            return ChainSimulation(
                event=ChainEvent.DUPLICATE_TX,
                success=False,
                message=f"该交易已回滚，不是重复入账场景"
            )
        
        # 触发重复标记
        self._duplicate_tx_hashes.add(tx_hash)
        record.status = DepositStatus.DUPLICATE
        
        simulation = ChainSimulation(
            event=ChainEvent.DUPLICATE_TX,
            success=True,
            message=f"重复充值检测: tx={tx_hash[:10]}... 已标记为重复",
            data={
                "tx_hash": tx_hash,
                "amount": record.amount,
                "previous_status": DepositStatus.CONFIRMED.value,
                "should_block_credit": True,  # 交易所应拒绝此次入账
            }
        )
        
        self._simulation_log.append(simulation)
        log.warning(f"[MockChain] 重复充值: {simulation.message} ⚠️ 交易所应拒绝此次入账")
        return simulation
    
    def simulate_deposit_under_confirmation(
        self,
        tx_hash: str,
        current_confirmations: int = 2,
        required_confirmations: int = 10
    ) -> ChainSimulation:
        """
        模拟区块确认不足的充值
        
        场景：交易上链但确认数未达门槛
        测试点：确认数不足时不应入账
        
        Args:
            tx_hash: 交易哈希
            current_confirmations: 当前确认数
            required_confirmations: 交易所要求的确认数
        """
        is_insufficient = current_confirmations < required_confirmations
        
        simulation = ChainSimulation(
            event=ChainEvent.NETWORK_DELAY if is_insufficient else ChainEvent.BLOCK_ROLLBACK,
            success=True,
            message=f"确认数不足检测: tx={tx_hash[:10]}... confirmations={current_confirmations}/{required_confirmations}",
            data={
                "tx_hash": tx_hash,
                "current_confirmations": current_confirmations,
                "required_confirmations": required_confirmations,
                "should_block_credit": is_insufficient,
                "reason": "insufficient_confirmations" if is_insufficient else "credit_allowed",
            }
        )
        
        self._simulation_log.append(simulation)
        
        if is_insufficient:
            log.warning(f"[MockChain] 确认数不足: 不应入账 (需{required_confirmations}，当前{current_confirmations})")
        else:
            log.success(f"[MockChain] 确认数充足: 允许入账")
        
        return simulation
    
    # ==================== 提币模拟 ====================
    
    def register_withdraw(
        self,
        withdraw_id: str,
        amount: float,
        to_address: str,
        gas_price: float = 1.0
    ) -> WithdrawRecord:
        """
        注册一笔提币（模拟提币申请已提交）
        
        Args:
            withdraw_id: 提币申请ID
            amount: 提币金额
            to_address: 接收地址
            gas_price: Gas 价格（Gwei）
        """
        record = WithdrawRecord(
            withdraw_id=withdraw_id,
            amount=amount,
            to_address=to_address,
            status=WithdrawStatus.PENDING,
            gas_price=gas_price
        )
        self._withdraws[withdraw_id] = record
        log.info(f"[MockChain] 提币注册: id={withdraw_id} amount={amount}")
        return record
    
    def simulate_withdraw_broadcast(
        self,
        withdraw_id: str,
        tx_hash: str = None
    ) -> ChainSimulation:
        """
        模拟提币上链广播成功
        
        Args:
            withdraw_id: 提币申请ID
            tx_hash: 链上交易哈希
        """
        if withdraw_id not in self._withdraws:
            return ChainSimulation(
                event=ChainEvent.WITHDRAW_FAILED,
                success=False,
                message=f"提币记录不存在: {withdraw_id}"
            )
        
        record = self._withdraws[withdraw_id]
        record.status = WithdrawStatus.BROADCASTED
        record.tx_hash = tx_hash or f"0x{int(time.time()*1000):064x}"
        
        simulation = ChainSimulation(
            event=ChainEvent.WITHDRAW_FAILED,
            success=True,
            message=f"提币广播成功: id={withdraw_id} tx={record.tx_hash[:10]}...",
            data={
                "withdraw_id": withdraw_id,
                "tx_hash": record.tx_hash,
                "status": record.status.value,
            }
        )
        
        self._simulation_log.append(simulation)
        log.info(f"[MockChain] 提币广播: {simulation.message}")
        return simulation
    
    def simulate_withdraw_failure(
        self,
        withdraw_id: str,
        reason: str = "insufficient_gas"
    ) -> ChainSimulation:
        """
        模拟提币上链失败
        
        场景：余额已扣减但链上转账失败
        测试点：资金是否正确退回用户账户
        
        Args:
            withdraw_id: 提币申请ID
            reason: 失败原因（insufficient_gas / network_error / invalid_address）
        """
        if withdraw_id not in self._withdraws:
            return ChainSimulation(
                event=ChainEvent.WITHDRAW_FAILED,
                success=False,
                message=f"提币记录不存在: {withdraw_id}"
            )
        
        record = self._withdraws[withdraw_id]
        record.status = WithdrawStatus.FAILED
        record.failure_reason = reason
        self._chain_state["failed_withdraws"] += 1
        
        reason_map = {
            "insufficient_gas": "Gas 费不足，交易被拒绝",
            "network_error": "网络异常，节点不可达",
            "invalid_address": "目标地址格式非法",
            "timeout": "交易打包超时",
            "nonce_conflict": "Nonce 冲突，交易被拒绝",
        }
        
        reason_desc = reason_map.get(reason, reason)
        
        simulation = ChainSimulation(
            event=ChainEvent.WITHDRAW_FAILED,
            success=True,
            message=f"提币失败: id={withdraw_id} reason={reason_desc}",
            data={
                "withdraw_id": withdraw_id,
                "amount": record.amount,
                "failure_reason": reason,
                "failure_description": reason_desc,
                "should_refund": True,  # 交易所应退回扣减的资金
                "refund_amount": record.amount,
                "current_status": record.status.value,
            }
        )
        
        self._simulation_log.append(simulation)
        log.error(f"[MockChain] 提币失败: {simulation.message} ⚠️ 需退回 {record.amount}")
        return simulation
    
    def simulate_withdraw_rollback(self, withdraw_id: str) -> ChainSimulation:
        """
        模拟提币链上回滚（已广播的交易被回滚）
        
        Args:
            withdraw_id: 提币申请ID
        """
        if withdraw_id not in self._withdraws:
            return ChainSimulation(
                event=ChainEvent.WITHDRAW_FAILED,
                success=False,
                message=f"提币记录不存在: {withdraw_id}"
            )
        
        record = self._withdraws[withdraw_id]
        
        if record.status != WithdrawStatus.BROADCASTED:
            return ChainSimulation(
                event=ChainEvent.WITHDRAW_FAILED,
                success=False,
                message=f"当前状态 {record.status.value} 无法触发回滚"
            )
        
        record.status = WithdrawStatus.ROLLED_BACK
        
        simulation = ChainSimulation(
            event=ChainEvent.BLOCK_ROLLBACK,
            success=True,
            message=f"提币回滚: id={withdraw_id} 交易被回滚",
            data={
                "withdraw_id": withdraw_id,
                "amount": record.amount,
                "tx_hash": record.tx_hash,
                "should_refund": True,
                "refund_amount": record.amount,
            }
        )
        
        self._simulation_log.append(simulation)
        log.warning(f"[MockChain] 提币回滚: {simulation.message} ⚠️ 需退回 {record.amount}")
        return simulation
    
    # ==================== 查询方法 ====================
    
    def get_deposit_status(self, tx_hash: str) -> Optional[DepositRecord]:
        """查询充值记录状态"""
        return self._deposits.get(tx_hash)
    
    def get_withdraw_status(self, withdraw_id: str) -> Optional[WithdrawRecord]:
        """查询提币记录状态"""
        return self._withdraws.get(withdraw_id)
    
    def get_simulation_log(self) -> List[ChainSimulation]:
        """获取模拟日志"""
        return self._simulation_log.copy()
    
    def get_chain_state(self) -> Dict[str, Any]:
        """获取模拟链上状态快照"""
        return self._chain_state.copy()
    
    def get_all_deposits(self, status: DepositStatus = None) -> List[DepositRecord]:
        """获取所有充值记录（可按状态过滤）"""
        records = list(self._deposits.values())
        if status:
            records = [r for r in records if r.status == status]
        return records
    
    def get_all_withdraws(self, status: WithdrawStatus = None) -> List[WithdrawRecord]:
        """获取所有提币记录（可按状态过滤）"""
        records = list(self._withdraws.values())
        if status:
            records = [r for r in records if r.status == status]
        return records
    
    # ==================== 对账辅助 ====================
    
    def calculate_net_deposits(self) -> float:
        """
        计算净充值额（已确认 - 已回滚）
        
        用于验证：交易所内部余额 vs 链上实际净充值额
        """
        confirmed = sum(r.amount for r in self._deposits.values() 
                       if r.status == DepositStatus.CONFIRMED)
        rolled_back = sum(r.amount for r in self._deposits.values() 
                         if r.status == DepositStatus.ROLLED_BACK)
        return confirmed - rolled_back
    
    def calculate_net_withdraws(self) -> float:
        """
        计算净提币额（已完成 - 已失败/回滚）
        """
        confirmed = sum(r.amount for r in self._withdraws.values() 
                       if r.status == WithdrawStatus.CONFIRMED)
        failed = sum(r.amount for r in self._withdraws.values() 
                    if r.status in [WithdrawStatus.FAILED, WithdrawStatus.ROLLED_BACK])
        return confirmed - failed
    
    def verify_balance_consistency(self, internal_balance: float) -> Dict[str, Any]:
        """
        验证余额一致性
        
        Args:
            internal_balance: 交易所内部记录的用户余额
        
        Returns:
            校验结果字典
        """
        net_deposits = self.calculate_net_deposits()
        net_withdraws = self.calculate_net_withdraws()
        expected_balance = net_deposits - net_withdraws
        
        is_consistent = abs(internal_balance - expected_balance) < 1e-8
        
        result = {
            "internal_balance": internal_balance,
            "net_deposits": net_deposits,
            "net_withdraws": net_withdraws,
            "expected_balance": expected_balance,
            "is_consistent": is_consistent,
            "difference": abs(internal_balance - expected_balance),
        }
        
        if is_consistent:
            log.success(f"[MockChain] 余额一致性校验通过")
        else:
            log.error(f"[MockChain] 余额不一致！内部={internal_balance} ≠ 预期={expected_balance}，差额={result['difference']}")
        
        return result
    
    # ==================== 重置 ====================
    
    def reset(self):
        """重置所有模拟数据"""
        self._deposits.clear()
        self._withdraws.clear()
        self._duplicate_tx_hashes.clear()
        self._simulation_log.clear()
        self._block_height = 100000
        self._chain_state = {
            "total_deposits": 0,
            "total_withdraws": 0,
            "rolled_back_deposits": 0,
            "failed_withdraws": 0,
        }
        log.info("[MockChain] 模拟环境已重置")
    
    def reset_deposits(self):
        """仅重置充值记录"""
        self._deposits.clear()
        self._duplicate_tx_hashes.clear()
        self._chain_state["total_deposits"] = 0
        self._chain_state["rolled_back_deposits"] = 0
        log.info("[MockChain] 充值记录已重置")
    
    def reset_withdraws(self):
        """仅重置提币记录"""
        self._withdraws.clear()
        self._chain_state["total_withdraws"] = 0
        self._chain_state["failed_withdraws"] = 0
        log.info("[MockChain] 提币记录已重置")
