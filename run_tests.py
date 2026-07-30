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
ALLURE_RESULTS_DIR = ROOT_DIR / "report" / "allure-results"
ALLURE_REPORT_DIR = ROOT_DIR / "report" / "allure-report"
PYTEST_CACHE_DIR = ROOT_DIR / ".pytest_cache"

# ==================== 企业级业务域映射（项目维度） ====================
# 支持通过 --project 一键运行对应业务域的全部测试，等价于 -m 标记 + 目录组合
PROJECT_MAPPING = {
    # contracts - 合约层（ERC20 + 自定义合约）
    "contracts": {
        "desc": "合约基础层（ERC20 代币标准 + 自定义合约逻辑）",
        "paths": ["tests/contracts/"],
        "marker": None,
        "modules": ["erc20", "custom"],
    },
    "erc20": {
        "desc": "ERC20 代币标准测试",
        "paths": ["tests/contracts/erc20/"],
        "marker": "ERC20",
        "modules": ["erc20"],
    },
    "custom": {
        "desc": "自定义合约逻辑测试（权限、参数、暂停机制）",
        "paths": ["tests/contracts/custom/"],
        "marker": None,
        "modules": ["custom"],
    },

    # dex - DEX 业务层
    "dex": {
        "desc": "DEX 业务层（Swap 交易 + 清算 + NFT）",
        "paths": ["tests/dex/"],
        "marker": None,
        "modules": ["swap", "liquidation", "nft"],
    },
    "swap": {
        "desc": "DEX 交易核心（MiniSwap Factory/Pair/Router）",
        "paths": ["tests/dex/swap/"],
        "marker": "DexSwap",
        "modules": ["swap"],
    },
    "liquidation": {
        "desc": "清算业务测试",
        "paths": ["tests/dex/liquidation/"],
        "marker": None,
        "modules": ["liquidation"],
    },
    "nft": {
        "desc": "NFT 业务测试（ERC721/ERC1155）",
        "paths": ["tests/dex/nft/"],
        "marker": None,
        "modules": ["nft"],
    },

    # cex - CEX 业务层
    "cex": {
        "desc": "CEX 中心化交易所（资金链路 + 订单系统 + 风控体系）",
        "paths": ["tests/cex/"],
        "marker": "CEX",
        "modules": ["fund", "order", "risk"],
    },
    "cex_fund": {
        "desc": "CEX 资金链路（充币/提币/划转/账户）",
        "paths": ["tests/cex/fund/"],
        "marker": "CEX_Fund",
        "modules": ["fund"],
    },
    "cex_order": {
        "desc": "CEX 订单系统（现货下单/撤单/撮合）",
        "paths": ["tests/cex/order/"],
        "marker": "CEX_Order",
        "modules": ["order"],
    },
    "cex_risk": {
        "desc": "CEX 风控体系（权限/白名单/资损防护）",
        "paths": ["tests/cex/risk/"],
        "marker": "CEX_Risk",
        "modules": ["risk"],
    },

    # security - 安全测试
    "security": {
        "desc": "安全测试（重入/溢出/授权/代理升级/时间锁）",
        "paths": ["tests/security/"],
        "marker": "Security",
        "modules": ["security"],
    },

    # all - 全部业务域
    "all": {
        "desc": "全部测试（合约 + DEX + CEX + 安全）",
        "paths": ["tests/contracts/", "tests/dex/", "tests/cex/", "tests/security/"],
        "marker": None,
        "modules": ["all"],
    },
}


def list_available_projects() -> str:
    """列出所有可用的业务域，用于 --help 展示"""
    lines = []
    for key, info in PROJECT_MAPPING.items():
        modules = ", ".join(info["modules"])
        marker = f" [marker: {info['marker']}]" if info["marker"] else ""
        lines.append(f"  {key:<15} {info['desc']}  (modules: {modules}){marker}")
    return "\n".join(lines)

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
        if latest_link.is_symlink() or latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(timestamp)
        
        log_section("Allure 测试报告")
        log_success(f"📊 报告目录: {timestamp_report_dir}")
        log_success(f"🔗 最新报告链接: {latest_link}")
        
        # 显示手动启动服务的提示
        if show_serve_hint:
            log_info(f"🌐 启动服务：cd /home/liuyoushan/ape-demo/report/allure-report && python3 -m http.server 8080")
            print()
            
    except FileNotFoundError:
        log_warning("Allure 命令未找到，请安装: pip install allure-pytest allure-python-commons")
    except subprocess.CalledProcessError as e:
        log_error(f"Allure 报告生成失败: {e.stderr}")

