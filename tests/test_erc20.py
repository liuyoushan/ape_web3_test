"""
==============================================================================
ERC20 同质化代币 基础标准用例
==============================================================================
"""

import pytest
from ape.exceptions import ContractLogicError, VirtualMachineError
from tests.helpers.assertions import (
    assert_token_metadata,
    assert_balance,
    assert_transfer_event,
    assert_address_format,
    assert_approval_event
)
from tests.helpers.formatters import format_ether
from tests.fixtures.token_fixture import mint_token, parse_ether


# ==============================================================================
# case_001 代币基础信息校验
# 测试目标：MyERC20 合约的元数据（名称、符号、小数位数、初始总发行量）
# 测试类型：P0 - 功能测试 / 正向测试
# ==============================================================================
def test_erc20_001_metadata_verification(token, erc20_test_data):
    """
    代币基础信息校验测试
    """
    data = erc20_test_data["common"]

    assert_token_metadata(
        token=token,
        expected_name=data["token_name"],
        expected_symbol=data["token_symbol"],
        expected_decimals=data["expected_decimals"],
        expected_supply=data["expected_initial_supply"]
    )

    assert_address_format(token.address)


# ==============================================================================
# case_002 正常转账功能测试
# 测试目标：普通地址间转账，校验余额变更、链上事件、交易状态
# 测试类型：P0 - 功能测试 / 正向测试
# ==============================================================================
def test_erc20_002_normal_transfer(token, deployer, user1, erc20_test_data):
    """
    正常转账功能测试
    """
    data = erc20_test_data["case_002_transfer"]
    transfer_amount = parse_ether(data["transfer_amount"])

    token = mint_token(token, deployer, deployer, data["mint_amount"])

    balance_deployer_before = token.balanceOf(deployer)
    balance_user1_before = token.balanceOf(user1)
    total_supply_before = token.totalSupply()

    print("[DEBUG] 转账前余额:")
    print(f"  - deployer 余额: {format_ether(balance_deployer_before)}")
    print(f"  - user1 余额: {format_ether(balance_user1_before)}")
    print(f"  - totalSupply: {format_ether(total_supply_before)}")

    receipt = token.transfer(
        user1,
        transfer_amount,
        sender=deployer
    )

    print(f"[DEBUG] 转账后余额:")
    print(f"  - deployer 余额: {format_ether(token.balanceOf(deployer))}")
    print(f"  - user1 余额: {format_ether(token.balanceOf(user1))}")
    print(f"  - totalSupply: {format_ether(token.totalSupply())}")

    assert_balance(token, deployer, balance_deployer_before - transfer_amount)
    assert_balance(token, user1, balance_user1_before + transfer_amount)
    assert token.totalSupply() == total_supply_before
    
    assert_transfer_event(receipt, deployer.address, user1.address, transfer_amount)


def test_erc20_002_normal_transfer_002(token, deployer, user1):
    """
    基于 test_erc20_002_normal_transfer 延伸一下，反向转账

    """
    transfer_amount_1 = parse_ether("200 ether")
    transfer_amount_2 = parse_ether("100 ether")

    token = mint_token(token, deployer, deployer, "1000 ether")

    print('kaishi')

    balance_deployer_before = token.balanceOf(deployer)
    balance_user1_before = token.balanceOf(user1)
    total_supply_before = token.totalSupply()

    print("[DEBUG] 转账前余额:")
    print(f"  - deployer 余额: {format_ether(balance_deployer_before)}")
    print(f"  - user1 余额: {format_ether(balance_user1_before)}")
    print(f"  - totalSupply: {format_ether(total_supply_before)}")

    receipt = token.transfer(
        user1,
        transfer_amount_1,
        sender=deployer
    )
    receipt_1 = token.transfer(
        deployer,
        transfer_amount_2,
        sender=user1
    )
    print(f"[DEBUG] 转账后余额:")
    print(f"  - deployer 余额: {format_ether(token.balanceOf(deployer))}")
    print(f"  - user1 余额: {format_ether(token.balanceOf(user1))}")
    print(f"  - totalSupply: {format_ether(token.totalSupply())}")

    assert_balance(token, deployer, balance_deployer_before - transfer_amount_2)
    assert_balance(token, user1, balance_user1_before + transfer_amount_2)
    assert token.totalSupply() == total_supply_before


