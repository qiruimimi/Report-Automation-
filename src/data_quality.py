#!/usr/bin/env python3
"""
数据质量模块

统一数据验证和质量分析功能
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
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


class DataQualityAnalyzer:
    """数据质量分析器"""

    def __init__(self, logger=None):
        self.logger = logger or get_logger('data_quality')
        self.validator = DataValidator(logger)

    def generate_quality_report(
        self,
        all_sections_data: Dict[str, List[Dict]],
        all_sections_analysis: Optional[Dict[str, Dict]] = None
    ) -> Dict:
        """
        生成数据质量报告

        Args:
            all_sections_data: 所有部分的数据字典
            all_sections_analysis: 所有部分的分析结果（可选）

        Returns:
            Dict: 数据质量报告
        """
        self.logger.info("生成数据质量报告...")

        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'overall_status': 'success',
            'sections': {},
            'summary': {
                'total_sections': len(all_sections_data),
                'valid_sections': 0,
                'warning_sections': 0,
                'error_sections': 0,
                'total_anomalies': 0
            },
            'recommendations': []
        }

        # 分析每个部分
        for section_name, data in all_sections_data.items():
            section_report = self._analyze_section(
                section_name,
                data,
                all_sections_analysis.get(section_name, {}) if all_sections_analysis else {}
            )
            report['sections'][section_name] = section_report

            # 更新统计信息
            if section_report['status'] == 'success':
                report['summary']['valid_sections'] += 1
            elif section_report['status'] == 'warning':
                report['summary']['warning_sections'] += 1
            else:
                report['summary']['error_sections'] += 1

            report['summary']['total_anomalies'] += len(section_report.get('anomalies', []))

        # 确定整体状态
        if report['summary']['error_sections'] > 0:
            report['overall_status'] = 'error'
        elif report['summary']['warning_sections'] > 0:
            report['overall_status'] = 'warning'

        # 生成建议
        report['recommendations'] = self._generate_recommendations(report)

        self.logger.info(f"✅ 数据质量报告生成完成: {report['overall_status']}")

        return report

    def _analyze_section(
        self,
        section_name: str,
        data: List[Dict],
        analysis: Dict
    ) -> Dict:
        """
        分析单个部分的数据质量

        Args:
            section_name: 部分名称
            data: 数据
            analysis: 分析结果

        Returns:
            Dict: 部分数据质量报告
        """
        section_report = {
            'name': section_name,
            'status': 'success',
            'data_count': len(data) if data else 0,
            'completeness': {'valid': True, 'issues': []},
            'anomalies': [],
            'notes': []
        }

        # 数据完整性检查
        is_valid, issues = self.validator.validate_data_completeness(section_name, data)
        section_report['completeness']['valid'] = is_valid
        section_report['completeness']['issues'] = issues

        if not is_valid:
            section_report['status'] = 'error'

        # 如果有上周数据，进行异常检测
        if analysis and 'previous_data' in analysis:
            anomalies = self.validator.check_anomalies(
                section_name,
                data,
                analysis['previous_data']
            )
            section_report['anomalies'] = anomalies

            if anomalies:
                section_report['status'] = 'warning'

        # 添加注意项
        if section_name == 'revenue' and not data:
            section_report['notes'].append('收入数据为空，可能是正常周期或数据源问题')

        if section_name == 'activation' and len(data) < 4:
            section_report['notes'].append('激活数据行数不足，可能漏斗步骤不完整')

        return section_report

    def _generate_recommendations(self, report: Dict) -> List[str]:
        """
        根据报告生成改进建议

        Args:
            report: 数据质量报告

        Returns:
            List[str]: 改进建议列表
        """
        recommendations = []

        # 基于异常数量生成建议
        if report['summary']['total_anomalies'] > 3:
            recommendations.append(
                f"⚠️ 发现 {report['summary']['total_anomalies']} 个数据异常，"
                f"建议检查数据源和计算逻辑，排除系统问题"
            )

        # 基于错误部分生成建议
        if report['summary']['error_sections'] > 0:
            recommendations.append(
                f"❌ {report['summary']['error_sections']} 个部分存在数据完整性问题，"
                f"建议检查数据采集和传输过程"
            )

        # 基于各部分状态生成建议
        for section_name, section_report in report['sections'].items():
            if section_report['status'] == 'error':
                recommendations.append(
                    f"❌ {section_name} 部分数据完整性检查失败，"
                    f"问题: {', '.join(section_report['completeness']['issues'])}"
                )
            elif section_report['status'] == 'warning':
                anomaly_count = len(section_report.get('anomalies', []))
                recommendations.append(
                    f"⚠️ {section_name} 部分发现 {anomaly_count} 个数据异常，"
                    f"建议验证数据变化的合理性"
                )

        # 如果没有严重问题
        if report['overall_status'] == 'success':
            recommendations.append("✅ 所有数据部分质量良好，可以正常生成报告")

        return recommendations

    def save_report_to_file(
        self,
        report: Dict,
        output_path: str
    ) -> None:
        """
        保存质量报告到文件

        Args:
            report: 数据质量报告
            output_path: 输出文件路径
        """
        self.logger.info(f"保存数据质量报告到: {output_path}")

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 生成Markdown格式报告
        md_content = self._format_report_as_markdown(report)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        self.logger.info("✅ 数据质量报告已保存")

    def _format_report_as_markdown(self, report: Dict) -> str:
        """
        将报告格式化为Markdown

        Args:
            report: 数据质量报告

        Returns:
            str: Markdown格式报告
        """
        lines = [
            "# 数据质量报告",
            "",
            f"**生成时间**: {report['timestamp']}",
            f"**整体状态**: {self._get_status_emoji(report['overall_status'])} {report['overall_status'].upper()}",
            "",
            "---",
            "",
            "## 📊 总体概览",
            "",
            f"- 总部分数: {report['summary']['total_sections']}",
            f"- 通过部分: {report['summary']['valid_sections']}",
            f"- 警告部分: {report['summary']['warning_sections']}",
            f"- 错误部分: {report['summary']['error_sections']}",
            f"- 异常总数: {report['summary']['total_anomalies']}",
            "",
            "---",
            "",
            "## 📋 各部分详情",
            ""
        ]

        # 各部分详情
        for section_name, section_report in report['sections'].items():
            lines.extend([
                f"### {self._get_section_display_name(section_name)}",
                "",
                f"- **状态**: {self._get_status_emoji(section_report['status'])} {section_report['status'].upper()}",
                f"- **数据行数**: {section_report['data_count']}",
                ""
            ])

            # 完整性问题
            if section_report['completeness']['issues']:
                lines.extend([
                    "**完整性问题**:",
                    ""
                ])
                for issue in section_report['completeness']['issues']:
                    lines.append(f"  - {issue}")
                lines.append("")

            # 异常信息
            if section_report['anomalies']:
                lines.extend([
                    "**数据异常**:",
                    ""
                ])
                for anomaly in section_report['anomalies']:
                    lines.append(f"  - {anomaly['message']} (严重程度: {anomaly['severity']})")
                lines.append("")

            # 注意项
            if section_report['notes']:
                lines.extend([
                    "**注意项**:",
                    ""
                ])
                for note in section_report['notes']:
                    lines.append(f"  - {note}")
                lines.append("")

        # 建议
        lines.extend([
            "---",
            "",
            "## 💡 改进建议",
            ""
        ])
        for recommendation in report['recommendations']:
            lines.append(f"- {recommendation}")
        lines.append("")

        return '\n'.join(lines)

    @staticmethod
    def _get_status_emoji(status: str) -> str:
        """获取状态对应的emoji"""
        emoji_map = {
            'success': '✅',
            'warning': '⚠️',
            'error': '❌'
        }
        return emoji_map.get(status, '❓')

    @staticmethod
    def _get_section_display_name(section_name: str) -> str:
        """获取部分显示名称"""
        name_map = {
            'traffic': '流量',
            'activation': '激活',
            'engagement': '活跃',
            'retention': '留存',
            'revenue': '收入'
        }
        return name_map.get(section_name, section_name)


if __name__ == "__main__":
    # 测试代码
    print("测试数据验证器\n")

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

    print("\n" + "="*50 + "\n")
    print("测试数据质量分析器\n")

    analyzer = DataQualityAnalyzer()

    # 测试数据
    test_data = {
        'traffic': [
            {'new_visitors': 1000, 'registrations': 500, 'conversion_rate': 50}
        ],
        'engagement': [
            {'wau': 50000, 'new_user_wau': 20000, 'old_user_wau': 30000}
        ]
    }

    test_analysis = {
        'engagement': {
            'previous_data': [
                {'wau': 45000, 'new_user_wau': 18000, 'old_user_wau': 27000}
            ]
        }
    }

    # 生成报告
    report = analyzer.generate_quality_report(test_data, test_analysis)

    # 打印报告
    print(f"整体状态: {report['overall_status']}")
    print(f"异常总数: {report['summary']['total_anomalies']}")
    print("\n建议:")
    for rec in report['recommendations']:
        print(f"  {rec}")

    # 保存报告
    analyzer.save_report_to_file(
        report,
        '/tmp/data_quality_report.md'
    )
    print("\n报告已保存到 /tmp/data_quality_report.md")