# ==================== 业务域解析 ====================
def resolve_project(project_name: str, test_path, marker):
    """
    根据 --project 解析对应的 test_path 和 marker
    
    优先级：
      1. 显式传 test_path > --project 自动推导
      2. --project 的 marker 会与 -m 参数合并（AND）
    """
    resolved_path = test_path
    resolved_marker = marker
    project_info = None

    if project_name:
        project_name = project_name.lower()
        if project_name not in PROJECT_MAPPING:
            available = list(PROJECT_MAPPING.keys())
            raise ValueError(
                f"未知项目: {project_name}\n"
                f"可选值: {', '.join(available)}\n\n"
                f"可用项目明细：\n{list_available_projects()}"
            )
        project_info = PROJECT_MAPPING[project_name]
        # 只有当 test_path 是默认值（未显式指定路径）时才覆盖
        if (isinstance(test_path, list) and test_path == ["tests/"]) or (
            isinstance(test_path, str) and test_path.endswith("tests/")
        ):
            resolved_path = project_info["paths"]
            log_info(f"📦 使用项目映射：{project_name} → {project_info['desc']}")
            log_info(f"   测试路径: {', '.join(project_info['paths'])}")
        else:
            log_warning(f"--project={project_name} 指定，但 test_path 已显式设置，使用显式 test_path")

        # 合并 marker（AND）
        project_marker = project_info.get("marker")
        if project_marker and resolved_marker:
            resolved_marker = f"({project_marker}) and ({resolved_marker})"
            log_info(f"🏷️  合并标记筛选: {resolved_marker}")
        elif project_marker:
            resolved_marker = project_marker
            log_info(f"🏷️  项目标记筛选: {resolved_marker}")

    return resolved_path, resolved_marker, project_info


# ==================== 运行测试 ====================
def run_tests(
    test_path,
    network: str = "ethereum:local",
    verbose: bool = True,
    clean: bool = True,
    generate_report: bool = True,
    marker: str = None,
    xfail: bool = False,
    serve_report: bool = False,
    report_port: int = 8080,
    capture: bool = False,
    project: str = None,
):
    """
    运行 pytest 测试
    
    Args:
        test_path: 测试文件或目录路径（支持单个字符串或多个路径列表）
        network: 网络配置 (ethereum:local, ethereum:mainnet:http)
        verbose: 是否显示详细输出
        clean: 是否清理缓存
        generate_report: 是否生成 Allure 报告
        marker: 测试标记筛选
        xfail: 是否允许预期失败的测试通过
        serve_report: 是否启动 Allure 报告服务
        report_port: Allure 服务端口
        capture: 是否禁用 stdout 捕获
        project: 业务域一键运行（见 PROJECT_MAPPING）
    """
    start_time = datetime.now()
    python_path = get_python_path()
    allure_available = has_allure_pytest(python_path)

    # 业务域解析（在清理缓存之前）
    test_path, marker, project_info = resolve_project(project, test_path, marker)
    
    # 清理缓存
    if clean:
        log_section("清理测试缓存")
        clean_cache()
    
    # 设置网络环境变量
    os.environ["APE_NETWORK"] = network
    
    # 打印网络信息
    print_network_info(network)

    # 打印业务域信息
    if project_info:
        print(f"\n{Color.CYAN}{'📦 业务域'.center(70)}{Color.RESET}")
        print(f"{Color.GREEN}  项目:    {project or 'custom'}{Color.RESET}")
        print(f"{Color.GREEN}  描述:    {project_info['desc']}{Color.RESET}")
        print(f"{Color.GREEN}  子模块:  {', '.join(project_info['modules'])}{Color.RESET}")
        if project_info.get("marker"):
            print(f"{Color.GREEN}  标记:    {project_info['marker']}{Color.RESET}")
        print(f"{Color.PURPLE}{'='*70}{Color.RESET}\n")
    
    # 构建 pytest 命令
    cmd = [python_path, "-m", "pytest"]
    if isinstance(test_path, list):
        cmd.extend(test_path)
    else:
        cmd.append(str(test_path))
    
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
    
    # 显示 print 输出（禁用 stdout 捕获）
    if capture:
        cmd.append("-s")
    
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
        description="企业级 Web3 测试运行器（支持按业务域一键运行）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
📌 一、按业务域一键运行（--project）:
  python run_tests.py --project contracts     # 合约基础层
  python run_tests.py --project dex           # DEX 业务层
  python run_tests.py --project cex           # CEX 中心化交易所
  python run_tests.py --project security      # 安全测试
  python run_tests.py --project cex_fund      # CEX 资金链路
  python run_tests.py --project all           # 全部测试

📌 二、业务域 + 标记组合筛选:
  python run_tests.py --project cex -m "P0"
  python run_tests.py --project contracts -m "P0 and ERC20"

📌 三、显式指定路径（优先级高于 --project）:
  python run_tests.py tests/contracts/erc20/scenarios/
  python run_tests.py tests/cex/fund/scenarios/test_account.py::test_case_001_account_info

📌 四、指定网络运行:
  python run_tests.py --project cex --network ethereum:local

可用 --project 列表：
{list_available_projects()}
        """
    )
    
    parser.add_argument(
        "test_path",
        nargs="*",
        default=["tests/"],
        help="测试文件或目录路径（支持多个）"
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
    
    parser.add_argument(
        "-s", "--capture",
        action="store_true",
        default=False,
        help="显示测试中的 print 输出（禁用 stdout 捕获）"
    )

    parser.add_argument(
        "-p", "--project",
        default=None,
        help="按业务域一键运行，可选值见下方 epilog 列表，如: contracts/dex/cex/cex_fund"
    )

    parser.add_argument(
        "--list-projects",
        action="store_true",
        default=False,
        help="列出所有可用的业务域（project）并退出"
    )

    args = parser.parse_args()

    # 仅列出可用项目
    if args.list_projects:
        print("\n📦 可用业务域列表（--project 参数）：\n")
        print(list_available_projects())
        print()
        sys.exit(0)

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
        report_port=args.port,
        capture=args.capture,
        project=args.project,
    )
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