# ==============================================================================
# case_003 余额不足异常转账测试
# 测试目标：发起超额转账，校验合约 revert、数据不回写
# 测试类型：P0 - 异常测试 / 负向测试
# ==============================================================================
def test_erc20_003_insufficient_balance_transfer(token, deployer, user1):
    """
    余额不足异常转账测试

    验证当转账金额超过余额时：
    - 交易 revert
    - 转账双方余额不变
    - totalSupply 不变
    """
    token = mint_token(token, deployer, deployer, "1000 ether")
    transfer_amount = parse_ether("2000 ether")

    balance_deployer_before = token.balanceOf(deployer)
    balance_user1_before = token.balanceOf(user1)
    total_supply_before = token.totalSupply()

    print("[DEBUG] 转账前余额:")
    print(f"  - deployer 余额: {format_ether(balance_deployer_before)}")
    print(f"  - user1 余额: {format_ether(balance_user1_before)}")
    print(f"  - totalSupply: {format_ether(total_supply_before)}")

    with pytest.raises((ContractLogicError, VirtualMachineError)):
        token.transfer(
            user1,
            transfer_amount,
            sender=deployer
        )

    balance_deployer_after = token.balanceOf(deployer)
    balance_user1_after = token.balanceOf(user1)
    total_supply_after = token.totalSupply()

    print("[DEBUG] 转账失败后余额（应保持不变）:")
    print(f"  - deployer 余额: {format_ether(balance_deployer_after)}")
    print(f"  - user1 余额: {format_ether(balance_user1_after)}")
    print(f"  - totalSupply: {format_ether(total_supply_after)}")

    assert balance_deployer_after == balance_deployer_before
    assert balance_user1_after == balance_user1_before
    assert total_supply_after == total_supply_before


# ==============================================================================
# case_004 Approve 授权基础测试
# 测试目标：对第三方地址/合约授权，校验授权额度存储值
# 测试类型：P0 - 功能测试 / 正向测试
# ==============================================================================
def test_erc20_004_approve_authorization(token, deployer, user1, erc20_test_data):
    """
    Approve 授权基础测试
    """
    data = erc20_test_data["case_004_approve"]
    approve_amount = parse_ether(data["approve_amount"])
    
    allowance_before = token.allowance(deployer, user1)
    print("[DEBUG] 授权前额度:")
    print(f"  - deployer -> user1 额度: {format_ether(allowance_before)}")
    
    receipt = token.approve(user1, approve_amount, sender=deployer)
    
    allowance_after = token.allowance(deployer, user1)
    print("[DEBUG] 授权后额度:")
    print(f"  - deployer -> user1 额度: {format_ether(allowance_after)}")
    
    assert allowance_before == 0, "初始授权额度应该为0"
    assert allowance_after == approve_amount, "授权额度不匹配"
    
    assert_approval_event(receipt, deployer.address, user1.address, approve_amount)


