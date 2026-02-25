#!/usr/bin/env python3
"""
报告生成器测试

测试report_generator模块的模板渲染功能
"""

import pytest
from src.report_generator import ReportGenerator


class TestReportGenerator:
    """报告生成器测试类"""

    def test_init_with_default_template_dir(self, logger):
        """测试使用默认模板目录初始化"""
        generator = ReportGenerator(logger=logger)

        assert generator is not None
        assert generator.logger is not None
        assert generator.jinja_env is not None

    def test_get_trend_class(self):
        """测试趋势CSS类获取"""
        assert ReportGenerator._get_trend_class(10) == 'up'
        assert ReportGenerator._get_trend_class(-10) == 'down'
        assert ReportGenerator._get_trend_class(0) == 'flat'

    def test_format_change(self):
        """测试变化值格式化"""
        assert ReportGenerator._format_change(10.5, '%') == '↑ 10.50%'
        assert ReportGenerator._format_change(-5.25, '%') == '↓ 5.25%'
        assert ReportGenerator._format_change(0, '%') == '→ 0.00%'
        assert ReportGenerator._format_change(100, '') == '↑ 100.00'

    def test_format_number(self):
        """测试数字格式化"""
        assert ReportGenerator._format_number(1000) == '1,000'
        assert ReportGenerator._format_number(1000000) == '1,000,000'
        assert ReportGenerator._format_number(0) == '0'
        assert ReportGenerator._format_number(0.0, format_int=False) == '0.00'
        assert ReportGenerator._format_number(1234.56, format_int=False) == '1,234.56'

    def test_render_traffic_section(self, logger, sample_traffic_data):
        """测试渲染流量部分"""
        generator = ReportGenerator(logger=logger)

        params = {
            'report_date': '2026-02-10',
            'data_week': '20260210'
        }

        analysis = {
            'new_visitors_current': 10000,
            'registrations_current': 5000,
            'conversion_rate_current': 50.0,
            'visitors_wow': {'change_rate': 10.0},
            'registrations_wow': {'change_rate': 5.0},
            'conversion_rate_wow': {'change_rate': -2.0},
            'attention_items': []
        }

        html = generator.render_traffic_section(
            params,
            sample_traffic_data,
            [],
            analysis
        )

        assert isinstance(html, str)
        assert len(html) > 0
        assert '流量' in html

    def test_render_revenue_section(self, logger, sample_revenue_data):
        """测试渲染收入部分"""
        generator = ReportGenerator(logger=logger)

        params = {'report_date': '2026-02-10'}

        analysis = {
            'total_current': 100000,
            'total_previous': 80000,
            'wow': {'change_abs': 20000, 'change_rate': 25.0},
            'renewal_revenue': 60000,
            'new_signing_revenue': 40000,
            'renewal_growth_rate': 10.0,
            'new_signing_growth_rate': 30.0,
            'ai_summary': 'AI生成的收入分析',
            'revenue_type': '订阅收入',
            'user_count': 100,
            'average_order_value': 1000,
            'historical_avg_revenue': 90000,
            'historical_trends': [],
            'attention_items': []
        }

        html = generator.generate_revenue_section_html(
            sample_revenue_data,
            [],
            analysis
        )

        assert isinstance(html, str)
        assert len(html) > 0
        assert '收入' in html
        assert '100,000' in html

    def test_render_engagement_section(self, logger, sample_engagement_data):
        """测试渲染活跃部分"""
        generator = ReportGenerator(logger=logger)

        params = {'report_date': '2026-02-10'}

        analysis = {
            'wau_current': 50000,
            'wau_wow': {'change_rate': 5.0},
            'wau_contribution': '新老用户共同贡献',
            'new_user_wau': 20000,
            'new_user_wau_wow': 10.0,
            'old_user_wau': 30000,
            'old_user_wau_wow': 2.0,
            'historical_weeks': 25,
            'historical_avg_wau': 48000,
            'historical_trends': [],
            'attention_items': []
        }

        html = generator.render_engagement_section(
            params,
            sample_engagement_data,
            [],
            analysis
        )

        assert isinstance(html, str)
        assert len(html) > 0
        assert '活跃' in html

    def test_render_retention_section(self, logger, sample_retention_data):
        """测试渲染留存部分"""
        generator = ReportGenerator(logger=logger)

        params = {'report_date': '2026-02-10'}

        analysis = {
            'new_user_retention_rate': 45.0,
            'new_user_retention_previous': 43.0,
            'new_user_retention_current': 45.0,
            'new_user_retention_min': 40.0,
            'new_user_retention_max': 48.0,
            'new_user_retention_level': '中等',
            'old_user_retention_rate': 60.0,
            'old_user_retention_previous': 58.0,
            'old_user_retention_current': 60.0,
            'old_user_retention_min': 55.0,
            'old_user_retention_max': 62.0,
            'old_user_retention_change': 2.0,
            'old_user_trend_note': '需要关注',
            'historical_new_user_avg': 44.0,
            'historical_old_user_avg': 59.0,
            'historical_trends': [],
            'insights': []
        }

        html = generator.render_retention_section(
            params,
            sample_retention_data,
            [],
            analysis
        )

        assert isinstance(html, str)
        assert len(html) > 0
        assert '留存' in html

    def test_render_insights_section(self, logger):
        """测试渲染洞察部分"""
        generator = ReportGenerator(logger=logger)

        params = {'report_date': '2026-02-10'}

        analysis = {
            'positive_insights': [
                '留存率稳定增长',
                '收入结构优化'
            ],
            'negative_insights': [
                '流量增长放缓'
            ],
            'key_findings': [
                '新用户转化率提升'
            ]
        }

        html = generator.render_insights_section(params, analysis)

        assert isinstance(html, str)
        assert len(html) > 0

    def test_render_suggestions_section(self, logger):
        """测试渲染建议部分"""
        generator = ReportGenerator(logger=logger)

        params = {'report_date': '2026-02-10'}

        analysis = {
            'short_term_suggestions': [
                '优化注册流程',
                '提升首日留存'
            ],
            'medium_term_suggestions': [
                '增加用户引导',
                '优化推荐算法'
            ],
            'long_term_suggestions': [
                '拓展国际市场',
                '开发新功能'
            ]
        }

        html = generator.render_suggestions_section(params, analysis)

        assert isinstance(html, str)
        assert len(html) > 0

    def test_generate_full_report_html(self, logger):
        """测试生成完整HTML报告"""
        generator = ReportGenerator(logger=logger)

        params = {
            'report_date': '2026-02-10',
            'data_week': '20260210',
            'data_end_date': '2026-02-09',
            'database_id': 2
        }

        current_data = {}
        previous_data = {}

        # 测试空数据情况
        full_html = generator.generate_full_report_html(
            params,
            current_data,
            previous_data,
            {},
            None
        )

        assert isinstance(full_html, str)
        assert len(full_html) > 0
        assert 'Coohom平台整体数据' in full_html


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
