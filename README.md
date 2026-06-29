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
| **架构设计** | 四层架构（框架层/模块层/数据层/用例层），模块化解耦                            |

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
├── framework/                       # 框架核心层（原子能力）
│   ├── core/                       # 核心工具
│   │   ├── logger.py              # 企业级日志模块
│   │   ├── formatters.py          # 格式转换工具（parse_ether 等）
│   │   ├── assertions.py           # 可复用断言函数
│   │   ├── config.py              # 配置管理
│   │   ├── retry_helper.py        # 重试机制
│   │   ├── polling_helper.py       # 轮询机制
│   │   └── test_data_factory.py    # 测试数据工厂
│   ├── api/                        # HTTP API 客户端（CEX 测试）
│   │   └── http_client.py
│   └── web3/                       # Web3 交互封装
│       └── ape_client.py
├── tests/                          # 测试用例层（四层架构）
│   ├── conftest.py                 # pytest 全局共享 Fixture
│   ├── erc20/                      # ERC20 模块
│   │   ├── apis/                   # API 原子封装
│   │   ├── fixtures/               # Fixture 环境准备
│   │   ├── data/                   # 测试数据
│   │   └── scenarios/              # 测试用例
│   ├── dex_swap/                   # DEX 模块
│   │   ├── apis/
│   │   ├── fixtures/
│   │   ├── data/
│   │   └── scenarios/
│   ├── liquidation/                # 清算模块
│   │   ├── apis/
│   │   ├── fixtures/
│   │   ├── data/
│   │   └── scenarios/
│   ├── security/                   # 安全模块
│   │   ├── apis/
│   │   ├── fixtures/
│   │   ├── data/
│   │   └── scenarios/
│   ├── nft/                        # NFT 模块
│   │   ├── fixtures/
│   │   ├── data/
│   │   └── scenarios/
│   ├── contract_custom/            # 自定义合约模块
│   │   ├── apis/
│   │   ├── fixtures/
│   │   ├── data/
│   │   └── scenarios/
│   └── api/                        # CEX API 模块（预留）
│       ├── apis/
│       ├── fixtures/
│       └── scenarios/
├── logs/                           # 运行日志目录
├── run_tests.py                    # 统一测试运行入口
└── case_list                       # 完整测试用例清单
```

### 四层架构说明

| 层级      | 目录                    | 职责                                            |
| ------- | --------------------- | --------------------------------------------- |
| **框架层** | `framework/`          | 原子能力：日志、格式化、断言、重试、轮询、配置                       |
| **模块层** | `tests/{module}/`     | 按业务域划分：erc20、dex\_swap、liquidation、security 等 |
| **数据层** | `{module}/data/`      | YAML 测试数据，与代码分离                               |
| **用例层** | `{module}/scenarios/` | 具体测试用例实现                                      |

### 各模块说明

| 模块                 | 目录                           | 职责                        |
| ------------------ | ---------------------------- | ------------------------- |
| `erc20/`           | apis/fixtures/data/scenarios | ERC20 代币测试（转账、授权、铸造、RBAC） |
| `dex_swap/`        | apis/fixtures/data/scenarios | DEX 交易所测试（Swap、流动性、手续费）   |
| `liquidation/`     | apis/fixtures/data/scenarios | 清算业务测试（清算触发、奖励计算）         |
| `security/`        | apis/fixtures/data/scenarios | 安全测试（重入、整数溢出、闪电贷）         |
| `nft/`             | fixtures/data/scenarios      | NFT 测试（ERC721/ERC1155）    |
| `contract_custom/` | apis/fixtures/data/scenarios | 自定义合约测试                   |
| `api/`             | apis/fixtures/scenarios      | CEX API 测试（预留）            |

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
python3 run_tests.py tests/erc20/scenarios/

# 运行特定用例
python3 run_tests.py tests/erc20/scenarios/test_erc20_metadata.py::test_erc20_001_metadata_verification

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
ape test tests/erc20/scenarios/ -v

# 运行特定用例
ape test -k "test_erc20_001" -v
```

***

## 测试用例规范

### 命名规范

- **测试文件**：`test_{业务域}_{编号}.py`（如 `test_erc20_metadata.py`）
- **测试函数**：`test_{业务域}_{编号}_{描述}`（如 `test_erc20_001_metadata_verification`）

### 用例优先级说明

| 优先级    | 标识 | 说明          |
| ------ | -- | ----------- |
| **P0** | 必测 | 核心业务流程      |
| **P1** | 推荐 | 进阶拓展、安全防护场景 |

### 测试用例分类

| 模块          | 用例数量 | 说明                        |
| ----------- | ---- | ------------------------- |
| ERC20 基础标准  | 10   | 代币转账、授权、铸造、销毁、RBAC 权限     |
| DEX 去中心化交易所 | 8    | Swap、流动性添加/移除、滑点控制、手续费    |
| 自定义业务合约     | 10   | 权限控制、参数配置、暂停恢复、黑名单        |
| 高阶安全场景      | 12   | 重入防护、整数溢出、授权安全、链上事件       |
| NFT/SFT     | 10   | ERC721/ERC1155 铸造、转账、交易场景 |
| 清算业务        | 11   | 清算触发、流程、奖励、安全防护           |
| Uniswap V3  | 10   | 集中流动性、多费率、TWAP 预言机        |

### YAML 测试数据格式

```yaml
# tests/erc20/data/test_erc20.yaml
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
def test_erc20_003_insufficient_balance_transfer(erc20_token, deployer, user1):
    """余额不足异常转账测试"""
    from framework.core.formatters import parse_ether

    mint_amount = parse_ether("1000")
    erc20_token.mint(deployer, mint_amount, sender=deployer)

    transfer_amount = parse_ether("2000")

    balance_before = erc20_token.balanceOf(deployer)

    with pytest.raises((ContractLogicError, VirtualMachineError)):
        erc20_token.transfer(user1, transfer_amount, sender=deployer)

    assert erc20_token.balanceOf(deployer) == balance_before
```

***

## 配置说明

核心配置见 `ape-config.yaml`：

- `plugins`: Solidity 编译器、Anvil 节点、Etherscan 验证插件
- `ethereum`: 多链网络配置（local/mainnet-fork/goerli/polygon）
- `test`: 测试助记词、账户数量、主网分叉配置
- `compiler`: Solc 版本锁定、优化器配置
- `dependencies`: OpenZeppelin 等第三方依赖库

***

## 项目业务价值

本自动化框架用于DeFi合约迭代全流程回归，替代人工重复测试：

1. 迭代版本回归耗时从2天缩短至20分钟，释放开发与手工测试人力；
2. 分层用例覆盖资金、权限、重入、整数溢出高危场景，上线前拦截全部资金逻辑漏洞；
3. CI流水线提交自动执行，阻断缺陷合入主分支，保障线上资产安全。

## 配套性能&稳定性测试仓库

并发压测、混沌故障注入、线上全链路监控：<https://github.com/liuyoushan/blockchain-perf-test>

## 报告目录下起服务查git actions的报告：

```
python -m http.server 8080
```

## 相关资源

- [ApeWorX 官方文档](https://docs.apeworx.io/)
- [完整用例清单](case_list)
- [合约源码目录](contracts/)

