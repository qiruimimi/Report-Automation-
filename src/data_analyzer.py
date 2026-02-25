#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析模块

分析从Metabase获取的数据，计算环比、转化率等指标
"""

from typing import Dict, List, Optional
from src.logger import get_logger


class DataAnalyzer:
    """数据分析器"""

    def __init__(self, logger=None):
        """
        初始化数据分析器

        Args:
            logger: 日志记录器
        """
        self.logger = logger or get_logger('data_analyzer')

    def calculate_week_over_week(self, current: Optional[float], previous: Optional[float]) -> Dict:
        """
        计算环比变化

        Args:
            current: 当前值
            previous: 上期值

        Returns:
            dict: 包含change_rate, change_abs, trend的字典
        """
        if current is None:
            current = 0
        if previous is None or previous == 0:
            return {
                'change_rate': 0,
                'change_abs': current,
                'trend': '→'
            }

        change_abs = current - previous
        change_rate = (change_abs / previous) * 100 if previous != 0 else 0

        if change_rate > 0:
            trend = '↑'
        elif change_rate < 0:
            trend = '↓'
        else:
            trend = '→'

        return {
            'change_rate': round(change_rate, 1),
            'change_abs': round(change_abs),
            'trend': trend
        }

    def analyze_all_sections(
        self,
        current_data: Dict[str, List[Dict]],
        previous_data: Dict[str, List[Dict]]
    ) -> Dict:
        """
        分析所有部分的数据

        Args:
            current_data: 本周所有数据
            previous_data: 上周所有数据

        Returns:
            dict: 所有分析结果
        """
        self.logger.info("开始分析所有部分...")

        results = {}

        # 流量分析
        if 'traffic' in current_data:
            results['traffic'] = self.analyze_traffic_data(
                current_data['traffic'],
                previous_data.get('traffic', [])
            )

        # 激活分析
        if 'activation' in current_data:
            results['activation'] = self.analyze_activation_data(
                current_data['activation'],
                previous_data.get('activation', [])
            )

        # 活跃分析
        if 'engagement' in current_data:
            results['engagement'] = self.analyze_engagement_data(
                current_data['engagement'],
                previous_data.get('engagement', [])
            )

        # 留存分析
        if 'retention' in current_data:
            results['retention'] = self.analyze_retention_data(
                current_data['retention'],
                previous_data.get('retention', [])
            )

        # 收入分析
        if 'revenue' in current_data:
            results['revenue'] = self.analyze_revenue_data(
                current_data['revenue'],
                previous_data.get('revenue', [])
            )

        self.logger.info("✅ 所有部分分析完成")
        return results

    def analyze_traffic_data(
        self,
        current_data: List[Dict],
        previous_data: List[Dict]
    ) -> Dict:
        """
        分析流量数据

        Args:
            current_data: 本周流量数据
            previous_data: 上周流量数据

        Returns:
            dict: 流量分析结果
        """
        self.logger.info("分析流量数据...")

        # 汇总当前周的新访客数和注册数
        total_new_visitors = 0
        total_new_registrations = 0
        total_registrations = 0

        for row in current_data:
            if '新访客数' in row:
                total_new_visitors += row.get('新访客数', 0) or 0
            if '新访客注册数' in row:
                total_new_registrations += row.get('新访客注册数', 0) or 0
            # 注册总数（包含所有注册用户）
            if '注册数' in row:
                total_registrations += row.get('注册数', 0) or 0

        # 汇总上周数据
        total_new_visitors_prev = 0
        total_new_registrations_prev = 0
        total_registrations_prev = 0

        for row in previous_data:
            if '新访客数' in row:
                total_new_visitors_prev += row.get('新访客数', 0) or 0
            if '新访客注册数' in row:
                total_new_registrations_prev += row.get('新访客注册数', 0) or 0
            if '注册数' in row:
                total_registrations_prev += row.get('注册数', 0) or 0

        # 计算转化率
        conversion_rate_current = (total_new_registrations / total_new_visitors * 100) if total_new_visitors > 0 else 0
        conversion_rate_previous = (total_new_registrations_prev / total_new_visitors_prev * 100) if total_new_visitors_prev > 0 else 0

        # 计算环比
        visitors_wow = self.calculate_week_over_week(total_new_visitors, total_new_visitors_prev)
        registrations_wow = self.calculate_week_over_week(total_new_registrations, total_new_registrations_prev)
        conversion_wow = self.calculate_week_over_week(conversion_rate_current, conversion_rate_previous)

        result = {
            'new_visitors_current': total_new_visitors,
            'new_visitors_previous': total_new_visitors_prev,
            'registrations_current': total_new_registrations,
            'registrations_previous': total_new_registrations_prev,
            'conversion_rate_current': round(conversion_rate_current, 2),
            'conversion_rate_previous': round(conversion_rate_previous, 2),
            'visitors_wow': visitors_wow,
            'registrations_wow': registrations_wow,
            'conversion_rate_wow': conversion_wow,
            'attention_items': [],
            'summary': f"总新访客 {total_new_visitors:,}，环比{visitors_wow['trend']} {visitors_wow['change_rate']:+.1f}%"
        }

        self.logger.info(f"✅ 流量数据分析完成: {result['summary']}")
        return result

    def analyze_activation_data(
        self,
        current_data: List[Dict],
        previous_data: List[Dict]
    ) -> Dict:
        """
        分析激活数据（漏斗）

        Args:
            current_data: 本周激活数据
            previous_data: 上周激活数据

        Returns:
            dict: 激活分析结果
        """
        self.logger.info("分析激活数据...")

        # 本周数据
        new_registered_users = 0
        entered_tool_users = 0
        valid_design_users = 0
        valid_model_users = 0
        render_users = 0

        for row in current_data:
            if '新注册用户数' in row:
                new_registered_users += row.get('新注册用户数', 0) or 0
            if '进工具用户数' in row:
                entered_tool_users += row.get('进工具用户数', 0) or 0
            if '有效画户型用户数' in row:
                valid_design_users += row.get('有效画户型用户数', 0) or 0
            if '有效拖模型用户数' in row:
                valid_model_users += row.get('有效拖模型用户数', 0) or 0
            if '渲染用户数' in row:
                render_users += row.get('渲染用户数', 0) or 0

        # 计算各阶段转化率
        step1_rate = (entered_tool_users / new_registered_users * 100) if new_registered_users > 0 else 0
        step2_rate = (valid_design_users / entered_tool_users * 100) if entered_tool_users > 0 else 0
        step3_rate = (valid_model_users / valid_design_users * 100) if valid_design_users > 0 else 0
        step4_rate = (render_users / valid_model_users * 100) if valid_model_users > 0 else 0

        # 上周数据（简化处理，取第一条记录）
        previous_week_data = previous_data[0] if previous_data else {}
        step1_prev_rate = previous_week_data.get('注册到进工具转化率', 0) or 0
        step2_prev_rate = previous_week_data.get('进工具到有效画户型转化率', 0) or 0
        step3_prev_rate = previous_week_data.get('有效画户型到有效拖模型转化率', 0) or 0
        step4_prev_rate = previous_week_data.get('有效拖模型到渲染转化率', 0) or 0

        result = {
            'new_registered_users': new_registered_users,
            'step1_current_rate': round(step1_rate, 2),
            'step1_previous_rate': round(step1_prev_rate, 2),
            'step1_change_rate': round(step1_rate - step1_prev_rate, 2),
            'step2_current_rate': round(step2_rate, 2),
            'step2_previous_rate': round(step2_prev_rate, 2),
            'step2_change_rate': round(step2_rate - step2_prev_rate, 2),
            'step3_current_rate': round(step3_rate, 2),
            'step3_previous_rate': round(step3_prev_rate, 2),
            'step3_change_rate': round(step3_rate - step3_prev_rate, 2),
            'step4_current_rate': round(step4_rate, 2),
            'step4_previous_rate': round(step4_prev_rate, 2),
            'step4_change_rate': round(step4_rate - step4_prev_rate, 2),
            'previous_week_label': '上周',
            'current_week_label': '本周',
            'is_current_week_incomplete': False,
            'current_week_metrics': [],
            'core_insights': [],
            'attention_items': []
        }

        self.logger.info(f"✅ 激活数据分析完成")
        return result

    def analyze_engagement_data(
        self,
        current_data: List[Dict],
        previous_data: List[Dict]
    ) -> Dict:
        """
        分析活跃数据

        Args:
            current_data: 本周活跃数据
            previous_data: 上周活跃数据

        Returns:
            dict: 活跃分析结果
        """
        self.logger.info("分析活跃数据...")

        # 新老用户WAU数据
        new_user_wau = 0
        old_user_wau = 0
        new_user_wau_prev = 0
        old_user_wau_prev = 0

        for row in current_data:
            if '新用户WAU' in row:
                new_user_wau = row.get('新用户WAU', 0) or 0
            if '老用户WAU' in row:
                old_user_wau = row.get('老用户WAU', 0) or 0

        for row in previous_data:
            if '新用户WAU' in row:
                new_user_wau_prev = row.get('新用户WAU', 0) or 0
            if '老用户WAU' in row:
                old_user_wau_prev = row.get('老用户WAU', 0) or 0

        # 计算总WAU和环比
        total_wau_current = new_user_wau + old_user_wau
        total_wau_previous = new_user_wau_prev + old_user_wau_prev
        wau_wow = self.calculate_week_over_week(total_wau_current, total_wau_previous)

        # 新老用户环比
        new_user_wow = self.calculate_week_over_week(new_user_wau, new_user_wau_prev)
        old_user_wow = self.calculate_week_over_week(old_user_wau, old_user_wau_prev)

        # 判断主要贡献者
        if new_user_wau > old_user_wau:
            contribution = '新用户为主'
        elif old_user_wau > new_user_wau:
            contribution = '老用户为主'
        else:
            contribution = '新老用户均衡'

        result = {
            'new_user_wau': new_user_wau,
            'old_user_wau': old_user_wau,
            'new_user_wau_wow': new_user_wow.get('change_rate', 0),
            'old_user_wau_wow': old_user_wow.get('change_rate', 0),
            'wau_current': total_wau_current,
            'wau_wow': wau_wow,
            'wau_contribution': contribution,
            'historical_weeks': 25,
            'historical_avg_wau': 0,
            'historical_trends': [],
            'attention_items': [],
            'summary': f"工具WAU {total_wau_current:,}，{wau_wow['trend']} {wau_wow['change_rate']:+.1f}%"
        }

        self.logger.info(f"✅ 活跃数据分析完成: {result['summary']}")
        return result

    def analyze_retention_data(
        self,
        current_data: List[Dict],
        previous_data: List[Dict]
    ) -> Dict:
        """
        分析留存数据

        Args:
            current_data: 本周留存数据
            previous_data: 上周留存数据

        Returns:
            dict: 留存分析结果
        """
        self.logger.info("分析留存数据...")

        # 新用户留存率
        new_user_retention_rates = []
        old_user_retention_rates = []

        for row in current_data:
            if '上周用户类型' in row:
                user_type = row.get('上周用户类型', '')
                retention_rate = row.get('工具次周留存', 0) or 0

                if user_type == '新注册':
                    new_user_retention_rates.append(retention_rate)
                elif user_type == '老用户':
                    old_user_retention_rates.append(retention_rate)

        # 计算平均留存率
        new_user_retention_rate = sum(new_user_retention_rates) / len(new_user_retention_rates) if new_user_retention_rates else 0
        old_user_retention_rate = sum(old_user_retention_rates) / len(old_user_retention_rates) if old_user_retention_rates else 0

        # 留存等级判断
        if new_user_retention_rate >= 40:
            retention_level = '高'
        elif new_user_retention_rate >= 30:
            retention_level = '中等'
        else:
            retention_level = '低'

        result = {
            'new_user_retention_rate': round(new_user_retention_rate, 2),
            'new_user_retention_previous': round(new_user_retention_rate, 2),  # 简化处理
            'new_user_retention_current': round(new_user_retention_rate, 2),
            'new_user_retention_min': min(new_user_retention_rates) if new_user_retention_rates else 0,
            'new_user_retention_max': max(new_user_retention_rates) if new_user_retention_rates else 0,
            'new_user_retention_level': retention_level,
            'old_user_retention_rate': round(old_user_retention_rate, 2),
            'old_user_retention_previous': round(old_user_retention_rate, 2),  # 简化处理
            'old_user_retention_current': round(old_user_retention_rate, 2),
            'old_user_retention_min': min(old_user_retention_rates) if old_user_retention_rates else 0,
            'old_user_retention_max': max(old_user_retention_rates) if old_user_retention_rates else 0,
            'old_user_retention_change': 0,  # 简化处理
            'old_user_trend_note': '需要关注' if old_user_retention_rate < 30 else '稳定',
            'historical_new_user_avg': round(new_user_retention_rate, 2),
            'historical_old_user_avg': round(old_user_retention_rate, 2),
            'historical_trends': [],
            'insights': [],
            'attention_items': []
        }

        self.logger.info(f"✅ 留存数据分析完成")
        return result

    def analyze_revenue_data(
        self,
        current_data: List[Dict],
        previous_data: List[Dict]
    ) -> Dict:
        """
        分析收入数据

        Args:
            current_data: 本周收入数据
            previous_data: 上周收入数据

        Returns:
            dict: 收入分析结果
        """
        self.logger.info("分析收入数据...")

        # 本周收入
        total_current = 0
        new_subscribe_amount = 0
        renewal_amount = 0

        for row in current_data:
            if 'Total_Amt' in row:
                total_current += row.get('Total_Amt', 0) or 0
            if 'NewSubscribe_Amt' in row:
                new_subscribe_amount += row.get('NewSubscribe_Amt', 0) or 0
            if 'Renewal_Amt' in row:
                renewal_amount += row.get('Renewal_Amt', 0) or 0

        # 上周收入
        total_previous = 0
        new_subscribe_amount_prev = 0
        renewal_amount_prev = 0

        for row in previous_data:
            if 'Total_Amt' in row:
                total_previous += row.get('Total_Amt', 0) or 0
            if 'NewSubscribe_Amt' in row:
                new_subscribe_amount_prev += row.get('NewSubscribe_Amt', 0) or 0
            if 'Renewal_Amt' in row:
                renewal_amount_prev += row.get('Renewal_Amt', 0) or 0

        # 计算环比
        wow = self.calculate_week_over_week(total_current, total_previous)
        new_subscribe_wow = self.calculate_week_over_week(new_subscribe_amount, new_subscribe_amount_prev)
        renewal_wow = self.calculate_week_over_week(renewal_amount, renewal_amount_prev)

        result = {
            'total_current': total_current,
            'total_previous': total_previous,
            'renewal_revenue': renewal_amount,
            'new_signing_revenue': new_subscribe_amount,
            'renewal_growth_rate': renewal_wow.get('change_rate', 0),
            'new_signing_growth_rate': new_subscribe_wow.get('change_rate', 0),
            'wow': wow,
            'ai_summary': '数据暂未加载',
            'revenue_type': '-',
            'user_count': '-',
            'average_order_value': '-',
            'historical_weeks': 12,
            'historical_avg_revenue': round(total_previous, 2),
            'historical_trends': [],
            'attention_items': [],
            'summary': f"总收入 {total_current:,}，环比{wow['trend']} {wow['change_rate']:+.1f}%"
        }

        self.logger.info(f"✅ 收入数据分析完成: {result['summary']}")
        return result


if __name__ == "__main__":
    # 测试代码
    print("测试数据分析模块\n")

    analyzer = DataAnalyzer()

    # 测试环比计算
    wow = analyzer.calculate_week_over_week(100, 80)
    print(f"环比测试: {wow}")

    # 测试流量分析
    current_traffic = [
        {'日期': '20260223', '渠道': 'organic search', '新访客数': 100, '新访客注册数': 20}
    ]
    previous_traffic = [
        {'日期': '20260216', '渠道': 'organic search', '新访客数': 80, '新访客注册数': 15}
    ]

    result = analyzer.analyze_traffic_data(current_traffic, previous_traffic)
    print(f"流量分析结果: {result}")
