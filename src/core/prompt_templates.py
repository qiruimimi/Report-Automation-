#!/usr/bin/env python3
"""
提示词模板模块

将LLM客户端使用的结构化提示词模板提取出来，便于维护和扩展。
"""

from typing import Dict, Optional
from src.logger import get_logger


class PromptTemplates:
    """提示词模板管理类"""

    def __init__(self, logger=None):
        """
        初始化提示词模板

        Args:
            logger: 日志记录器
        """
        self.logger = logger or get_logger('prompt_templates')

    def get_prompt_template(
        self,
        section: str,
        data: Optional[Dict] = None
    ) -> str:
        """
        获取指定部分的提示词模板

        Args:
            section: 报告部分（traffic, activation, engagement, retention, revenue）
            data: 数据字典（可选）

        Returns:
            str: 提示词模板字符串
        """
        if section not in self._templates:
            self.logger.warning(f"⚠️  未找到部分 {section} 的提示词模板")
            return self._get_fallback_prompt(section, data) if data else ""

        # 流量部分
        if section == 'traffic':
            return self._get_traffic_prompt(data)

        # 激活部分
        elif section == 'activation':
            return self._get_activation_prompt(data)

        # 活跃部分
        elif section == 'engagement':
            return self._get_engagement_prompt(data)

        # 留存部分
        elif section == 'retention':
            return self._get_retention_prompt(data)

        # 收入部分
        elif section == 'revenue':
            return self._get_revenue_prompt(data)

        # 默认fallback模板
        return self._get_fallback_prompt(section, data)

    def _get_fallback_prompt(self, section: str, data: Dict) -> str:
        """
        默认降级提示词模板（规则驱动方式）
        """
        return self._get_traffic_prompt(data)

    def _get_traffic_prompt(self, data: Dict) -> str:
        """获取流量部分提示词（数据驱动）"""
        new_visitors = data.get('new_visitors_current', 0)
        visitors_change = data.get('visitors_wow', {}).get('change_rate', 0)

        prompt = f"""请分析以下流量数据并生成总结：
【数据概览】
- 新访客数：{new_visitors:,}人
- 注册数：{data.get('registrations_current', 0):,}人
- 转化率：{data.get('conversion_rate_current', 0):.2f}%

【环比变化】
- 访客变化：{visitors_change:.1f}%{'增长' if visitors_change > 0 else '下降'}
- 注册变化：{data.get('registrations_wow', {}).get('change_rate', 0):.2f}%{'增长' if data.get('registrations_wow', {}).get('change_rate', 0) > 0 else '下降'}
- 转化率变化：{data.get('conversion_rate_wow', {}).get('change_rate', 0):.2f}%{'增长' if data.get('conversion_rate_wow', {}).get('change_rate', 0) > 0 else '下降'}

请用1-2句话总结关键洞察，突出异常值和重要趋势。字数控制在80字以内。"""

        return prompt

    def _get_activation_prompt(self, data: Dict) -> str:
        """获取激活部分提示词（数据驱动）"""
        new_users = data.get('new_registered_users', 0)
        step1 = data.get('step1_current_rate', 0)
        step2 = data.get('step2_current_rate', 0)
        step3 = data.get('step3_current_rate', 0)
        step4 = data.get('step4_current_rate', 0)
        step1_prev = data.get('step1_previous_rate', 0)
        step2_prev = data.get('step2_previous_rate', 0)
        step3_prev = data.get('step3_previous_rate', 0)
        step4_prev = data.get('step4_previous_rate', 0)

        prompt = f"""请分析以下激活漏斗数据并生成总结：
【漏斗数据】
- 新注册用户：{new_users:,}人
- 注册→进工具：{step1:}
- 进工具→画户型：{step2:}
- 画户型→拖模型：{step3:}
- 拖模型→渲染：{step4:}

【环比变化】
- 注册→进工具变化：{(step1 - step1_prev):.2f}%{'增长' if step1 > step1_prev else '下降' if step1 < step1_prev else '持平'}
- 进工具→画户型变化：{(step2 - step2_prev):.2f}%{'增长' if step2 > step2_prev else '下降' if step2 < step2_prev else '持平'}
- 画户型→拖模型变化：{(step3 - step3_prev):.2f}%{'增长' if step3 > step3_prev else '下降' if step3 < step3_prev else '持平'}
- 拖模型→渲染变化：{(step4 - step4_prev):.2f}%{'增长' if step4 > step4_prev else '下降' if step4 < step4_prev else '持平'}
- 总体转化率变化：{(step4 - step4_prev):.2f}%{'增长' if step4 > step4_prev else '下降'}

请总结转化率明显变化的步骤和可能的原因。字数控制在100字以内。"""

        return prompt

    def _get_engagement_prompt(self, data: Dict) -> str:
        """获取活跃部分提示词（数据驱动）"""
        wau = data.get('wau_current', 0)
        wau_change = data.get('wau_wow', {}).get('change_rate', 0)
        new_user_wau = data.get('new_user_wau', 0)
        old_user_wau = data.get('old_user_wau', 0)
        new_user_change = data.get('new_user_wow', 0)
        old_user_change = data.get('old_user_wow', 0)

        prompt = f"""请分析以下活跃数据并生成总结：
【活跃数据】
- WAU总数：{wau:,}人
- 新用户WAU：{new_user_wau:,}人
- 老用户WAU：{old_user_wau:,}人

【环比变化】
- WAU变化：{wau_change:.1f}%{'增长' if wau_change > 0 else '下降'}
- 新用户WAU变化：{new_user_change:.1f}%{'增长' if new_user_change > 0 else '下降'}
- 老用户WAU变化：{old_user_change:.1f}%{'增长' if old_user_change > 0 else '下降'}

请分析新老用户贡献的变化趋势。字数控制在100字以内。"""

        return prompt

    def _get_retention_prompt(self, data: Dict) -> str:
        """获取留存部分提示词（数据驱动）"""
        new_rate = data.get('new_user_retention_rate', 0)
        old_rate = data.get('old_user_retention_rate', 0)
        level = data.get('new_user_retention_level', '')
        trend = data.get('old_user_trend_note', '')

        prompt = f"""请分析以下留存数据并生成总结：
【留存数据】
- 新用户留存率：{new_rate:}
- 老用户留存率：{old_rate:}

【对比分析】
- 新用户留存处于：{level}水平
- 老用户留存状态：{trend}

请提供留存率变化的原因分析和改进建议。字数控制在100字以内。"""

        return prompt

    def _get_revenue_prompt(self, data: Dict) -> str:
        """获取收入部分提示词（数据驱动）"""
        total = data.get('total_current', 0)
        previous = data.get('total_previous', 0)
        renewal = data.get('renewal_revenue', 0)
        new_signing = data.get('new_signing_revenue', 0)
        change = data.get('wow', {}).get('change_rate', 0)

        prompt = f"""请分析以下收入数据并生成总结：
【收入数据】
- 总收入：{total:}美元
- 续约收入：{renewal:}美元
- 新签收入：{new_signing:}美元

【环比变化】
- 总收入变化：{change:.1f}%{'增长' if change > 0 else '下降'}
- 续约收入变化：{((renewal - previous) / previous * 100):.2f if previous > 0 else 0:.2f}%{'增长' if (renewal - previous) > 0 else '持平'}
- 新签收入变化：{((new_signing - data.get('new_signing_previous', 0)) / data.get('new_signing_previous', 0) * 100):.2f if data.get('new_signing_previous', 0) > 0 else 0:.2f}%{'增长' if (new_signing - data.get('new_signing_previous', 0)) > 0 else '持平'}

请分析收入变化的主要原因和后续趋势预测。字数控制在100字以内。"""

        return prompt

    def _get_traffic_prompt_template(self, data: Dict) -> str:
        """
        流量部分提示词模板（数据驱动）
        """
        new_visitors = data.get('new_visitors_current', 0)
        visitors_change = data.get('visitors_wow', {}).get('change_rate', 0)

        prompt = f"""请分析以下流量数据并生成总结：
【数据概览】
- 新访客数：{new_visitors:,}人
- 注册数：{data.get('registrations_current', 0):,}人
- 转化率：{data.get('conversion_rate_current', 0):.2f}%

【环比变化】
- 访客变化：{visitors_change:.1f}%{'增长' if visitors_change > 0 else '下降'}
- 注册变化：{data.get('registrations_wow', {}).get('change_rate', 0):.2f}%{'增长' if data.get('registrations_wow', {}).get('change_rate', 0) > 0 else '下降'}
- 转化率变化：{data.get('conversion_rate_wow', {}).get('change_rate', 0):.2f}%{'增长' if data.get('conversion_rate_wow', {}).get('change_rate', 0) > 0 else '下降'}

请用1-2句话总结关键洞察，突出异常值和重要趋势。字数控制在80字以内。"""

        return prompt