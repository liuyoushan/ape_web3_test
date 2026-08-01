# Web3 & CEX 全栈自动化测试框架

一套企业级自动化测试解决方案，覆盖 **智能合约层（ERC20/DEX/Custom）、DEX 业务层、CEX 中心化交易层** 三大业务域，支持按项目维度一键运行。

***

## 项目概述

本项目提供标准化的全栈测试架构，支持合约测试与 CEX 接口测试统一管理：

| 特性       | 说明                                                     |
| -------- | ------------------------------------------------------ |
| **测试框架** | ApeWorX + Pytest 企业级自动化测试体系                            |
| **合约覆盖** | ERC20(RBAC)、Uniswap 式 DEX(Factory/Pair/Router)、自定义业务合约 |
| **CEX 覆盖** | 资金链路（充币/提币/划转）、订单系统、风控体系（API 权限/资损防护）          |
| **用例设计** | 功能测试与安全测试分层设计，覆盖正向与异常场景                                |
| **断言体系** | 链上事件校验、余额变化验证、权限边界检查、异常 revert 验证                      |
| **业务域管理** | `--project` 一键运行对应业务域（contracts/dex/cex/cex_fund 等）        |
| **架构设计** | 四层架构（框架层/模块层/数据层/用例层），模块化解耦                            |

***

## 项目结构

```
ape-demo/
├── ape-config.yaml                  # Ape 框架配置（多链网络、测试、编译器）
├── config/                          # 环境配置模板
│   └── config.example.yaml         # CEX API Key / base_url 等配置示例
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
│   ├── api/                        # HTTP API 客户端
│   │   ├── http_client.py         # 通用 HTTP 客户端
│   │   └── api_validator.py        # 接口响应校验器（状态码/字段/schema）
│   ├── cex/                        # CEX 专属工具（与合约断言分离）
│   │   ├── base_client.py         # HMAC-SHA256 签名基础客户端
│   │   ├── cex_assertions.py      # CEX 专属断言
│   │   └── mock_chain.py          # 模拟链上事件（回滚/重复 TxHash）
│   └── web3/                       # Web3 交互封装
│       └── ape_client.py
├── tests/                          # 测试用例层（四大业务域）
│   ├── conftest.py                 # pytest 全局共享 Fixture
│   ├── contracts/                  # ✅ 合约基础层
│   │   ├── erc20/                  #   ERC20 代币标准测试
│   │   └── custom/                 #   自定义合约逻辑（权限/参数/暂停）
│   ├── dex/                        # ✅ DEX 业务层
│   │   ├── swap/                   #   MiniSwap 交易核心
│   │   ├── liquidation/            #   清算业务
│   │   └── nft/                    #   NFT 业务
│   ├── cex/                        # ✅ CEX 中心化交易层
│   │   ├── api/                    #   CEX 基础设施（签名客户端）
│   │   ├── fund/                   #   资金链路（充币/提币/划转/账户）
│   │   ├── order/                  #   订单系统（现货下单/撤单）
│   │   └── risk/                   #   风控体系（权限/资损防护）
│   └── security/                   # ✅ 安全测试（通用合约级安全）
│       ├── apis/
│       ├── fixtures/
│       ├── data/
│       └── scenarios/
├── logs/                           # 运行日志目录
├── run_tests.py                    # 统一测试运行入口（支持 --project 一键按业务域运行）
├── case_list                       # 合约/DEX 测试用例清单
└── cex_case_list                   # CEX 测试用例清单（28 接口 + 4 资损场景）
```

### 四层架构说明

| 层级      | 目录                    | 职责                                                         |
| ------- | --------------------- | ---------------------------------------------------------- |
| **框架层** | `framework/`          | 原子能力：日志、格式化、断言、重试、轮询、配置、CEX 签名客户端              |
| **模块层** | `tests/{domain}/{module}/` | 按**业务域**划分：contracts（合约层）/dex / cex / security 四大域 |
| **数据层** | `{module}/data/`      | YAML 测试数据，与代码分离                                             |
| **用例层** | `{module}/scenarios/` | 具体测试用例实现                                                    |

### 四大业务域说明

