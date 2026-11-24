"""日志配置模块。

基于 loguru 配置控制台与文件日志输出，文件保存在 backend/logs/ 目录。
"""
import sys
from pathlib import Path

from loguru import logger

# 日志目录（兼容 Windows 路径）
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 日志文件路径
LOG_FILE = LOG_DIR / "app.log"
ROTATION_FILE = LOG_DIR / "app_{time:YYYY-MM-DD}.log"


def setup_logging() -> None:
    """配置 loguru 日志。

    - 控制台输出：彩色、DEBUG 级别（生产环境为 INFO）。
    - 文件输出：按天滚动，保留 14 天，UTF-8 编码。
    """
    # 清除默认 handler
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stderr,
        level="DEBUG",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # 文件输出（按天滚动）
    logger.add(
        str(ROTATION_FILE),
        level="INFO",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
            "{name}:{function}:{line} | {message}"
        ),
        rotation="00:00",  # 每天 0 点滚动
        retention="14 days",
        encoding="utf-8",
        enqueue=True,  # 多进程安全
    )

    # 错误日志单独文件
    logger.add(
        str(LOG_DIR / "error_{time:YYYY-MM-DD}.log"),
        level="ERROR",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
            "{name}:{function}:{line} | {message}"
        ),
        rotation="00:00",
        retention="30 days",
        encoding="utf-8",
        enqueue=True,
    )


# 模块导入即配置默认日志（确保 logger 可用）
setup_logging()
