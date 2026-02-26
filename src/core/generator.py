#!/usr/bin/env python3
"""
报告生成器

支持 Markdown 格式报告生成，每部分包含 AI 简短客观总结
"""

from typing import Dict, Optional, List
from pathlib import Path
from datetime import datetime
from src.logger import get_logger
from src.models.types import WeekParams

logger = get_logger('core.generator')


class ReportGenerator:
    """
    报告生成器

    支持 Markdown 和 HTML 两种格式
    """

    def __init__(self, templates_dir: Optional[str] = None, logger=None):
        """
        初始化报告生成器

        Args:
            templates_dir: 模板目录路径
            logger: 日志记录器
        """
        self.logger = logger or get_logger('core.generator')
        self.templates_dir = templates_dir or Path(__file__).parent / 'templates'

    def generate_markdown_report(
        self,
        params: WeekParams,
        data: Dict,
        analysis: Optional[Dict] = None
    ) -> str:
        """
        生成 Markdown 格式报告

        Args:
            params: 周参数
            data: 各部分原始数据
            analysis: 分析结果（可选）

        Returns:
            str: Markdown 格式的完整报告
        """
        sections_order = ['traffic', 'activation', 'engagement', 'retention', 'revenue']

        lines = []
        lines.extend([
            f"# {params.get('report_date', datetime.now().strftime('%Y%m%d'))} 周报",
            "",
            f"**数据周**: {params.get('week_monday', '')} ~ {params.get('week_saturday', '')}",
            ""
        ])

        # 为每个部分生成内容
        for section in sections_order:
            section_data = data.get(section, [])
            section_analysis = analysis.get(section, {}) if analysis else {}

            lines.append(f"\n## {self._get_section_title(section)}")

            if not section_data:
                lines.append(f"\n> **暂无数据**")
                continue

            # 数据表格
            lines.append("\n### 数据明细")
            lines.append(self._format_data_table(section_data, section))

            # 环比数据
            if section_analysis:
                wow_data = self._extract_wow_data(section, section_analysis)
                if wow_data:
                    lines.append("\n### 环比变化")
                    lines.append("| 指标 | 上周 | 本周 | 变化 | 变化率 |")
                    lines.append("|------|--------|--------|------|--------|")
                    for metric, value in wow_data.items():
                        change = value.get('change_abs', 0)
                        rate = value.get('change_rate', 0)
                        trend = value.get('trend', '→')
                        lines.append(f"| {metric} | {value.get('previous', 0)} | {value.get('current', 0)} | {trend} {change} | {rate}% |")

            # AI 总结
            if section_analysis.get('ai_summary'):
                lines.append("\n### 🤖 AI 总结")
                lines.append(section_analysis['ai_summary'])

            # 趋势分析
            if section_analysis.get('trend'):
                lines.append("\n### 📈 趋势分析")
                lines.append(section_analysis['trend'])

            # 关键洞察
            if section_analysis.get('attention_items'):
                items = section_analysis['attention_items']
                if items:
                    lines.append("\n### ⚠️ 关注事项")
                    for item in items:
                        lines.append(f"- {item}")

        lines.extend([
            "",
            "---",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ])

        report_md = '\n'.join(lines)
        self.logger.info("✅ Markdown 报告生成完成")
        return report_md

    def generate_html_report(
        self,
        params: WeekParams,
        data: Dict,
        analysis: Optional[Dict] = None,
        revenue_md_content: Optional[str] = None
    ) -> str:
        """
        生成 HTML 格式报告（兼容现有功能）

        Args:
            params: 周参数
            data: 各部分原始数据
            analysis: 分析结果（可选）
            revenue_md_content: 收入 MD 文档内容（可选）

        Returns:
            str: HTML 格式的完整报告
        """
        sections_order = ['traffic', 'activation', 'engagement', 'retention', 'revenue']

        html_parts = []
        html_parts.append(f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{params.get('report_date', '')} 周报</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; margin: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .positive {{ color: #27ae60; }}
        .negative {{ color: #e74c3c; }}
        .neutral {{ color: #7f8c8d; }}
        .summary {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        .ai-summary {{ background-color: #e8f5e9; border-left: 4px solid #4caf50; padding: 10px; margin: 10px 0; }}
        .attention {{ background-color: #fff3e0; border-left: 4px solid #ff9800; padding: 10px; margin: 10px 0; }}
    </style>
</head>
<body>
    <h1>{params.get('report_date', '')} 周报</h1>
    <p><strong>数据周:</strong> {params.get('week_monday', '')} ~ {params.get('week_saturday', '')}</p>
""")

        # 为每个部分生成内容
        for section in sections_order:
            section_data = data.get(section, [])
            section_analysis = analysis.get(section, {}) if analysis else {}

            html_parts.append(f'\n    <h2>{self._get_section_title(section)}</h2>')

            if not section_data:
                html_parts.append('    <p><em>暂无数据</em></p>')
                continue

            # 数据表格
            html_parts.append(self._format_html_table(section_data, section))

            # 环比数据
            if section_analysis:
                wow_data = self._extract_wow_data(section, section_analysis)
                if wow_data:
                    html_parts.append('\n    <h3>环比变化</h3>')
                    html_parts.append('    <table>')
                    html_parts.append('        <thead><tr><th>指标</th><th>上周</th><th>本周</th><th>变化</th><th>变化率</th></tr></thead>')
                    html_parts.append('        <tbody>')
                    for metric, value in wow_data.items():
                        change = value.get('change_abs', 0)
                        rate = value.get('change_rate', 0)
                        trend = value.get('trend', '→')
                        trend_class = 'positive' if trend == '↑' else ('negative' if trend == '↓' else 'neutral')
                        html_parts.append(
                            f'            <tr>'
                            f'<td>{metric}</td>'
                            f'<td>{value.get("previous", 0)}</td>'
                            f'<td>{value.get("current", 0)}</td>'
                            f'<td class="{trend_class}">{trend} {change}</td>'
                            f'<td class="{trend_class}">{rate}%</td>'
                            f'</tr>'
                        )
                    html_parts.append('        </tbody></table>')

            # AI 总结
            if section_analysis.get('ai_summary'):
                html_parts.append('\n    <div class="ai-summary">')
                html_parts.append(f'        <strong>🤖 AI 总结:</strong> {section_analysis["ai_summary"]}')
                html_parts.append('    </div>')

            # 收入 MD 内容
            if section == 'revenue' and revenue_md_content:
                html_parts.append('\n    <div class="summary">')
                html_parts.append(f'        <h3>收入详细分析</h3>')
                html_parts.append(f'        <pre>{revenue_md_content}</pre>')
                html_parts.append('    </div>')

            # 关键洞察
            if section_analysis.get('attention_items'):
                items = section_analysis['attention_items']
                if items:
                    html_parts.append('\n    <div class="attention">')
                    html_parts.append('        <strong>⚠️ 关注事项:</strong>')
                    html_parts.append('        <ul>')
                    for item in items:
                        html_parts.append(f'            <li>{item}</li>')
                    html_parts.append('        </ul>')
                    html_parts.append('    </div>')

        html_parts.append(f"""
    <hr>
    <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</body>
</html>
""")

        html = '\n'.join(html_parts)
        self.logger.info("✅ HTML 报告生成完成")
        return html

    def generate_full_report(
        self,
        params: WeekParams,
        current_data: Dict,
        previous_data: Dict,
        analysis: Optional[Dict] = None,
        revenue_md_content: Optional[str] = None,
        format: str = 'markdown'
    ) -> str:
        """
        生成完整报告

        Args:
            params: 周参数
            current_data: 本周数据
            previous_data: 上周数据
            analysis: 分析结果（可选）
            revenue_md_content: 收入 MD 文档内容（可选）
            format: 报告格式 ('markdown' 或 'html')

        Returns:
            str: 生成的报告内容
        """
        # 合并当前和上周数据
        data = {
            'current': current_data,
            'previous': previous_data
        }

        if format == 'markdown':
            return self.generate_markdown_report(params, current_data, analysis)
        else:
            return self.generate_html_report(params, current_data, analysis, revenue_md_content)

    def _get_section_title(self, section: str) -> str:
        """
        获取部分标题

        Args:
            section: 部分名称

        Returns:
            str: 部分中文名称
        """
        titles = {
            'traffic': '1. 流量/投放',
            'activation': '2. 激活/注册',
            'engagement': '3. 活跃-新老用户',
            'retention': '4. 留存',
            'revenue': '5. 收入'
        }
        return titles.get(section, section)

    def _format_data_table(self, data: List[Dict], section: str) -> str:
        """
        格式化数据为 Markdown 表格

        Args:
            data: 数据列表
            section: 部分名称

        Returns:
            str: Markdown 表格
        """
        if not data:
            return ""

        # 获取所有列名
        all_keys = set()
        for row in data:
            all_keys.update(row.keys())
        columns = sorted(all_keys)

        # 限制列数，避免表格过宽
        max_columns = 6
        if len(columns) > max_columns:
            columns = columns[:max_columns]

        lines = []
        lines.append("| " + " | ".join(columns) + " |")
        lines.append("| " + " | ".join(["---"] * len(columns)) + " |")

        for row in data[:10]:  # 只显示前10条
            values = []
            for col in columns:
                value = row.get(col, '')
                # 格式化数值
                if isinstance(value, (int, float)):
                    value = f"{value:,}" if isinstance(value, int) else f"{value:.2f}"
                values.append(str(value))
            lines.append("| " + " | ".join(values) + " |")

        if len(data) > 10:
            lines.append(f"| ... | 共 {len(data)} 条记录 |")

        return '\n'.join(lines)

    def _format_html_table(self, data: List[Dict], section: str) -> str:
        """
        格式化数据为 HTML 表格

        Args:
            data: 数据列表
            section: 部分名称

        Returns:
            str: HTML 表格
        """
        if not data:
            return "<p>无数据</p>"

        # 获取所有列名
        all_keys = set()
        for row in data:
            all_keys.update(row.keys())
        columns = sorted(all_keys)

        # 限制列数
        max_columns = 6
        if len(columns) > max_columns:
            columns = columns[:max_columns]

        lines = ['    <table>', '        <thead><tr>']
        for col in columns:
            lines.append(f'            <th>{col}</th>')
        lines.extend(['        </tr></thead>', '        <tbody>'])

        for row in data[:10]:
            lines.append('            <tr>')
            for col in columns:
                value = row.get(col, '')
                if isinstance(value, (int, float)):
                    value = f"{value:,}" if isinstance(value, int) else f"{value:.2f}"
                lines.append(f'                <td>{value}</td>')
            lines.append('            </tr>')

        if len(data) > 10:
            lines.append(f'            <tr><td colspan="{len(columns)}">... 共 {len(data)} 条记录</td></tr>')

        lines.extend(['        </tbody>', '    </table>'])

        return '\n'.join(lines)

    def _extract_wow_data(self, section: str, analysis: Dict) -> Dict:
        """
        从分析结果中提取环比数据

        Args:
            section: 部分名称
            analysis: 分析结果

        Returns:
            dict: 环比数据
        """
        wow_map = {
            'traffic': {
                '新访客数': 'visitors_wow',
                '注册数': 'registrations_wow',
                '转化率': 'conversion_rate_wow'
            },
            'activation': {
                '注册进工具': 'step1_change_rate',
                '进工具到画户型': 'step2_change_rate',
                '画户型到拖模型': 'step3_change_rate',
                '拖模型到渲染': 'step4_change_rate'
            },
            'engagement': {
                '总WAU': 'wau_wow',
                '新用户WAU': 'new_user_wau_wow',
                '老用户WAU': 'old_user_wau_wow'
            },
            'retention': {
                '新用户留存': 'new_user_retention_rate',
                '老用户留存': 'old_user_retention_rate'
            },
            'revenue': {
                '总收入': 'wow',
                '续费收入': 'renewal_growth_rate',
                '新签收入': 'new_signing_growth_rate'
            }
        }

        section_wow_map = wow_map.get(section, {})
        result = {}

        for label, key in section_wow_map.items():
            value = analysis.get(key)
            if value is None:
                continue
            if isinstance(value, dict):
                result[label] = value
            else:
                result[label] = {
                    'previous': analysis.get(f'{key}_previous', 0),
                    'current': analysis.get(f'{key}_current', value),
                    'change_abs': analysis.get(f'{key}_change_rate', value) if 'rate' in key else 0,
                    'change_rate': value if isinstance(value, (int, float)) else 0,
                    'trend': '→'
                }

        return result


if __name__ == "__main__":
    # 测试代码
    print("测试报告生成器\n")

    generator = ReportGenerator()

    # 测试参数
    params = {
        'report_date': '20260223',
        'week_monday': '2026-02-17',
        'week_saturday': '2026-02-22'
    }

    # 测试数据
    data = {
        'traffic': [
            {'日期': '20260217', '渠道': 'organic', '新访客数': 100, '新访客注册数': 20},
            {'日期': '20260218', '渠道': 'direct', '新访客数': 80, '新访客注册数': 15}
        ],
        'activation': [],
        'engagement': [],
        'retention': [],
        'revenue': []
    }

    # 测试分析结果
    analysis = {
        'traffic': {
            'visitors_wow': {
                'previous': 160,
                'current': 180,
                'change_abs': 20,
                'change_rate': 12.5,
                'trend': '↑'
            },
            'ai_summary': '本周流量稳步增长，主要来自 organic 渠道。',
            'attention_items': ['新访客注册转化率略低于上周']
        }
    }

    # 生成 Markdown 报告
    md_report = generator.generate_markdown_report(params, data, analysis)
    print(md_report)