| 业务域         | 子模块                                  | 职责                                         | 对应 `--project` 值          |
| ----------- | ------------------------------------ | ------------------------------------------ | -------------------------- |
| **contracts** | `contracts/erc20/`、`contracts/custom/` | 合约基础层：ERC20 代币标准 + 自定义合约逻辑           | contracts / erc20 / custom |
| **dex**       | `dex/swap/`、`dex/liquidation/`、`dex/nft/` | DEX 业务层：交易核心 + 清算 + NFT              | dex / swap / liquidation / nft |
| **cex**       | `cex/fund/`、`cex/order/`、`cex/risk/` | CEX 业务层：资金链路 + 订单系统 + 风控体系             | cex / cex_fund / cex_order / cex_risk |
| **security**  | `security/`                          | 通用安全层：重入、溢出、授权、代理升级、时间锁                   | security                   |

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

本项目提供 `run_tests.py` 作为统一的测试运行入口，支持按 **业务域（--project）** 一键运行：

```bash
# ============================================================
# 📦 方式一：按业务域一键运行（推荐，企业级常用）
# ============================================================
python3 run_tests.py -s --project contracts    # 合约基础层
python3 run_tests.py -s --project dex          # DEX 业务层
python3 run_tests.py -s --project cex          # CEX 中心化交易所
python3 run_tests.py -s --project cex_fund     # 只跑 CEX 资金链路
python3 run_tests.py -s --project security     # 安全测试
python3 run_tests.py -s --project all          # 全部业务域

# 查看所有可用业务域
python3 run_tests.py --list-projects

# ============================================================
# 🔍 方式二：业务域 + 优先级标记 组合筛选
# ============================================================
python3 run_tests.py -s --project cex -m "P0"            # CEX 所有 P0 用例
python3 run_tests.py -s --project contracts -m "P0"      # 合约层所有 P0

# ============================================================
# 🛠️  方式三：显式指定路径（优先级最高）
# ============================================================
python3 run_tests.py -s tests/contracts/erc20/scenarios/
python3 run_tests.py -s tests/cex/fund/scenarios/test_account.py::test_case_001_account_info

# ============================================================
# ⚙️ 其他常用参数
# ============================================================
python3 run_tests.py -s --network ethereum:local    # 指定网络
python3 run_tests.py -s --no-report                  # 不生成 Allure 报告
python3 run_tests.py --help                          # 查看全部帮助
python3 run_tests.py -s                          # 打印print
```

**备用方式**：直接使用 Ape 框架（不推荐）