# ==============================================================================
# case_005 TransferFrom 代付转账测试
# 测试目标：授权后第三方扣币划转，校验余额、授权额度扣减
# 测试类型：P0 - 功能测试 / 正向测试
# ==============================================================================
def test_erc20_005_transfer_from(token, deployer, user1, user2, erc20_test_data):
    """
    TransferFrom 代付转账测试
    
    测试流程：
    1. deployer 铸造代币
    2. deployer 授权 user1 可以花费代币
    3. user1 调用 transferFrom 从 deployer 转账给 user2
    4. 验证余额变化和授权额度扣减
    """
    data = erc20_test_data["case_005_transfer_from"]
    mint_amount = parse_ether(data["mint_amount"])
    approve_amount = parse_ether(data["approve_amount"])
    transfer_amount = parse_ether(data["transfer_amount"])
    
    token = mint_token(token, deployer, deployer, data["mint_amount"])
    
    allowance_before = token.allowance(deployer, user1)
    balance_deployer_before = token.balanceOf(deployer)
    balance_user1_before = token.balanceOf(user1)
    balance_user2_before = token.balanceOf(user2)
    
    print("[DEBUG] 初始状态:")
    print(f"  - deployer 余额: {format_ether(balance_deployer_before)}")
    print(f"  - user1 余额: {format_ether(balance_user1_before)}")
    print(f"  - user2 余额: {format_ether(balance_user2_before)}")
    print(f"  - deployer -> user1 授权额度: {format_ether(allowance_before)}")
    
    token.approve(user1, approve_amount, sender=deployer)
    
    allowance_after_approve = token.allowance(deployer, user1)
    print("[DEBUG] 授权后:")
    print(f"  - deployer -> user1 授权额度: {format_ether(allowance_after_approve)}")
    
    receipt = token.transferFrom(
        deployer,
        user2,
        transfer_amount,
        sender=user1
    )
    
    allowance_after_transfer_from = token.allowance(deployer, user1)
    balance_deployer_after = token.balanceOf(deployer)
    balance_user2_after = token.balanceOf(user2)
    
    print("[DEBUG] transferFrom 转账后:")
    print(f"  - deployer 余额: {format_ether(balance_deployer_after)}")
    print(f"  - user2 余额: {format_ether(balance_user2_after)}")
    print(f"  - deployer -> user1 剩余授权额度: {format_ether(allowance_after_transfer_from)}")
    
    assert allowance_after_transfer_from == approve_amount - transfer_amount, "transferFrom后授权额度扣减不正确"
    
    additional_transfer_amount = parse_ether("50 ether")
    receipt_2 = token.transferFrom(
        deployer,
        user1,
        additional_transfer_amount,
        sender=user1
    )
    
    allowance_after_all = token.allowance(deployer, user1)
    balance_user1_final = token.balanceOf(user1)
    
    print("[DEBUG] 全部转账完成后:")
    print(f"  - user1 最终余额: {format_ether(balance_user1_final)}")
    print(f"  - deployer -> user1 最终授权额度: {format_ether(allowance_after_all)}")
    
    assert allowance_after_all == approve_amount - transfer_amount - additional_transfer_amount, "授权额度应剩余50 ether"
    assert balance_user1_final == balance_user1_before + additional_transfer_amount, "user1最终余额不正确"
    
    assert_transfer_event(receipt, deployer.address, user2.address, transfer_amount)
    assert_transfer_event(receipt_2, deployer.address, user1.address, additional_transfer_amount)
    
    excess_amount = parse_ether("100 ether")
    balance_deployer_before_excess = token.balanceOf(deployer)
    balance_user2_before_excess = token.balanceOf(user2)
    allowance_before_excess = token.allowance(deployer, user1)
    
    with pytest.raises((ContractLogicError, VirtualMachineError)):
        token.transferFrom(
            deployer,
            user2,
            excess_amount,
            sender=user1
        )
    
    balance_deployer_after_excess = token.balanceOf(deployer)
    balance_user2_after_excess = token.balanceOf(user2)
    allowance_after_excess = token.allowance(deployer, user1)
    
    print("[DEBUG] 超出授权额度转账失败后:")
    print(f"  - deployer 余额: {format_ether(balance_deployer_after_excess)}")
    print(f"  - user2 余额: {format_ether(balance_user2_after_excess)}")
    print(f"  - deployer -> user1 授权额度: {format_ether(allowance_after_excess)}")
    
    assert balance_deployer_after_excess == balance_deployer_before_excess, "deployer余额不应变化"
    assert balance_user2_after_excess == balance_user2_before_excess, "user2余额不应变化"
    assert allowance_after_excess == allowance_before_excess, "授权额度不应变化"


