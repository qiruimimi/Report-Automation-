#!/usr/bin/env python3
"""
日志配置模块

提供统一的日志配置，支持彩色控制台输出和文件日志
"""

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

try:
    from colorlog import ColoredFormatter
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


def setup_logging(
    name: str = 'weekly_report',
    level: str = 'INFO',
    log_file: Optional[str] = None,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    console_colors: bool = True
) -> logging.Logger:
    """
    配置日志系统

    Args:
        name: 日志记录器名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径（可选）
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的日志文件备份数量
        console_colors: 是否在控制台使用彩色输出

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 避免重复添加handler
    if logger.handlers:
        logger.handlers.clear()

    # 定义日志格式
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    if console_colors and HAS_COLORLOG:
        # 使用彩色日志
        color_format = '%(log_color)s%(asctime)s - %(levelname)s - %(message)s'
        console_formatter = ColoredFormatter(
            color_format,
            datefmt=date_format,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    else:
        # 普通日志
        console_formatter = logging.Formatter(log_format, datefmt=date_format)

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 文件处理器（如果指定）
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别

        # 文件使用详细格式
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt=date_format
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = 'weekly_report') -> logging.Logger:
    """
    获取已配置的日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        logging.Logger: 日志记录器实例
    """
    logger = logging.getLogger(name)

    # 如果记录器还没有handler，使用默认配置
    if not logger.handlers:
        return setup_logging(name)

    return logger


class LoggerContext:
    """
    日志上下文管理器

    用于在特定操作中添加上下文信息到日志中
    """

    def __init__(self, logger: logging.Logger, context: str):
        self.logger = logger
        self.context = context
        self.original_handlers = None

    def __enter__(self):
        # 添加上下文前缀到日志格式
        for handler in self.logger.handlers:
            if isinstance(handler.formatter, logging.Formatter):
                old_format = handler.formatter._fmt
                handler.formatter._fmt = f"[{self.context}] {old_format}"
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 恢复原日志格式
        for handler in self.logger.handlers:
            if isinstance(handler.formatter, logging.Formatter):
                formatter = handler.formatter
                if formatter._fmt.startswith(f"[{self.context}] "):
                    formatter._fmt = formatter._fmt[len(f"[{self.context}] "):]


def log_execution_summary(logger: logging.Logger, stats: dict):
    """
    记录执行摘要

    Args:
        logger: 日志记录器
        stats: 执行统计信息字典
            {
                'start_time': datetime,
                'end_time': datetime,
                'sections_updated': list,
                'sections_failed': list,
                'confluence_updated': bool
            }
    """
    duration = (stats['end_time'] - stats['start_time']).total_seconds()

    logger.info("=" * 60)
    logger.info("执行摘要")
    logger.info("=" * 60)
    logger.info(f"执行时长: {duration:.2f}秒")
    logger.info(f"更新成功: {len(stats['sections_updated'])}个部分")
    logger.info(f"更新失败: {len(stats['sections_failed'])}个部分")

    if stats['sections_updated']:
        logger.info(f"  成功: {', '.join(stats['sections_updated'])}")

    if stats['sections_failed']:
        logger.error(f"  失败: {', '.join(stats['sections_failed'])}")

    logger.info(f"Confluence更新: {'✅ 成功' if stats['confluence_updated'] else '❌ 失败'}")
    logger.info("=" * 60)


if __name__ == "__main__":
    # 测试日志配置
    print("测试日志配置模块\n")

    logger = setup_logging(log_file=None, console_colors=True)

    logger.debug("这是一条DEBUG消息")
    logger.info("这是一条INFO消息")
    logger.warning("这是一条WARNING消息")
    logger.error("这是一条ERROR消息")
    logger.critical("这是一条CRITICAL消息")

    # 测试上下文管理器
    with LoggerContext(logger, "数据获取"):
        logger.info("使用上下文管理器的日志消息")

    # 测试执行摘要
    from datetime import datetime

    summary_stats = {
        'start_time': datetime.now(),
        'end_time': datetime.now(),
        'sections_updated': ['traffic', 'activation', 'revenue'],
        'sections_failed': ['retention'],
        'confluence_updated': True
    }

    log_execution_summary(logger, summary_stats)
