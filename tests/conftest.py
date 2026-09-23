"""
==============================================================================
共享 Fixture 配置
==============================================================================

注意：各模块的 fixtures 已迁移到对应模块的 fixtures 目录中，
通过各模块的 conftest.py 自动加载。

本文件仅保留全局共享的基础 fixtures（如账户）。
==============================================================================
"""
import os
import signal
import subprocess
import time
import pytest
import requests
from ape import project


# ==================== Fork 节点自动管理 ====================

def _is_node_alive(host: str = "127.0.0.1", port: int = 8545, timeout: float = 2.0) -> bool:
    """检测 Anvil/Geth 节点是否存活"""
    try:
        resp = requests.post(
            f"http://{host}:{port}",
            json={"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1},
            timeout=timeout,
        )
        return resp.status_code == 200 and "result" in resp.json()
    except Exception:
        return False


def _start_fork_node():
    """
    启动 Anvil 主网 Fork 节点（后台进程）。
    优先使用 start_fork_node.sh 的环境变量配置。
    """
    host = os.environ.get("WEB3_HOST", "127.0.0.1")
    port = int(os.environ.get("WEB3_PORT", "8545"))
    rpc_url = os.environ.get("WEB3_RPC_URL", os.environ.get("RPC_URL", "https://eth.drpc.org"))
    block_number = os.environ.get("WEB3_BLOCK_NUMBER", "19500000")
    chain_id = os.environ.get("WEB3_CHAIN_ID", "1")
    balance = os.environ.get("WEB3_BALANCE", "100000")

    if _is_node_alive(host, port):
        return None

    cmd = [
        "anvil",
        "--fork-url", rpc_url,
        "--fork-block-number", block_number,
        "--chain-id", chain_id,
        "--balance", balance,
        "--port", str(port),
        "--host", "0.0.0.0",
        "--silent",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for _ in range(30):
        if _is_node_alive(host, port):
            return proc
        time.sleep(0.5)

    proc.kill()
    raise RuntimeError(f"Anvil 启动失败：30 秒内未在 {host}:{port} 检测到节点")


@pytest.fixture(scope="session", autouse=True)
def _ensure_fork_node():
    """Session 级自动 fixture：确保 Fork 节点运行，测试结束后清理"""
    proc = _start_fork_node()
    yield
    if proc is not None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


# ==================== 快照隔离 ====================

@pytest.fixture(scope="function")
def snapshot_restore(chain):
    """
    Function 级快照隔离：测试前创建快照，测试后回滚。
    用于需要干净链状态的测试。
    """
    snap = chain.snapshot()
    yield
    chain.restore(snap)


# ==================== 账户 Fixtures ====================

@pytest.fixture(scope="session")
def deployer(accounts):
    """部署者账户"""
    return accounts[0]


@pytest.fixture(scope="session")
def user1(accounts):
    """测试用户1"""
    return accounts[1]


@pytest.fixture(scope="session")
def user2(accounts):
    """测试用户2"""
    return accounts[2]


@pytest.fixture(scope="session")
def user3(accounts):
    """测试用户3"""
    return accounts[3]