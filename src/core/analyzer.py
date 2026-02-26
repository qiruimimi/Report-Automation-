#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析模块

分析从Metabase获取的数据，计算环比、转化率等指标
支持配置化的列名映射
"""

from typing import Dict, List, Optional
from src.logger import get_logger
from src.ai_summary import AISummaryGenerator


class Analyzer:
    """
    数据分析器

    使用配置化的列名映射来分析数据
    """

    def __init__(self, config=None, column_mappings=None, logger=None):
        """
        初始化数据分析器

        Args:
            config: ConfigManager 实例（可选）
            column_mappings: 列名映射字典（可选）
            logger: 日志记录器
        """
        self.logger = logger or get_logger('core.analyzer')

        # 使用传入的配置或默认映射
        self.column_mappings = column_mappings or {}

        if config:
            self.column_mappings = config.get_column_mappings()

        # 初始化AI总结生成器（传入config以支持LLM）
        self.ai_summary_generator = AISummaryGenerator(config=config, logger=self.logger)

    def _get_column_mapping(self, section: str) -> Dict:
        """
        获取指定部分的列名映射

        Args:
            section: 部分名称 (traffic, activation, engagement, retention, revenue)

        Returns:
            dict: 列名映射配置
        """
        return self.column_mappings.get(section, {})

    def _get_mapped_column(self, section: str, chinese_name: str, default=None):
        """
        获取列名用于访问数据

        由于数据字典的键是中文名（从SQL SELECT别名而来），
        直接返回中文名用于访问数据

        Args:
            section: 部分名称
            chinese_name: 中文列名
            default: 默认值

        Returns:
            中文列名或默认值
        """
        return chinese_name

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
                'trend': '→',
                'previous': previous or 0,
                'current': current
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
            'trend': trend,
            'previous': previous,
            'current': current
        }

    def _extract_target_week_data(self, data: List[Dict], week_config: Dict, section: str) -> Dict:
        """
        从SQL返回的数据中提取目标周和上周的数据

        SQL使用CURRENT_DATE()返回12周历史数据，需要从中找到对应的目标周和上周数据
        如果配置的目标周没有数据，则使用SQL返回的最新周作为目标周

        对于留存部分（retention）："次周留存"需要使用再往前推一周的数据
        例如：目标周是20260216，则current_data应该取20260209周的数据，previous_data取20260216周的数据

        Args:
            data: SQL返回的数据列表
            week_config: 周配置（包含week_monday, last_week_monday等）
            section: 部分名称

        Returns:
            dict: 包含current_week_data和previous_week_data的字典
        """
        if not data:
            return {'current_week_data': [], 'previous_week_data': []}

        # 根据不同的section使用不同的日期列名
        if section in ['traffic', 'revenue', 'activation']:
            date_col = '日期'
        elif section == 'engagement':
            date_col = '周'
        elif section == 'retention':
            date_col = '上周'
        else:
            date_col = '日期'

        # 找出数据中的所有唯一日期并转换为整数
        unique_dates = set()
        for row in data:
            date_val = row.get(date_col, '0')
            try:
                date_int = int(date_val) if isinstance(date_val, str) else int(date_val) if isinstance(date_val, int) else 0
                unique_dates.add(date_int)
            except (ValueError, TypeError):
                pass

        if not unique_dates:
            return {'current_week_data': [], 'previous_week_data': []}

        # 使用最大的日期作为目标周（最新的数据）
        max_date = max(unique_dates)
        self.logger.info(f"SQL返回的数据日期范围: {min(unique_dates)} ~ {max_date}, 共 {len(unique_dates)} 个周")

        # 根据最大日期计算该周的开始和结束日期（周日为一周结束日）
        # Python weekday: Monday=0, Sunday=6
        from datetime import datetime, timedelta
        max_date_obj = datetime.strptime(str(max_date), '%Y%m%d')
        days_from_monday = max_date_obj.weekday()  # 周一到当前日期的天数
        week_start = max_date_obj - timedelta(days=days_from_monday)
        week_end = max_date_obj  # 周日

        week_start_int = int(week_start.strftime('%Y%m%d'))
        week_end_int = int(week_end.strftime('%Y%m%d'))
        last_week_start_int = int((week_start - timedelta(days=7)).strftime('%Y%m%d'))
        last_week_end_int = int((week_end - timedelta(days=7)).strftime('%Y%m%d'))

        # 留存部分特殊处理：往前推一周
        # 目标周（如20260216）的留存数据来源于20260209周
        # 所以current_data应取20260209周（上周），previous_data取20260216周（本周）
        if section == 'retention':
            self.logger.info(f"留存部分特殊处理：目标周{max_date}，往前推一周为20260209")
            # 往前推一周，把current和previous都往前推一周
            week_start_int = int((week_start - timedelta(days=7)).strftime('%Y%m%d'))
            week_end_int = int((week_end - timedelta(days=7)).strftime('%Y%m%d'))
            last_week_start_int = int((week_start - timedelta(days=14)).strftime('%Y%m%d'))
            last_week_end_int = int((week_end - timedelta(days=14)).strftime('%Y%m%d'))

        self.logger.info(f"识别目标周: {week_start_int} ~ {week_end_int}, 上周: {last_week_start_int} ~ {last_week_end_int}")

        # 提取目标周数据和上周数据
        current_week_data = []
        previous_week_data = []

        for row in data:
            date_val = row.get(date_col, '0')
            try:
                date_int = int(date_val) if isinstance(date_val, str) else int(date_val) if isinstance(date_val, int) else 0
            except (ValueError, TypeError):
                date_int = 0

            if week_start_int <= date_int <= week_end_int:
                current_week_data.append(row)
            elif last_week_start_int <= date_int <= last_week_end_int:
                previous_week_data.append(row)

        self.logger.info(f"从 {len(data)} 行数据中提取: 目标周 {len(current_week_data)} 行, 上周 {len(previous_week_data)} 行")

        return {
            'current_week_data': current_week_data,
            'previous_week_data': previous_week_data,
            'target_week_start': week_start.strftime('%Y%m%d'),
            'target_week_end': week_end.strftime('%Y%m%d'),
            'last_week_start': (week_start - timedelta(days=7)).strftime('%Y%m%d'),
            'last_week_end': (week_end - timedelta(days=7)).strftime('%Y%m%d')
        }

    def analyze_all_sections(
        self,
        current_data: Dict[str, List[Dict]],
        previous_data: Dict[str, List[Dict]],
        week_config: Dict = None
    ) -> Dict:
        """
        分析所有部分的数据

        Args:
            current_data: 本周所有数据（SQL使用CURRENT_DATE()返回12周数据）
            previous_data: 上周所有数据（暂未使用，统一从current_data中提取）
            week_config: 周配置（用于识别目标周）

        Returns:
            dict: 所有分析结果
        """
        self.logger.info("开始分析所有部分...")

        results = {}

        # 流量分析 - 从SQL返回的数据中提取目标周和上周数据
        if 'traffic' in current_data:
            traffic_data = self._extract_target_week_data(current_data['traffic'], week_config, 'traffic')
            results['traffic'] = self.analyze_traffic_data(
                traffic_data['current_week_data'],
                traffic_data['previous_week_data']
            )

        # 激活分析
        if 'activation' in current_data:
            activation_data = self._extract_target_week_data(current_data['activation'], week_config, 'activation')
            results['activation'] = self.analyze_activation_data(
                activation_data['current_week_data'],
                activation_data['previous_week_data']
            )

        # 活跃分析
        if 'engagement' in current_data:
            engagement_data = self._extract_target_week_data(current_data['engagement'], week_config, 'engagement')
            results['engagement'] = self.analyze_engagement_data(
                engagement_data['current_week_data'],
                engagement_data['previous_week_data']
            )

        # 留存分析
        if 'retention' in current_data:
            retention_data = self._extract_target_week_data(current_data['retention'], week_config, 'retention')
            results['retention'] = self.analyze_retention_data(
                retention_data['current_week_data'],
                retention_data['previous_week_data']
            )

        # 收入分析
        if 'revenue' in current_data:
            revenue_data = self._extract_target_week_data(current_data['revenue'], week_config, 'revenue')
            results['revenue'] = self.analyze_revenue_data(
                revenue_data['current_week_data'],
                revenue_data['previous_week_data']
            )

        self.logger.info("✅ 所有部分分析完成")
        return results

    def analyze_traffic_data(
        self,
        current_data: List[Dict],
        previous_data: List[Dict],
        week_config: Dict = None
    ) -> Dict:
        """
        分析流量数据

        Args:
            current_data: 本周流量数据（已通过_extract_target_week_data过滤）
            previous_data: 上周流量数据（已通过_extract_target_week_data过滤）
            week_config: 周配置

        Returns:
            dict: 流量分析结果
        """
        self.logger.info("分析流量数据...")

        # 使用映射的列名
        visitors_col = self._get_mapped_column('traffic', '新访客数')
        new_visitor_regs_col = self._get_mapped_column('traffic', '新访客注册数')

        # 汇总当前周的新访客数和注册数
        total_new_visitors = 0
        total_new_registrations = 0

        for row in current_data:
            total_new_visitors += row.get(visitors_col, 0) or 0
            total_new_registrations += row.get(new_visitor_regs_col, 0) or 0

        # 汇总上周数据
        total_new_visitors_prev = 0
        total_new_registrations_prev = 0

        for row in previous_data:
            total_new_visitors_prev += row.get(visitors_col, 0) or 0
            total_new_registrations_prev += row.get(new_visitor_regs_col, 0) or 0

        # 计算转化率
        conversion_rate_current = (total_new_registrations / total_new_visitors * 100) if total_new_visitors > 0 else 0
        conversion_rate_previous = (total_new_registrations_prev / total_new_visitors_prev * 100) if total_new_visitors_prev > 0 else 0

        # 计算环比
        visitors_wow = self.calculate_week_over_week(total_new_visitors, total_new_visitors_prev)
        registrations_wow = self.calculate_week_over_week(total_new_registrations, total_new_registrations_prev)
        conversion_wow = self.calculate_week_over_week(conversion_rate_current, conversion_rate_previous)

        # 生成AI总结
        ai_summary = self.ai_summary_generator.generate_summary(
            'traffic',
            {
                'new_visitors_current': total_new_visitors,
                'visitors_wow': visitors_wow,
                'registrations_current': total_new_registrations,
                'registrations_wow': registrations_wow,
                'conversion_rate_current': conversion_rate_current,
                'conversion_rate_wow': conversion_wow
            }
        )

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
            'ai_summary': ai_summary,
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

        # 使用映射的列名
        new_registered_col = self._get_mapped_column('activation', '新注册用户数')
        entered_tool_col = self._get_mapped_column('activation', '进工具用户数')
        valid_design_col = self._get_mapped_column('activation', '有效画户型用户数')
        valid_model_col = self._get_mapped_column('activation', '有效拖模型用户数')
        render_col = self._get_mapped_column('activation', '渲染用户数')

        # 本周数据
        new_registered_users = 0
        entered_tool_users = 0
        valid_design_users = 0
        valid_model_users = 0
        render_users = 0

        for row in current_data:
            new_registered_users += row.get(new_registered_col, 0) or 0
            entered_tool_users += row.get(entered_tool_col, 0) or 0
            valid_design_users += row.get(valid_design_col, 0) or 0
            valid_model_users += row.get(valid_model_col, 0) or 0
            render_users += row.get(render_col, 0) or 0

        # 计算各阶段转化率
        step1_rate = (entered_tool_users / new_registered_users * 100) if new_registered_users > 0 else 0
        step2_rate = (valid_design_users / entered_tool_users * 100) if entered_tool_users > 0 else 0
        step3_rate = (valid_model_users / valid_design_users * 100) if valid_design_users > 0 else 0
        step4_rate = (render_users / valid_model_users * 100) if valid_model_users > 0 else 0

        # 上周数据（简化处理，取第一条记录）
        # SQL返回的转化率是decimal格式（如0.774823），需要乘以100转为百分比
        previous_week_data = previous_data[0] if previous_data else {}
        step1_prev_rate = (previous_week_data.get('注册到进工具转化率', 0) or 0) * 100
        step2_prev_rate = (previous_week_data.get('进工具到有效画户型转化率', 0) or 0) * 100
        step3_prev_rate = (previous_week_data.get('有效画户型到有效拖模型转化率', 0) or 0) * 100
        step4_prev_rate = (previous_week_data.get('有效拖模型到渲染转化率', 0) or 0) * 100

        # 生成AI总结
        ai_summary = self.ai_summary_generator.generate_summary(
            'activation',
            {
                'new_registered_users': new_registered_users,
                'step1_current_rate': round(step1_rate, 2),
                'step1_previous_rate': round(step1_prev_rate, 2),
                'step1_change_rate': round(step1_rate - step1_prev_rate, 2),
                'step4_current_rate': round(step4_rate, 2)
            },
            current_data
        )

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
            # 从数据中提取周日期（如果存在）
            'previous_week_label': previous_data[0].get('日期', '上上周') if previous_data else '上上周',
            'current_week_label': current_data[0].get('日期', '本周') if current_data else '本周',
            'is_current_week_incomplete': False,
            'current_week_metrics': [],
            'core_insights': [],
            'attention_items': [],
            'ai_summary': ai_summary
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

        # 使用映射的列名
        new_user_wau_col = self._get_mapped_column('engagement', '新用户WAU')
        old_user_wau_col = self._get_mapped_column('engagement', '老用户WAU')

        # 新老用户WAU数据
        new_user_wau = 0
        old_user_wau = 0
        new_user_wau_prev = 0
        old_user_wau_prev = 0

        for row in current_data:
            new_user_wau = row.get(new_user_wau_col, 0) or 0
            old_user_wau = row.get(old_user_wau_col, 0) or 0

        for row in previous_data:
            new_user_wau_prev = row.get(new_user_wau_col, 0) or 0
            old_user_wau_prev = row.get(old_user_wau_col, 0) or 0

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

        # 生成AI总结
        ai_summary = self.ai_summary_generator.generate_summary(
            'engagement',
            {
                'new_user_wau': new_user_wau,
                'old_user_wau': old_user_wau,
                'wau_current': total_wau_current,
                'wau_wow': wau_wow,
                'wau_contribution': contribution
            }
        )

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
            'ai_summary': ai_summary,
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

        # 处理当前周数据（目标周）
        for row in current_data:
            if '上周用户类型' in row:
                user_type = row.get('上周用户类型', '')
                # SQL返回的留存率是decimal格式（如0.4388），需要乘以100转为百分比
                retention_rate = (row.get('工具次周留存', 0) or 0) * 100

                if user_type == '新注册':
                    new_user_retention_rates.append(retention_rate)
                elif user_type == '老用户':
                    old_user_retention_rates.append(retention_rate)

        # 计算当前周平均留存率
        new_user_retention_rate = sum(new_user_retention_rates) / len(new_user_retention_rates) if new_user_retention_rates else 0
        old_user_retention_rate = sum(old_user_retention_rates) / len(old_user_retention_rates) if old_user_retention_rates else 0

        # 处理上一周数据（用于环比比较）
        new_user_retention_rates_prev = []
        old_user_retention_rates_prev = []

        for row in previous_data:
            if '上周用户类型' in row:
                user_type = row.get('上周用户类型', '')
                retention_rate_prev = (row.get('工具次周留存', 0) or 0) * 100

                if user_type == '新注册':
                    new_user_retention_rates_prev.append(retention_rate_prev)
                elif user_type == '老用户':
                    old_user_retention_rates_prev.append(retention_rate_prev)

        # 计算上一周平均留存率
        new_user_retention_rate_prev = sum(new_user_retention_rates_prev) / len(new_user_retention_rates_prev) if new_user_retention_rates_prev else 0
        old_user_retention_rate_prev = sum(old_user_retention_rates_prev) / len(old_user_retention_rates_prev) if old_user_retention_rates_prev else 0

        # 留存等级判断（使用百分比阈值）
        if new_user_retention_rate >= 40:
            retention_level = '高'
        elif new_user_retention_rate >= 30:
            retention_level = '中等'
        else:
            retention_level = '低'

        result = {
            'new_user_retention_rate': round(new_user_retention_rate, 2),
            'new_user_retention_previous': round(new_user_retention_rate_prev, 2),
            'new_user_retention_current': round(new_user_retention_rate, 2),
            'new_user_retention_min': min(new_user_retention_rates) if new_user_retention_rates else 0,
            'new_user_retention_max': max(new_user_retention_rates) if new_user_retention_rates else 0,
            'new_user_retention_level': retention_level,
            'old_user_retention_rate': round(old_user_retention_rate, 2),
            'old_user_retention_previous': round(old_user_retention_rate_prev, 2),
            'old_user_retention_current': round(old_user_retention_rate, 2),
            'old_user_retention_min': min(old_user_retention_rates) if old_user_retention_rates else 0,
            'old_user_retention_max': max(old_user_retention_rates) if old_user_retention_rates else 0,
            'old_user_retention_change': round(old_user_retention_rate - old_user_retention_rate_prev, 2),
            'old_user_trend_note': '需要关注' if old_user_retention_rate < 30 else '稳定',
            'historical_new_user_avg': round(new_user_retention_rate, 2),
            'historical_old_user_avg': round(old_user_retention_rate, 2),
            'historical_trends': [],
            'insights': [],
            'attention_items': [],
            'ai_summary': self.ai_summary_generator.generate_summary(
                'retention',
                {
                    'new_user_retention_rate': new_user_retention_rate,
                    'old_user_retention_rate': old_user_retention_rate,
                    'new_user_retention_level': retention_level,
                    'old_user_trend_note': '需要关注' if old_user_retention_rate < 30 else '稳定'
                }
            )
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

        # 使用映射的列名（SQL返回的是中文名）
        total_amt_col = self._get_mapped_column('revenue', '总收入')
        new_subscribe_col = self._get_mapped_column('revenue', '新签收入')
        renewal_col = self._get_mapped_column('revenue', '续约收入')

        # 本周收入
        total_current = 0
        new_subscribe_amount = 0
        renewal_amount = 0

        for row in current_data:
            total_current += row.get(total_amt_col, 0) or 0
            new_subscribe_amount += row.get(new_subscribe_col, 0) or 0
            renewal_amount += row.get(renewal_col, 0) or 0

        # 上周收入
        total_previous = 0
        new_subscribe_amount_prev = 0
        renewal_amount_prev = 0

        for row in previous_data:
            total_previous += row.get(total_amt_col, 0) or 0
            new_subscribe_amount_prev += row.get(new_subscribe_col, 0) or 0
            renewal_amount_prev += row.get(renewal_col, 0) or 0

        # 计算环比
        wow = self.calculate_week_over_week(total_current, total_previous)
        new_subscribe_wow = self.calculate_week_over_week(new_subscribe_amount, new_subscribe_amount_prev)
        renewal_wow = self.calculate_week_over_week(renewal_amount, renewal_amount_prev)

        # 生成AI总结
        ai_summary = self.ai_summary_generator.generate_summary(
            'revenue',
            {
                'total_current': total_current,
                'total_previous': total_previous,
                'wow': wow,
                'renewal_revenue': renewal_amount,
                'new_signing_revenue': new_subscribe_amount,
                'renewal_growth_rate': renewal_wow.get('change_rate', 0),
                'new_signing_growth_rate': new_subscribe_wow.get('change_rate', 0)
            }
        )

        result = {
            'total_current': total_current,
            'total_previous': total_previous,
            'renewal_revenue': renewal_amount,
            'new_signing_revenue': new_subscribe_amount,
            'renewal_growth_rate': renewal_wow.get('change_rate', 0),
            'new_signing_growth_rate': new_subscribe_wow.get('change_rate', 0),
            'wow': wow,
            'ai_summary': ai_summary,
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

    analyzer = Analyzer()

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
