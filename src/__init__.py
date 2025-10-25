"""ReasoningBank MCP 服务器包"""
__version__ = "0.1.0"
__author__ = "Your Name"
__description__ = "Memory-augmented reasoning for AI agents via MCP"

from .config import load_config, get_config
# 注意：为了避免循环导入和RuntimeWarning，不从server模块导入ReasoningBankServer和main

# 为了脚本入口点，我们需要导入run_server函数
from .server import run_server

__all__ = [
    "load_config",
    "get_config",
    "run_server",  # 为脚本入口点导出
]