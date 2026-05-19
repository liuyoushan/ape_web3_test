import pytest


@pytest.fixture(scope="function")
def myerc20_token(deployer, project):
    """
    case_018~case_025 通用测试 token fixture
    """
    return deployer.deploy(project.MyERC20, "TestToken", "TT")


@pytest.fixture(scope="function")
def role_constants(token):
    """
    统一导出 MyERC20 的角色常量
    """
    return {
        "MINTER_ROLE": token.MINTER_ROLE(),
        "PAUSER_ROLE": token.PAUSER_ROLE(),
        "ADMIN_ROLE": token.ADMIN_ROLE(),
    }
