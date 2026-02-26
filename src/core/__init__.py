#!/usr/bin/env python3
"""
核心业务逻辑层
"""

from .config import ConfigManager
from .analyzer import Analyzer  # 将在后续创建
from .generator import ReportGenerator  # 将在后续创建

from src.logger import get_logger

logger = get_logger('core')
