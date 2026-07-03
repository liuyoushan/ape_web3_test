#!/bin/bash
# ==============================================================================
# 企业级主网分叉节点启动脚本
# ==============================================================================
# 功能特性：
#   - 支持多个 RPC 提供商（Infura/Alchemy/DRPC）
#   - 支持块号锁定（避免链重组）
#   - 自动检测并终止残留进程
#   - 彩色日志输出
#   - 详细的启动信息展示
#   - 主网链 ID 模拟（chain-id: 1）
# ==============================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
DEFAULT_RPC_URL="https://eth.drpc.org"
DEFAULT_BLOCK_NUMBER="19500000"  # 固定块号，避免链重组
DEFAULT_BALANCE="100000"          # 每个测试账户 ETH 余额
DEFAULT_PORT="8545"
DEFAULT_HOST="0.0.0.0"
DEFAULT_CHAIN_ID="1"              # 主网链 ID

# 读取环境变量配置
RPC_URL="${WEB3_RPC_URL:-$DEFAULT_RPC_URL}"
BLOCK_NUMBER="${WEB3_BLOCK_NUMBER:-$DEFAULT_BLOCK_NUMBER}"
BALANCE="${WEB3_BALANCE:-$DEFAULT_BALANCE}"
PORT="${WEB3_PORT:-$DEFAULT_PORT}"
HOST="${WEB3_HOST:-$DEFAULT_HOST}"
CHAIN_ID="${WEB3_CHAIN_ID:-$DEFAULT_CHAIN_ID}"

# 检查 anvil 是否安装
if ! command -v anvil &> /dev/null; then
    echo -e "${RED}❌ 错误：anvil 未安装${NC}"
    echo "请运行: curl -L https://foundry.paradigm.xyz | bash"
    echo "然后重新打开终端"
    exit 1
fi

# 终止残留进程
echo -e "${YELLOW}ℹ️ 正在清理残留进程...${NC}"
pkill -f "anvil.*--port $PORT" 2>/dev/null
sleep 1

# 显示启动配置
echo -e "\n${BLUE}==============================================${NC}"
echo -e "${BLUE}          主网 Fork 节点启动配置${NC}"
echo -e "${BLUE}==============================================${NC}"
echo -e "${YELLOW}RPC 端点:${NC} $RPC_URL"
echo -e "${YELLOW}锁定块号:${NC} $BLOCK_NUMBER"
echo -e "${YELLOW}链 ID:${NC} $CHAIN_ID"
echo -e "${YELLOW}账户余额:${NC} $BALANCE ETH"
echo -e "${YELLOW}监听端口:${NC} $PORT"
echo -e "${YELLOW}监听地址:${NC} $HOST"
echo -e "${BLUE}==============================================${NC}\n"

# 启动 fork 节点
echo -e "${GREEN}🚀 启动主网 Fork 节点...${NC}"
echo -e "${YELLOW}提示: 按 Ctrl+C 停止节点${NC}\n"

anvil \
  --fork-url "$RPC_URL" \
  --fork-block-number "$BLOCK_NUMBER" \
  --chain-id "$CHAIN_ID" \
  --balance "$BALANCE" \
  --port "$PORT" \
  --host "$HOST" \
  --silent 2>&1 | while read line; do
    # 添加时间戳和颜色
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    if echo "$line" | grep -q "Listening on"; then
        echo -e "${GREEN}[${timestamp}] $line${NC}"
    elif echo "$line" | grep -q "Error"; then
        echo -e "${RED}[${timestamp}] $line${NC}"
    else
        echo -e "${BLUE}[${timestamp}] $line${NC}"
    fi
done
