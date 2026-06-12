# Web3 智能合约自动化测试框架

一套基于 ApeWorX 的企业级智能合约自动化测试解决方案，覆盖 ERC20、DEX、权限控制等核心区块链业务场景。

***

## 项目概述

本项目提供标准化的智能合约测试架构，支持数据驱动测试、事件断言、异常场景覆盖等企业级测试能力：

| 特性       | 说明                                                     |
| -------- | ------------------------------------------------------ |
| **测试框架** | ApeWorX + Pytest 企业级自动化测试体系                            |
| **合约覆盖** | ERC20(RBAC)、Uniswap 式 DEX(Factory/Pair/Router)、自定义业务合约 |
| **用例设计** | 功能测试与安全测试分层设计，覆盖正向与异常场景                                |
| **断言体系** | 链上事件校验、余额变化验证、权限边界检查、异常 revert 验证                      |
| **架构设计** | Fixture 工厂 + YAML 数据驱动 + 断言助手，模块化解耦                    |

***

## 项目结构

```
ape-demo/
├── ape-config.yaml                  # Ape 框架配置（多链网络、测试、编译器）
├── contracts/                       # 智能合约
│   ├── MyERC20.sol                 # RBAC 权限控制的 ERC20 代币
│   ├── MiniSwapFactory.sol         # DEX 工厂合约
│   ├── MiniSwapPair.sol            # DEX 交易对合约
│   ├── MiniSwapRouter.sol          # DEX 路由合约
│   ├── Liquidation.sol             # 清算业务合约
│   ├── SimpleFlashLoan.sol         # 闪电贷合约（测试用）
│   ├── MaliciousAttacker.sol       # 恶意攻击者合约（安全测试）
│   ├── MaliciousToken.sol          # 恶意代币合约（安全测试）
│   └── HelloWorld.sol              # 示例合约
├── scripts/
│   └── deploy.py                   # 合约部署脚本
├── tests/
│   ├── conftest.py                 # pytest 共享 Fixture 配置
│   ├── data/                       # 测试数据（YAML 格式）
│   │   ├── test_erc20.yaml
│   │   ├── test_dex_swap.yaml
│   │   ├── test_dex_swap_v3.yaml
│   │   ├── test_liquidation.yaml
│   │   ├── test_nft.yaml
│   │   ├── test_security_advanced.yaml
│   │   └── test_swap_custom_func.yaml
│   ├── fixtures/                   # Fixture 工厂模块
│   │   ├── token_fixture.py        # ERC20 相关 Fixture
│   │   ├── dex_fixture.py          # DEX 相关 Fixture
│   │   ├── liquidation_fixture.py  # 清算相关 Fixture
│   │   ├── swap_v3_fixture.py      # Uniswap V3 相关 Fixture
│   │   ├── security_fixture.py     # 安全测试 Fixture
│   │   └── contract_custom_fixture.py # 自定义合约 Fixture
│   ├── helpers/                    # 测试助手
│   │   ├── assertions.py           # 可复用断言函数
│   │   ├── formatters.py           # 格式转换工具
│   │   └── logger.py               # 企业级日志模块
│   ├── test_erc20.py               # ERC20 代币测试
│   ├── test_dex_swap.py            # DEX 交易所测试
│   ├── test_dex_swap_v3.py         # Uniswap V3 测试
│   ├── test_liquidation.py         # 清算业务测试
│   ├── test_nft.py                 # NFT/SFT 测试
│   ├── test_security_advanced.py   # 安全场景测试
│   ├── test_contract_custom.py     # 业务合约测试
│   └── test_swap_custom_func.py    # DEX 高阶流程测试
├── logs/                           # 运行日志目录
├── run_tests.py                    # 统一测试运行入口
└── case_list                       # 完整测试用例清单
```

### 核心模块说明

| 模块                  | 职责                           |
| ------------------- | ---------------------------- |
| `tests/data/*.yaml` | 存储测试参数（金额、地址、期望结果），实现数据与代码分离 |
| `tests/fixtures/`   | 合约部署、工具函数、共享上下文封装            |
| `tests/helpers/`    | 可复用断言函数、格式化工具、日志模块            |
| `tests/conftest.py` | pytest 共享入口，统一导出所有 Fixtures       |
| `run_tests.py`      | 企业级测试运行器，支持 Allure 报告、网络配置等    |

