#!/usr/bin/env python3
# ==============================================================================
# 企业级 Web3 测试运行器
# ==============================================================================
# 功能特性：
#   - 纯 Python 实现，支持 pytest 直接运行
#   - 完整的命令行参数支持
#   - 企业级日志系统
#   - Allure 报告自动生成
#   - 网络配置管理
#   - 缓存清理机制
#   - 测试结果汇总统计
#   - 自动检测 pipx 环境
# ==============================================================================

import os
import sys
import subprocess
import argparse
import shutil
from datetime import datetime
from pathlib import Path

# ==================== 配置常量 ====================
ROOT_DIR = Path(__file__).parent
TEST_DIR = ROOT_DIR / "tests"
ALLURE_RESULTS_DIR = ROOT_DIR / "allure-results"
ALLURE_REPORT_DIR = ROOT_DIR / "allure-report"
PYTEST_CACHE_DIR = ROOT_DIR / ".pytest_cache"

# 项目 venv 环境路径
VENV_PYTHON_PATH = ROOT_DIR / ".venv" / "bin" / "python"

# pipx 环境路径（备用）
PIPX_ETH_APE_PATH = Path(os.path.expanduser("~/.local/share/pipx/venvs/eth-ape/bin/python"))

# ==================== 颜色输出 ====================
class Color:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    RESET = "\033[0m"

def log_info(message: str):
    """信息日志"""
    print(f"{Color.BLUE}[INFO] {message}{Color.RESET}")

def log_success(message: str):
    """成功日志"""
    print(f"{Color.GREEN}[SUCCESS] {message}{Color.RESET}")

def log_warning(message: str):
    """警告日志"""
    print(f"{Color.YELLOW}[WARNING] {message}{Color.RESET}")

def log_error(message: str):
    """错误日志"""
    print(f"{Color.RED}[ERROR] {message}{Color.RESET}")

def log_section(title: str):
    """打印分隔线"""
    print(f"\n{Color.PURPLE}{'='*70}{Color.RESET}")
    print(f"{Color.CYAN}{title.center(70)}{Color.RESET}")
    print(f"{Color.PURPLE}{'='*70}{Color.RESET}")

# ==================== 获取 Python 路径 ====================
def get_python_path() -> str:
    """获取正确的 Python 路径（优先使用项目 venv 环境）"""
    # 优先使用项目目录下的 venv
    if VENV_PYTHON_PATH.exists():
        log_info(f"使用项目 venv 环境: {VENV_PYTHON_PATH}")
        return str(VENV_PYTHON_PATH)
    
    # 备用：使用 pipx 环境
    if PIPX_ETH_APE_PATH.exists():
        log_info(f"使用 pipx 环境: {PIPX_ETH_APE_PATH}")
        return str(PIPX_ETH_APE_PATH)
    
    # 检查当前环境
    if "ape" in sys.modules:
        log_info("使用当前 Python 环境")
        return sys.executable
    
    log_warning("未检测到虚拟环境，使用系统 Python")
    return "python3"

