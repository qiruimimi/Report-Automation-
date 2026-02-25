#!/usr/bin/env python3
"""
Pytest配置文件

配置测试环境和fixtures
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_traffic_data():
    """流量测试数据fixture"""
    return [
        {
            'new_visitors': 10000,
            'registrations': 5000,
            'conversion_rate': 50.0
        }
    ]


@pytest.fixture
def sample_revenue_data():
    """收入测试数据fixture"""
    return [
        {
            'total_revenue': 100000,
            'renewal_revenue': 60000,
            'new_signing_revenue': 40000
        }
    ]


@pytest.fixture
def sample_engagement_data():
    """活跃测试数据fixture"""
    return [
        {
            'wau': 50000,
            'new_user_wau': 20000,
            'old_user_wau': 30000
        }
    ]


@pytest.fixture
def sample_retention_data():
    """留存测试数据fixture"""
    return [
        {
            'new_user_retention_rate': 45.0,
            'old_user_retention_rate': 60.0
        }
    ]


@pytest.fixture
def sample_activation_data():
    """激活测试数据fixture"""
    return [
        {
            'step1_rate': 80.0,
            'step2_rate': 60.0,
            'step3_rate': 30.0,
            'step4_rate': 25.0
        }
    ]


@pytest.fixture
def empty_data():
    """空数据fixture"""
    return []


@pytest.fixture
def logger():
    """日志fixture"""
    from src.logger import get_logger
    return get_logger('test')