# ==============================================================================
# case_006 管理员铸币 Mint 测试
# 测试目标：权限账户增发代币，校验总量、目标地址余额
# 测试类型：P0 - 功能测试 / 正向测试
# ==============================================================================
def test_erc20_006_mint_tokens(token, deployer, user1, erc20_test_data):
    """
    管理员铸币 Mint 测试
    
    测试流程：
    1. 查询铸币前状态
    2. 调用 mint 给 user1 铸造代币（owner 操作）
    3. 验证余额和总量变化
    4. 验证 Transfer 事件
    5. 验证非 owner 不能铸币
    """
    data = erc20_test_data["case_006_mint"]
    mint_amount = parse_ether(data["mint_amount"])
    
    assert token.owner() == deployer.address, "deployer 应该是合约所有者"
    
    balance_user1_before = token.balanceOf(user1)
    total_supply_before = token.totalSupply()
    
    print("[DEBUG] 铸币前状态:")
    print(f"  - user1 余额: {format_ether(balance_user1_before)}")
    print(f"  - totalSupply: {format_ether(total_supply_before)}")
    
    receipt = token.mint(user1, mint_amount, sender=deployer)
    
    balance_user1_after = token.balanceOf(user1)
    total_supply_after = token.totalSupply()
    
    print("[DEBUG] 铸币后状态:")
    print(f"  - user1 余额: {format_ether(balance_user1_after)}")
    print(f"  - totalSupply: {format_ether(total_supply_after)}")
    
    assert balance_user1_after == balance_user1_before + mint_amount, "user1余额应增加"
    assert total_supply_after == total_supply_before + mint_amount, "总量应增加"
    
    assert_transfer_event(receipt, "0x0000000000000000000000000000000000000000", user1.address, mint_amount)
    
    balance_before_unauthorized = token.balanceOf(user1)
    total_supply_before_unauthorized = token.totalSupply()
    
    print("[DEBUG] 测试非授权用户铸币...")
    
    with pytest.raises((ContractLogicError, VirtualMachineError)):
        token.mint(user1, mint_amount, sender=user1)
    
    balance_after_unauthorized = token.balanceOf(user1)
    total_supply_after_unauthorized = token.totalSupply()
    
    print("[DEBUG] 非授权用户尝试铸币失败后:")
    print(f"  - user1 余额: {format_ether(balance_after_unauthorized)}")
    print(f"  - totalSupply: {format_ether(total_supply_after_unauthorized)}")
    
    assert balance_after_unauthorized == balance_before_unauthorized, "非授权铸币不应改变余额"
    assert total_supply_after_unauthorized == total_supply_before_unauthorized, "非授权铸币不应改变总量"


