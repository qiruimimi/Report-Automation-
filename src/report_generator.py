#!/usr/bin/env python3
"""
报告生成模块（Jinja2模板版）

生成Confluence兼容的HTML报告和Markdown报告
"""

from typing import Dict, List, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from src.logger import get_logger


class ReportGenerator:
    """报告生成器（使用Jinja2模板）"""

    def __init__(self, logger=None, template_dir: Optional[str] = None):
        self.logger = logger or get_logger('report_generator')

        # 设置模板目录
        if template_dir is None:
            base_dir = Path(__file__).parent.parent
            template_dir = base_dir / 'templates' / 'confluence'

        template_dir = Path(template_dir)
        self.logger.info(f"模板目录: {template_dir}")

        # 加载Jinja2环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=False
        )

        # 缓存模板
        self._templates = {}

    def _get_template(self, template_name: str):
        """获取模板（带缓存）"""
        if template_name not in self._templates:
            self._templates[template_name] = self.jinja_env.get_template(template_name)
            self.logger.debug(f"加载模板: {template_name}")
        return self._templates[template_name]

    # ==================== 辅助方法 ====================

    @staticmethod
    def _get_trend_class(value: float) -> str:
        """获取趋势CSS类"""
        if value > 0:
            return 'up'
        elif value < 0:
            return 'down'
        return 'flat'

    @staticmethod
    def _format_change(value: float, unit: str = '') -> str:
        """格式化变化值"""
        symbol = '↑' if value > 0 else ('↓' if value < 0 else '→')
        return f"{symbol} {abs(value):.2f}{unit}"

    @staticmethod
    def _format_number(value, format_int: bool = True) -> str:
        """格式化数字"""
        if value is None or value == 0:
            return '0'
        return f"{int(value):,}" if format_int else f"{value:,.2f}"

    # ==================== 各部分渲染方法 ====================

    def render_traffic_section(
        self,
        params: Dict,
        current_data: List[Dict],
        previous_data: List[Dict],
        analysis: Dict
    ) -> str:
        """渲染流量部分"""
        self.logger.info("渲染流量部分...")

        template = self._get_template('sections/traffic.html')

        # 提取数据
        total_visitors = analysis.get('new_visitors_current', 0)
        total_registrations = analysis.get('registrations_current', 0)
        conversion_rate = analysis.get('conversion_rate_current', 0)

        # 环比数据
        visitors_wow = analysis.get('visitors_wow', {}).get('change_rate', 0)
        registrations_wow = analysis.get('registrations_wow', {}).get('change_rate', 0)
        conversion_wow = analysis.get('conversion_rate_wow', {}).get('change_rate', 0)

        # 渲染模板
        html = template.render(
            ai_summary=analysis.get('ai_summary', ''),
            total_visitors=self._format_number(total_visitors),
            total_registrations=self._format_number(total_registrations),
            conversion_rate=f"{conversion_rate:.2f}",
            visitors_trend_class=self._get_trend_class(visitors_wow),
            visitors_change_str=self._format_change(visitors_wow, '%'),
            registrations_trend_class=self._get_trend_class(registrations_wow),
            registrations_change_str=self._format_change(registrations_wow, '%'),
            conversion_trend_class=self._get_trend_class(conversion_wow),
            conversion_change_str=f"{self._format_change(conversion_wow, '%')}",
            attention_items=analysis.get('attention_items', [])
        )

        self.logger.info("✅ 流量部分渲染完成")
        return html

    def render_activation_section(
        self,
        params: Dict,
        current_data: List[Dict],
        previous_data: List[Dict],
        analysis: Dict
    ) -> str:
        """渲染激活部分"""
        self.logger.info("渲染激活部分...")

        template = self._get_template('sections/activation.html')

        # 漏斗步骤
        funnel_steps = [
            {
                'name': '注册→进工具',
                'previous_rate': analysis.get('step1_previous_rate', 0),
                'current_rate': analysis.get('step1_current_rate', 0),
                'trend_class': self._get_trend_class(analysis.get('step1_change_rate', 0)),
                'change_str': self._format_change(analysis.get('step1_change_rate', 0), '%')
            },
            {
                'name': '进工具→画户型',
                'previous_rate': analysis.get('step2_previous_rate', 0),
                'current_rate': analysis.get('step2_current_rate', 0),
                'trend_class': self._get_trend_class(analysis.get('step2_change_rate', 0)),
                'change_str': self._format_change(analysis.get('step2_change_rate', 0), '%')
            },
            {
                'name': '画户型→拖模型',
                'previous_rate': analysis.get('step3_previous_rate', 0),
                'current_rate': analysis.get('step3_current_rate', 0),
                'trend_class': self._get_trend_class(analysis.get('step3_change_rate', 0)),
                'change_str': self._format_change(analysis.get('step3_change_rate', 0), '%')
            },
            {
                'name': '拖模型→渲染',
                'previous_rate': analysis.get('step4_previous_rate', 0),
                'current_rate': analysis.get('step4_current_rate', 0),
                'trend_class': self._get_trend_class(analysis.get('step4_change_rate', 0)),
                'change_str': self._format_change(analysis.get('step4_change_rate', 0), '%')
            }
        ]

        # 渲染模板（使用analysis中的周标签）
        html = template.render(
            ai_summary=analysis.get('ai_summary', ''),
            previous_week_label=analysis.get('previous_week_label', '上上周'),
            current_week_label=analysis.get('current_week_label', '上周'),
            funnel_steps=funnel_steps,
            # 使用 step4 作为总体转化率，替代不存在的 overall_* 字段
            overall_previous_rate=analysis.get('step4_previous_rate', 0),
            overall_current_rate=analysis.get('step4_current_rate', 0),
            overall_trend_class=self._get_trend_class(analysis.get('step4_change_rate', 0)),
            overall_change_str=self._format_change(analysis.get('step4_change_rate', 0), '%'),
            is_current_week_incomplete=False,
            current_week_metrics=[],
            core_insights=[]
        )

        self.logger.info("✅ 激活部分渲染完成")
        return html

    def render_engagement_section(
        self,
        params: Dict,
        current_data: List[Dict],
        previous_data: List[Dict],
        analysis: Dict
    ) -> str:
        """渲染活跃部分"""
        self.logger.info("渲染活跃部分...")

        template = self._get_template('sections/engagement.html')

        wau = analysis.get('wau_current', 0)
        wau_wow = analysis.get('wau_wow', {}).get('change_rate', 0)

        # 渲染模板
        html = template.render(
            ai_summary=analysis.get('ai_summary', ''),
            wau=self._format_number(wau),
            wau_trend_class=self._get_trend_class(wau_wow),
            wau_change_str=self._format_change(wau_wow, '%') if 'wau_wow' in analysis else '→',
            wau_contribution=analysis.get('wau_contribution', '新老用户共同贡献'),
            new_user_wau=analysis.get('new_user_wau', 0),
            new_user_wau_trend_class=self._get_trend_class(analysis.get('new_user_wau_wow', 0)),
            new_user_wau_change_str=self._format_change(analysis.get('new_user_wau_wow', 0), '%'),
            old_user_wau=analysis.get('old_user_wau', 0),
            old_user_wau_trend_class=self._get_trend_class(analysis.get('old_user_wau_wow', 0)),
            old_user_wau_change_str=self._format_change(analysis.get('old_user_wau_wow', 0), '%'),
            historical_weeks=analysis.get('historical_weeks', 25),
            historical_avg_wau=analysis.get('historical_avg_wau', 0),
            historical_trends=analysis.get('historical_trends', []),
            attention_items=analysis.get('attention_items', [])
        )

        self.logger.info("✅ 活跃部分渲染完成")
        return html

    def render_retention_section(
        self,
        params: Dict,
        current_data: List[Dict],
        previous_data: List[Dict],
        analysis: Dict
    ) -> str:
        """渲染留存部分"""
        self.logger.info("渲染留存部分...")

        template = self._get_template('sections/retention.html')

        # 渲染模板
        html = template.render(
            ai_summary=analysis.get('ai_summary', ''),
            new_user_retention_rate=analysis.get('new_user_retention_rate', 0),
            new_user_retention_previous=analysis.get('new_user_retention_previous', 0),
            new_user_retention_current=analysis.get('new_user_retention_current', 0),
            new_user_retention_min=analysis.get('new_user_retention_min', 0),
            new_user_retention_max=analysis.get('new_user_retention_max', 0),
            new_user_retention_level=analysis.get('new_user_retention_level', '中等'),
            new_user_retention_level_class='positive-trend' if analysis.get('new_user_retention_level') == '高' else 'negative-trend',
            old_user_retention_rate=analysis.get('old_user_retention_rate', 0),
            old_user_retention_previous=analysis.get('old_user_retention_previous', 0),
            old_user_retention_current=analysis.get('old_user_retention_current', 0),
            old_user_retention_min=analysis.get('old_user_retention_min', 0),
            old_user_retention_max=analysis.get('old_user_retention_max', 0),
            old_user_trend_class=self._get_trend_class(analysis.get('old_user_retention_change', 0)),
            old_user_trend_note=analysis.get('old_user_trend_note', '需要关注'),
            historical_new_user_avg=analysis.get('historical_new_user_avg', 0),
            historical_old_user_avg=analysis.get('historical_old_user_avg', 0),
            historical_trends=analysis.get('historical_trends', []),
            insights=analysis.get('insights', [])
        )

        self.logger.info("✅ 留存部分渲染完成")
        return html

    def generate_revenue_section_html(
        self,
        current_data: List[Dict],
        previous_data: List[Dict],
        analysis: Dict,
        md_content: Optional[str] = None
    ) -> str:
        """生成收入部分的HTML（兼容旧版）"""
        self.logger.info("生成收入部分HTML...")

        template = self._get_template('sections/revenue.html')

        total_revenue = analysis.get('total_current', 0)
        last_revenue = analysis.get('total_previous', 0)
        revenue_change = analysis.get('wow', {}).get('change_abs', 0)
        revenue_growth = analysis.get('wow', {}).get('change_rate', 0)

        # 渲染模板
        html = template.render(
            total_revenue=self._format_number(total_revenue),
            previous_revenue=self._format_number(last_revenue),
            revenue_change_abs=revenue_change,
            revenue_change_str=self._format_change(revenue_change, ''),
            revenue_trend_class=self._get_trend_class(revenue_change),
            revenue_growth_rate=revenue_growth,
            revenue_growth_trend_class=self._get_trend_class(revenue_growth),
            renewal_revenue=self._format_number(analysis.get('renewal_revenue', 0)),
            renewal_growth_rate=analysis.get('renewal_growth_rate', 0),
            new_signing_revenue=self._format_number(analysis.get('new_signing_revenue', 0)),
            new_signing_growth_rate=analysis.get('new_signing_growth_rate', 0),
            md_content=md_content,
            ai_summary=analysis.get('ai_summary', '数据暂未加载'),
            revenue_type=analysis.get('revenue_type', '-'),
            user_count=analysis.get('user_count', '-'),
            average_order_value=analysis.get('average_order_value', '-'),
            historical_weeks=analysis.get('historical_weeks', 12),
            historical_avg_revenue=analysis.get('historical_avg_revenue', 0),
            historical_trends=analysis.get('historical_trends', []),
            attention_items=analysis.get('attention_items', [])
        )

        self.logger.info("✅ 收入部分HTML生成完成")
        return html

    def render_insights_section(
        self,
        params: Dict,
        analysis: Dict
    ) -> str:
        """渲染洞察部分"""
        self.logger.info("渲染洞察部分...")

        template = self._get_template('sections/insights.html')

        html = template.render(
            positive_insights=analysis.get('positive_insights', []),
            negative_insights=analysis.get('negative_insights', []),
            key_findings=analysis.get('key_findings', [])
        )

        self.logger.info("✅ 洞察部分渲染完成")
        return html

    def render_suggestions_section(
        self,
        params: Dict,
        analysis: Dict
    ) -> str:
        """渲染建议部分"""
        self.logger.info("渲染建议部分...")

        template = self._get_template('sections/suggestions.html')

        html = template.render(
            short_term_suggestions=analysis.get('short_term_suggestions', []),
            medium_term_suggestions=analysis.get('medium_term_suggestions', []),
            long_term_suggestions=analysis.get('long_term_suggestions', [])
        )

        self.logger.info("✅ 建议部分渲染完成")
        return html


    def generate_full_report_html(
        self,
        params: Dict,
        current_data: Dict,
        previous_data: Dict,
        analysis: Dict,
        revenue_md_content: Optional[str] = None
    ) -> str:
        """
        生成完整HTML报告

        Args:
            params: 日期参数
            current_data: 本周所有数据
            previous_data: 上周所有数据
            analysis: 所有分析结果
            revenue_md_content: 收入MD文档内容

        Returns:
            str: 完整的HTML报告
        """
        self.logger.info("生成完整HTML报告...")

        # 渲染各部分
        sections = []

        # 流量部分
        if 'traffic' in current_data:
            sections.append(self.render_traffic_section(
                params,
                current_data['traffic'],
                previous_data.get('traffic', []),
                analysis.get('traffic', {})
            ))

        # 激活部分
        if 'activation' in current_data:
            sections.append(self.render_activation_section(
                params,
                current_data['activation'],
                previous_data.get('activation', []),
                analysis.get('activation', {})
            ))

        # 活跃部分
        if 'engagement' in current_data:
            sections.append(self.render_engagement_section(
                params,
                current_data['engagement'],
                previous_data.get('engagement', []),
                analysis.get('engagement', {})
            ))

        # 留存部分
        if 'retention' in current_data:
            sections.append(self.render_retention_section(
                params,
                current_data['retention'],
                previous_data.get('retention', []),
                analysis.get('retention', {})
            ))

        # 收入部分
        if 'revenue' in current_data:
            sections.append(self.generate_revenue_section_html(
                current_data['revenue'],
                previous_data.get('revenue', []),
                analysis.get('revenue', {}),
                revenue_md_content
            ))

        # 洞察与建议
        if 'insights' in analysis:
            sections.append(self.render_insights_section(params, analysis['insights']))
        if 'suggestions' in analysis:
            sections.append(self.render_suggestions_section(params, analysis['suggestions']))

        # 渲染基础模板
        base_template = self._get_template('base.html')

        from datetime import datetime
        execution_time = datetime.now().strftime('%Y-%m-%d %H:%M')

        full_html = base_template.render(
            report_date=params.get('report_date', datetime.now().strftime('%Y-%m-%d')),
            data_week=params.get('data_week', ''),
            data_end_date=params.get('data_end_date', ''),
            sections=sections,
            database_id=params.get('database_id', 2),
            execution_time=execution_time
        )

        self.logger.info("✅ 完整HTML报告生成完成")
        return full_html

    def generate_full_report_markdown(
        self,
        params: Dict,
        current_data: Dict,
        previous_data: Dict,
        analysis: Dict,
        revenue_md_content: Optional[str] = None
    ) -> str:
        """
        生成完整Markdown报告

        Args:
            params: 日期参数
            current_data: 本周所有数据
            previous_data: 上周所有数据
            analysis: 所有分析结果
            revenue_md_content: 收入MD文档内容

        Returns:
            str: 完整的Markdown报告
        """
        self.logger.info("生成完整Markdown报告...")

        # 渲染模板
        template = self._get_template('report.md')

        from datetime import datetime
        execution_time = datetime.now().strftime('%Y-%m-%d %H:%M')

        # 准备渲染参数
        render_params = {
            'report_date': params.get('report_date', datetime.now().strftime('%Y-%m-%d')),
            'data_week': params.get('data_week', ''),
            'data_end_date': params.get('data_end_date', ''),
            'database_id': params.get('database_id', 2),
            'execution_time': execution_time,
            # 流量
            'total_visitors': analysis.get('traffic', {}).get('new_visitors_current', 0),
            'total_registrations': analysis.get('traffic', {}).get('registrations_current', 0),
            'conversion_rate': analysis.get('traffic', {}).get('conversion_rate_current', 0),
            'visitors_wow': analysis.get('traffic', {}).get('visitors_wow', {}).get('change_rate', 0),
            'registrations_wow': analysis.get('traffic', {}).get('registrations_wow', {}).get('change_rate', 0),
            'conversion_wow': analysis.get('traffic', {}).get('conversion_rate_wow', {}).get('change_rate', 0),
            'attention_items_traffic': analysis.get('traffic', {}).get('attention_items', []),
            # 激活
            'previous_week_label': analysis.get('activation', {}).get('previous_week_label', ''),
            'current_week_label': analysis.get('activation', {}).get('current_week_label', ''),
            'funnel_steps': self._prepare_funnel_steps_for_md(analysis.get('activation', {})),
            'overall_previous_rate': analysis.get('activation', {}).get('overall_previous_rate', 0),
            'overall_current_rate': analysis.get('activation', {}).get('overall_current_rate', 0),
            'overall_change_rate': analysis.get('activation', {}).get('overall_change_rate', 0),
            'is_current_week_incomplete': analysis.get('activation', {}).get('is_current_week_incomplete', False),
            'current_week_metrics': analysis.get('activation', {}).get('current_week_metrics', []),
            'core_insights': analysis.get('activation', {}).get('core_insights', []),
            # 活跃
            'wau': analysis.get('engagement', {}).get('wau_current', 0),
            'wau_wow': analysis.get('engagement', {}).get('wau_wow', {}).get('change_rate', 0),
            'wau_contribution': analysis.get('engagement', {}).get('wau_contribution', '新老用户共同贡献'),
            'new_user_wau': analysis.get('engagement', {}).get('new_user_wau', 0),
            'new_user_wau_wow': analysis.get('engagement', {}).get('new_user_wau_wow', 0),
            'old_user_wau': analysis.get('engagement', {}).get('old_user_wau', 0),
            'old_user_wau_wow': analysis.get('engagement', {}).get('old_user_wau_wow', 0),
            'historical_weeks_engagement': analysis.get('engagement', {}).get('historical_weeks', 25),
            'historical_avg_wau': analysis.get('engagement', {}).get('historical_avg_wau', 0),
            'historical_trends_engagement': analysis.get('engagement', {}).get('historical_trends', []),
            'attention_items_engagement': analysis.get('engagement', {}).get('attention_items', []),
            # 留存
            'new_user_retention_rate': analysis.get('retention', {}).get('new_user_retention_rate', 0),
            'new_user_retention_previous': analysis.get('retention', {}).get('new_user_retention_previous', 0),
            'new_user_retention_current': analysis.get('retention', {}).get('new_user_retention_current', 0),
            'new_user_retention_min': analysis.get('retention', {}).get('new_user_retention_min', 0),
            'new_user_retention_max': analysis.get('retention', {}).get('new_user_retention_max', 0),
            'new_user_retention_level': analysis.get('retention', {}).get('new_user_retention_level', '中等'),
            'old_user_retention_rate': analysis.get('retention', {}).get('old_user_retention_rate', 0),
            'old_user_retention_previous': analysis.get('retention', {}).get('old_user_retention_previous', 0),
            'old_user_retention_current': analysis.get('retention', {}).get('old_user_retention_current', 0),
            'old_user_retention_min': analysis.get('retention', {}).get('old_user_retention_min', 0),
            'old_user_retention_max': analysis.get('retention', {}).get('old_user_retention_max', 0),
            'old_user_retention_change': analysis.get('retention', {}).get('old_user_retention_change', 0),
            'old_user_trend_note': analysis.get('retention', {}).get('old_user_trend_note', '需要关注'),
            'historical_new_user_avg': analysis.get('retention', {}).get('historical_new_user_avg', 0),
            'historical_old_user_avg': analysis.get('retention', {}).get('historical_old_user_avg', 0),
            'historical_trends_retention': analysis.get('retention', {}).get('historical_trends', []),
            'insights_retention': analysis.get('retention', {}).get('insights', []),
            # 收入
            'total_revenue': analysis.get('revenue', {}).get('total_current', 0),
            'previous_revenue': analysis.get('revenue', {}).get('total_previous', 0),
            'revenue_change_abs': analysis.get('revenue', {}).get('wow', {}).get('change_abs', 0),
            'revenue_change_rate': analysis.get('revenue', {}).get('wow', {}).get('change_rate', 0),
            'renewal_revenue': analysis.get('revenue', {}).get('renewal_revenue', 0),
            'renewal_growth_rate': analysis.get('revenue', {}).get('renewal_growth_rate', 0),
            'new_signing_revenue': analysis.get('revenue', {}).get('new_signing_revenue', 0),
            'new_signing_growth_rate': analysis.get('revenue', {}).get('new_signing_growth_rate', 0),
            'md_content': revenue_md_content,
            'ai_summary': analysis.get('revenue', {}).get('ai_summary', '数据暂未加载'),
            'revenue_type': analysis.get('revenue', {}).get('revenue_type', '-'),
            'user_count_revenue': analysis.get('revenue', {}).get('user_count', '-'),
            'average_order_value': analysis.get('revenue', {}).get('average_order_value', '-'),
            'historical_weeks_revenue': analysis.get('revenue', {}).get('historical_weeks', 12),
            'historical_avg_revenue': analysis.get('revenue', {}).get('historical_avg_revenue', 0),
            'historical_trends_revenue': analysis.get('revenue', {}).get('historical_trends', []),
            'attention_items_revenue': analysis.get('revenue', {}).get('attention_items', []),
            # 洞察与建议
            'positive_insights': analysis.get('insights', {}).get('positive_insights', []),
            'negative_insights': analysis.get('insights', {}).get('negative_insights', []),
            'key_findings': analysis.get('insights', {}).get('key_findings', []),
            'short_term_suggestions': analysis.get('suggestions', {}).get('short_term_suggestions', []),
            'medium_term_suggestions': analysis.get('suggestions', {}).get('medium_term_suggestions', []),
            'long_term_suggestions': analysis.get('suggestions', {}).get('long_term_suggestions', []),
        }

        full_md = template.render(**render_params)

        self.logger.info("✅ 完整Markdown报告生成完成")
        return full_md

    @staticmethod
    def _prepare_funnel_steps_for_md(activation_analysis: Dict) -> List[Dict]:
        """准备激活漏斗步骤数据用于Markdown渲染"""
        steps = [
            {
                'name': '注册→进工具',
                'previous_rate': activation_analysis.get('step1_previous_rate', 0),
                'current_rate': activation_analysis.get('step1_current_rate', 0),
                'change_str': ReportGenerator._format_change(activation_analysis.get('step1_change_rate', 0), '%')
            },
            {
                'name': '进工具→画户型',
                'previous_rate': activation_analysis.get('step2_previous_rate', 0),
                'current_rate': activation_analysis.get('step2_current_rate', 0),
                'change_str': ReportGenerator._format_change(activation_analysis.get('step2_change_rate', 0), '%')
            },
            {
                'name': '画户型→拖模型',
                'previous_rate': activation_analysis.get('step3_previous_rate', 0),
                'current_rate': activation_analysis.get('step3_current_rate', 0),
                'change_str': ReportGenerator._format_change(activation_analysis.get('step3_change_rate', 0), '%')
            },
            {
                'name': '拖模型→渲染',
                'previous_rate': activation_analysis.get('step4_previous_rate', 0),
                'current_rate': activation_analysis.get('step4_current_rate', 0),
                'change_str': ReportGenerator._format_change(activation_analysis.get('step4_change_rate', 0), '%')
            }
        ]
        return steps

    # ==================== 兼容旧版方法 ====================

    def generate_full_report(
        self,
        params: Dict,
        current_data: Dict,
        previous_data: Dict,
        analysis: Dict,
        revenue_md_content: Optional[str] = None
    ) -> str:
        """
        生成完整报告HTML

        Args:
            params: 日期参数
            current_data: 本周所有数据
            previous_data: 上周所有数据
            analysis: 所有分析结果
            revenue_md_content: 收入MD文档内容

        Returns:
            str: 完整的HTML报告
        """
        return self.generate_full_report_html(
            params=params,
            current_data=current_data,
            previous_data=previous_data,
            analysis=analysis,
            revenue_md_content=revenue_md_content
        )


if __name__ == "__main__":
    # 测试代码
    print("测试报告生成模块\n")

    generator = ReportGenerator()

    # 测试数据
    current_revenue = [{'Total_Amt': 68968}]
    previous_revenue = [{'Total_Amt': 71381}]

    analysis = {
        'total_current': 68968,
        'total_previous': 71381,
        'wow': {
            'change_rate': -3.37,
            'change_abs': -2413,
            'trend': '↓'
        }
    }

    html = generator.generate_revenue_section_html(
        current_revenue,
        previous_revenue,
        analysis
    )

    print(f"生成的HTML长度: {len(html)} 字符")
    print(f"\nHTML预览（前500字符）:\n{html[:500]}...")
