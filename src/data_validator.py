#!/usr/bin/env python3
"""
数据验证模块

实现数据完整性校验、异常检测
"""

from typing import Dict, List, Optional, Tuple, Any
from src.logger import get_logger


class DataValidator:
    """数据验证器 - 用于数据验证和异常检测"""

    def __init__(self, logger=None):
        self.logger = logger or get_logger('data_validator')

        # 定义各部分的关键字段
        self.required_fields = {
            'traffic': ['new_visitors', 'registrations', 'conversion_rate'],
            'activation': ['step1_rate', 'step2_rate', 'step3_rate', 'step4_rate'],
            'engagement': ['wau', 'new_user_wau', 'old_user_wau'],
            'retention': ['new_user_retention_rate', 'old_user_retention_rate'],
            'revenue': ['total_revenue', 'renewal_revenue', 'new_signing_revenue']
        }

        # 定义异常阈值（百分比）
        self.anomaly_thresholds = {
            'traffic': {
                'new_visitors': 50,      # 新访客波动超过50%为异常
                'registrations': 50,      # 注册数波动超过50%为异常
                'conversion_rate': 20       # 转化率波动超过20%为异常
            },
            'engagement': {
                'wau': 30,             # WAU波动超过30%为异常
                'new_user_wau': 40,      # 新用户WAU波动超过40%为异常
                'old_user_wau': 20        # 老用户WAU波动超过20%为异常
            },
            'retention': {
                'new_user_retention_rate': 15,  # 新用户留存波动超过15%为异常
                'old_user_retention_rate': 10    # 老用户留存波动超过10%为异常
            },
            'revenue': {
                'total_revenue': 30,      # 总收入波动超过30%为异常
                'renewal_revenue': 40,    # 续约收入波动超过40%为异常
                'new_signing_revenue': 50  # 新签收入波动超过50%为异常
            }
        }

    def validate_data_completeness(
        self,
        section_name: str,
        data: List[Dict],
        raise_on_error: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        验证数据完整性

        Args:
            section_name: 部分名称 (traffic, activation, engagement, retention, revenue)
            data: 数据列表
            raise_on_error: 发现错误时是否抛出异常

        Returns:
            Tuple[bool, List[str]]: (是否有效, 问题列表)
        """
        self.logger.debug(f"验证 {section_name} 数据完整性...")

        issues = []

        # 检查数据是否为空
        if not data:
            issues.append(f"{section_name} 数据为空")
            if raise_on_error:
                raise ValueError(f"{section_name} 数据为空")
            return False, issues

        # 检查关键字段是否存在
        required = self.required_fields.get(section_name, [])
        if required:
            for row in data:
                missing_fields = [f for f in required if f not in row or row[f] is None]
                if missing_fields:
                    issues.append(f"{section_name} 数据缺少字段: {', '.join(missing_fields)}")

        # 检查数值字段是否合理
        for row in data:
            for key, value in row.items():
                if isinstance(value, (int, float)):
                    # 检查负值
                    if value < 0 and key not in ['change_rate', 'change_abs', 'growth_rate']:
                        issues.append(f"{section_name} 数据中发现负值: {key}={value}")

        is_valid = len(issues) == 0

        if not is_valid:
            self.logger.warning(f"{section_name} 数据完整性检查失败: {issues}")

        return is_valid, issues

    def check_anomalies(
        self,
        section_name: str,
        current_data: List[Dict],
        previous_data: List[Dict],
        key_field: str = None
    ) -> List[Dict[str, Any]]:
        """
        检查数据异常（环比波动）

        Args:
            section_name: 部分名称
            current_data: 本周数据
            previous_data: 上周数据
            key_field: 用于比较的字段（可选）

        Returns:
            List[Dict]: 异常列表
        """
        self.logger.debug(f"检查 {section_name} 数据异常...")

        anomalies = []

        if not current_data or not previous_data:
            return anomalies

        # 获取阈值配置
        thresholds = self.anomaly_thresholds.get(section_name, {})

        # 如果未指定字段，使用第一个数值字段
        if key_field is None:
            for key in current_data[0].keys():
                if key in thresholds:
                    key_field = key
                    break

        if key_field is None:
            return anomalies

        # 提取当前值和上周值
        current_value = self._extract_numeric_value(current_data[0], key_field)
        previous_value = self._extract_numeric_value(previous_data[0], key_field)

        if current_value is None or previous_value is None:
            return anomalies

        # 计算环比变化率
        if previous_value == 0:
            change_rate = float('inf') if current_value > 0 else 0
        else:
            change_rate = abs((current_value - previous_value) / previous_value) * 100

        # 检查是否超过阈值
        threshold = thresholds.get(key_field, 30)  # 默认30%

        if change_rate > threshold:
            direction = '增长' if current_value > previous_value else '下降'
            anomalies.append({
                'section': section_name,
                'field': key_field,
                'previous_value': previous_value,
                'current_value': current_value,
                'change_rate': change_rate,
                'threshold': threshold,
                'severity': self._get_severity(change_rate, threshold),
                'message': f"{section_name}.{key_field} {direction}{change_rate:.1f}%，超过阈值{threshold}%"
            })
            self.logger.warning(f"{section_name} 异常检测: {key_field} {direction}{change_rate:.1f}%")

        return anomalies

    @staticmethod
    def _extract_numeric_value(row: Dict, key: str) -> Optional[float]:
        """从行中提取数值"""
        value = row.get(key)
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _get_severity(change_rate: float, threshold: float) -> str:
        """获取异常严重程度"""
        ratio = change_rate / threshold
        if ratio > 2.0:
            return 'critical'
        elif ratio > 1.5:
            return 'high'
        elif ratio > 1.0:
            return 'medium'
        return 'low'

    def validate_all_sections(
        self,
        all_sections_data: Dict[str, List[Dict]],
        raise_on_error: bool = False
    ) -> Dict[str, Dict]:
        """
        验证所有部分的数据完整性

        Args:
            all_sections_data: 所有部分的数据字典
            raise_on_error: 发现错误时是否抛出异常

        Returns:
            Dict: 各部分的验证结果
                {
                    'traffic': {'valid': bool, 'issues': List[str]},
                    'activation': {'valid': bool, 'issues': List[str]},
                    ...
                }
        """
        self.logger.info("验证所有部分数据完整性...")

        results = {}

        for section_name, data in all_sections_data.items():
            is_valid, issues = self.validate_data_completeness(
                section_name,
                data,
                raise_on_error
            )
            results[section_name] = {
                'valid': is_valid,
                'issues': issues,
                'data_count': len(data) if data else 0
            }

        return results


if __name__ == "__main__":
    # 测试代码
    print("测试数据验证模块\n")

    validator = DataValidator()

    # 测试数据完整性检查
    test_data = [
        {'new_visitors': 1000, 'registrations': 500, 'conversion_rate': 50},
        {'new_visitors': 2000, 'registrations': 1000, 'conversion_rate': 50}
    ]

    is_valid, issues = validator.validate_data_completeness('traffic', test_data)
    print(f"数据完整性验证: {'通过' if is_valid else '失败'}")
    if issues:
        print(f"问题: {issues}")

    # 测试异常检测
    current_data = [{'new_visitors': 2000}]
    previous_data = [{'new_visitors': 1000}]
    anomalies = validator.check_anomalies('traffic', current_data, previous_data, 'new_visitors')
    print(f"\n异常检测结果: 发现 {len(anomalies)} 个异常")
    for anomaly in anomalies:
        print(f"  - {anomaly['message']}")
