#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI总结生成模块

支持两种模式：
1. LLM模式：调用外部大模型API（OpenAI、Claude等）生成智能总结
2. 规则模式：基于预定义规则生成客观总结（作为fallback）
"""

from typing import Dict, List, Optional
from src.logger import get_logger

logger = get_logger('ai_summary')


class AISummaryGenerator:
    """
    AI总结生成器

    支持LLM API调用和规则驱动两种模式
    当LLM不可用时自动降级到规则驱动
    """

    def __init__(self, config: Dict = None, logger=None):
        """
        初始化AI总结生成器

        Args:
            config: 配置字典，包含LLM相关配置
            logger: 日志记录器
        """
        self.config = config or {}
        self.logger = logger or get_logger('ai_summary')
        self.llm_client = None

        # 初始化LLM客户端（如果配置了LLM）
        llm_config = self.config.get('llm', {})
        if llm_config.get('enabled', False):
            try:
                from src.core.llm_client import LLMClient
                self.llm_client = LLMClient(self.config, self.logger)
                self.logger.info("✅ LLM客户端初始化成功")
            except ImportError as e:
                self.logger.warning(f"⚠️ 无法导入LLMClient: {e}")
            except Exception as e:
                self.logger.warning(f"⚠️ LLM客户端初始化失败: {e}")

        # 降级策略配置
        self.fallback_to_rule = llm_config.get('fallback_to_rule', True)

    def generate_summary(
        self,
        section: str,
        analysis: Dict,
        current_data: List[Dict] = None
    ) -> str:
        """
        生成指定部分的AI总结

        优先使用LLM API，失败时降级到规则驱动

        Args:
            section: 部分名称 (traffic, activation, engagement, retention, revenue)
            analysis: 分析结果字典
            current_data: 当前数据列表（可选）

        Returns:
            str: AI生成的总结文本
        """
        # 优先使用LLM
        if self.llm_client:
            try:
                summary = self.llm_client.generate_summary(section, analysis, current_data)
                self.logger.info(f"✅ LLM生成 {section} 总结成功")
                return summary
            except Exception as e:
                self.logger.warning(f"⚠️ LLM调用失败，降级到规则生成: {e}")
                if self.fallback_to_rule:
                    return self._generate_rule_based_summary(section, analysis, current_data)
                else:
                    return f"{section}总结生成失败"
        else:
            # LLM未配置，使用规则生成
            self.logger.debug(f"使用规则驱动生成 {section} 总结")
            return self._generate_rule_based_summary(section, analysis, current_data)

    def _generate_rule_based_summary(
        self,
        section: str,
        analysis: Dict,
        current_data: List[Dict] = None
    ) -> str:
        """
        使用规则驱动生成总结（fallback模式）

        Args:
            section: 部分名称
            analysis: 分析结果
            current_data: 当前数据

        Returns:
            str: 规则生成的总结文本
        """
        try:
            if section == 'traffic':
                return self._generate_traffic_summary(analysis)
            elif section == 'activation':
                return self._generate_activation_summary(analysis, current_data)
            elif section == 'engagement':
                return self._generate_engagement_summary(analysis)
            elif section == 'retention':
                return self._generate_retention_summary(analysis)
            elif section == 'revenue':
                return self._generate_revenue_summary(analysis)
            else:
                return f"{section}部分暂无AI总结"
        except Exception as e:
            self.logger.warning(f"生成{section}总结时出错: {e}")
            return f"{section}总结生成失败"

    def _generate_traffic_summary(self, analysis: Dict) -> str:
        """生成流量部分总结（规则驱动）"""
        visitors_current = analysis.get('new_visitors_current', 0)
        visitors_wow = analysis.get('visitors_wow', {})
        registrations_current = analysis.get('registrations_current', 0)
        registrations_wow = analysis.get('registrations_wow', {})
        conversion_rate_current = analysis.get('conversion_rate_current', 0)

        # 构建总结
        summary_parts = []

        # 访客情况
        if visitors_current > 0:
            visitors_change = visitors_wow.get('change_rate', 0)
            if visitors_change > 5:
                summary_parts.append(f"新访客{visitors_current:,}人，环比大幅增长{visitors_change:.1f}%")
            elif visitors_change > 0:
                summary_parts.append(f"新访客{visitors_current:,}人，环比增长{visitors_change:.1f}%")
            elif visitors_change < -5:
                summary_parts.append(f"新访客{visitors_current:,}人，环比大幅下降{abs(visitors_change):.1f}%")
            else:
                summary_parts.append(f"新访客{visitors_current:,}人，环比基本持平")
        else:
            summary_parts.append("暂无访客数据")

        # 注册情况
        if registrations_current > 0:
            regs_change = registrations_wow.get('change_rate', 0)
            if regs_change > 5:
                summary_parts.append(f"注册{registrations_current:,}人，环比增长{regs_change:.1f}%")
            elif regs_change < -5:
                summary_parts.append(f"注册{registrations_current:,}人，环比下降{abs(regs_change):.1f}%")

        # 转化率情况
        if conversion_rate_current > 0:
            summary_parts.append(f"整体转化率{conversion_rate_current:.2f}%")

        return "，".join(summary_parts) if summary_parts else "暂无足够数据进行分析"

    def _generate_activation_summary(self, analysis: Dict, current_data: List[Dict]) -> str:
        """生成激活部分总结（规则驱动）"""
        new_registered = analysis.get('new_registered_users', 0)
        step1_rate = analysis.get('step1_current_rate', 0)
        step4_rate = analysis.get('step4_current_rate', 0)

        summary_parts = []

        if new_registered > 0:
            summary_parts.append(f"本周新注册用户{new_registered:,}人")

            # 注册到进工具转化
            step1_change = analysis.get('step1_change_rate', 0)
            if abs(step1_change) > 5:
                direction = "显著" if step1_change > 0 else "明显"
                summary_parts.append(f"注册到进工具转化率{step1_rate:.2f}%，环比{direction}{abs(step1_change):.2f}%")
            else:
                summary_parts.append(f"注册到进工具转化率{step1_rate:.2f}%")

            # 整体转化率（拖模型到渲染）
            step4_change = analysis.get('step4_change_rate', 0)
            if abs(step4_change) > 5:
                direction = "提升" if step4_change > 0 else "下降"
                summary_parts.append(f"整体转化率{step4_rate:.2f}%，环比{direction}{abs(step4_change):.2f}%")
            else:
                summary_parts.append(f"整体转化率{step4_rate:.2f}%")

        return "，".join(summary_parts) if summary_parts else "暂无足够数据进行分析"

    def _generate_engagement_summary(self, analysis: Dict) -> str:
        """生成活跃部分总结（规则驱动）"""
        wau_current = analysis.get('wau_current', 0)
        wau_wow = analysis.get('wau_wow', {})
        wau_contribution = analysis.get('wau_contribution', '')
        new_user_wau = analysis.get('new_user_wau', 0)
        old_user_wau = analysis.get('old_user_wau', 0)

        summary_parts = []

        if wau_current > 0:
            wau_change = wau_wow.get('change_rate', 0)
            if abs(wau_change) > 5:
                trend_desc = "显著增长" if wau_change > 0 else "显著下降"
                summary_parts.append(f"工具WAU{wau_current:,}人，环比{trend_desc}{abs(wau_change):.1f}%")
            elif abs(wau_change) > 0:
                trend_desc = "增长" if wau_change > 0 else "下降"
                summary_parts.append(f"工具WAU{wau_current:,}人，环比{trend_desc}{abs(wau_change):.1f}%")
            else:
                summary_parts.append(f"工具WAU{wau_current:,}人，环比基本持平")

            # 用户构成
            if '新用户' in wau_contribution:
                summary_parts.append(f"以新用户为主（{new_user_wau:,}人）")
            elif '老用户' in wau_contribution:
                summary_parts.append(f"以老用户为主（{old_user_wau:,}人）")
            else:
                summary_parts.append(f"新老用户均衡（新用户{new_user_wau:,}人，老用户{old_user_wau:,}人）")
        else:
            summary_parts.append("暂无活跃数据")

        return "，".join(summary_parts) if summary_parts else "暂无足够数据进行分析"

    def _generate_retention_summary(self, analysis: Dict) -> str:
        """生成留存部分总结（规则驱动）"""
        new_user_rate = analysis.get('new_user_retention_rate', 0)
        old_user_rate = analysis.get('old_user_retention_rate', 0)
        new_user_level = analysis.get('new_user_retention_level', '')

        summary_parts = []

        if new_user_rate > 0 and old_user_rate > 0:
            # 新用户留存
            if new_user_level == '高':
                summary_parts.append(f"新用户次周留存率{new_user_rate:.2f}%，处于近12周高水平")
            elif new_user_level == '中等':
                summary_parts.append(f"新用户次周留存率{new_user_rate:.2f}%，处于近12周中等水平")
            else:
                summary_parts.append(f"新用户次周留存率{new_user_rate:.2f}%，处于近12周较低水平")

            # 老用户留存
            old_trend_note = analysis.get('old_user_trend_note', '')
            if old_trend_note == '稳定':
                summary_parts.append(f"老用户次周留存率{old_user_rate:.2f}%，保持稳定")
            else:
                summary_parts.append(f"老用户次周留存率{old_user_rate:.2f}%，{old_trend_note}")

            # 留存率比较
            if old_user_rate > new_user_rate:
                gap = old_user_rate - new_user_rate
                summary_parts.append(f"老用户留存率比新用户高{gap:.2f}%")
            elif new_user_rate > old_user_rate:
                gap = new_user_rate - old_user_rate
                summary_parts.append(f"新用户留存率比老用户高{gap:.2f}%")
        else:
            summary_parts.append("暂无足够留存数据进行分析")

        return "，".join(summary_parts) if summary_parts else "暂无足够数据进行分析"

    def _generate_revenue_summary(self, analysis: Dict) -> str:
        """生成收入部分总结（规则驱动）"""
        total_current = analysis.get('total_current', 0)
        total_previous = analysis.get('total_previous', 0)
        wow = analysis.get('wow', {})
        renewal_revenue = analysis.get('renewal_revenue', 0)
        new_signing_revenue = analysis.get('new_signing_revenue', 0)

        summary_parts = []

        if total_current > 0:
            # 总收入环比
            change_rate = wow.get('change_rate', 0)
            if abs(change_rate) > 10:
                trend_desc = "大幅" if change_rate > 0 else "显著"
                summary_parts.append(f"本周收入{total_current:,.0f}美元，环比{trend_desc}{abs(change_rate):.2f}%")
            elif abs(change_rate) > 0:
                trend_desc = "" if abs(change_rate) < 2 else ("增长" if change_rate > 0 else "下降")
                summary_parts.append(f"本周收入{total_current:,.0f}美元，环比{trend_desc}{abs(change_rate):.2f}%")
            else:
                summary_parts.append(f"本周收入{total_current:,.0f}美元，环比基本持平")

            # 收入结构分析
            if renewal_revenue > 0 and new_signing_revenue > 0:
                renewal_ratio = renewal_revenue / total_current * 100
                new_signing_ratio = new_signing_revenue / total_current * 100
                renewal_growth = analysis.get('renewal_growth_rate', 0)
                new_signing_growth = analysis.get('new_signing_growth_rate', 0)

                if renewal_ratio > new_signing_ratio:
                    summary_parts.append(f"续约收入占主导（{renewal_ratio:.1f}%），环比增长{renewal_growth:.2f}%")
                    summary_parts.append(f"新签收入占{new_signing_ratio:.1f}%，环比增长{new_signing_growth:.2f}%")
                elif renewal_ratio < new_signing_ratio:
                    summary_parts.append(f"新签收入占主导（{new_signing_ratio:.1f}%），环比增长{new_signing_growth:.2f}%")
                    summary_parts.append(f"续约收入占{renewal_ratio:.1f}%，环比增长{renewal_growth:.2f}%")
                else:
                    summary_parts.append(f"续约与新签收入均衡（各占50%左右）")
                    if renewal_growth > 0:
                        summary_parts.append(f"续约收入环比增长{renewal_growth:.2f}%")
                    if new_signing_growth > 0:
                        summary_parts.append(f"新签收入环比增长{new_signing_growth:.2f}%")
            elif renewal_revenue > 0:
                summary_parts.append(f"续约收入{renewal_revenue:,.0f}美元，环比增长{analysis.get('renewal_growth_rate', 0):.2f}%")
            elif new_signing_revenue > 0:
                summary_parts.append(f"新签收入{new_signing_revenue:,.0f}美元，环比增长{analysis.get('new_signing_growth_rate', 0):.2f}%")

        else:
            summary_parts.append("暂无收入数据")

        return "，".join(summary_parts) if summary_parts else "暂无足够数据进行分析"

    def generate_all_summaries(
        self,
        analysis_results: Dict,
        current_data: Dict = None
    ) -> Dict[str, str]:
        """
        生成所有部分的AI总结

        Args:
            analysis_results: 所有分析结果
            current_data: 当前数据（可选）

        Returns:
            dict: 各部分的AI总结
        """
        summaries = {}

        sections = ['traffic', 'activation', 'engagement', 'retention', 'revenue']

        for section in sections:
            if section in analysis_results:
                section_data = current_data.get(section, []) if current_data else None
                summaries[section] = self.generate_summary(section, analysis_results[section], section_data)

        self.logger.info("✅ 所有部分AI总结生成完成")
        return summaries


if __name__ == "__main__":
    # 测试代码
    print("测试AI总结生成模块\n")

    # 测试规则驱动模式
    generator = AISummaryGenerator(config={'llm': {'enabled': False}})

    # 测试流量总结
    traffic_analysis = {
        'new_visitors_current': 1000,
        'visitors_wow': {'change_rate': 10.5},
        'registrations_current': 200,
        'registrations_wow': {'change_rate': 5.2},
        'conversion_rate_current': 20.0
    }
    print(f"\n流量总结（规则驱动）: {generator.generate_summary('traffic', traffic_analysis)}")

    # 测试活跃总结
    engagement_analysis = {
        'wau_current': 50000,
        'wau_wow': {'change_rate': 4.17},
        'wau_contribution': '新用户为主',
        'new_user_wau': 20000,
        'old_user_wau': 30000
    }
    print(f"\n活跃总结（规则驱动）: {generator.generate_summary('engagement', engagement_analysis)}")

    # 测试留存总结
    retention_analysis = {
        'new_user_retention_rate': 45.0,
        'new_user_retention_level': '中等',
        'old_user_retention_rate': 60.0,
        'old_user_trend_note': '稳定'
    }
    print(f"\n留存总结（规则驱动）: {generator.generate_summary('retention', retention_analysis)}")

    # 测试收入总结
    revenue_analysis = {
        'total_current': 100000,
        'total_previous': 90000,
        'wow': {'change_rate': 11.11},
        'renewal_revenue': 60000,
        'new_signing_revenue': 40000,
        'renewal_growth_rate': 11.11,
        'new_signing_growth_rate': 11.11
    }
    print(f"\n收入总结（规则驱动）: {generator.generate_summary('revenue', revenue_analysis)}")

    print("\n" + "=" * 50)
    print("如需测试LLM模式，请配置 config/config.yaml 中的 llm.enabled")
