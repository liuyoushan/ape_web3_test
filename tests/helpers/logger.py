"""
==============================================================================
企业级日志模块 - 基于 Python 标准 logging 库
==============================================================================
支持特性：
  - 四级日志级别：DEBUG / INFO / WARNING / ERROR
  - CLI 彩色输出（支持 ANSI）
  - 可配置：环境变量控制级别、持久化文件
  - 双输出：同时支持 stdout 彩色 + 文件持久化
  - 兼容 Allure 装饰器风格调用

快速接入：
    >>> from tests.helpers.logger import get_logger, log
    >>> log.debug("状态: %s", "ok")      # 蓝色  [DEBUG]
    >>> log.info("步骤完成")              # 绿色  [INFO]
    >>> log.warning("边界情况")           # 黄色  [WARNING]
    >>> log.error("异常发生")             # 红色  [ERROR]

环境变量配置：
    # 级别过滤：DEBUG | INFO | WARNING | ERROR
    export WEB3_TEST_LOG_LEVEL=INFO

    # 持久化到文件（同时保留 stdout）
    export WEB3_TEST_LOG_FILE=./run.log
"""

import logging
import os
import sys
from datetime import datetime


# ======================================
# 常量定义
# ======================================

LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
}

# ANSI 彩色编码（CLI 专用）
ANSI_COLORS = {
    'DEBUG': '\033[94m',      # 蓝色
    'INFO': '\033[92m',       # 绿色
    'WARNING': '\033[93m',    # 黄色
    'ERROR': '\033[91m',      # 红色
    'RESET': '\033[0m',       # 重置
}

# 全局 logger 单例
_LOGGER = None


# ======================================
# Formatter：彩色输出 vs 文件持久化
# ======================================

class _ColoredConsoleFormatter(logging.Formatter):
    """用于 stdout 控制台，支持彩色前缀"""

    def format(self, record):
        raw = super().format(record)
        level = record.levelname
        color = ANSI_COLORS.get(level, ANSI_COLORS['RESET'])
        reset = ANSI_COLORS['RESET']
        return f"{color}[{level}] {raw}{reset}"


class _PlainFileFormatter(logging.Formatter):
    """用于文件持久化，不染色但带时间戳"""

    def __init__(self):
        super().__init__(
            '%(asctime)s | %(levelname)-7s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


# ======================================
# 工厂：获取全局统一 logger
# ======================================

def get_logger(name='chain_game_fi_logger'):
    """
    返回全局统一配置的 logger（单例）
    """
    global _LOGGER

    if _LOGGER is not None:
        # 已初始化直接返回
        for h in _LOGGER.handlers:
            h.acquire()
            h.release()
        return _LOGGER

    # ======================================
    # 第一次初始化：从环境变量读配置
    # ======================================
    logger = logging.getLogger(name)
    logger.propagate = False

    level_str = os.environ.get('WEB3_TEST_LOG_LEVEL', 'DEBUG').upper()
    log_file = os.environ.get('WEB3_TEST_LOG_FILE')

    effective_level = LOG_LEVELS.get(level_str, logging.DEBUG)
    logger.setLevel(effective_level)

    # 基础格式化（只打印消息本身，前缀由 formatter 加）
    msg_formatter = logging.Formatter('%(message)s')

    # ======================================
    # Handler 1: stdout 彩色输出
    # ======================================
    console_h = logging.StreamHandler(sys.stdout)
    console_h.setLevel(effective_level)

    if sys.stdout.isatty():
        # 真终端启用彩色
        console_h.setFormatter(_ColoredConsoleFormatter('%(message)s'))
    else:
        # 管道/CI 环境用无色前缀
        console_h.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))

    logger.addHandler(console_h)

    # ======================================
    # Handler 2: 文件持久化（环境变量启用时）
    # ======================================
    if log_file:
        try:
            parent = os.path.dirname(log_file)
            if parent and not os.path.isdir(parent):
                os.makedirs(parent, exist_ok=True)

            file_h = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            file_h.setLevel(effective_level)
            file_h.setFormatter(_PlainFileFormatter())
            logger.addHandler(file_h)
        except Exception:
            # 持久化失败也不影响主流程
            pass

    _LOGGER = logger
    return logger


# ======================================
# 快捷 API：log.debug / log.info 风格
# ======================================

class _LogProxy:
    """代理类，延迟初始化 logger"""

    def __init__(self):
        self._backing = None

    def _logger(self):
        if self._backing is None:
            self._backing = get_logger()
        return self._backing

    def debug(self, msg, *args, **kwargs):
        self._logger().debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._logger().info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._logger().warning(msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        self._logger().warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._logger().error(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self._logger().exception(msg, *args, **kwargs)

    def step(self, title):
        """步骤：同时输出 INFO 级日志（兼容测试流程输出风格）"""
        self._logger().info("---------- %s ----------", title)


# 默认全局快捷实例
log = _LogProxy()