# ==============================================================================
# case_007 代币销毁 Burn 测试
# 测试目标：用户自主销毁、授权销毁，校验通缩总量与余额
# 测试类型：P0 - 功能测试 / 正向测试
# ==============================================================================
def test_erc20_007_burn_tokens(token, deployer, user1, user2, erc20_test_data):
    """
    代币销毁 Burn 测试
    
    测试流程：
    1. 用户自主销毁（burn）：用户销毁自己的代币
    2. 授权销毁（burnFrom）：第三方销毁授权额度内的代币
    3. 验证余额减少、总量通缩
    4. 验证 Transfer 事件（to 为 address(0)）
    5. 验证余额不足时销毁失败
    6. 验证授权不足时 burnFrom 失败
    """
    data = erc20_test_data["case_007_burn"]
    mint_amount = parse_ether(data["mint_amount"])
    burn_amount = parse_ether(data["burn_amount"])
    
    token = mint_token(token, deployer, user1, data["mint_amount"]) # owner账户给user1账户授权mint了1000代币
    
    balance_user1_before = token.balanceOf(user1)
    total_supply_before = token.totalSupply()
    
    print("[DEBUG] 销毁前状态:")
    print(f"  - user1 余额: {format_ether(balance_user1_before)}")
    print(f"  - totalSupply: {format_ether(total_supply_before)}")
    
    receipt = token.burn(burn_amount, sender=user1) # 调用burn函数注销200代币
    
    balance_user1_after = token.balanceOf(user1)
    total_supply_after = token.totalSupply()
    
    print("[DEBUG] 销毁后状态:")
    print(f"  - user1 余额: {format_ether(balance_user1_after)}")
    print(f"  - totalSupply: {format_ether(total_supply_after)}")
    
    assert balance_user1_after == balance_user1_before - burn_amount, "user1余额应减少"
    assert total_supply_after == total_supply_before - burn_amount, "总量应减少"
    
    assert_transfer_event(receipt, user1.address, "0x0000000000000000000000000000000000000000", burn_amount)
    
    token = mint_token(token, deployer, user2, data["mint_amount"]) # 给user2 mint了1000
    approve_amount = parse_ether(data["approve_amount"])
    burn_from_amount = parse_ether(data["burn_from_amount"])
    
    token.approve(user1, approve_amount, sender=user2)  # 授权给user2，额度300
    
    balance_user2_before = token.balanceOf(user2)
    allowance_before = token.allowance(user2, user1)
    
    print("[DEBUG] burnFrom 前状态:")
    print(f"  - user2 余额: {format_ether(balance_user2_before)}")
    print(f"  - user2 -> user1 授权额度: {format_ether(allowance_before)}")
    
    receipt_2 = token.burnFrom(user2, burn_from_amount, sender=user1)   # user2注销100
    
    balance_user2_after = token.balanceOf(user2)
    allowance_after = token.allowance(user2, user1)
    total_supply_final = token.totalSupply()
    
    print("[DEBUG] burnFrom 后状态:")
    print(f"  - user2 余额: {format_ether(balance_user2_after)}")   # 注销后余额900
    print(f"  - user2 -> user1 剩余授权额度: {format_ether(allowance_after)}")  # 剩余额度200
    print(f"  - totalSupply: {format_ether(total_supply_final)}")  # 给不同账户mint共2000，burn共300，mint总发行量=1700
    
    assert balance_user2_after == balance_user2_before - burn_from_amount, "user2余额应减少"
    assert allowance_after == approve_amount - burn_from_amount, "授权额度应减少"
    assert_transfer_event(receipt_2, user2.address, "0x0000000000000000000000000000000000000000", burn_from_amount)
    
    excess_burn_amount = parse_ether(data["excess_burn_amount"])
    balance_before_excess = token.balanceOf(user1)
    
    with pytest.raises((ContractLogicError, VirtualMachineError)):  # 只剩余900，注销1000此时会失败
        token.burn(excess_burn_amount, sender=user1)
    
    balance_after_excess = token.balanceOf(user1)
    assert balance_after_excess == balance_before_excess, "余额不足时销毁不应改变余额"
    print("[DEBUG] 余额不足时销毁失败（正确）")


