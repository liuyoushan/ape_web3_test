# Web3 智能合约自动化测试实战（ApeWorX 企业级方案）

**📌 简历亮点关键词**：智能合约测试 | ApeWorX | Pytest | ERC20 | DEX | RBAC权限 | 链上事件断言 | YAML数据驱动 | Foundry/Anvil

---

## 📋 项目定位与亮点

本项目是一套**面向 Web3 中级岗面试/企业落地**的标准化智能合约测试方案，系统性覆盖区块链核心业务场景：

| 维度 | 实现亮点 |
|------|----------|
| **测试框架** | ApeWorX + Pytest 企业级自动化测试体系 |
| **合约覆盖** | ERC20(RBAC)、Uniswap 式 DEX(Factory/Pair/Router)、暂停/黑白名单自定义合约 |
| **用例设计** | P0 面试核心考点 → P1 进阶安全场景，分层分级 |
| **断言体系** | 链上事件校验、余额变化、权限边界、异常 revert 全维度 |
| **架构设计** | Fixture 工厂 + YAML 数据驱动 + 断言助手，完全解耦便于协作/AI生成 |

---

## 🏗️ 项目架构

```
ape-demo/
├── ape-config.yaml          # 多链网络配置（Local/Mainnet-Fork/Polygon）、编译器优化
├── contracts/               # Solidity 合约实现
│   ├── MyERC20.sol         # OpenZeppelin + RBAC 三角色分立（Minter/Pauser/Admin）
│   ├── MiniSwapFactory.sol # DEX 工厂合约（Pair 创建/管理）
│   ├── MiniSwapPair.sol    # 交易对合约（K值守恒/0.3%手续费）
│   ├── MiniSwapRouter.sol  # 路由合约（滑点控制/多币兑换）
│   └── HelloWorld.sol
├── scripts/
│   └── deploy.py           # 合约部署脚本
├── tests/
│   ├── conftest.py         # pytest 共享入口（accounts + Fixtures 统一导出）
│   ├── data/                # YAML 测试数据集（参数与代码分离）
│   ├── fixtures/            # Fixture 工厂层（合约部署/工具函数封装）
│   ├── helpers/             # 断言助手层（可复用验证逻辑抽离）
│   ├── test_erc20.py        # ERC20 核心测试（≈面试题标准答案级）
│   ├── test_dex_swap.py     # DEX 兑换/流动性测试
│   ├── test_contract_custom.py  # 业务合约通用场景
│   ├── test_swap_custom_func.py # DEX 高阶流程
│   └── test_security_advanced.py # 安全场景
└── case_list                # P0/P1 分级用例清单（≈面试考点提纲）
```

### 核心模块职责

| 模块 | 职责 | AI 编程提示 |
|------|------|-------------|

---

## 🏗️ 项目架构

```
ape-demo/
├── ape-config.yaml          # Ape 框架配置文件（多链网络、测试、编译器配置）
├── contracts/               # 智能合约目录
│   ├── MyERC20.sol         # RBAC 权限控制的 ERC20 代币合约
│   ├── MiniSwapFactory.sol # DEX 工厂合约
│   ├── MiniSwapPair.sol    # DEX 交易对合约
│   ├── MiniSwapRouter.sol  # DEX 路由合约
│   └── HelloWorld.sol      # 入门示例合约
├── scripts/                 # 部署和交互脚本
│   └── deploy.py           # 合约部署脚本
├── tests/                   # 测试用例根目录
│   ├── conftest.py         # pytest 共享 Fixture 配置入口
│   ├── data/                # 测试数据目录（YAML 格式）
│   │   ├── test_erc20.yaml
│   │   ├── test_dex_swap.yaml
│   │   ├── test_nft.yaml
│   │   ├── test_contract_custom.yaml
│   │   └── ...
│   ├── fixtures/            # Fixture 工厂模块
│   │   ├── token_fixture.py      # ERC20 相关 Fixture
│   │   ├── dex_fixture.py        # DEX 相关 Fixture
│   │   └── contract_custom_fixture.py  # 自定义合约 Fixture
│   ├── helpers/             # 测试助手模块
│   │   ├── assertions.py    # 标准化断言函数
│   │   └── formatters.py    # 格式转换工具函数
│   ├── test_erc20.py        # ERC20 代币测试用例集
│   ├── test_dex_swap.py     # DEX 交易所测试用例集
│   ├── test_nft.py          # NFT/SFT 测试用例集
│   ├── test_contract_custom.py # 自定义业务合约测试
│   ├── test_swap_custom_func.py # DEX 自定义流程测试
│   └── test_security_advanced.py # 高阶安全场景测试
├── start_local_node.sh      # 本地测试节点启动脚本
└── case_list                # 完整测试用例清单（P0/P1 分级）
```

