#!/usr/bin/env python3
"""
数据验证器测试

测试data_validator模块的数据验证和异常检测功能
"""

import pytest
from src.data_quality import DataValidator


class TestDataValidator:
    """数据验证器测试类"""

    def test_validate_traffic_data_valid(self, sample_traffic_data):
        """测试验证有效的流量数据"""
        validator = DataValidator()

        is_valid, issues = validator.validate_data_completeness('traffic', sample_traffic_data)

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_revenue_data_valid(self, sample_revenue_data):
        """测试验证有效的收入数据"""
        validator = DataValidator()

        is_valid, issues = validator.validate_data_completeness('revenue', sample_revenue_data)

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_empty_data(self):
        """测试验证空数据"""
        validator = DataValidator()

        is_valid, issues = validator.validate_data_completeness('traffic', [])

        assert is_valid is False
        assert len(issues) > 0
        assert '数据为空' in issues[0]

    def test_validate_data_missing_fields(self):
        """测试验证缺少字段的数据"""
        validator = DataValidator()

        # 缺少必需字段的数据
        incomplete_data = [{'new_visitors': 1000}]  # 缺少registrations和conversion_rate

        is_valid, issues = validator.validate_data_completeness('traffic', incomplete_data)

        assert is_valid is False
        assert len(issues) > 0

    def test_check_anomalies_no_anomaly(self, sample_traffic_data, logger):
        """测试无异常数据检测"""
        validator = DataValidator(logger)

        # 相似的数据，无异常
        previous_data = [{'new_visitors': 10500, 'registrations': 5200}]

        anomalies = validator.check_anomalies('traffic', sample_traffic_data, previous_data, 'new_visitors')

        assert len(anomalies) == 0

    def test_check_anomalies_with_anomaly(self, logger):
        """测试有异常数据检测"""
        validator = DataValidator(logger)

        # 当前值比上周高60%，超过50%阈值 (ratio=1.2, 应为medium)
        current_data = [{'new_visitors': 16000}]
        previous_data = [{'new_visitors': 10000}]

        anomalies = validator.check_anomalies('traffic', current_data, previous_data, 'new_visitors')

        assert len(anomalies) == 1
        assert anomalies[0]['severity'] == 'medium'  # 60/50=1.2, 在1.0-1.5之间为medium
        assert '60.0%' in anomalies[0]['message']

    def test_check_anomalies_critical_severity(self, logger):
        """测试严重异常检测"""
        validator = DataValidator(logger)

        # 当前值比上周高3倍，超过阈值的2倍
        current_data = [{'new_visitors': 30000}]
        previous_data = [{'new_visitors': 10000}]

        anomalies = validator.check_anomalies('traffic', current_data, previous_data, 'new_visitors')

        assert len(anomalies) == 1
        assert anomalies[0]['severity'] == 'critical'

    def test_validate_all_sections(self, sample_traffic_data, sample_revenue_data, logger):
        """测试验证所有部分"""
        validator = DataValidator(logger)

        all_sections = {
            'traffic': sample_traffic_data,
            'revenue': sample_revenue_data,
            'engagement': [],  # 空数据
            'retention': None  # None数据
        }

        results = validator.validate_all_sections(all_sections)

        assert 'traffic' in results
        assert 'revenue' in results
        assert 'engagement' in results
        assert 'retention' in results

        # 验证结果结构
        for section_name, result in results.items():
            assert 'valid' in result
            assert 'issues' in result
            assert 'data_count' in result

    def test_extract_numeric_value(self):
        """测试提取数值"""
        validator = DataValidator()

        # 测试正常数值
        assert validator._extract_numeric_value({'value': 100}, 'value') == 100.0

        # 测试字符串数值
        assert validator._extract_numeric_value({'value': '100'}, 'value') == 100.0

        # 测试None值
        assert validator._extract_numeric_value({'value': None}, 'value') is None

        # 测试无效字符串
        assert validator._extract_numeric_value({'value': 'abc'}, 'value') is None

    def test_get_severity_levels(self):
        """测试严重程度判断"""
        validator = DataValidator()

        # 低严重程度 (ratio <= 1.0)
        assert validator._get_severity(40, 50) == 'low'
        assert validator._get_severity(50, 50) == 'low'

        # 中等严重程度 (1.0 < ratio <= 1.5)
        assert validator._get_severity(60, 50) == 'medium'

        # 高严重程度 (1.5 < ratio <= 2.0)
        assert validator._get_severity(80, 50) == 'high'

        # 严重 (ratio > 2.0)
        assert validator._get_severity(110, 50) == 'critical'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
