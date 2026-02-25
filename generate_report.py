#!/usr/bin/env python3
"""
周报生成器 - 优化版

生成符合参考格式的标准化周报
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from jinja2 import Environment, FileSystemLoader


class WeeklyReportGenerator:
    """周报生成器"""

    def __init__(self, template_path: str = None):
        """
        初始化生成器

        Args:
            template_path: MD模板文件路径
        """
        if template_path is None:
            template_path = Path(__file__).parent / 'templates' / 'weekly_report_template.md'

        self.template_path = Path(template_path)
        self.template_dir = self.template_path.parent

        # 使用Jinja2环境
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # 添加自定义过滤器
        self.env.filters['format_number'] = self._format_number

    def _format_number(self, value):
        """格式化数字，添加千分位分隔符"""
        if value is None:
            return '0'
        try:
            return f"{int(value):,}"
        except (ValueError, TypeError):
            return str(value)

    def generate_report(
        self,
        report_date: str,
        week_label: str,
        week_end_date: str,
        traffic_data: Dict,
        activation_data: Dict,
        engagement_data: Dict,
        retention_data: Dict,
        revenue_data: Dict
    ) -> str:
        """
        生成完整周报

        Args:
            report_date: 报告日期 (YYYY-MM-DD)
            week_label: 周标签 (YYYYMMDD)
            week_end_date: 周结束日期 (YYYY-MM-DD)
            traffic_data: 流量数据
            activation_data: 激活数据
            engagement_data: 活跃数据
            retention_data: 留存数据
            revenue_data: 收入数据

        Returns:
            str: 完整的MD报告
        """
        # 加载模板
        template = self.env.get_template(self.template_path.name)

        # 准备模板变量
        template_vars = {
            # 基本信息
            'report_date': report_date,
            'week_label': week_label,
            'week_end_date': week_end_date,
            'database_id': 2,
            'execution_time': datetime.now().strftime('%Y-%m-%d %H:%M'),

            # 流量部分
            'traffic_total_guests': traffic_data.get('total_guests', 0),
            'traffic_total_registers': traffic_data.get('total_registers', 0),
            'traffic_conversion_rate': traffic_data.get('conversion_rate', 0),
            'traffic_guests_wow': traffic_data.get('guests_wow', '+0.0%'),
            'traffic_guests_trend': traffic_data.get('guests_trend', '↑'),
            'traffic_registers_wow': traffic_data.get('registers_wow', '+0.0%'),
            'traffic_registers_trend': traffic_data.get('registers_trend', '↑'),
            'traffic_conversion_wow': traffic_data.get('conversion_wow', '+0.0%'),
            'traffic_conversion_trend': traffic_data.get('conversion_trend', '↑'),
            'traffic_notes': traffic_data.get('notes', []),

            # 激活部分
            'last_week_label': activation_data.get('last_week_label', ''),
            'current_week_label': activation_data.get('current_week_label', ''),
            'last_last_week_label': activation_data.get('last_last_week_label', ''),
            'activation_step1_llw': activation_data.get('step1_llw', 0),
            'activation_step1_lw': activation_data.get('step1_lw', 0),
            'activation_step1_change': activation_data.get('step1_change', ''),
            'activation_step2_llw': activation_data.get('step2_llw', 0),
            'activation_step2_lw': activation_data.get('step2_lw', 0),
            'activation_step2_change': activation_data.get('step2_change', ''),
            'activation_step3_llw': activation_data.get('step3_llw', 0),
            'activation_step3_lw': activation_data.get('step3_lw', 0),
            'activation_step3_change': activation_data.get('step3_change', ''),
            'activation_step4_llw': activation_data.get('step4_llw', 0),
            'activation_step4_lw': activation_data.get('step4_lw', 0),
            'activation_step4_change': activation_data.get('step4_change', ''),
            'activation_total_llw': activation_data.get('total_llw', 0),
            'activation_total_lw': activation_data.get('total_lw', 0),
            'activation_total_change': activation_data.get('total_change', ''),
            'incomplete_data': activation_data.get('incomplete_data', False),
            'activation_new_users': activation_data.get('new_users', 0),
            'activation_step1_curr': activation_data.get('step1_curr', 0),
            'activation_step2_curr': activation_data.get('step2_curr', 0),
            'activation_step3_curr': activation_data.get('step3_curr', 0),
            'activation_step4_curr': activation_data.get('step4_curr', 0),

            # 活跃部分
            'engagement_total_wau': engagement_data.get('total_wau', 0),
            'engagement_wow': engagement_data.get('wow', '+0.0'),
            'engagement_driver': engagement_data.get('driver', '新老用户'),
            'engagement_new_wau': engagement_data.get('new_wau', 0),
            'engagement_new_wow': engagement_data.get('new_wow', '+0.0'),
            'engagement_old_wau': engagement_data.get('old_wau', 0),
            'engagement_old_wow': engagement_data.get('old_wow', '+0.0'),
            'engagement_historical_avg': engagement_data.get('historical_avg', 0),

            # 留存部分
            'retention_new_rate': retention_data.get('new_rate', 0),
            'retention_new_last': retention_data.get('new_last', 0),
            'retention_new_trend': retention_data.get('new_trend', ''),
            'retention_old_rate': retention_data.get('old_rate', 0),
            'retention_old_last': retention_data.get('old_last', 0),
            'retention_old_trend': retention_data.get('old_trend', ''),
            'retention_new_12w_avg': retention_data.get('new_12w_avg', 0),
            'retention_old_12w_avg': retention_data.get('old_12w_avg', 0),

            # 收入部分
            'revenue_total': revenue_data.get('total', 0),
            'revenue_change_abs': revenue_data.get('change_abs', 0),
            'revenue_trend': revenue_data.get('trend', '↑'),
            'revenue_change_rate': revenue_data.get('change_rate', 0),
            'revenue_renewal_change': revenue_data.get('renewal_change', 0),
            'revenue_renewal_rate': revenue_data.get('renewal_rate', 0),
            'revenue_new_change': revenue_data.get('new_change', 0),
            'revenue_new_rate': revenue_data.get('new_rate', 0),
            'revenue_ai_summary': revenue_data.get('ai_summary', ''),
            'revenue_normal_change': revenue_data.get('normal_change', 0),
            'revenue_type_analysis': revenue_data.get('type_analysis', ''),
            'revenue_users_analysis': revenue_data.get('users_analysis', ''),
            'revenue_arpu_analysis': revenue_data.get('arpu_analysis', ''),
            'revenue_sku_analysis': revenue_data.get('sku_analysis', ''),
            'revenue_country_analysis': revenue_data.get('country_analysis', ''),
            'revenue_tier_analysis': revenue_data.get('tier_analysis', ''),
        }

        # 使用Jinja2渲染模板
        report_content = template.render(**template_vars)

        return report_content

    def save_report(self, content: str, output_path: str):
        """
        保存报告到文件

        Args:
            content: 报告内容
            output_path: 输出文件路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ 报告已保存到: {output_file}")