### 核心模块职责

| 模块 | 职责 | AI 编程提示 |
|------|------|-------------|
| `tests/data/*.yaml` | 存储测试参数（金额、地址、期望结果） | 新增用例先在此定义数据，代码引用 `xxx_test_data["case_xxx"]` |
| `tests/fixtures/` | 合约部署、工具函数、共享上下文 | 通用逻辑在此封装，测试文件直接 import 使用 |
| `tests/helpers/assertions.py` | 可复用断言函数 | 重复验证逻辑抽离到此，保持用例简洁 |
| `tests/conftest.py` | pytest 共享入口 | 所有 fixtures 在此统一导出，用例文件无需重复导入 |

---

## 🎯 用例风格规范

### 1. 命名规范

**测试文件命名**：`test_{业务域}.py`
- 示例：`test_erc20.py`、`test_dex_swap.py`

**测试函数命名**：`test_{业务域}_{编号}_{描述性名称}`
- 示例：`test_erc20_001_metadata_verification`
- 示例：`test_dex_010_swap_tokenA_to_tokenB`

### 2. 文件头部规范

```python
"""
==============================================================================
【模块概览】ERC20 同质化代币 基础标准用例
对应用例编号：case_001 ~ case_010
测试范围：MyERC20 合约核心功能（元数据、转账、授权、铸币、销毁）
==============================================================================
"""
import pytest
from ape.exceptions import ContractLogicError, VirtualMachineError
from tests.helpers.assertions import (
    assert_token_metadata,
    assert_balance,
    assert_transfer_event
)
```

### 3. 单条用例完整模板

```python
# ==============================================================================
# case_001 代币基础信息校验
# 测试目标：验证合约元数据（名称、符号、小数位数、初始总发行量）
# 测试类型：P0 - 功能测试 / 正向测试
# ==============================================================================
def test_erc20_001_metadata_verification(token, deployer, user1, erc20_test_data):
    """
    ==============================================================================
    【用例编号】case_001
    【用例名称】代币基础信息校验
    【测试目标】验证合约部署后元数据字段正确性
    【测试类型】P0 - 功能测试 / 正向测试
    ==============================================================================
    
    测试流程详解：
    ┌───────────────────────────────────────────────────────────────────────┐
    │ 步骤1: 加载测试数据    从 YAML 读取预期值                            │
    │ 步骤2: 调用合约方法    读取 token.name()/symbol()/decimals()        │
    │ 步骤3: 断言验证        实际值与期望值逐一比对                         │
    └───────────────────────────────────────────────────────────────────────┘
    
    核心验证点：
    1. name 与预期一致
    2. symbol 与预期一致
    3. decimals 固定为 18
    4. 地址格式符合以太坊规范（0x 开头，长度 42）
    
    数据来源：tests/data/test_erc20.yaml -> common
    """
    # ==================== 步骤1: 加载测试数据 ====================
    data = erc20_test_data["common"]
    
    # ==================== 步骤2 & 3: 调用方法 & 断言验证 ====================
    assert_token_metadata(
        token=token,
        expected_name=data["token_name"],
        expected_symbol=data["token_symbol"],
        expected_decimals=data["expected_decimals"],
        expected_supply=data["expected_initial_supply"]
    )
    
    assert_address_format(token.address)
    
    # DEBUG 输出（关键节点日志）
    print("[DEBUG] 代币元数据校验完成:")
    print(f"  - name: {token.name()}")
    print(f"  - symbol: {token.symbol()}")
```

### 4. YAML 测试数据格式

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

case_004_approve:
  approve_amount: "500 ether"
```

### 5. 异常/负向测试模板

```python
def test_erc20_003_insufficient_balance_transfer(token, deployer, user1):
    """
    余额不足异常转账测试
    
    验证当转账金额超过余额时：
    - 交易 revert（ContractLogicError/VirtualMachineError）
    - 转账双方余额不变
    - totalSupply 不变
    """
    token = mint_token(token, deployer, deployer, "1000 ether")
    transfer_amount = parse_ether("2000 ether")  # 超过余额
    
    balance_before = token.balanceOf(deployer)
    
    # 关键：用 pytest.raises 捕获异常
    with pytest.raises((ContractLogicError, VirtualMachineError)):
        token.transfer(user1, transfer_amount, sender=deployer)
    
    # 异常后状态不变断言
    assert token.balanceOf(deployer) == balance_before