***

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+（用于 Anvil 本地测试节点）

### 安装依赖

```bash
# 安装 ApeWorX 框架
pip install eth-ape

# 安装项目依赖
pip install -r requirements.txt

# 安装 Ape 插件
ape plugins install solidity anvil
```

### 运行测试

本项目提供 `run_tests.py` 作为统一的测试运行入口：

```bash
# 运行所有测试
python3 run_tests.py

# 运行指定测试文件
python3 run_tests.py tests/test_erc20.py

# 运行特定用例
python3 run_tests.py tests/test_erc20.py::test_erc20_001_metadata_verification

# 指定网络运行
python3 run_tests.py --network ethereum:local

# 运行带有特定标记的测试
python3 run_tests.py -m "P0 and ERC20"

# 显示测试中的 print 输出
python3 run_tests.py -s

# 不生成 Allure 报告
python3 run_tests.py --no-report

# 显示帮助信息
python3 run_tests.py --help
```

**备用方式**：直接使用 Ape 框架（不推荐）
```bash
# 运行全部测试
ape test

# 运行特定模块测试
ape test tests/test_erc20.py -v

# 运行特定用例
ape test -k "test_erc20_001" -v
```

***

## 测试用例规范

### 命名规范

- **测试文件**：`test_{业务域}.py`（如 `test_erc20.py`）
- **测试函数**：`test_{业务域}_{编号}_{描述}`（如 `test_erc20_001_metadata_verification`）

### 用例优先级说明

| 优先级 | 标识 | 说明 |
|--------|------|------|
| **P0** | 必测 | 中级岗刚需、面试高频、核心业务流程 |
| **P1** | 推荐 | 进阶拓展、拔高加分、安全防护场景 |

### 测试用例分类

| 模块 | 用例数量 | 说明 |
|------|----------|------|
| ERC20 基础标准 | 10 | 代币转账、授权、铸造、销毁、RBAC 权限 |
| DEX 去中心化交易所 | 8 | Swap、流动性添加/移除、滑点控制、手续费 |
| 自定义业务合约 | 10 | 权限控制、参数配置、暂停恢复、黑名单 |
| 高阶安全场景 | 12 | 重入防护、整数溢出、授权安全、链上事件 |
| NFT/SFT | 10 | ERC721/ERC1155 铸造、转账、交易场景 |
| 清算业务 | 11 | 清算触发、流程、奖励、安全防护 |
| Uniswap V3 | 10 | 集中流动性、多费率、TWAP 预言机 |

### YAML 测试数据格式

```yaml
# tests/data/test_erc20.yaml
common:
  token_name: "My Advanced Token"
  token_symbol: "MAT"
  expected_decimals: 18
  expected_initial_supply: 0

case_002_transfer:
  transfer_amount: "100 ether"
  mint_amount: "1000 ether"
```

### 异常测试示例

```python
def test_erc20_003_insufficient_balance_transfer(token, deployer, user1):
    """余额不足异常转账测试"""
    token = mint_token(token, deployer, deployer, "1000 ether")
    transfer_amount = parse_ether("2000 ether")
    
    balance_before = token.balanceOf(deployer)
    
    with pytest.raises((ContractLogicError, VirtualMachineError)):
        token.transfer(user1, transfer_amount, sender=deployer)
    
    assert token.balanceOf(deployer) == balance_before
```

***

## 配置说明

核心配置见 [ape-config.yaml](ape-config.yaml)：

- `plugins`: Solidity 编译器、Anvil 节点、Etherscan 验证插件
- `ethereum`: 多链网络配置（local/mainnet-fork/goerli/polygon）
- `test`: 测试助记词、账户数量、主网分叉配置
- `compiler`: Solc 版本锁定、优化器配置
- `dependencies`: OpenZeppelin 等第三方依赖库

***

## 相关资源

- [ApeWorX 官方文档](https://docs.apeworx.io/)
- [完整用例清单](case_list)
- [合约源码目录](contracts/)