# ==================== 检查 allure-pytest 是否安装 ====================
def has_allure_pytest(python_path: str) -> bool:
    """检查 allure-pytest 是否安装"""
    result = subprocess.run(
        [python_path, "-c", "import allure_pytest"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

# ==================== 网络检测 ====================
def detect_network(network: str) -> dict:
    """
    检测网络类型并返回网络信息
    
    Returns:
        dict: 包含 network_type, chain_id, description 的字典
    """
    network_info = {
        "network_type": "unknown",
        "chain_id": None,
        "description": "未知网络",
        "is_mainnet_fork": False
    }
    
    # 根据网络配置判断类型
    if "mainnet" in network.lower():
        network_info["network_type"] = "mainnet_fork"
        network_info["chain_id"] = 1
        network_info["description"] = "以太坊主网 Fork"
        network_info["is_mainnet_fork"] = True
    elif "local" in network.lower():
        # 本地网络，需要连接节点检测
        try:
            import requests
            response = requests.post(
                "http://localhost:8545",
                json={"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1},
                timeout=2
            )
            result = response.json()
            chain_id_hex = result.get("result", "0x0")
            chain_id = int(chain_id_hex, 16)
            
            network_info["chain_id"] = chain_id
            
            if chain_id == 1:
                network_info["network_type"] = "mainnet_fork"
                network_info["description"] = "以太坊主网 Fork (通过本地节点)"
                network_info["is_mainnet_fork"] = True
            elif chain_id == 1337:
                network_info["network_type"] = "local"
                network_info["description"] = "本地测试链 (Ganache)"
            elif chain_id == 31337:
                network_info["network_type"] = "local"
                network_info["description"] = "本地测试链 (Anvil)"
            else:
                network_info["network_type"] = "local"
                network_info["description"] = f"本地测试链 (Chain ID: {chain_id})"
        except Exception:
            network_info["network_type"] = "local"
            network_info["description"] = "本地测试链 (节点未连接)"
    elif "goerli" in network.lower():
        network_info["network_type"] = "testnet"
        network_info["chain_id"] = 5
        network_info["description"] = "Goerli 测试网"
    elif "sepolia" in network.lower():
        network_info["network_type"] = "testnet"
        network_info["chain_id"] = 11155111
        network_info["description"] = "Sepolia 测试网"
    
    return network_info


def print_network_info(network: str):
    """打印网络信息（醒目显示）"""
    info = detect_network(network)
    
    print(f"\n{Color.PURPLE}{'='*70}{Color.RESET}")
    print(f"{Color.CYAN}{'📡 网络连接信息'.center(70)}{Color.RESET}")
    print(f"{Color.PURPLE}{'='*70}{Color.RESET}")
    
    # 网络类型（醒目显示）
    if info["is_mainnet_fork"]:
        print(f"{Color.GREEN}⭐ 网络类型: {info['description']}{Color.RESET}")
        print(f"{Color.GREEN}✅ 正在运行在 主网 Fork 环境！{Color.RESET}")
    else:
        print(f"{Color.YELLOW}📌 网络类型: {info['description']}{Color.RESET}")
        print(f"{Color.YELLOW}⚠️  不是主网 Fork 环境{Color.RESET}")
    
    if info["chain_id"]:
        print(f"{Color.BLUE}🔗 链 ID: {info['chain_id']}{Color.RESET}")
    
    print(f"{Color.PURPLE}{'='*70}{Color.RESET}\n")


# ==================== 缓存清理 ====================
def clean_cache():
    """清理测试缓存"""
    cache_dirs = [PYTEST_CACHE_DIR, ALLURE_RESULTS_DIR]
    
    for cache_dir in cache_dirs:
        if cache_dir.exists():
            if cache_dir.is_symlink():
                cache_dir.unlink()
                log_info(f"已清理缓存: {cache_dir.name} (符号链接)")
            else:
                shutil.rmtree(cache_dir)
                log_info(f"已清理缓存: {cache_dir.name}")
    
    # 不清理 allure-report 目录，保留所有历史报告

# ==================== 生成 Allure 报告 ====================
def generate_allure_report(show_serve_hint: bool = False, port: int = 8080):
    """
    生成 Allure 测试报告
    
    Args:
        show_serve_hint: 是否显示手动启动服务的提示
        port: 服务端口
    """
    if not ALLURE_RESULTS_DIR.exists():
        log_warning("Allure 结果目录不存在，跳过报告生成")
        return
    
    try:
        # 确保 allure-report 目录存在
        if ALLURE_REPORT_DIR.is_symlink():
            ALLURE_REPORT_DIR.unlink()
        if not ALLURE_REPORT_DIR.exists():
            ALLURE_REPORT_DIR.mkdir(parents=True)
        
        # 生成带时间戳的报告目录（在 allure-report 目录下）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamp_report_dir = ALLURE_REPORT_DIR / timestamp
        
        # 生成新报告
        subprocess.run(
            ["allure", "generate", str(ALLURE_RESULTS_DIR), "--clean", "-o", str(timestamp_report_dir)],
            check=True,
            capture_output=True,
            text=True
        )
        
        # 创建最新报告的软链接
        latest_link = ALLURE_REPORT_DIR / "latest"
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(timestamp)
        
        log_section("Allure 测试报告")
        log_success(f"📊 报告目录: {timestamp_report_dir}")
        log_success(f"🔗 最新报告链接: {latest_link}")
        
        # 显示手动启动服务的提示
        if show_serve_hint:
            log_info(f"🌐 启动服务: cd /home/liuyoushan/ape-demo/allure-report && python3 -m http.server 8080")
            print()
            
    except FileNotFoundError:
        log_warning("Allure 命令未找到，请安装: pip install allure-pytest allure-python-commons")
    except subprocess.CalledProcessError as e:
        log_error(f"Allure 报告生成失败: {e.stderr}")

# ==================== 运行测试 ====================
def run_tests(
    test_path: str = "tests/",
    network: str = "ethereum:local",
    verbose: bool = True,
    clean: bool = True,
    generate_report: bool = True,
    marker: str = None,
    xfail: bool = False,
    serve_report: bool = False,
    report_port: int = 8080
):
    """
    运行 pytest 测试
    
    Args:
        test_path: 测试文件或目录路径
        network: 网络配置 (ethereum:local, ethereum:mainnet:http)
        verbose: 是否显示详细输出
        clean: 是否清理缓存
        generate_report: 是否生成 Allure 报告
        marker: 测试标记筛选
        xfail: 是否允许预期失败的测试通过
        serve_report: 是否启动 Allure 报告服务
        report_port: Allure 服务端口
    """
    start_time = datetime.now()
    python_path = get_python_path()
    allure_available = has_allure_pytest(python_path)
    
    # 清理缓存
    if clean:
        log_section("清理测试缓存")
        clean_cache()
    
    # 设置网络环境变量
    os.environ["APE_NETWORK"] = network
    
    # 打印网络信息
    print_network_info(network)
    
    # 构建 pytest 命令
    cmd = [python_path, "-m", "pytest", str(test_path)]
    
    # 详细输出
    if verbose:
        cmd.append("-v")
    
    # Allure 报告（仅当可用时）
    if generate_report and allure_available:
        cmd.extend(["--alluredir", str(ALLURE_RESULTS_DIR)])
    elif generate_report:
        log_warning("allure-pytest 未安装，跳过 Allure 报告")
    
    # 标记筛选
    if marker:
        cmd.extend(["-m", marker])
    
    # 预期失败处理
    if xfail:
        cmd.append("--runxfail")
    
    # 添加颜色输出
    cmd.append("--color=yes")
    
    # 显示命令
    log_section("测试配置")
    log_info(f"测试路径: {test_path}")
    log_info(f"网络配置: {network}")
    log_info(f"Python 路径: {python_path}")
    log_info(f"Allure 支持: {'✓' if allure_available else '✗'}")
    log_info(f"运行命令: {' '.join(cmd)}")
    
    # 运行测试
    log_section("开始测试")
    result = subprocess.run(
        cmd,
        cwd=ROOT_DIR,
        capture_output=False,
        text=True
    )
    
    # 统计结果
    elapsed_time = datetime.now() - start_time
    log_section("测试结果")
    
    if result.returncode == 0:
        log_success(f"所有测试通过！耗时: {elapsed_time}")
    else:
        log_error(f"测试失败！返回码: {result.returncode}")
    
    # 生成报告
    if generate_report and allure_available:
        log_section("生成测试报告")
        generate_allure_report(show_serve_hint=serve_report, port=report_port)
    
    return result.returncode

# ==================== 主函数 ====================
def main():
    parser = argparse.ArgumentParser(
        prog="run_tests.py",
        description="企业级 Web3 测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 运行所有测试
  python run_tests.py

  # 运行指定测试文件
  python run_tests.py tests/test_erc20.py

  # 运行指定测试用例
  python run_tests.py tests/test_erc20.py::test_erc20_001_metadata_verification

  # 指定网络运行
  python run_tests.py --network ethereum:mainnet:http

  # 运行带有特定标记的测试
  python run_tests.py -m "P0 and ERC20"

  # 不生成报告
  python run_tests.py --no-report
        """
    )
    
    parser.add_argument(
        "test_path",
        nargs="?",
        default="tests/",
        help="测试文件或目录路径"
    )
    
    parser.add_argument(
        "-n", "--network",
        default="ethereum:local",
        help="网络配置 (默认: ethereum:local)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=True,
        help="详细输出"
    )
    
    parser.add_argument(
        "-c", "--clean",
        action="store_true",
        default=True,
        help="运行前清理缓存"
    )
    
    parser.add_argument(
        "--no-report",
        action="store_true",
        default=False,
        help="不生成 Allure 报告"
    )
    
    parser.add_argument(
        "-m", "--marker",
        help="按标记筛选测试 (如: -m \"P0 and ERC20\")"
    )
    
    parser.add_argument(
        "--runxfail",
        action="store_true",
        default=False,
        help="运行预期失败的测试"
    )
    
    parser.add_argument(
        "--serve",
        action="store_true",
        default=False,
        help="显示手动启动服务的命令"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=34567,
        help="服务端口 (默认: 34567)"
    )
    
    args = parser.parse_args()
    
    # 运行测试
    exit_code = run_tests(
        test_path=args.test_path,
        network=args.network,
        verbose=args.verbose,
        clean=args.clean,
        generate_report=not args.no_report,
        marker=args.marker,
        xfail=args.runxfail,
        serve_report=args.serve,
        report_port=args.port
    )
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
