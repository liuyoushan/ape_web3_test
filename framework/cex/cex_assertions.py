"""
==============================================================================
CEX 专用断言助手
==============================================================================
与合约断言（framework/core/assertions.py）分离，专注于 CEX 业务校验：
- 资金对账平衡
- 手续费计算
- 订单状态流转
- 余额变更一致性
- 风控拦截校验
"""

from typing import Dict, Any, Optional
from framework.core.logger import log


class CEXAssertions:
    """CEX 业务断言集合"""
    
    # ==================== 资金类断言 ====================
    
    @staticmethod
    def assert_balance_unchanged(response, field: str, original_balance: float, tolerance: float = 0.0):
        """
        断言余额未变更（操作被拦截时校验）
        
        Args:
            response: API 响应对象
            field: 余额字段名
            original_balance: 原始余额
            tolerance: 允许误差范围
        """
        data = response.json()
        actual = float(data.get(field, 0))
        assert abs(actual - original_balance) <= tolerance, \
            f"余额应未变更，但 {field} 从 {original_balance} 变为 {actual}"
        log.success(f"✅ 余额未变更断言通过: {field} = {actual}")
    
    @staticmethod
    def assert_balance_increased(response, field: str, expected_increase: float, original_balance: float, tolerance: float = 1e-8):
        """
        断言余额增加指定金额（充币入账等场景）
        
        Args:
            response: API 响应对象
            field: 余额字段名
            expected_increase: 预期增加额
            original_balance: 原始余额
            tolerance: 允许误差范围
        """
        data = response.json()
        actual = float(data.get(field, 0))
        expected = original_balance + expected_increase
        assert abs(actual - expected) <= tolerance, \
            f"余额应增加 {expected_increase}，但 {field} 从 {original_balance} 变为 {actual}（预期 {expected}）"
        log.success(f"✅ 余额增加断言通过: {field} +{expected_increase}")
    
    @staticmethod
    def assert_balance_decreased(response, field: str, expected_decrease: float, original_balance: float, tolerance: float = 1e-8):
        """
        断言余额减少指定金额（提币/扣费等场景）
        
        Args:
            response: API 响应对象
            field: 余额字段名
            expected_decrease: 预期减少额
            original_balance: 原始余额
            tolerance: 允许误差范围
        """
        data = response.json()
        actual = float(data.get(field, 0))
        expected = original_balance - expected_decrease
        assert abs(actual - expected) <= tolerance, \
            f"余额应减少 {expected_decrease}，但 {field} 从 {original_balance} 变为 {actual}（预期 {expected}）"
        log.success(f"✅ 余额减少断言通过: {field} -{expected_decrease}")
    
    @staticmethod
    def assert_reconciliation(intra_ledger: float, chain_balance: float, tolerance: float = 1e-8):
        """
        资金对账：内层流水总额 vs 外层链上持仓
        
        Args:
            intra_ledger: 交易所内部流水汇总额
            chain_balance: 链上钱包实际持仓
            tolerance: 允许误差范围
        """
        assert abs(intra_ledger - chain_balance) <= tolerance, \
            f"资金对账不平！内部流水 {intra_ledger} ≠ 链上持仓 {chain_balance}，差额 {abs(intra_ledger - chain_balance)}"
        log.success(f"✅ 资金对账通过: 内部流水 = 链上持仓 = {intra_ledger}")
    
    @staticmethod
    def assert_transfer_bilateral(send_account_balance: float, recv_account_balance: float,
                                   original_send: float, original_recv: float,
                                   transfer_amount: float, tolerance: float = 1e-8):
        """
        划转双边校验：发送方减少 = 接收方增加 = 划转金额
        
        Args:
            send_account_balance: 发送方账户新余额
            recv_account_balance: 接收方账户新余额
            original_send: 发送方原始余额
            original_recv: 接收方原始余额
            transfer_amount: 划转金额
            tolerance: 允许误差范围
        """
        send_decrease = original_send - send_account_balance
        recv_increase = recv_account_balance - original_recv
        
        assert abs(send_decrease - transfer_amount) <= tolerance, \
            f"发送方余额减少 {send_decrease} ≠ 划转金额 {transfer_amount}"
        assert abs(recv_increase - transfer_amount) <= tolerance, \
            f"接收方余额增加 {recv_increase} ≠ 划转金额 {transfer_amount}"
        log.success(f"✅ 划转双边校验通过: {transfer_amount}")
    
    # ==================== 订单类断言 ====================
    
    @staticmethod
    def assert_order_status(response, expected_status: str, order_id_field: str = "orderId"):
        """
        断言订单状态
        
        Args:
            response: API 响应对象
            expected_status: 预期状态（NEW/PARTIALLY_FILLED/FILLED/CANCELED/EXPIRED）
            order_id_field: 订单ID字段名
        """
        data = response.json()
        actual_status = data.get("status", "")
        actual_id = data.get(order_id_field, "N/A")
        
        assert actual_status == expected_status, \
            f"订单 {actual_id} 状态不匹配: 预期 {expected_status}, 实际 {actual_status}"
        log.success(f"✅ 订单状态断言通过: orderId={actual_id}, status={actual_status}")
    
    @staticmethod
    def assert_order_immutable(response, immutable_statuses: list = None):
        """
        断言订单状态不可逆（已成交/已撤单后不可变更）
        
        Args:
            response: API 响应对象
            immutable_statuses: 不可逆状态列表
        """
        if immutable_statuses is None:
            immutable_statuses = ["FILLED", "CANCELED", "EXPIRED", "REJECTED"]
        
        data = response.json()
        current_status = data.get("status", "")
        
        assert current_status not in immutable_statuses, \
            f"订单当前状态 {current_status} 为不可逆状态，不应接受状态变更"
        log.success(f"✅ 订单状态不可逆断言通过")
    
    @staticmethod
    def assert_order_cancelable(response, cancelable_statuses: list = None):
        """
        断言订单可撤单状态
        
        Args:
            response: API 响应对象
            cancelable_statuses: 可撤单状态列表
        """
        if cancelable_statuses is None:
            cancelable_statuses = ["NEW", "PARTIALLY_FILLED"]
        
        data = response.json()
        current_status = data.get("status", "")
        
        assert current_status in cancelable_statuses, \
            f"订单状态 {current_status} 不可撤单（可撤单状态: {cancelable_statuses}）"
        log.success(f"✅ 订单可撤断言通过: status={current_status}")
    
    # ==================== 手续费类断言 ====================
    
    @staticmethod
    def assert_fee_calculation(actual_fee: float, expected_fee: float, tolerance: float = 1e-8):
        """
        断言手续费计算正确
        
        Args:
            actual_fee: 实际扣费
            expected_fee: 预期手续费
            tolerance: 允许误差范围
        """
        assert abs(actual_fee - expected_fee) <= tolerance, \
            f"手续费不匹配: 实际 {actual_fee} ≠ 预期 {expected_fee}"
        log.success(f"✅ 手续费断言通过: fee={actual_fee}")
    
    @staticmethod
    def assert_maker_fee(taker_fee: float, maker_fee: float):
        """
        断言 Maker 费率 < Taker 费率（Maker 应享受更低费率）
        
        Args:
            taker_fee: Taker 费率
            maker_fee: Maker 费率
        """
        assert maker_fee < taker_fee, \
            f"Maker 费率 ({maker_fee}) 应低于 Taker 费率 ({taker_fee})"
        log.success(f"✅ Maker/Taker 费率关系断言通过: maker={maker_fee} < taker={taker_fee}")
    
    # ==================== 风控类断言 ====================
    
    @staticmethod
    def assert_risk_blocked(response, expected_error_code: str = None, expected_error_msg: str = None):
        """
        断言风控拦截生效（操作被阻止）
        
        Args:
            response: API 响应对象
            expected_error_code: 预期错误码
            expected_error_msg: 预期错误信息
        """
        data = response.json()
        
        if expected_error_code:
            actual_code = str(data.get("code", data.get("error_code", "")))
            assert actual_code == expected_error_code, \
                f"风控拦截码不匹配: 预期 {expected_error_code}, 实际 {actual_code}"
        
        if expected_error_msg:
            actual_msg = str(data.get("msg", data.get("message", "")))
            assert expected_error_msg in actual_msg, \
                f"风控拦截信息不匹配: 预期包含 '{expected_error_msg}', 实际 '{actual_msg}'"
        
        log.success(f"✅ 风控拦截断言通过")
    
    @staticmethod
    def assert_kyc_level_restricted(kyc_level: int, required_level: int, operation: str):
        """
        断言 KYC 等级限制生效
        
        Args:
            kyc_level: 用户当前 KYC 等级
            required_level: 操作要求的最低等级
            operation: 操作描述
        """
        assert kyc_level >= required_level, \
            f"KYC 等级不足: 当前 L{kyc_level}，{operation} 要求 L{required_level}+"
        log.success(f"✅ KYC 等级断言通过: L{kyc_level} >= L{required_level}")
    
    # ==================== 通用业务断言 ====================
    
    @staticmethod
    def assert_response_code(response, expected_code: int = 200):
        """
        断言响应码正确
        
        Args:
            response: API 响应对象
            expected_code: 预期 HTTP 状态码
        """
        assert response.status_code == expected_code, \
            f"响应码不匹配: 预期 {expected_code}, 实际 {response.status_code}"
        log.success(f"✅ 响应码断言通过: {expected_code}")
    
    @staticmethod
    def assert_not_duplicate(response, existing_ids: list, id_field: str = "orderId"):
        """
        断言不重复创建（幂等校验）
        
        Args:
            response: API 响应对象
            existing_ids: 已存在的 ID 列表
            id_field: ID 字段名
        """
        data = response.json()
        new_id = data.get(id_field)
        
        if new_id is not None:
            assert new_id not in existing_ids, \
                f"检测到重复创建: {id_field}={new_id} 已存在于 {existing_ids}"
            log.success(f"✅ 幂等断言通过: {id_field}={new_id} 未重复")
        else:
            log.warning(f"响应中未找到 {id_field}，跳过幂等校验")


# 全局实例
cex_assertions = CEXAssertions()
