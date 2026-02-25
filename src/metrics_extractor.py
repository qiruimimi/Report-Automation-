#!/usr/bin/env python3
"""
指标提取器 - 从JSON数据中提取关键指标

功能:
- 从SQL查询结果中提取关键指标
- 计算环比变化
- 计算平均值和汇总
- 生成分析文字
"""

from typing import Dict, List, Optional
from logger import get_logger


class MetricsExtractor:
    """指标提取器"""

    def __init__(self, logger=None):
        self.logger = logger or get_logger('metrics_extractor')

    def calculate_wow_change(self, current: float, previous: float) -> Dict:
        """
        计算环比变化

        Args:
            current: 本周数值
            previous: 上周数值

        Returns:
            dict: {change_abs: 绝对变化, change_rate: 变化率, trend: 趋势符号}
        """
        if previous == 0:
            return {
                'change_abs': current,
                'change_rate': 0,
                'trend': '→'
            }

        change_abs = current - previous
        change_rate = (change_abs / previous) * 100 if previous != 0 else 0

        trend = '↑' if change_abs > 0 else ('↓' if change_abs < 0 else '→')

        return {
            'change_abs': round(change_abs, 1),
            'change_rate': round(change_rate, 1),
            'trend': trend
        }

    def calculate_historical_avg(self, data: List[Dict], key: str) -> float:
        """
        计算历史平均值

        Args:
            data: 历史数据列表
            key: 要平均的字段名

        Returns:
            float: 平均值
        """
        if not data:
            return 0

        values = [row.get(key, 0) for row in data if row.get(key) is not None]

        if not values:
            return 0

        return round(sum(values) / len(values), 1)

    def extract_traffic_metrics(
        self,
        current_data: List[Dict],
        previous_data: List[Dict],
        current_latest_week: Optional[str] = None,
        previous_latest_week: Optional[str] = None
    ) -> Dict:
        """
        提取流量指标

        Args:
            current_data: 本周流量数据（可能包含多周）
            previous_data: 上周流量数据（可能包含多周）
            current_latest_week: 本周的数据周标签（优先使用，不提供则自动选择）
            previous_latest_week: 上周的数据周标签（优先使用，不提供则自动选择）

        Returns:
            dict: 流量指标字典
        """
        self.logger.info("提取流量指标...")

        # 如果提供了 latest_week，使用它；否则选择数据行数最多的一周
        if current_data and len(current_data) > 0 and '日期' in current_data[0]:
            if current_latest_week:
                latest_date = current_latest_week
                current_week_data = [row for row in current_data if row.get('日期', '') == latest_date]
                self.logger.info(f"使用指定数据周: {latest_date} ({len(current_week_data)} 个渠道)")
            else:
                # 统计每个日期的数据行数，选择最多的一周
                date_counts = {}
                for row in current_data:
                    date = row.get('日期', '')
                    date_counts[date] = date_counts.get(date, 0) + 1

                latest_date = max(date_counts, key=lambda d: (date_counts[d], d))
                current_week_data = [row for row in current_data if row.get('日期', '') == latest_date]
                self.logger.info(f"自动选择数据周: {latest_date} ({len(current_week_data)} 个渠道)")
        else:
            current_week_data = current_data

        # 如果上周数据提供了 latest_week，使用它
        if previous_data and len(previous_data) > 0 and '日期' in previous_data[0]:
            if previous_latest_week:
                latest_date = previous_latest_week
                previous_week_data = [row for row in previous_data if row.get('日期', '') == latest_date]
                self.logger.info(f"使用指定上周数据周: {latest_date} ({len(previous_week_data)} 个渠道)")
            else:
                # 统计每个日期的数据行数，选择最多的一周
                date_counts = {}
                for row in previous_data:
                    date = row.get('日期', '')
                    date_counts[date] = date_counts.get(date, 0) + 1

                latest_date = max(date_counts, key=lambda d: (date_counts[d], d))
                previous_week_data = [row for row in previous_data if row.get('日期', '') == latest_date]
                self.logger.info(f"自动选择上周数据周: {latest_date} ({len(previous_week_data)} 个渠道)")
        else:
            previous_week_data = previous_data

        # 汇总本周数据
        current_total_guests = sum(row.get('新访客数', 0) for row in current_week_data)
        current_total_registers = sum(row.get('新访客注册数', 0) for row in current_week_data)
        current_conversion_rate = (current_total_registers / current_total_guests * 100) if current_total_guests > 0 else 0

        # 汇总上周数据
        previous_total_guests = sum(row.get('新访客数', 0) for row in previous_week_data)
        previous_total_registers = sum(row.get('新访客注册数', 0) for row in previous_week_data)
        previous_conversion_rate = (previous_total_registers / previous_total_guests * 100) if previous_total_guests > 0 else 0

        # 计算环比变化
        guests_wow = self.calculate_wow_change(current_total_guests, previous_total_guests)
        registers_wow = self.calculate_wow_change(current_total_registers, previous_total_registers)
        conversion_wow = self.calculate_wow_change(current_conversion_rate, previous_conversion_rate)

        # 生成渠道分析
        notes = self._generate_traffic_notes(current_week_data, previous_week_data)

        metrics = {
            'total_guests': int(current_total_guests),
            'total_registers': int(current_total_registers),
            'conversion_rate': round(current_conversion_rate, 1),
            'guests_wow': f"{guests_wow['change_rate']:+.1f}%",
            'guests_trend': guests_wow['trend'],
            'registers_wow': f"{registers_wow['change_rate']:+.1f}%",
            'registers_trend': registers_wow['trend'],
            'conversion_wow': f"{conversion_wow['change_rate']:+.2f}%",
            'conversion_trend': conversion_wow['trend'],
            'notes': notes
        }

        self.logger.info(f"✅ 流量指标提取完成: 访客{metrics['total_guests']}, 注册{metrics['total_registers']}")

        return metrics

    def _generate_traffic_notes(
        self,
        current_data: List[Dict],
        previous_data: List[Dict]
    ) -> List[Dict]:
        """生成流量渠道分析"""
        notes = []

        # 按渠道汇总数据
        current_by_channel = {}
        previous_by_channel = {}

        for row in current_data:
            channel = row.get('渠道', 'Unknown')
            guests = row.get('新访客数', 0)
            registers = row.get('新访客注册数', 0)
            current_by_channel[channel] = {'guests': guests, 'registers': registers}

        for row in previous_data:
            channel = row.get('渠道', 'Unknown')
            guests = row.get('新访客数', 0)
            registers = row.get('新访客注册数', 0)
            previous_by_channel[channel] = {'guests': guests, 'registers': registers}

        # 分析主要渠道
        for channel in current_by_channel:
            current_guests = current_by_channel[channel]['guests']
            previous_guests = previous_by_channel.get(channel, {}).get('guests', 0)

            if current_guests > 10000 or abs(current_guests - previous_guests) > 5000:
                change = self.calculate_wow_change(current_guests, previous_guests)
                conversion_rate = (current_by_channel[channel]['registers'] / current_guests * 100) if current_guests > 0 else 0

                # 根据变化方向选择"增至"或"降至"
                direction = "增至" if change['change_abs'] > 0 else "降至"
                trend = "增长" if change['change_abs'] > 0 else "下降"
                magnitude = "大幅" if abs(change['change_rate']) > 50 else ""

                note = {
                    'channel': f"{channel}",
                    'description': f"新访客{magnitude}{trend}{abs(change['change_rate']):.1f}%（从{previous_guests:,}{direction}{current_guests:,}），转化率{conversion_rate:.0f}%"
                }

                notes.append(note)

        return notes

    def extract_engagement_metrics(
        self,
        current_data: List[Dict],
        previous_data: List[Dict],
        historical_data: Optional[List[Dict]] = None,
        current_latest_week: Optional[str] = None,
        previous_latest_week: Optional[str] = None
    ) -> Dict:
        """
        提取活跃指标

        Args:
            current_data: 本周活跃数据（可能包含多周）
            previous_data: 上周活跃数据（可能包含多周）
            historical_data: 25周历史数据
            current_latest_week: 本周的数据周标签（优先使用，不提供则自动选择）
            previous_latest_week: 上周的数据周标签（优先使用，不提供则自动选择）

        Returns:
            dict: 活跃指标字典
        """
        self.logger.info("提取活跃指标...")

        # 如果数据包含多周，筛选指定周或最新一周
        if current_data and len(current_data) > 0 and '周' in current_data[0]:
            if current_latest_week:
                current_week_rows = [row for row in current_data if row.get('周', '') == current_latest_week]
                self.logger.info(f"使用指定数据周: {current_latest_week}")
            else:
                # 获取最新一周的日期
                latest_week = max(row.get('周', '') for row in current_data)
                current_week_rows = [row for row in current_data if row.get('周', '') == latest_week]
                self.logger.info(f"筛选最新一周数据: {latest_week}")
        else:
            # 假设最后两行就是最新一周的新老用户数据
            current_week_rows = current_data[-2:] if len(current_data) >= 2 else current_data

        # 如果上周数据包含多周，筛选指定周或最新一周
        if previous_data and len(previous_data) > 0 and '周' in previous_data[0]:
            if previous_latest_week:
                previous_week_rows = [row for row in previous_data if row.get('周', '') == previous_latest_week]
                self.logger.info(f"使用指定上周数据周: {previous_latest_week}")
            else:
                latest_week = max(row.get('周', '') for row in previous_data)
                previous_week_rows = [row for row in previous_data if row.get('周', '') == latest_week]
                self.logger.info(f"筛选上周数据: {latest_week}")
        else:
            previous_week_rows = previous_data[-2:] if len(previous_data) >= 2 else previous_data

        # 提取本周数据
        current_week = {}
        for row in current_week_rows:
            user_type = row.get('用户类型（新老）', 'Unknown')
            wau = row.get('上周工具WAU', 0)
            current_week[user_type] = wau

        total_wau = sum(current_week.values())
        new_wau = current_week.get('新注册', 0)
        old_wau = current_week.get('老用户', 0)

        # 提取上周数据
        previous_week = {}
        for row in previous_week_rows:
            user_type = row.get('用户类型（新老）', 'Unknown')
            wau = row.get('上周工具WAU', 0)
            previous_week[user_type] = wau

        previous_total = sum(previous_week.values())
        previous_new = previous_week.get('新注册', 0)
        previous_old = previous_week.get('老用户', 0)

        # 计算环比
        total_wow = self.calculate_wow_change(total_wau, previous_total)
        new_wow = self.calculate_wow_change(new_wau, previous_new)
        old_wow = self.calculate_wow_change(old_wau, previous_old)

        # 计算历史平均
        historical_avg = 0
        if historical_data:
            historical_avg = self.calculate_historical_avg(historical_data, 'WAU')

        # 判断主要驱动因素
        if abs(new_wow['change_rate']) > abs(old_wow['change_rate']):
            driver = '新用户'
        elif abs(old_wow['change_rate']) > abs(new_wow['change_rate']):
            driver = '老用户'
        else:
            driver = '新老用户'

        metrics = {
            'total_wau': int(total_wau),
            'wow': f"{total_wow['change_rate']:+.1f}",
            'driver': driver,
            'new_wau': int(new_wau),
            'new_wow': f"{new_wow['change_rate']:+.1f}",
            'old_wau': int(old_wau),
            'old_wow': f"{old_wow['change_rate']:+.1f}",
            'historical_avg': int(historical_avg) if historical_avg > 0 else total_wau
        }

        self.logger.info(f"✅ 活跃指标提取完成: WAU{metrics['total_wau']}, 环比{metrics['wow']}%")

        return metrics

    def extract_activation_metrics(
        self,
        current_data: List[Dict],
        previous_data: List[Dict]
    ) -> Dict:
        """
        提取激活指标

        Args:
            current_data: 本周激活数据
            previous_data: 上周激活数据

        Returns:
            dict: 激活指标字典
        """
        self.logger.info("提取激活指标...")

        # 获取最后三周数据（用于对比）
        if len(current_data) >= 3:
            week_llw = current_data[-3]  # 上上周
            week_lw = current_data[-2]   # 上周
            week_curr = current_data[-1] # 本周
        else:
            self.logger.warning("⚠️ 激活数据不足3周，无法计算完整对比")
            return {
                'last_week_label': '',
                'current_week_label': '',
                'last_last_week_label': '',
                'step1_llw': 0,
                'step1_lw': 0,
                'step1_change': '',
                'step2_llw': 0,
                'step2_lw': 0,
                'step2_change': '',
                'step3_llw': 0,
                'step3_lw': 0,
                'step3_change': '',
                'step4_llw': 0,
                'step4_lw': 0,
                'step4_change': '',
                'total_llw': 0,
                'total_lw': 0,
                'total_change': '',
                'incomplete_data': True,
                'new_users': 0,
                'step1_curr': 0,
                'step2_curr': 0,
                'step3_curr': 0,
                'step4_curr': 0,
            }

        # 提取上上周数据
        step1_llw = round(week_llw.get('注册到进工具转化率', 0) * 100, 2)
        step2_llw = round(week_llw.get('进工具到有效画户型转化率', 0) * 100, 2)
        step3_llw = round(week_llw.get('有效画户型到有效拖模型转化率', 0) * 100, 2)
        step4_llw = round(week_llw.get('有效拖模型到渲染转化率', 0) * 100, 2)
        total_llw = round(week_llw.get('渲染总转化率', 0) * 100, 2)

        # 提取上周数据
        step1_lw = round(week_lw.get('注册到进工具转化率', 0) * 100, 2)
        step2_lw = round(week_lw.get('进工具到有效画户型转化率', 0) * 100, 2)
        step3_lw = round(week_lw.get('有效画户型到有效拖模型转化率', 0) * 100, 2)
        step4_lw = round(week_lw.get('有效拖模型到渲染转化率', 0) * 100, 2)
        total_lw = round(week_lw.get('渲染总转化率', 0) * 100, 2)

        # 计算变化
        step1_change_calc = step1_lw - step1_llw
        step2_change_calc = step2_lw - step2_llw
        step3_change_calc = step3_lw - step3_llw
        step4_change_calc = step4_lw - step4_llw
        total_change_calc = total_lw - total_llw

        # 格式化变化字符串
        def format_change(val):
            if val > 0:
                return f"↑ +{val:.2f}%"
            elif val < 0:
                return f"↓ {val:.2f}%"
            else:
                return "→ 0.00%"

        # 提取本周数据（可能不完整）
        new_users = week_curr.get('新注册用户数', 0)
        step1_curr = round(week_curr.get('注册到进工具转化率', 0) * 100, 2)
        step2_curr = round(week_curr.get('进工具到有效画户型转化率', 0) * 100, 2)
        step3_curr = round(week_curr.get('有效画户型到有效拖模型转化率', 0) * 100, 2)
        step4_curr = round(week_curr.get('有效拖模型到渲染转化率', 0) * 100, 2)

        metrics = {
            'last_week_label': week_lw.get('日期', ''),
            'current_week_label': week_curr.get('日期', ''),
            'last_last_week_label': week_llw.get('日期', ''),
            'step1_llw': step1_llw,
            'step1_lw': step1_lw,
            'step1_change': format_change(step1_change_calc),
            'step2_llw': step2_llw,
            'step2_lw': step2_lw,
            'step2_change': format_change(step2_change_calc),
            'step3_llw': step3_llw,
            'step3_lw': step3_lw,
            'step3_change': format_change(step3_change_calc),
            'step4_llw': step4_llw,
            'step4_lw': step4_lw,
            'step4_change': format_change(step4_change_calc),
            'total_llw': total_llw,
            'total_lw': total_lw,
            'total_change': format_change(total_change_calc),
            'incomplete_data': True,  # 本周数据不完整
            'new_users': new_users,
            'step1_curr': step1_curr,
            'step2_curr': step2_curr,
            'step3_curr': step3_curr,
            'step4_curr': step4_curr,
        }

        self.logger.info(f"✅ 激活指标提取完成: {week_lw.get('日期')} vs {week_llw.get('日期')}")

        return metrics

    def extract_retention_metrics(
        self,
        current_data: List[Dict],
        previous_data: List[Dict],
        historical_data: Optional[List[Dict]] = None,
        current_latest_week: Optional[str] = None,
        previous_latest_week: Optional[str] = None
    ) -> Dict:
        """
        提取留存指标

        Args:
            current_data: 本周留存数据（可能包含多周）
            previous_data: 上周留存数据（可能包含多周）
            historical_data: 近12周留存数据
            current_latest_week: 本周的数据周标签（优先使用，不提供则自动选择）
            previous_latest_week: 上周的数据周标签（优先使用，不提供则自动选择）

        Returns:
            dict: 留存指标字典
        """
        self.logger.info("提取留存指标...")

        # 如果数据包含多周，筛选指定周或最新一周
        if current_data and len(current_data) > 0 and '上周' in current_data[0]:
            if current_latest_week:
                latest_date = current_latest_week
                current_week_rows = [row for row in current_data if row.get('上周', '') == latest_date]
                self.logger.info(f"使用指定数据周: {latest_date} ({len(current_week_rows)} 行)")
            else:
                # 获取最新一周的日期
                latest_week = max(row.get('上周', '') for row in current_data)
                current_week_rows = [row for row in current_data if row.get('上周', '') == latest_week]
                self.logger.info(f"筛选最新一周数据: {latest_week}")
        else:
            # 假设最后两行就是最新一周的新老用户数据
            current_week_rows = current_data[-2:] if len(current_data) >= 2 else current_data

        # 如果上周数据包含多周，筛选指定周或最新一周
        if previous_data and len(previous_data) > 0 and '上周' in previous_data[0]:
            if previous_latest_week:
                latest_date = previous_latest_week
                previous_week_rows = [row for row in previous_data if row.get('上周', '') == latest_date]
                self.logger.info(f"使用指定上周数据周: {latest_date} ({len(previous_week_rows)} 行)")
            else:
                latest_week = max(row.get('上周', '') for row in previous_data)
                previous_week_rows = [row for row in previous_data if row.get('上周', '') == latest_week]
                self.logger.info(f"筛选上周数据: {latest_week}")
        else:
            previous_week_rows = previous_data[-2:] if len(previous_data) >= 2 else previous_data

        # 提取本周留存率
        current_rates = {}
        for row in current_week_rows:
            user_type = row.get('上周用户类型', 'Unknown')
            retention_rate = row.get('工具次周留存', 0)
            current_rates[user_type] = retention_rate * 100 if retention_rate < 1 else retention_rate

        # 提取上周留存率
        previous_rates = {}
        for row in previous_week_rows:
            user_type = row.get('上周用户类型', 'Unknown')
            retention_rate = row.get('工具次周留存', 0)
            previous_rates[user_type] = retention_rate * 100 if retention_rate < 1 else retention_rate

        new_rate = round(current_rates.get('新注册', 0), 1)
        new_last = round(previous_rates.get('新注册', 0), 1)
        old_rate = round(current_rates.get('老用户', 0), 1)
        old_last = round(previous_rates.get('老用户', 0), 1)

        # 计算历史平均
        new_12w_avg = 0
        old_12w_avg = 0

        if historical_data:
            new_rates = [row.get('次周留存率', 0) * 100 for row in historical_data if row.get('用户类型') == '新注册']
            old_rates = [row.get('次周留存率', 0) * 100 for row in historical_data if row.get('用户类型') == '老用户']

            if new_rates:
                new_12w_avg = round(sum(new_rates) / len(new_rates), 1)
            if old_rates:
                old_12w_avg = round(sum(old_rates) / len(old_rates), 1)

        # 生成趋势描述
        if new_rate > new_last:
            new_trend = f"从{new_last}%提升至{new_rate}%，处于近12周{'较高' if new_rate > new_12w_avg else '中等'}水平"
        else:
            new_trend = f"从{new_last}%下降至{new_rate}%，处于近12周{'较低' if new_rate < new_12w_avg else '中等'}水平"

        if old_rate > old_last:
            old_trend = f"从{old_last}%提升至{old_rate}%，{'达到近12周最高点' if old_rate >= max(old_12w_avg, old_last) else '保持稳定'}"
        else:
            old_trend = f"从{old_last}%下降至{old_rate}%，需要关注"

        metrics = {
            'new_rate': new_rate,
            'new_last': new_last,
            'new_trend': new_trend,
            'old_rate': old_rate,
            'old_last': old_last,
            'old_trend': old_trend,
            'new_12w_avg': new_12w_avg if new_12w_avg > 0 else new_rate,
            'old_12w_avg': old_12w_avg if old_12w_avg > 0 else old_rate
        }

        self.logger.info(f"✅ 留存指标提取完成: 新用户{metrics['new_rate']}%, 老用户{metrics['old_rate']}%")

        return metrics

    def extract_revenue_metrics(
        self,
        current_data: List[Dict],
        previous_data: List[Dict],
        sku_data: Optional[List[Dict]] = None,
        country_data: Optional[List[Dict]] = None,
        tier_data: Optional[List[Dict]] = None,
        current_latest_week: Optional[str] = None,
        previous_latest_week: Optional[str] = None
    ) -> Dict:
        """
        提取收入指标

        Args:
            current_data: 本周收入数据（可能包含多周）
            previous_data: 上周收入数据（可能包含多周）
            sku_data: SKU维度数据
            country_data: 国家维度数据
            tier_data: 账单分层数据
            current_latest_week: 本周的数据周标签（优先使用，不提供则自动选择）
            previous_latest_week: 上周的数据周标签（优先使用，不提供则自动选择）

        Returns:
            dict: 收入指标字典
        """
        self.logger.info("提取收入指标...")

        # 如果数据包含多周，筛选指定周或最新一周
        if current_data and len(current_data) > 0 and '日期' in current_data[0]:
            if current_latest_week:
                current_week_data = [row for row in current_data if row.get('日期', '') == current_latest_week][0]
                self.logger.info(f"使用指定数据周: {current_latest_week}")
            else:
                # 获取最新一周的日期
                latest_date = max(row.get('日期', '') for row in current_data)
                current_week_data = [row for row in current_data if row.get('日期', '') == latest_date][0]  # 取唯一的一周数据
                self.logger.info(f"筛选最新一周数据: {latest_date}")
        else:
            current_week_data = current_data[-1] if current_data else {}

        # 如果上周数据包含多周，筛选指定周或最新一周
        if previous_data and len(previous_data) > 0 and '日期' in previous_data[0]:
            if previous_latest_week:
                previous_week_data = [row for row in previous_data if row.get('日期', '') == previous_latest_week][0]
                self.logger.info(f"使用指定上周数据周: {previous_latest_week}")
            else:
                latest_date = max(row.get('日期', '') for row in previous_data)
                previous_week_data = [row for row in previous_data if row.get('日期', '') == latest_date][0]  # 取唯一的一周数据
                self.logger.info(f"筛选上周数据: {latest_date}")
        else:
            previous_week_data = previous_data[-1] if previous_data else {}

        # 提取本周数据
        current_total = current_week_data.get('Total_Amt', 0)
        current_new = current_week_data.get('NewSubscribe_Amt', 0)
        current_renewal = current_week_data.get('Renewal_Amt', 0)

        current_new_users = current_week_data.get('NewSubscribe_Users', 0)
        current_renewal_users = current_week_data.get('Renewal_Users', 0)
        current_total_users = current_week_data.get('Total_Paid_Users', 0)

        # 提取上周数据
        previous_total = previous_week_data.get('Total_Amt', 0)
        previous_new = previous_week_data.get('NewSubscribe_Amt', 0)
        previous_renewal = previous_week_data.get('Renewal_Amt', 0)

        previous_new_users = previous_week_data.get('NewSubscribe_Users', 0)
        previous_renewal_users = previous_week_data.get('Renewal_Users', 0)
        previous_total_users = previous_week_data.get('Total_Paid_Users', 0)

        # 计算环比
        total_change = self.calculate_wow_change(current_total, previous_total)
        new_change = self.calculate_wow_change(current_new, previous_new)
        renewal_change = self.calculate_wow_change(current_renewal, previous_renewal)

        # 计算客单价
        current_arpu = current_week_data.get('整体客单价', 0)
        previous_arpu = previous_week_data.get('整体客单价', 0)

        new_arpu = current_week_data.get('新签首购订单价', 0)
        previous_new_arpu = previous_week_data.get('新签首购订单价', 0)

        renewal_arpu = current_week_data.get('续约复购订单价', 0)
        previous_renewal_arpu = previous_week_data.get('续约复购订单价', 0)

        # 生成分析
        metrics = {
            'total': round(current_total, 1),
            'change_abs': int(total_change['change_abs']),
            'trend': total_change['trend'],
            'change_rate': round(total_change['change_rate'], 1),
            'renewal_change': f"{int(renewal_change['change_abs']):+,}",
            'renewal_rate': round(renewal_change['change_rate'], 1),
            'new_change': f"{int(new_change['change_abs']):+,}",
            'new_rate': round(new_change['change_rate'], 1),
            'ai_summary': self._generate_revenue_ai_summary(current_total, previous_total, current_new, previous_new, current_renewal, previous_renewal),
            'normal_change': f"{int(total_change['change_abs']):+,}",
            'type_analysis': f"续约收入（{int(renewal_change['change_abs']):,} 美元）、新签（{int(new_change['change_abs']):,} 美元）",
            'users_analysis': f"付费用户数{int(current_total_users)}人（环比{round((current_total_users - previous_total_users) / previous_total_users * 100, 1) if previous_total_users > 0 else 0}%）",
            'arpu_analysis': f"整体客单价${current_arpu:.1f}（上周${previous_arpu:.1f}）"
        }

        # 添加维度分析
        if sku_data:
            metrics['sku_analysis'] = self._generate_sku_analysis(sku_data, previous_data)

        if country_data:
            metrics['country_analysis'] = self._generate_country_analysis(country_data)

        if tier_data:
            metrics['tier_analysis'] = self._generate_tier_analysis(tier_data)

        self.logger.info(f"✅ 收入指标提取完成: 总收入{metrics['total']:,}美元, 环比{metrics['change_rate']:.1f}%")

        return metrics

    def _generate_revenue_ai_summary(
        self,
        current_total: float,
        previous_total: float,
        current_new: float,
        previous_new: float,
        current_renewal: float,
        previous_renewal: float
    ) -> str:
        """生成收入AI总结"""
        lines = []

        # 收入趋势
        if current_total > previous_total:
            lines.append(f"📌 收入金额连续增长，当前收入（{int(current_total):,}美元）{'高于' if current_total > previous_total else '低于'}上周水平")
        else:
            lines.append(f"📌 收入金额连续{'2周' if current_renewal < previous_renewal else '1周'}下行，当前收入（{int(current_total):,}美元）{'高于' if current_total > previous_total else '低于'}上周水平")

        # 续约分析
        if current_renewal < previous_renewal:
            lines.append(f" ⦁📌 续约收入：连续续约收入减少{int(previous_renewal - current_renewal):,}美元，是收入{'降低' if current_total < previous_total else '增长'}的主因，续约收入已连续两周下滑，处于近期较低水平。")
        else:
            lines.append(f" ⦁📌 续约收入：续约收入增加{int(current_renewal - previous_renewal):,}美元，贡献显著。")

        # 新签分析
        if current_new > previous_new:
            lines.append(f" ⦁📌 新签收入：新签收入增加{int(current_new - previous_new):,}美元，新签用户数增长，表现良好。")
        else:
            lines.append(f" ⦁📌 新签收入：新签收入下降{int(previous_new - current_new):,}美元，需要关注获客质量。")

        return '\n'.join(lines)

    def _generate_sku_analysis(self, sku_data: List[Dict], previous_data: List[Dict]) -> str:
        """生成SKU维度分析"""
        # 实现SKU分析逻辑
        lines = ["SKU维度分析暂未实现"]
        return '\n'.join(lines)

    def _generate_country_analysis(self, country_data: List[Dict]) -> str:
        """生成国家维度分析"""
        # 实现国家分析逻辑
        lines = ["国家维度分析暂未实现"]
        return '\n'.join(lines)

    def _generate_tier_analysis(self, tier_data: List[Dict]) -> str:
        """生成账单分层分析"""
        # 实现账单分层分析逻辑
        lines = ["账单分层分析暂未实现"]
        return '\n'.join(lines)


if __name__ == '__main__':
    # 测试代码
    print("测试指标提取器\n")

    extractor = MetricsExtractor()

    # 测试环比计算
    result = extractor.calculate_wow_change(100, 80)
    print(f"环比变化: {result}")

    # 测试历史平均
    data = [
        {'WAU': 50000},
        {'WAU': 55000},
        {'WAU': 60000}
    ]
    avg = extractor.calculate_historical_avg(data, 'WAU')
    print(f"历史平均: {avg}")