```

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+（用于 Anvil 节点）

### 安装依赖

```bash
# 安装 ApeWorX 框架
pip install eth-ape

# 安装项目依赖（根据 requirements.txt）
pip install -r requirements.txt  # 如有

# 安装 Ape 插件
ape plugins install solidity anvil
```

### 运行测试

```bash
# 运行全部测试
ape test

# 运行特定模块测试
ape test tests/test_erc20.py -v

# 运行特定用例（按函数名匹配）
ape test -k "test_erc20_001" -v

# 显示 print 输出
ape test -s

# 启动本地节点（单独终端）
./start_local_node.sh
```

---

## 📚 用例优先级与面试考点映射

### 🔥 P0 - Web3 测试岗核心考点（≈80% 面试题来源）

**目标：对标中级岗日常工作 + 技术面高频题**

| 业务域 | 覆盖场景 | 对应面试题原型 |
|--------|----------|---------------|
| **ERC20** | 元数据、转账、余额不足 revert、Approve/TransferFrom 授权流转、Mint/Burn | "说下 ERC20 的标准方法有哪些？" / "transfer vs transferFrom 区别？" |
| **DEX** | TokenA↔TokenB 双向兑换、添加/移除流动性、K 值守恒校验、滑点边界 | "Uniswap V2 的 x×y=k 公式理解？" / "LP 代币怎么算？" |
| **权限控制** | onlyOwner 校验、RBAC 三角色分离（Minter/Pauser/Admin）、暂停/恢复 | "合约权限怎么设计？" / "怎么防止未授权调用？" |
| **异常分支** | 余额不足、授权不足、零地址、合约暂停态下拒交易 | "写测试时你主要 cover 哪些异常场景？" |
| **全链路** | 授权→铸币→转账→销毁，事件日志（Transfer/Approval）精准校验 | "链上事件怎么取？你断言哪些维度？" |

---

### 💎 P1 - 加分项 / 源码级深度场景

**目标：区别于普通候选人，体现对协议/安全的深度理解**

1. **DEX 高阶**：多路由跨池兑换（A→C→B）、大额交易滑点极值校验
2. **安全场景**：重入攻击防护校验、整数溢出/下溢边界、零地址拦截
3. **权限进阶**：Ownable→RBAC 平滑迁移、权限撤销后立即失效
4. **异常兼容**：低 Gas / 超限 Gas 交易失败原子性、主网 Fork 测试
5. **跨域适配**：多链参数格式兼容、链上事件→链下解析数据对齐

---

## 🤖 AI 编程协作指南

### 新增用例 SOP（AI 遵循此流程）

1. **检查 YAML 数据**：先看 `tests/data/` 对应文件是否已有所需参数
2. **检查 Fixture**：看 `tests/fixtures/` 是否有可复用的合约部署/工具函数
3. **检查断言助手**：看 `tests/helpers/assertions.py` 是否有现成断言
4. **复制模板**：从现有用例复制结构，保持注释风格统一
5. **数据驱动**：所有可变参数从 YAML 读取，不要硬编码 magic number
6. **DEBUG 输出**：关键节点加 `print("[DEBUG] ...")`，便于定位问题
7. **链式断言**：先验证正向路径，再异常分支，最后事件校验

### 代码风格统一要求

- 缩进：4 空格
- 引号：双引号优先
- 分行：长参数按 pep8 换行对齐
- 注释：每个测试函数必须有 docstring 说明业务意图
- 变量名：见名知意，`balance_before` / `receipt` / `mint_amount`

---

## 📄 配置文件说明

核心配置见 [ape-config.yaml](ape-config.yaml)：

- `plugins`: Solidity 编译器、Anvil 节点、Etherscan 验证
- `ethereum`: 多链网络（local/mainnet-fork/goerli/polygon）
- `test`: 测试助记词、账户数量、主网分叉固定区块号
- `compiler`: Solc 版本锁定、优化器配置
- `dependencies`: OpenZeppelin 等第三方依赖库

---

## 🔗 相关链接

- [ApeWorX 官方文档](https://docs.apeworx.io/)
- [案例清单 - 完整用例分级](case_list)
- [Solidity 合约目录](contracts/)
