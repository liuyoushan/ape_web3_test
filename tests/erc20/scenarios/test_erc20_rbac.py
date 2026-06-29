"""
==============================================================================
【ERC20 场景】RBAC 角色控制测试
==============================================================================
"""
try:
    import allure
except ImportError:
    class dummy_allure:
        @staticmethod
        def title(*args, **kwargs):
            return lambda f: f
        @staticmethod
        def description(*args, **kwargs):
            return lambda f: f
        @staticmethod
        def tag(*args, **kwargs):
            return lambda f: f
    allure = dummy_allure()

from ape import reverts
from framework.core.logger import log
from framework.core.formatters import format_ether, parse_ether


@allure.title("case_008 RBAC 角色控制测试")
@allure.description("验证没有权限的账户无法执行受限操作（铸币、暂停）")
@allure.tag("ERC20", "P0", "安全测试", "RBAC", "反向测试")
def test_erc20_008_rbac_role_control(erc20_api, user1, user2):
    """
    case_008 RBAC 角色控制测试
    
    验证权限控制的安全性：
    - 普通用户无法 mint（需要 MINTER_ROLE）
    - 普通用户无法 pause（需要 PAUSER_ROLE）
    - 无权限用户无法授权他人角色（需要 ADMIN_ROLE）
    """
    log.step("case_008: RBAC 角色控制测试")
    
    with reverts():
        erc20_api.mint(user1, "100", user1)
    log.debug("✓ 普通用户铸币失败")
    
    with reverts():
        erc20_api.pause(user1)
    log.debug("✓ 普通用户暂停失败")
    
    MINTER_ROLE = erc20_api.get_minter_role()
    with reverts():
        erc20_api.grant_role(MINTER_ROLE, user2, user1)
    log.debug("✓ 无权限用户授权失败")
    
    log.success("✅ case_008 RBAC 角色控制测试通过")


@allure.title("case_009 RBAC 角色正常操作测试")
@allure.description("验证拥有权限的账户可以执行受限操作")
@allure.tag("ERC20", "P0", "功能测试", "RBAC", "正向测试")
def test_erc20_009_role_normal_operations(erc20_api, deployer, user1, user2):
    log.step("case_009: RBAC 角色正常操作测试")
    
    MINTER_ROLE = erc20_api.get_minter_role()
    PAUSER_ROLE = erc20_api.get_pauser_role()
    
    erc20_api.grant_role(MINTER_ROLE, user1, deployer)
    assert erc20_api.has_role(MINTER_ROLE, user1)
    log.debug("✓ user1 已获得 MINTER_ROLE")
    
    erc20_api.mint(user1, "500", user1)
    balance = erc20_api.get_balance(user1)
    assert balance == parse_ether("500")
    log.debug("✓ user1 铸币成功")
    
    erc20_api.grant_role(PAUSER_ROLE, user2, deployer)
    assert erc20_api.has_role(PAUSER_ROLE, user2)
    log.debug("✓ user2 已获得 PAUSER_ROLE")
    
    erc20_api.pause(user2)
    assert erc20_api.is_paused()
    log.debug("✓ 合约已暂停")
    
    with reverts():
        erc20_api.transfer(user2, "10", user1)
    log.debug("✓ 暂停期间转账失败")
    
    erc20_api.unpause(deployer)
    assert not erc20_api.is_paused()
    log.debug("✓ 合约已恢复")
    
    log.success("✅ case_009 RBAC 角色正常操作测试通过")


@allure.title("case_010 权限升级测试")
@allure.description("验证 ADMIN 角色可以管理其他角色的权限")
@allure.tag("ERC20", "P1", "功能测试", "RBAC", "权限管理")
def test_erc20_010_permission_upgrade(erc20_api, deployer, user1):
    log.step("case_010: 权限升级测试")
    
    MINTER_ROLE = erc20_api.get_minter_role()
    ADMIN_ROLE = erc20_api.get_admin_role()
    
    assert erc20_api.has_role(ADMIN_ROLE, deployer)
    
    erc20_api.grant_role(MINTER_ROLE, user1, deployer)
    assert erc20_api.has_role(MINTER_ROLE, user1)
    
    erc20_api.mint(user1, "200", user1)
    log.debug("✓ user1 铸币成功")
    
    erc20_api.revoke_role(MINTER_ROLE, user1, deployer)
    assert not erc20_api.has_role(MINTER_ROLE, user1)
    
    with reverts():
        erc20_api.mint(user1, "100", user1)
    log.debug("✓ user1 铸币失败")
    
    log.success("✅ case_010 权限升级测试通过")