# ==============================================================================
# case_008 RBAC 多角色权限测试
# 测试目标：Minter/Pauser/Admin 角色分离，权限分配与校验
# 测试类型：P1 - 进阶测试 / 权限测试
# ==============================================================================
def test_erc20_008_rbac_role_control(token, deployer, user1, user2, user3):
    """
    RBAC 多角色权限控制测试
    
    测试流程：
    1. 验证 deployer 初始拥有所有角色
    2. deployer 正常行使 Minter 和 Pauser 权限
    3. deployer 授权 user1 为 Minter
    4. deployer 授权 user2 为 Pauser
    5. 验证各角色权限边界：
       - Minter 仅能铸币，不能暂停
       - Pauser 仅能暂停，不能铸币
       - 未授权用户既不能铸币也不能暂停
    6. 撤销角色后权限失效
    """
    minter_role = token.MINTER_ROLE()
    pauser_role = token.PAUSER_ROLE()
    admin_role = token.ADMIN_ROLE()
    
    print("[DEBUG] ========== 第一步：初始角色检查 ==========")
    print(f"  - deployer 有 ADMIN_ROLE: {token.hasRole(admin_role, deployer)}")
    print(f"  - deployer 有 MINTER_ROLE: {token.hasRole(minter_role, deployer)}")
    print(f"  - deployer 有 PAUSER_ROLE: {token.hasRole(pauser_role, deployer)}")
    
    assert token.hasRole(admin_role, deployer), "deployer 应拥有 ADMIN_ROLE"
    assert token.hasRole(minter_role, deployer), "deployer 应拥有 MINTER_ROLE"
    assert token.hasRole(pauser_role, deployer), "deployer 应拥有 PAUSER_ROLE"
    
    print("[DEBUG] ========== 第二步：deployer 正常行使 Minter 权限 ==========")
    mint_amount = parse_ether("500 ether")
    balance_before = token.balanceOf(deployer)
    total_supply_before = token.totalSupply()
    
    receipt = token.mint(deployer, mint_amount, sender=deployer)
    assert token.balanceOf(deployer) == balance_before + mint_amount, "deployer 铸币后余额应增加"
    assert token.totalSupply() == total_supply_before + mint_amount, "总量应增加"
    assert_transfer_event(receipt, "0x0000000000000000000000000000000000000000", deployer.address, mint_amount)
    print(f"  - deployer 成功铸造 {format_ether(mint_amount)}")
    
    print("[DEBUG] ========== 第三步：deployer 正常行使 Pauser 权限 ==========")
    assert token.paused() == False, "合约初始状态应为未暂停"
    
    token.pause(sender=deployer)
    assert token.paused() == True, "deployer 暂停后合约应为暂停状态"
    print("  - deployer 成功暂停合约")
    
    token.unpause(sender=deployer)
    assert token.paused() == False, "deployer 恢复后合约应为未暂停状态"
    print("  - deployer 成功恢复合约")
    
    print("[DEBUG] ========== 第四步：授权 user1 为 Minter，user2 为 Pauser ==========")
    token.grantRole(minter_role, user1, sender=deployer)
    token.grantRole(pauser_role, user2, sender=deployer)
    
    print(f"  - user1 有 MINTER_ROLE: {token.hasRole(minter_role, user1)}")
    print(f"  - user2 有 PAUSER_ROLE: {token.hasRole(pauser_role, user2)}")
    
    assert token.hasRole(minter_role, user1), "user1 应拥有 MINTER_ROLE"
    assert token.hasRole(pauser_role, user2), "user2 应拥有 PAUSER_ROLE"
    
    print("[DEBUG] ========== 第五步：user1 (Minter) 正常铸币 ==========")
    user1_mint_amount = parse_ether("100 ether")
    balance_user1_before = token.balanceOf(user1)
    
    receipt = token.mint(user1, user1_mint_amount, sender=user1)
    assert token.balanceOf(user1) == balance_user1_before + user1_mint_amount, "user1 铸币后余额应增加"
    assert_transfer_event(receipt, "0x0000000000000000000000000000000000000000", user1.address, user1_mint_amount)
    print(f"  - user1 (Minter) 成功铸造 {format_ether(user1_mint_amount)}")
    
    print("[DEBUG] ========== 第六步：user1 (Minter) 尝试暂停（应失败） ==========")
    with pytest.raises((ContractLogicError, VirtualMachineError)):
        token.pause(sender=user1)
    print("  - user1 (Minter) 尝试暂停失败（正确，权限分离）")
    
    print("[DEBUG] ========== 第七步：user2 (Pauser) 正常暂停和恢复 ==========")
    assert token.paused() == False, "合约应为未暂停状态"
    
    token.pause(sender=user2)
    assert token.paused() == True, "user2 暂停后合约应为暂停状态"
    print("  - user2 (Pauser) 成功暂停合约")
    
    token.unpause(sender=user2)
    assert token.paused() == False, "user2 恢复后合约应为未暂停状态"
    print("  - user2 (Pauser) 成功恢复合约")
    
    print("[DEBUG] ========== 第八步：user2 (Pauser) 尝试铸币（应失败） ==========")
    with pytest.raises((ContractLogicError, VirtualMachineError)):
        token.mint(user2, mint_amount, sender=user2)
    print("  - user2 (Pauser) 尝试铸币失败（正确，权限分离）")
    
    print("[DEBUG] ========== 第九步：user3 (未授权) 尝试所有操作（应失败） ==========")
    with pytest.raises((ContractLogicError, VirtualMachineError)):
        token.mint(user3, mint_amount, sender=user3)
    print("  - user3 尝试铸币失败（正确）")
    
    with pytest.raises((ContractLogicError, VirtualMachineError)):
        token.pause(sender=user3)
    print("  - user3 尝试暂停失败（正确）")
    
    print("[DEBUG] ========== 第十步：撤销角色后权限失效 ==========")
    token.revokeRole(minter_role, user1, sender=deployer)
    assert not token.hasRole(minter_role, user1), "user1 应失去 MINTER_ROLE"
    print("  - 已撤销 user1 的 MINTER_ROLE")
    
    with pytest.raises((ContractLogicError, VirtualMachineError)):
        token.mint(user1, mint_amount, sender=user1)
    print("  - 角色撤销后 user1 无法铸币（正确）")


