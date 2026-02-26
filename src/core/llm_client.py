#!/usr/bin/env python3
"""
外部大模型API客户端（支持OpenAI、Claude等）

支持多种LLM Provider：
- openai: OpenAI
- claude: Claude API
- 自定义: 可以添加其他provider

提供统一的调用接口，支持fallback到规则驱动方式
"""

import os
import requests
from typing import Dict, Optional
from src.logger import get_logger


class LLMClient:
    """外部大模型API客户端"""

    def __init__(
        self,
        config: Dict,
        logger=None
    ):
        """
        初始化LLM客户端

        Args:
            config: 配置字典，包含LLM相关配置
            logger: 日志记录器
        """
        self.config = config
        self.logger = logger or get_logger('llm_client')

        # 读取配置
        self.provider = self.config.get('llm', {}).get('provider', 'openai')
        self.api_key = self.config.get('llm', {}).get('api_key')
        self.model = self.config.get('llm', {}).get('model', 'gpt-3.5-turbo')
        self.base_url = self.config.get('llm', {}).get('base_url', '')
        self.timeout = self.config.get('llm', {}).get('timeout', 30)
        self.max_tokens = self.config.get('llm', {}).get('max_tokens', 500)
        self.temperature = self.config.get('llm', {}).get('temperature', 0.3)

        # 降级策略配置
        self.fallback_to_rule = self.config.get('llm', {}).get('fallback_to_rule', True)
        self.max_retries = self.config.get('llm', {}).get('max_retries', 2)
        self.retry_delay = self.config.get('llm', {}).get('retry_delay', 5)

        self.logger.info(f"LLM客户端初始化 - Provider: {self.provider}")

        # 检查API密钥配置
        if not self.api_key:
            # 优先从 LLM_API_KEY 读取，兼容 OPENAI_API_KEY
            env_key = os.getenv('LLM_API_KEY') or os.getenv('OPENAI_API_KEY')
            if env_key:
                self.api_key = env_key
                self.logger.info(f"✅ 从环境变量读取API密钥: {self.provider[:8]}...")
            else:
                self.logger.warning("⚠️ 未设置LLM_API_KEY或OPENAI_API_KEY环境变量")

    def generate_summary(
        self,
        section: str,
        data: Dict,
        current_data: Optional[Dict] = None
    ) -> str:
        """
        生成AI总结

        Args:
            section: 报告部分（traffic, activation, engagement, retention, revenue）
            data: 数据字典
            current_data: 当前周数据列表（可选）

        Returns:
            str: AI生成的总结内容
        """
        if not self.api_key:
            self.logger.warning("⚠️  API密钥未配置，无法调用LLM API")
            return "AI总结功能未配置，请检查API密钥设置。"

        # 构建提示词
        prompt = self._build_prompt(section, data)
        self.logger.debug(f"构建提示词完成，长度: {len(prompt)} 字符")

        # 调用对应的API方法
        if self.provider == 'openai':
            return self._call_openai(prompt)
        elif self.provider == 'claude':
            return self._call_claude(prompt)
        else:
            # 未知provider，降级到规则生成
            self.logger.warning(f"⚠️ 未知LLM Provider: {self.provider}")
            return self._call_openai_compatible(prompt)

    def _build_prompt(
        self,
        section: str,
        data: Dict
    ) -> str:
        """
        构建各部分的提示词模板

        Args:
            section: 报告部分
            data: 数据字典

        Returns:
            str: 提示词
        """

        # 流量部分提示词
        if section == 'traffic':
            return self._build_traffic_prompt(data)
        elif section == 'activation':
            return self._build_activation_prompt(data)
        elif section == 'engagement':
            return self._build_engagement_prompt(data)
        elif section == 'retention':
            return self._build_retention_prompt(data)
        elif section == 'revenue':
            return self._build_revenue_prompt(data)
        else:
            return self._build_generic_prompt(section, data)

    def _build_traffic_prompt(self, data: Dict) -> str:
        """构建流量部分提示词"""
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

    def _build_activation_prompt(self, data: Dict) -> str:
        """构建激活部分提示词"""
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

    def _build_engagement_prompt(self, data: Dict) -> str:
        """构建活跃部分提示词"""
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

    def _build_retention_prompt(self, data: Dict) -> str:
        """构建留存部分提示词"""
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

    def _build_revenue_prompt(self, data: Dict) -> str:
        """构建收入部分提示词"""
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
- 续约收入变化：{((renewal - data.get('renewal_previous', 0)) / data.get('renewal_previous', 0) * 100):.2f if data.get('renewal_previous', 0) > 0 else 0:.2f}%{'增长' if (renewal - data.get('renewal_previous', 0)) > 0 else '持平'}
- 新签收入变化：{((new_signing - data.get('new_signing_previous', 0)) / data.get('new_signing_previous', 0) * 100):.2f if data.get('new_signing_previous', 0) > 0 else 0:.2f}%{'增长' if (new_signing - data.get('new_signing_previous', 0)) > 0 else '持平'}

请分析收入变化的主要原因和后续趋势预测。字数控制在100字以内。"""

        return prompt

    def _build_generic_prompt(self, section: str, data: Dict) -> str:
        """构建通用提示词"""
        prompt = f"""请分析以下{section}数据并生成总结，字数控制在50字以内。"""
        return prompt

    def _call_openai(
        self,
        prompt: str
    ) -> str:
        """
        调用OpenAI兼容API（支持自定义base_url）

        Args:
            prompt: 提示词

        Returns:
            str: API响应
        """
        # 如果使用自定义base_url，使用requests库而不是官方SDK
        if self.base_url and self.base_url != "https://api.openai.com/v1/chat/completions":
            return self._call_openai_compatible(prompt)
        else:
            # 使用官方SDK
            try:
                import openai
                response = openai.Chat.completion.create(
                    api_key=self.api_key,
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    timeout=self.timeout
                )
                return response.choices[0].message.content
            except Exception as e:
                self.logger.error(f"❌ OpenAI API调用失败: {e}")
                raise

    def _call_claude(
        self,
        prompt: str
    ) -> str:
        """
        调用Claude API（通用兼容接口）

        Args:
            prompt: 提示词

        Returns:
            str: API响应
        """
        # 使用HTTP请求调用（通用接口，支持多种provider）
        try:
            # Claude API端点示例
            if self.provider == 'claude':
                base_url = "https://api.anthropic.com/v1/messages"
            elif self.provider == 'openai':
                base_url = self.base_url if self.base_url else "https://api.openai.com/v1/chat/completions"

            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }

            payload = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            }

            import requests
            response = requests.post(
                base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()['content'][0]['text']
            else:
                self.logger.error(f"❌ {self.provider.upper()} API调用失败 - HTTP {response.status_code}")
                raise Exception(f"{self.provider} API调用失败")

    def _call_openai_compatible(
        self,
        prompt: str
    ) -> str:
        """
        OpenAI兼容接口调用（降级默认）

        通用OpenAI SDK格式，避免区分不同provider的实现细节
        """
        """
        return self._call_openai(prompt)
