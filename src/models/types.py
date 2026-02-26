#!/usr/bin/env python3
"""
类型定义模块
"""

from typing import TypedDict
from datetime import datetime


class WeekParams(TypedDict, total=False):
    """周参数类型定义"""
    report_date: str
    week_monday: str
    week_saturday: str
    week_offset: int
    database_id: int


class ColumnMappings(TypedDict):
    """列名映射配置类型"""
    traffic: dict
    revenue: dict
    engagement: dict
    retention: dict