# ==============================================================================
# case_009 角色权限正常流程测试
# 测试目标：Minter 角色铸币、Pauser 角色暂停/恢复的完整正常流程
# 测试类型：P0 - 功能测试 / 正向测试
# ==============================================================================
def test_erc20_009_role_normal_operations(token, deployer, user1, user2):
    """
    角色权限正常流程测试
    
    测试场景：
    1. deployer 授权 user1 为 Minter（铸币角色）
    2. deployer 授权 user2 为 Pauser（暂停角色）
    3. user1 使用 Minter 权限铸币
    4. user2 使用 Pauser 权限暂停合约
    5. user2 使用 Pauser 权限恢复合约
    6. user1 继续铸币（合约恢复后正常工作）
    """
    minter_role = token.MINTER_ROLE()
    pauser_role = token.PAUSER_ROLE()
    
    print("[DEBUG] ========== 第一步：授权角色 ==========")
    token.grantRole(minter_role, user1, sender=deployer)
    token.grantRole(pauser_role, user2, sender=deployer)
    
    assert token.hasRole(minter_role, user1), "user1 应拥有 MINTER_ROLE"
    assert token.hasRole(pauser_role, user2), "user2 应拥有 PAUSER_ROLE"
    
    print(f"  - user1 已获得 MINTER_ROLE")
    print(f"  - user2 已获得 PAUSER_ROLE")
    
    print("[DEBUG] ========== 第二步：user1 (Minter) 铸币 ==========")
    mint_amount = parse_ether("200 ether")
    balance_before = token.balanceOf(user1)
    total_supply_before = token.totalSupply()
    
    receipt = token.mint(user1, mint_amount, sender=user1)
    
    assert token.balanceOf(user1) == balance_before + mint_amount, "user1 余额应增加"
    assert token.totalSupply() == total_supply_before + mint_amount, "总量应增加"
    assert_transfer_event(receipt, "0x0000000000000000000000000000000000000000", user1.address, mint_amount)
    
    print(f"  - user1 成功铸造 {format_ether(mint_amount)}")
    print(f"  - user1 当前余额: {format_ether(token.balanceOf(user1))}")
    print(f"  - 当前总量: {format_ether(token.totalSupply())}")
    
    print("[DEBUG] ========== 第三步：user2 (Pauser) 暂停合约 ==========")
    assert token.paused() == False, "合约初始状态应为未暂停"
    
    token.pause(sender=user2)
    
    assert token.paused() == True, "合约应被暂停"
    print("  - user2 成功暂停合约")
    
    print("[DEBUG] ========== 第四步：暂停期间无法铸币 ==========")
    with pytest.raises((ContractLogicError, VirtualMachineError)):
        token.mint(user1, mint_amount, sender=user1)
    print("  - 暂停期间铸币失败（预期行为）")
    
    print("[DEBUG] ========== 第五步：user2 (Pauser) 恢复合约 ==========")
    token.unpause(sender=user2)
    
    assert token.paused() == False, "合约应恢复为未暂停"
    print("  - user2 成功恢复合约")
    
    print("[DEBUG] ========== 第六步：恢复后 user1 继续铸币 ==========")
    balance_before_second = token.balanceOf(user1)
    
    receipt = token.mint(user1, mint_amount, sender=user1)
    
    assert token.balanceOf(user1) == balance_before_second + mint_amount, "user1 余额应继续增加"
    assert_transfer_event(receipt, "0x0000000000000000000000000000000000000000", user1.address, mint_amount)
    
    print(f"  - user1 再次成功铸造 {format_ether(mint_amount)}")
    print(f"  - user1 最终余额: {format_ether(token.balanceOf(user1))}")
    print(f"  - 最终总量: {format_ether(token.totalSupply())}")


