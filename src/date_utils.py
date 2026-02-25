#!/usr/bin/env python3
"""
日期工具模块

提供周报所需的日期计算功能，支持任意周的日期参数计算
"""

from datetime import datetime, timedelta
from typing import Dict


def calculate_week_params(target_date: str = None, week_offset: int = 0) -> Dict:
    """
    计算周报所需的所有日期参数

    Args:
        target_date: 目标日期字符串 'YYYYMMDD'（默认为今天）
        week_offset: 周偏移量
                    0 = 当前周（默认）
                    1 = 下一周
                    -1 = 上一周
                    以此类推...

    Returns:
        dict: 包含所有日期参数的字典，包括：
            - week_monday: 本周一
            - week_saturday: 本周六
            - week_sunday: 本周日（周结束日）
            - last_week_monday: 上周一
            - last_week_saturday: 上周六
            - last_week_sunday: 上周日
            - partition_start: 数据分区起始日期
            - partition_end: 数据分区结束日期
            - snapshot_date: 快照日期（周日）
            - history_start_date: 历史数据起始日期（2个月前）
            - pay_start_date: 支付起始日期
            - pay_end_date: 支付结束日期
            - report_date: 格式化的报告日期 (YYYY-MM-DD)
            - week_offset: 周偏移量

    Examples:
        >>> # 本周（默认）
        >>> params = calculate_week_params()

        >>> # 下一周
        >>> params = calculate_week_params(week_offset=1)

        >>> # 指定日期的周
        >>> params = calculate_week_params(target_date='20260201')

        >>> # 下一周的指定日期
        >>> params = calculate_week_params(target_date='20260120', week_offset=1)
    """
    # 解析目标日期
    if target_date is None:
        target_date = datetime.now().date()
    else:
        target_date = datetime.strptime(target_date, '%Y%m%d').date()

    # 计算目标周日（周日为一周的最后一天）
    # Python的weekday(): Monday=0, Sunday=6
    days_until_sunday = 6 - target_date.weekday()
    week_sunday = target_date + timedelta(days=days_until_sunday)

    # 应用周偏移
    week_sunday = week_sunday + timedelta(weeks=week_offset)

    # 计算本周的周六和周一
    week_saturday = week_sunday - timedelta(days=1)
    week_monday = week_sunday - timedelta(days=6)

    # 计算上周日和周六（用于环比）
    last_week_sunday = week_sunday - timedelta(days=7)
    last_week_saturday = week_saturday - timedelta(days=7)
    last_week_monday = week_monday - timedelta(days=7)

    # 计算数据分区日期（需要包含整个周的数据）
    # 流量SQL需要提前一周的数据
    partition_end = week_sunday.strftime('%Y%m%d')
    partition_start = (week_monday - timedelta(days=7)).strftime('%Y%m%d')

    # 计算2个月前的日期（用于历史数据查询）
    # 用于激活和收入SQL的历史数据起始点
    two_months_ago = (week_sunday - timedelta(days=60)).strftime('%Y%m%d')

    return {
        # 本周日期
        'week_monday': week_monday.strftime('%Y%m%d'),
        'week_saturday': week_saturday.strftime('%Y%m%d'),
        'week_sunday': week_sunday.strftime('%Y%m%d'),

        # 上周日期（用于环比）
        'last_week_monday': last_week_monday.strftime('%Y%m%d'),
        'last_week_saturday': last_week_saturday.strftime('%Y%m%d'),
        'last_week_sunday': last_week_sunday.strftime('%Y%m%d'),

        # 数据分区日期（流量SQL使用）
        'partition_start': partition_start,
        'partition_end': partition_end,

        # 快照日期（激活、收入SQL使用）
        'snapshot_date': week_sunday.strftime('%Y%m%d'),

        # 历史数据起始日期（激活、收入SQL使用）
        'history_start_date': two_months_ago,

        # 支付日期范围（收入SQL使用）
        'pay_start_date': two_months_ago,
        'pay_end_date': week_saturday.strftime('%Y%m%d'),

        # 格式化的日期（用于报告标题）
        'report_date': week_saturday.strftime('%Y-%m-%d'),

        # 周偏移信息（用于日志）
        'week_offset': week_offset
    }


def format_date_display(params: Dict) -> str:
    """
    格式化日期参数为可读字符串（用于日志输出）

    Args:
        params: calculate_week_params返回的日期参数字典

    Returns:
        str: 格式化的日期信息
    """
    offset_desc = {
        0: "本周",
        1: "下周",
        -1: "上周",
    }.get(params['week_offset'], f"偏移{params['week_offset']}周")

    return (
        f"{offset_desc} ({params['week_monday']} ~ {params['week_saturday']})"
    )


def validate_date_format(date_str: str) -> bool:
    """
    验证日期格式是否为YYYYMMDD

    Args:
        date_str: 日期字符串

    Returns:
        bool: 是否为有效格式
    """
    try:
        datetime.strptime(date_str, '%Y%m%d')
        return True
    except ValueError:
        return False


def get_week_range_from_date(date_str: str) -> tuple:
    """
    从任意日期获取所在周的周一和周日

    Args:
        date_str: 日期字符串 (YYYYMMDD)

    Returns:
        tuple: (周一日期, 周日日期) 格式均为YYYYMMDD
    """
    target_date = datetime.strptime(date_str, '%Y%m%d').date()

    # 计算周一（weekday()=0）
    days_until_monday = target_date.weekday()
    week_monday = target_date - timedelta(days=days_until_monday)

    # 计算周日（weekday()=6）
    days_until_sunday = 6 - target_date.weekday()
    week_sunday = target_date + timedelta(days=days_until_sunday)

    return (week_monday.strftime('%Y%m%d'), week_sunday.strftime('%Y%m%d'))


if __name__ == "__main__":
    # 测试代码
    print("测试日期工具模块\n")

    # 测试本周
    print("本周日期参数:")
    params_this_week = calculate_week_params()
    for key, value in params_this_week.items():
        print(f"  {key}: {value}")

    print(f"\n格式化显示: {format_date_display(params_this_week)}")

    # 测试下周
    print("\n下周日期参数:")
    params_next_week = calculate_week_params(week_offset=1)
    print(f"  报告日期: {params_next_week['report_date']}")
    print(f"  周范围: {params_next_week['week_monday']} ~ {params_next_week['week_saturday']}")
    print(f"  格式化显示: {format_date_display(params_next_week)}")

    # 测试指定日期
    print("\n指定日期 (20260205) 的周:")
    params_custom = calculate_week_params(target_date='20260205')
    print(f"  报告日期: {params_custom['report_date']}")
    print(f"  周范围: {params_custom['week_monday']} ~ {params_custom['week_saturday']}")
    print(f"  格式化显示: {format_date_display(params_custom)}")
