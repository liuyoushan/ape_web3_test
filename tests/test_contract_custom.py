"""
================================================================================
【模块概览】项目自定义自研合约 业务用例
对应用例编号：case_018 ~ case_025
测试范围：自研合约的权限控制、参数管理、业务逻辑等
================================================================================
"""

from ape import project


# ================================================================================
# case_018 管理员权限接口校验
# 测试目标：仅指定 owner/admin 可调用，非权限地址调用强制报错
# 测试类型：P0 - 权限测试
# ================================================================================
def test_custom_018_admin_permission_check(deployer, user1, user2):
    """
    管理员权限接口校验

    测试 MyERC20 基于角色的权限控制：
    - MINTER_ROLE：仅该角色可 mint
    - PAUSER_ROLE：仅该角色可 pause
    - ADMIN_ROLE：仅该角色可 grant/revoke
    - 普通用户调用以上接口 revert
    """
    token = deployer.deploy(project.MyERC20, "TestToken", "TT")

    MINTER_ROLE = token.MINTER_ROLE()
    PAUSER_ROLE = token.PAUSER_ROLE()
    ADMIN_ROLE = token.ADMIN_ROLE()

    print("\n[DEBUG] ========== 角色常量校验 ==========")
    print(f"  - deployer 是初始 ADMIN/MINTER/PAUSER: {deployer.address}")

    # ==================== 场景1：deployer 有所有角色，调用成功 ====================
    print("\n[DEBUG] ========== 场景1: 合法角色调用成功 ==========")

    token.mint(user1, int(1000 * 10**18), sender=deployer)
    balance_user1 = token.balanceOf(user1)
    print(f"  - deployer(有MINTER) mint 1000 成功: {balance_user1 / 1e18}")

    token.pause(sender=deployer)
    assert token.paused() == True
    print(f"  - deployer(有PAUSER) pause 成功: paused={token.paused()}")

    token.unpause(sender=deployer)
    assert token.paused() == False
    print(f"  - deployer unpause 成功: paused={token.paused()}")

    token.grantRole(MINTER_ROLE, user2, sender=deployer)
    assert token.roles(MINTER_ROLE, user2) == True
    print(f"  - deployer(有ADMIN) grantRole 给 user2 成功")

    # ==================== 场景2：普通用户 user1 无角色调用 revert ====================
    print("\n[DEBUG] ========== 场景2: 无角色用户调用 revert ==========")

    try:
        token.mint(user1, int(100 * 10**18), sender=user1)
        assert False, "应 revert"
    except Exception as e:
        assert "Missing required role" in str(e)
        print(f"  - user1(无MINTER) mint 拦截成功: {str(e)[:60]}...")

    try:
        token.pause(sender=user1)
        assert False, "应 revert"
    except Exception as e:
        assert "Missing required role" in str(e)
        print(f"  - user1(无PAUSER) pause 拦截成功: {str(e)[:60]}...")

    try:
        token.grantRole(MINTER_ROLE, user1, sender=user1)
        assert False, "应 revert"
    except Exception as e:
        assert "Missing required role" in str(e)
        print(f"  - user1(无ADMIN) grantRole 拦截成功: {str(e)[:60]}...")

    print("\n[DEBUG] ✓ 管理员权限校验全场景通过")


# ================================================================================
# case_019 自定义全局参数读写
# 测试目标：费率、开关、阈值等自定义变量，修改 + 读取双向断言
# 测试类型：P0 - 功能测试
# ================================================================================
def test_custom_019_global_parameter_rw(deployer):
    """
    自定义全局参数读写测试

    验证合约参数管理：
    - 参数可读可写
    - 修改后立即生效
    - 参数值与设置一致
    """
    raise NotImplementedError("用例待实现")


# ================================================================================
# case_020 项目独有业务接口
# 测试目标：定制化计算、资产分发、数据统计等独有函数逻辑校验
# 测试类型：P1 - 业务逻辑测试
# ================================================================================
def test_custom_020_custom_business_logic(deployer, user1):
    """
    项目独有业务接口测试

    验证自定义业务逻辑：
    - 特殊计算公式正确
    - 资产分发规则正确
    - 数据统计准确
    """
    raise NotImplementedError("用例待实现")


# ================================================================================
# case_021 合约暂停 / 恢复功能
# 测试目标：Pause 锁停核心业务、Unpause 恢复功能，状态隔离校验
# 测试类型：P0 - 状态测试
# ================================================================================
def test_custom_021_pause_unpause(deployer, user1):
    """
    合约暂停/恢复功能测试

    验证暂停机制：
    - pause 后核心业务无法调用
    - unpause 后业务恢复正常
    - 状态切换事件正确触发
    """
    raise NotImplementedError("用例待实现")


# ================================================================================
# case_022 黑白名单控制接口
# 测试目标：名单内地址特权、名单外地址功能限制 / 拦截校验
# 测试类型：P0 - 权限测试
# ================================================================================
def test_custom_022_blacklist_whitelist(deployer, user1):
    """
    黑白名单控制接口测试

    验证名单控制机制：
    - 白名单地址享受特权
    - 黑名单地址被限制
    - 名单更新权限正确
    """
    raise NotImplementedError("用例待实现")


# ================================================================================
# case_023 动态参数修改接口
# 测试目标：后台调整手续费、奖励比例、质押系数等参数生效校验
# 测试类型：P0 - 配置测试
# ================================================================================
def test_custom_023_dynamic_parameter_update(deployer):
    """
    动态参数修改接口测试

    验证参数动态调整：
    - 手续费率可调整
    - 奖励比例可修改
    - 修改后立即生效
    """
    raise NotImplementedError("用例待实现")


# ================================================================================
# case_024 外部合约依赖调用
# 测试目标：预言机、外部池、跨合约读取数据的返回值容错校验
# 测试类型：P1 - 集成测试
# ================================================================================
def test_custom_024_external_contract_call(deployer):
    """
    外部合约依赖调用测试

    验证外部依赖处理：
    - 预言机数据读取
    - 外部池数据查询
    - 异常情况容错处理
    """
    raise NotImplementedError("用例待实现")


# ================================================================================
# case_025 自定义业务异常拦截
# 测试目标：非法参数、不符合业务规则操作，校验定制化 revert 提示
# 测试类型：P0 - 异常测试
# ================================================================================
def test_custom_025_custom_error_revert(deployer, user1):
    """
    自定义业务异常拦截测试

    验证业务规则校验：
    - 非法参数触发 revert
    - 错误消息清晰可辨
    - 边界条件正确处理
    """
    raise NotImplementedError("用例待实现")
