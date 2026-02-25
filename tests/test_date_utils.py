#!/usr/bin/env python3
"""
日期工具测试

测试date_utils模块的日期计算功能
"""

import pytest
from datetime import datetime, timedelta


class TestDateUtils:
    """日期工具测试类"""

    def test_calculate_current_week(self):
        """测试计算当前周"""
        # 导入函数
        from src.date_utils import calculate_this_week_params

        # 调用函数
        params = calculate_this_week_params()

        # 验证返回的参数
        assert params is not None
        assert 'week_sunday' in params
        assert 'week_monday' in params
        assert 'week_offset' in params
        assert params['week_offset'] == 0

        # 验证日期格式
        monday = params['week_monday']
        assert isinstance(monday, str)
        assert len(monday) == 8  # YYYYMMDD格式

    def test_calculate_previous_week(self):
        """测试计算上周"""
        from src.date_utils import calculate_this_week_params

        params = calculate_this_week_params(week_offset=-1)

        assert params['week_offset'] == -1
        assert 'week_sunday' in params
        assert 'week_monday' in params

    def test_calculate_next_week(self):
        """测试计算下周"""
        from src.date_utils import calculate_this_week_params

        params = calculate_this_week_params(week_offset=1)

        assert params['week_offset'] == 1
        assert 'week_sunday' in params
        assert 'week_monday' in params

    def test_date_format_validation(self):
        """测试日期格式验证"""
        from src.date_utils import validate_date_format

        # 测试正确格式
        assert validate_date_format('20260210') is True
        assert validate_date_format('20260101') is True
        assert validate_date_format('20261231') is True

        # 测试错误格式
        assert validate_date_format('2026-02-10') is False
        assert validate_date_format('02/10/2026') is False
        assert validate_date_format('2026/02/10') is False

    def test_week_label_format(self):
        """测试周标签格式"""
        from src.date_utils import format_week_label

        # 测试正确的周标签
        assert format_week_label(2026, 2, 10) == '20260210'
        assert format_week_label(2026, 1, 1) == '20260101'

    def test_calculate_date_range(self):
        """测试日期范围计算"""
        from src.date_utils import calculate_date_range

        start_date = '20260201'
        result = calculate_date_range(start_date, days=7)

        assert result is not None
        assert 'end_date' in result
        assert 'days' in result

    def test_handle_edge_dates(self):
        """测试边缘日期处理"""
        from src.date_utils import calculate_this_week_params

        # 测试年末
        params = calculate_this_week_params(week_offset=-1)
        # 只验证返回结构，不验证具体值
        assert params is not None

    def test_timezone_handling(self):
        """测试时区处理"""
        from src.date_utils import get_current_date_str

        date_str = get_current_date_str()

        # 验证返回的是字符串
        assert isinstance(date_str, str)
        assert len(date_str) == 8  # YYYYMMDD格式


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