def process_json_data(json_files: Dict[str, str]) -> Dict:
    """
    处理JSON数据文件，提取关键指标

    Args:
        json_files: 各部分JSON文件路径的字典

    Returns:
        Dict: 处理后的数据字典
    """
    result = {}

    # 处理流量数据
    if 'traffic' in json_files:
        with open(json_files['traffic'], 'r', encoding='utf-8') as f:
            traffic_json = json.load(f)
            result['traffic'] = extract_traffic_metrics(traffic_json)

    # 处理其他部分类似...

    return result


def extract_traffic_metrics(data: List[Dict]) -> Dict:
    """从流量数据中提取关键指标"""
    # 实现流量数据提取逻辑
    return {}


if __name__ == '__main__':
    import sys
    from pathlib import Path

    # 添加项目根目录到Python路径
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    # 测试代码
    generator = WeeklyReportGenerator()

    # 模拟数据
    test_data = {
        'report_date': '2026-02-03',
        'week_label': '20260126',
        'week_end_date': '2026-02-01',
        'traffic_data': {
            'total_guests': 154968,
            'total_registers': 32089,
            'conversion_rate': 20.7,
            'guests_wow': '+40.1%',
            'guests_trend': '↑',
            'registers_wow': '+49.0%',
            'registers_trend': '↑',
            'conversion_wow': '+4.83%',
            'conversion_trend': '↑',
            'notes': [
                {
                    'channel': '付费广告 (paid ads)',
                    'description': '新访客数大幅增长110.6%（从27,510增至57,945），转化率保持在42%高水平'
                },
                {
                    'channel': '自然搜索 (organic search)',
                    'description': '环比下降18.1%，仍是最大流量来源（59,749人）'
                }
            ]
        },
        'activation_data': {
            'last_week_label': '20260119',
            'current_week_label': '20260126',
            'last_last_week_label': '20260112',
            'step1_llw': 83.56,
            'step1_lw': 81.79,
            'step1_change': '↓ -1.77%',
            'incomplete_data': True
        },
        'engagement_data': {
            'total_wau': 58584,
            'wow': '+17.5',
            'driver': '新用户',
            'new_wau': 27570,
            'new_wow': '+42.9',
            'old_wau': 31014,
            'old_wow': '+1.5',
            'historical_avg': 60850
        },
        'retention_data': {
            'new_rate': 11.7,
            'new_last': 10.6,
            'new_trend': '处于近12周较高水平',
            'old_rate': 46.5,
            'old_last': 45.4,
            'old_trend': '达到近12周最高点',
            'new_12w_avg': 11.23,
            'old_12w_avg': 44.43
        },
        'revenue_data': {
            'total': 59889,
            'change_abs': -4896,
            'trend': '⬇️',
            'change_rate': -7.6,
            'renewal_change': '-6,655',
            'renewal_rate': -12.2,
            'new_change': '+1,786',
            'new_rate': 17.8,
            'ai_summary': '收入金额连续2周下行...',
            'normal_change': '-4,896',
            'type_analysis': '续约收入（-6,655 美元）、 新签（+1,786 美元）',
            'users_analysis': '付费用户数减少84人（-4.6%）',
            'arpu_analysis': '整体客单价下降1.1美元（从35.4降至34.3）'
        }
    }

    report = generator.generate_report(**test_data)

    # 保存报告
    output_dir = Path(__file__).parent.parent / 'output'
    generator.save_report(report, output_dir / 'test_report.md')

    print("\n生成的报告预览（前500字符）:")
    print(report[:500] + '...')
