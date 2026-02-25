#!/usr/bin/env python3
"""
端到端集成测试

测试完整的周报生成流程
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.report_generator import ReportGenerator
from src.data_validator import DataValidator
from src.data_quality import DataQualityAnalyzer


class TestEndToEnd:
    """端到端测试类"""

    @pytest.fixture
    def mock_report_data(self):
        """模拟完整报告数据"""
        return {
            'params': {
                'report_date': '2026-02-10',
                'data_week': '20260210',
                'data_end_date': '2026-02-09',
                'database_id': 2
            },
            'current_data': {
                'traffic': [
                    {'new_visitors': 10000, 'registrations': 5000, 'conversion_rate': 50.0}
                ],
                'revenue': [
                    {'total_revenue': 100000, 'renewal_revenue': 60000, 'new_signing_revenue': 40000}
                ],
                'engagement': [
                    {'wau': 50000, 'new_user_wau': 20000, 'old_user_wau': 30000}
                ],
                'retention': [
                    {'new_user_retention_rate': 45.0, 'old_user_retention_rate': 60.0}
                ]
            },
            'previous_data': {
                'traffic': [
                    {'new_visitors': 9500, 'registrations': 4800, 'conversion_rate': 50.5}
                ],
                'revenue': [
                    {'total_revenue': 90000, 'renewal_revenue': 54000, 'new_signing_revenue': 36000}
                ],
                'engagement': [
                    {'wau': 48000, 'new_user_wau': 18000, 'old_user_wau': 30000}
                ],
                'retention': [
                    {'new_user_retention_rate': 44.0, 'old_user_retention_rate': 59.0}
                ]
            },
            'analysis': {
                'traffic': {
                    'new_visitors_current': 10000,
                    'registrations_current': 5000,
                    'conversion_rate_current': 50.0,
                    'visitors_wow': {'change_rate': 5.26},
                    'registrations_wow': {'change_rate': 4.17},
                    'conversion_rate_wow': {'change_rate': -1.0},
                    'attention_items': []
                },
                'revenue': {
                    'total_current': 100000,
                    'total_previous': 90000,
                    'wow': {'change_abs': 10000, 'change_rate': 11.11},
                    'renewal_revenue': 60000,
                    'new_signing_revenue': 40000,
                    'renewal_growth_rate': 11.11,
                    'new_signing_growth_rate': 11.11,
                    'ai_summary': 'AI生成的收入分析',
                    'revenue_type': '订阅收入',
                    'user_count': 100,
                    'average_order_value': 1000,
                    'historical_avg_revenue': 95000,
                    'historical_trends': [],
                    'attention_items': []
                },
                'engagement': {
                    'wau_current': 50000,
                    'wau_wow': {'change_rate': 4.17},
                    'wau_contribution': '新老用户共同贡献',
                    'new_user_wau': 20000,
                    'new_user_wau_wow': 11.11,
                    'old_user_wau': 30000,
                    'old_user_wau_wow': 0.0,
                    'historical_weeks': 25,
                    'historical_avg_wau': 48000,
                    'historical_trends': [],
                    'attention_items': []
                },
                'retention': {
                    'new_user_retention_rate': 45.0,
                    'new_user_retention_previous': 44.0,
                    'new_user_retention_current': 45.0,
                    'new_user_retention_min': 40.0,
                    'new_user_retention_max': 48.0,
                    'new_user_retention_level': '中等',
                    'old_user_retention_rate': 60.0,
                    'old_user_retention_previous': 59.0,
                    'old_user_retention_current': 60.0,
                    'old_user_retention_min': 55.0,
                    'old_user_retention_max': 62.0,
                    'old_user_retention_change': 1.69,
                    'old_user_trend_note': '需要关注',
                    'historical_new_user_avg': 44.0,
                    'historical_old_user_avg': 59.0,
                    'historical_trends': [],
                    'insights': []
                },
                'insights': {
                    'positive_insights': ['留存率稳定增长', '收入结构优化'],
                    'negative_insights': ['流量增长放缓'],
                    'key_findings': ['新用户转化率提升']
                },
                'suggestions': {
                    'short_term_suggestions': ['优化注册流程'],
                    'medium_term_suggestions': ['增加用户引导'],
                    'long_term_suggestions': ['拓展国际市场']
                }
            }
        }

    def test_full_report_generation(self, mock_report_data, logger):
        """测试完整报告生成"""
        generator = ReportGenerator(logger=logger)

        html = generator.generate_full_report_html(
            mock_report_data['params'],
            mock_report_data['current_data'],
            mock_report_data['previous_data'],
            mock_report_data['analysis'],
            None
        )

        # 验证HTML包含所有部分
        assert '流量' in html
        assert '收入' in html
        assert '活跃' in html
        assert '留存' in html
        assert '洞察' in html
        assert '建议' in html

        # 验证报告日期
        assert mock_report_data['params']['report_date'] in html

    def test_markdown_report_generation(self, mock_report_data, logger):
        """测试Markdown报告生成"""
        generator = ReportGenerator(logger=logger)

        md = generator.generate_full_report_markdown(
            mock_report_data['params'],
            mock_report_data['current_data'],
            mock_report_data['previous_data'],
            mock_report_data['analysis'],
            None
        )

        # 验证Markdown包含所有部分
        assert '## 1.流量' in md
        assert '## 2.激活' in md
        assert '## 3.活跃' in md
        assert '## 4.留存' in md
        assert '## 5.收入' in md
        assert '## 6.核心洞察与建议' in md

    def test_data_validation_pipeline(self, mock_report_data, logger):
        """测试数据验证流程"""
        validator = DataValidator(logger)

        # 验证所有部分
        results = validator.validate_all_sections(mock_report_data['current_data'])

        # 验证结果包含所有部分
        assert 'traffic' in results
        assert 'revenue' in results
        assert 'engagement' in results
        assert 'retention' in results

        # 验证测试数据应该通过验证
        assert results['traffic']['valid'] is True
        assert results['revenue']['valid'] is True
        assert results['engagement']['valid'] is True
        assert results['retention']['valid'] is True

    def test_data_quality_analysis(self, mock_report_data, logger):
        """测试数据质量分析"""
        analyzer = DataQualityAnalyzer(logger)

        report = analyzer.generate_quality_report(
            mock_report_data['current_data'],
            mock_report_data['analysis']
        )

        # 验证报告结构
        assert 'timestamp' in report
        assert 'overall_status' in report
        assert 'sections' in report
        assert 'summary' in report
        assert 'recommendations' in report

        # 验证摘要信息
        assert report['summary']['total_sections'] == 4
        assert report['summary']['total_anomalies'] >= 0

    def test_output_file_writing(self, mock_report_data, logger, tmp_path):
        """测试输出文件写入"""
        generator = ReportGenerator(logger=logger)

        # 生成HTML报告
        html = generator.generate_full_report_html(
            mock_report_data['params'],
            mock_report_data['current_data'],
            mock_report_data['previous_data'],
            mock_report_data['analysis'],
            None
        )

        # 写入文件
        output_file = tmp_path / 'test_report.html'
        output_file.write_text(html, encoding='utf-8')

        # 验证文件存在
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_error_handling_with_missing_data(self, logger):
        """测试缺失数据的错误处理"""
        generator = ReportGenerator(logger=logger)

        params = {
            'report_date': '2026-02-10',
            'data_week': '20260210',
            'database_id': 2
        }

        # 缺失部分数据
        current_data = {
            'traffic': []
        }
        previous_data = {}
        analysis = {}

        # 应该不会崩溃，返回空报告
        html = generator.generate_full_report_html(
            params,
            current_data,
            previous_data,
            analysis,
            None
        )

        assert isinstance(html, str)
        assert len(html) > 0

    def test_template_caching(self, logger):
        """测试模板缓存"""
        generator = ReportGenerator(logger=logger)

        # 第一次加载
        template1 = generator._get_template('sections/traffic.html')
        assert template1 is not None

        # 第二次加载（应该从缓存获取）
        template2 = generator._get_template('sections/traffic.html')
        assert template2 is not None
        assert template1 == template2


class TestIntegrationWithMocks:
    """使用Mock的集成测试"""

    @patch('src.report_generator.Jinja2')
    def test_jinja2_integration_error_handling(self, mock_jinja2, logger):
        """测试Jinja2集成错误处理"""
        # 模拟模板加载失败
        mock_jinja2.FileSystemLoader.return_value.list_templates.side_effect = Exception("模板错误")

        generator = ReportGenerator(logger=logger)

        params = {
            'report_date': '2026-02-10',
            'data_week': '20260210',
            'database_id': 2
        }

        # 应该优雅地处理错误
        html = generator.generate_full_report_html(
            params,
            {},
            {},
            {},
            None
        )

        # 验证返回结果
        assert isinstance(html, str)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
