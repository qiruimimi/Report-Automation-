#!/usr/bin/env python3
"""
SQL参数替换模块（简化版）

读取SQL模板文件并替换日期参数
"""

import yaml
from pathlib import Path
from typing import Dict, List


def get_column_mapping_for_section(
    config: Dict,
    section: str
) -> Dict[str, str]:
    """
    从配置中获取指定部分的列名映射

    Args:
        config: 配置字典
        section: 部分名称 (traffic, activation, engagement, retention, revenue)

    Returns:
        dict: 列名映射字典 {中文列名: 英文键名}
    """
    column_mappings = config.get('column_mappings', {})
    section_config = column_mappings.get(section, {})
    return section_config.get('columns', {})


def apply_column_mapping(
    data: List[Dict],
    column_mapping: Dict[str, str]
) -> List[Dict]:
    """
    应用列名映射到查询结果

    Args:
        data: 查询结果列表
        column_mapping: 列名映射字典 {中文列名: 英文键名}

    Returns:
        list: 映射后的数据
    """
    if not column_mapping:
        return data

    mapped_data = []
    for row in data:
        mapped_row = {}
        for key, value in row.items():
            # 如果有映射规则，使用映射后的键名；否则保持原键名
            new_key = column_mapping.get(key, key)
            mapped_row[new_key] = value
        mapped_data.append(mapped_row)

    return mapped_data


def load_config(config_path: str = None) -> Dict:
    """加载配置文件"""
    if config_path is None:
        config_path = Path(__file__).parent.parent / 'config' / 'sql_replacement_rules.yaml'

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def replace_sql_params(sql_content: str, params: Dict) -> str:
    """
    替换SQL中的参数

    Args:
        sql_content: SQL模板内容
        params: 日期参数字典

    Returns:
        str: 替换后的SQL
    """
    result = sql_content

    # 检测SQL中是否包含DATE_TRUNC函数（线下SQL使用动态日期计算）
    # 如果包含DATE_TRUNC，不进行参数替换，保持原样
    # 注意：DATE_TRUNC格式可能为 DATE_TRUNC('week', STR_TO_DATE(...)) 或 DATE_FORMAT(DATE_TRUNC(...))
    if 'DATE_TRUNC(' in sql_content or 'DATE_TRUNC(DATE_TRUNC(' in sql_content:
        # 线下SQL使用DATE_TRUNC动态计算日期，不替换参数，保持原样
        return sql_content

    # 替换所有可能的参数（对不使用DATE_TRUNC的SQL）
    replacements = {
        '{partition_start}': params.get('partition_start', ''),
        '{partition_end}': params.get('partition_end', ''),
        '{week_sunday}': params.get('week_sunday', ''),
        '{week_saturday}': params.get('week_saturday', ''),
        '{week_monday}': params.get('week_monday', ''),
        '{snapshot_date}': params.get('snapshot_date', ''),
        '{history_start_date}': params.get('history_start_date', ''),
        '{pay_start_date}': params.get('pay_start_date', ''),
        '{pay_end_date}': params.get('pay_end_date', ''),
    }

    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)

    # 修复中文列名的反引号问题 - 直接去除中文列名的反引号
    # Metabase API通过JSON传递SQL时，反引号可能导致解析问题
    # 查找所有 `中文字符串` 格式并去除反引号
    import re
    result = re.sub(r'`([\u4e00-\u9fff]+)`', r'\1', result)

    return result


def preprocess_sql_file(
    sql_file: str,
    params: Dict,
    base_path: str = None
) -> str:
    """
    预处理SQL文件（简化版）

    Args:
        sql_file: SQL文件名（相对于sql目录）
        params: 日期参数字典
        base_path: 项目根目录

    Returns:
        str: 处理后的SQL内容
    """
    if base_path is None:
        base_path = Path(__file__).parent.parent

    sql_path = Path(base_path) / 'sql' / sql_file

    if not sql_path.exists():
        raise FileNotFoundError(f"SQL文件不存在: {sql_path}")

    # 读取SQL文件
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # 替换参数
    processed_sql = replace_sql_params(sql_content, params)

    return processed_sql


if __name__ == "__main__":
    # 测试代码
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from date_utils import calculate_week_params

    print("测试SQL预处理模块\n")

    # 计算本周日期参数
    params = calculate_week_params()

    print("日期参数:")
    for key, value in params.items():
        print(f"  {key}: {value}")

    # 测试预处理一个SQL文件
    print("\n预处理 01_traffic.sql:")
    try:
        processed_sql = preprocess_sql_file('01_traffic.sql', params)
        print(f"✅ SQL预处理成功")
        print(f"预处理后SQL长度: {len(processed_sql)} 字符")
        # 显示前200字符
        print(f"\n前200字符预览:\n{processed_sql[:200]}...")
    except Exception as e:
        print(f"❌ 错误: {e}")