```bash
# 运行全部测试
ape test

# 运行特定模块测试
ape test tests/contracts/erc20/scenarios/ -v

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

| 业务域         | 模块          | 用例数量 | 说明                        |
| ----------- | ----------- | ---- | ------------------------- |
| **contracts** | ERC20 基础标准  | 11   | 代币转账、授权、铸造、销毁、RBAC 权限     |
| **contracts** | 自定义业务合约     | 8    | 权限控制、参数配置、暂停恢复、黑名单        |
| **dex**       | DEX 去中心化交易所 | 11   | Swap、流动性添加/移除、滑点控制、手续费、多跳路由 |
| **dex**       | 清算业务        | 11   | 清算触发、流程、奖励、安全防护           |
| **dex**       | NFT/SFT     | 10   | ERC721/ERC1155 铸造、转账、交易场景 |
| **cex**       | CEX 资金链路    | 19   | 充币5 + 提币6 + 划转4 + 账户4（含资损/权限场景） |
| **cex**       | CEX 订单系统    | 9    | 现货下单/撤单/查询/撮合               |
| **cex**       | CEX 风控体系    | 4    | API 权限、IP 白名单、冻结、大额审核      |
| **security**  | 高阶安全场景      | 10   | 重入防护、整数溢出、授权安全、代理升级、时间锁  |
| 合计          |             | **93** |                           |

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

## 报告目录下起服务查allure的报告：

```
python -m http.server 8080
```

***

## 🤖 AI 集成规划

> 本章节说明测试框架与 AI 工具的集成思路和未来规划。

### 为什么当前不直接集成？

**核心判断**：AI 辅助测试的价值需要**真实业务数据**才能充分体现。当前框架处于建设初期，直接集成 AI 容易产生"伪效果"——AI 在缺乏真实场景约束下生成的用例和分析结果质量不稳定，无法体现 AI 的真正价值。

**采取的策略**：
1. **先搭框架，后接 AI**：优先完成测试框架的核心能力建设，确保测试用例、日志、数据的质量
2. **独立验证，双向对接**：AI 能力在独立的 `test-ai-rag-workflow` 仓库中验证，成熟后再对接主框架
3. **预留接口，平滑接入**：在框架设计时预留 AI 扩展点，未来可无侵入式集成

### 预留的 AI 扩展点

框架设计时已考虑 AI 集成需求，预留以下扩展接口（当前为设计规范，非代码实现）：

| 扩展点 | 位置 | 功能 | 对接时机 |
|-------|------|------|---------|
| **用例生成接口** | `framework/core/case_generator.py` | 接收 AI 生成的用例格式，自动转换为 pytest 测试代码 | 当 AI 用例生成准确率 > 85% 时 |
| **日志分析 Hook** | `framework/core/log_analyzer.py` | 测试执行失败时自动触发 AI 分析，返回根因和修复建议 | 当 Bad Case 知识库覆盖 > 80% 错误类型时 |
| **知识库对接点** | `framework/core/knowledge_base.py` | 将测试结果自动沉淀到 AI 知识库，形成闭环 | 当 CI/CD 流水线稳定运行后 |
| **智能数据工厂** | `framework/core/smart_data_factory.py` | 根据接口定义自动生成测试数据（边界值、异常值） | 当测试数据规范完善后 |

### AI 技术选型方向

| 场景 | 技术方案 | 选型理由 |
|------|---------|---------|
| **用例生成** | RAG + 知识库检索 | 基于历史用例格式生成，保证风格一致性 |
| **日志分析** | 分类模型 + 规则引擎 | 匹配已知错误模式，快速定位根因 |
| **智能推荐** | Embedding 相似度匹配 | 推荐相关测试用例和历史解决方案 |

### 与 AI 知识库仓库的关系

```
ape-demo (主框架)  ←→  test-ai-rag-workflow (AI 配置库)
     │                        │
     │  测试用例执行结果          │  AI 能力验证
     │  异常日志                │  用例生成效果
     │                        │  日志分析准确率
     └──────── 数据双向流通 ────────┘
```

**当前状态**：
- ✅ `test-ai-rag-workflow` 已完成三层架构（知识库 + Skills + Workflow）搭建
- ✅ 已沉淀 68 个 Golden Case 和 12 类 Bad Case
- ✅ 在用例生成、日志分析场景下验证通过
- ⏳ 待主框架稳定后，评估 AI 能力成熟度并决定集成时机

### 集成时机判断标准

当满足以下条件时，启动 AI 集成工作：

- [ ] 测试框架核心功能稳定（当前进行中）
- [ ] 测试用例覆盖核心业务场景（覆盖率 > 90%）
- [ ] AI 知识库沉淀足够样本（Golden Case > 100，Bad Case > 50）
- [ ] AI 用例生成准确率达到可接受水平（> 85%）
- [ ] Bad Case 知识库覆盖主要错误类型（> 80%）

### 扩展阅读

AI 辅助测试的详细实现和效果评估，请参考：
- [test-ai-rag-workflow 仓库](https://github.com/liuyoushan/test-ai-rag-workflow)
- [AI 知识库设计文档](https://github.com/liuyoushan/test-ai-rag-workflow/tree/main/knowledge_base)
- [AI Skills 定义](https://github.com/liuyoushan/test-ai-rag-workflow/tree/main/skills)

***

## 相关资源

- [ApeWorX 官方文档](https://docs.apeworx.io/)
- [合约/DEX 用例清单](case_list)
- [CEX 用例清单（28 接口 + 4 资损场景）](cex_case_list)
- [合约源码目录](contracts/)
- [AI 辅助测试仓库](https://github.com/liuyoushan/test-ai-rag-workflow)

