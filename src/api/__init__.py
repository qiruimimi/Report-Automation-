#!/usr/bin/env python3
"""
API 基础设施
"""

from typing import Protocol, runtime_checkable

from src.logger import get_logger

logger = get_logger('api')


class APIClient(Protocol):
    """API 客户端接口"""

    @runtime_checkable
    def fetch_section_data(self, section: str, params: dict) -> list:
        """获取某部分数据"""
        raise NotImplementedError

    def execute_sql(self, sql_query: str, params: dict) -> list:
        """执行 SQL 查询"""
        raise NotImplementedError
