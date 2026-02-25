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
        from src.date_utils import calculate_week_params

        # 调用函数
        params = calculate_week_params()

        # 验证返回的参数
        assert params is not None
        assert 'week_sunday' in params
        assert 'week_saturday' in params
        assert 'week_offset' in params
        assert params['week_offset'] == 0

        # 验证日期格式
        monday = params['week_monday']
        assert isinstance(monday, str)
        assert len(monday) == 8  # YYYYMMDD格式

    def test_calculate_previous_week(self):
        """测试计算上周"""
        from src.date_utils import calculate_week_params

        params = calculate_week_params(week_offset=-1)

        assert params['week_offset'] == -1
        assert 'week_sunday' in params
        assert 'week_saturday' in params
        assert 'week_monday' in params

    def test_calculate_next_week(self):
        """测试计算下周"""
        from src.date_utils import calculate_week_params

        params = calculate_week_params(week_offset=1)

        assert params['week_offset'] == 1
        assert 'week_sunday' in params
        assert 'week_saturday' in params
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

    def test_calculate_specific_date_week(self):
        """测试指定日期的周计算"""
        from src.date_utils import calculate_week_params

        # 测试指定日期的周
        params = calculate_week_params(target_date='20260210')

        assert params is not None
        assert 'report_date' in params
        assert '2026-02' in params['report_date']

    def test_format_date_display(self):
        """测试日期格式化显示"""
        from src.date_utils import calculate_week_params, format_date_display

        params = calculate_week_params()
        display = format_date_display(params)

        assert isinstance(display, str)
        assert '本周' in display

        params_next = calculate_week_params(week_offset=1)
        display_next = format_date_display(params_next)
        assert '下周' in display_next

    def test_get_week_range_from_date(self):
        """测试从日期获取周范围"""
        from src.date_utils import get_week_range_from_date

        monday, sunday = get_week_range_from_date('20260210')

        assert isinstance(monday, str)
        assert isinstance(sunday, str)
        assert len(monday) == 8
        assert len(sunday) == 8
        assert monday < sunday

    def test_handle_edge_dates(self):
        """测试边缘日期处理"""
        from src.date_utils import calculate_week_params

        # 测试年末
        params = calculate_week_params(target_date='20261231')

        # 只验证返回结构，不验证具体值
        assert params is not None
        assert 'week_sunday' in params

    def test_all_date_params_present(self):
        """测试所有日期参数都存在"""
        from src.date_utils import calculate_week_params

        params = calculate_week_params()

        # 验证所有必需的参数
        required_keys = [
            'week_monday', 'week_saturday', 'week_sunday',
            'last_week_monday', 'last_week_saturday', 'last_week_sunday',
            'partition_start', 'partition_end',
            'snapshot_date', 'history_start_date',
            'pay_start_date', 'pay_end_date',
            'report_date', 'week_offset'
        ]

        for key in required_keys:
            assert key in params, f"缺少必需的日期参数: {key}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
