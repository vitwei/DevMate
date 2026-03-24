"""日志配置模块.

配置统一的日志输出格式和级别.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
    level: int = logging.INFO,
    log_file: str | None = None,
    error_log_file: str | None = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """设置日志配置.

    Args:
        level: 日志级别
        log_file: 普通日志文件路径，默认使用 logs/devmate.log
        error_log_file: 错误日志文件路径，默认使用 logs/error.log
        max_bytes: 单个日志文件最大大小（字节）
        backup_count: 保留的备份文件数量
    """
    root_logger = logging.getLogger()

    if root_logger.handlers:
        return

    root_logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if log_file is None:
        log_file = "logs/devmate.log"

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    if error_log_file is None:
        error_log_file = "logs/error.log"

    error_log_path = Path(error_log_file)
    error_log_path.parent.mkdir(parents=True, exist_ok=True)
    error_file_handler = RotatingFileHandler(
        error_log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    root_logger.addHandler(error_file_handler)


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器.

    Args:
        name: 日志记录器名称，通常为模块名

    Returns:
        配置好的 Logger 实例
    """
    return logging.getLogger(name)