# ==============================================================================
# case_010 权限升级机制测试
# 测试目标：从 Ownable 迁移到 RBAC，原权限平滑过渡
# 测试类型：P1 - 进阶测试 / 权限测试
# ==============================================================================
def test_erc20_010_permission_upgrade(token, deployer, user1):
    """
    权限体系平滑升级测试
    
    测试流程：
    1. 验证初始状态：deployer 既是 owner 又拥有所有 RBAC 角色
    2. 模拟从 Ownable 到 RBAC 的迁移：
       - 撤销 deployer 的 MINTER_ROLE
       - 验证 deployer（作为 owner）不再能铸币
    3. 授权 user1 为新的 Minter
    4. 验证 user1 可以铸币
    5. 验证权限体系升级后业务正常
    """
    minter_role = token.MINTER_ROLE()
    
    print("[DEBUG] 初始状态:")
    print(f"  - deployer 是 owner: {token.owner() == deployer.address}")
    print(f"  - deployer 有 MINTER_ROLE: {token.hasRole(minter_role, deployer)}")
    
    assert token.owner() == deployer.address, "deployer 应是 owner"
    assert token.hasRole(minter_role, deployer), "deployer 应拥有 MINTER_ROLE"
    
    mint_amount = parse_ether("100 ether")
    token.mint(deployer, mint_amount, sender=deployer)
    assert token.balanceOf(deployer) == mint_amount, "deployer 初始铸币成功"
    
    token.revokeRole(minter_role, deployer, sender=deployer)
    print("[DEBUG] 撤销 deployer 的 MINTER_ROLE")
    assert not token.hasRole(minter_role, deployer), "deployer 应失去 MINTER_ROLE"
    
    with pytest.raises((ContractLogicError, VirtualMachineError)):
        token.mint(deployer, mint_amount, sender=deployer)
    print("[DEBUG] deployer 不再能铸币（即使是 owner）")
    
    token.grantRole(minter_role, user1, sender=deployer)
    print("[DEBUG] 授权 user1 为新的 Minter")
    
    token.mint(user1, mint_amount, sender=user1)
    assert token.balanceOf(user1) == mint_amount, "user1 作为新 Minter 可以铸币"
    print("[DEBUG] 权限升级完成，新 Minter 正常工作")
