#!/usr/bin/env python3
"""
数据处理器 - 整合所有数据并生成报告

功能:
- 整合多个SQL查询结果
- 执行跨部分的数据关联
- 生成标准化数据结构
- 调用指标提取器
"""

import json
from typing import Dict, List, Optional
from pathlib import Path

from metrics_extractor import MetricsExtractor
from logger import get_logger


class DataProcessor:
    """数据处理器"""

    def __init__(self, extractor: MetricsExtractor = None, logger=None):
        """
        初始化数据处理器

        Args:
            extractor: 指标提取器
            logger: 日志记录器
        """
        self.extractor = extractor or MetricsExtractor()
        self.logger = logger or get_logger('data_processor')

    def process_all_sections(
        self,
        current_data: Dict[str, List[Dict]],
        previous_data: Dict[str, List[Dict]],
        historical_data: Optional[Dict[str, List[Dict]]] = None,
        dimension_data: Optional[Dict[str, List[Dict]]] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        处理所有部分的数据

        Args:
            current_data: 本周所有数据
            previous_data: 上周所有数据
            historical_data: 历史数据（可选）
            dimension_data: 维度数据（可选）
            metadata: 元数据，包含 latest_week 等信息（可选）

        Returns:
            dict: 处理后的所有指标
        """
        self.logger.info("=" * 60)
        self.logger.info("开始处理所有数据部分")
        self.logger.info("=" * 60)

        if historical_data is None:
            historical_data = {}

        if dimension_data is None:
            dimension_data = {}

        if metadata is None:
            metadata = {}

        results = {}

        # 1. 流量部分
        if 'traffic' in current_data:
            self.logger.info("\n处理流量部分...")
            results['traffic'] = self.process_traffic_data(
                current_data['traffic'],
                previous_data.get('traffic', []),
                current_latest_week=metadata.get('traffic_latest_week'),
                previous_latest_week=metadata.get('traffic_previous_latest_week')
            )
        else:
            self.logger.warning("⚠️  流量数据缺失")

        # 2. 激活部分
        if 'activation' in current_data:
            self.logger.info("\n处理激活部分...")
            results['activation'] = self.process_activation_data(
                current_data['activation'],
                previous_data.get('activation', [])
            )
        else:
            self.logger.warning("⚠️  激活数据缺失")

        # 3. 活跃部分
        if 'engagement' in current_data:
            self.logger.info("\n处理活跃部分...")
            results['engagement'] = self.process_engagement_data(
                current_data.get('engagement', []),
                previous_data.get('engagement', []),
                historical_data.get('engagement_historical', []),
                current_latest_week=metadata.get('engagement_latest_week'),
                previous_latest_week=metadata.get('engagement_previous_latest_week')
            )
        else:
            self.logger.warning("⚠️  活跃数据缺失")

        # 4. 留存部分
        if 'retention' in current_data:
            self.logger.info("\n处理留存部分...")
            results['retention'] = self.process_retention_data(
                current_data['retention'],
                previous_data.get('retention', []),
                historical_data.get('retention_historical', []),
                current_latest_week=metadata.get('retention_latest_week'),
                previous_latest_week=metadata.get('retention_previous_latest_week')
            )
        else:
            self.logger.warning("⚠️  留存数据缺失")

        # 5. 收入部分
        if 'revenue' in current_data:
            self.logger.info("\n处理收入部分...")
            results['revenue'] = self.process_revenue_data(
                current_data['revenue'],
                previous_data.get('revenue', []),
                dimension_data.get('revenue_by_sku', []),
                dimension_data.get('revenue_by_country', []),
                dimension_data.get('revenue_by_tier', []),
                current_latest_week=metadata.get('revenue_latest_week'),
                previous_latest_week=metadata.get('revenue_previous_latest_week')
            )
        else:
            self.logger.warning("⚠️  收入数据缺失")

        self.logger.info("\n" + "=" * 60)
        self.logger.info("✅ 所有数据处理完成")
        self.logger.info("=" * 60)

        return results

    def process_traffic_data(
        self,
        current_data: List[Dict],
        previous_data: List[Dict],
        current_latest_week: Optional[str] = None,
        previous_latest_week: Optional[str] = None
    ) -> Dict:
        """
        处理流量数据

        Args:
            current_data: 本周流量数据
            previous_data: 上周流量数据
            current_latest_week: 本周的数据周标签（从JSON元数据中读取）
            previous_latest_week: 上周的数据周标签（从JSON元数据中读取）

        Returns:
            dict: 流量指标
        """
        try:
            metrics = self.extractor.extract_traffic_metrics(
                current_data,
                previous_data,
                current_latest_week,
                previous_latest_week
            )
            self.logger.info(f"✅ 流量指标: 访客{metrics['total_guests']:,}, 注册{metrics['total_registers']:,}")
            return metrics
        except Exception as e:
            self.logger.error(f"❌ 流量数据处理失败: {e}")
            return self._get_default_traffic_metrics()

    def process_activation_data(
        self,
        current_data: List[Dict],
        previous_data: List[Dict]
    ) -> Dict:
        """
        处理激活数据

        Args:
            current_data: 本周激活数据
            previous_data: 上周激活数据

        Returns:
            dict: 激活指标
        """
        try:
            metrics = self.extractor.extract_activation_metrics(
                current_data,
                previous_data
            )
            self.logger.info(f"✅ 激活指标: 总转化率{metrics.get('total_lw', 0)}%")
            return metrics
        except Exception as e:
            self.logger.error(f"❌ 激活数据处理失败: {e}")
            return self._get_default_activation_metrics()

    def process_engagement_data(
        self,
        current_data: List[Dict],
        previous_data: List[Dict],
        historical_data: List[Dict],
        current_latest_week: Optional[str] = None,
        previous_latest_week: Optional[str] = None
    ) -> Dict:
        """
        处理活跃数据

        Args:
            current_data: 本周活跃数据
            previous_data: 上周活跃数据
            historical_data: 历史活跃数据
            current_latest_week: 本周的数据周标签（从JSON元数据中读取）
            previous_latest_week: 上周的数据周标签（从JSON元数据中读取）

        Returns:
            dict: 活跃指标
        """
        try:
            metrics = self.extractor.extract_engagement_metrics(
                current_data,
                previous_data,
                historical_data if historical_data else None,
                current_latest_week,
                previous_latest_week
            )
            self.logger.info(f"✅ 活跃指标: WAU{metrics['total_wau']:,}, 环比{metrics['wow']}%")
            return metrics
        except Exception as e:
            self.logger.error(f"❌ 活跃数据处理失败: {e}")
            return self._get_default_engagement_metrics()

    def process_retention_data(
        self,
        current_data: List[Dict],
        previous_data: List[Dict],
        historical_data: List[Dict],
        current_latest_week: Optional[str] = None,
        previous_latest_week: Optional[str] = None
    ) -> Dict:
        """
        处理留存数据

        Args:
            current_data: 本周留存数据
            previous_data: 上周留存数据
            historical_data: 历史留存数据
            current_latest_week: 本周的数据周标签（从JSON元数据中读取）
            previous_latest_week: 上周的数据周标签（从JSON元数据中读取）

        Returns:
            dict: 留存指标
        """
        try:
            metrics = self.extractor.extract_retention_metrics(
                current_data,
                previous_data,
                historical_data if historical_data else None,
                current_latest_week,
                previous_latest_week
            )
            self.logger.info(f"✅ 留存指标: 新用户{metrics['new_rate']}%, 老用户{metrics['old_rate']}%")
            return metrics
        except Exception as e:
            self.logger.error(f"❌ 留存数据处理失败: {e}")
            return self._get_default_retention_metrics()

    def process_revenue_data(
        self,
        current_data: List[Dict],
        previous_data: List[Dict],
        sku_data: List[Dict],
        country_data: List[Dict],
        tier_data: List[Dict],
        current_latest_week: Optional[str] = None,
        previous_latest_week: Optional[str] = None
    ) -> Dict:
        """
        处理收入数据

        Args:
            current_data: 本周收入数据
            previous_data: 上周收入数据
            sku_data: SKU维度数据
            country_data: 国家维度数据
            tier_data: 账单分层数据
            current_latest_week: 本周的数据周标签（从JSON元数据中读取）
            previous_latest_week: 上周的数据周标签（从JSON元数据中读取）

        Returns:
            dict: 收入指标
        """
        try:
            metrics = self.extractor.extract_revenue_metrics(
                current_data,
                previous_data,
                sku_data if sku_data else None,
                country_data if country_data else None,
                tier_data if tier_data else None,
                current_latest_week,
                previous_latest_week
            )
            self.logger.info(f"✅ 收入指标: 总收入${metrics['total']:,}, 环比{metrics['change_rate']:.1f}%")
            return metrics
        except Exception as e:
            self.logger.error(f"❌ 收入数据处理失败: {e}")
            return self._get_default_revenue_metrics()

    def load_data_from_files(
        self,
        base_dir: str,
        week_label: str,
        previous_week_label: Optional[str] = None
    ) -> Dict[str, Dict[str, List[Dict]]]:
        """
        从文件加载数据

        Args:
            base_dir: 基础目录
            week_label: 本周标签
            previous_week_label: 上周标签（可选）

        Returns:
            dict: 加载的数据，包含 'current', 'previous', 'historical', 'dimension' 四个部分
        """
        base_path = Path(base_dir)
        data = {
            'current': {},
            'previous': {},
            'historical': {},
            'dimension': {}
        }

        self.logger.info(f"开始加载数据文件: base_dir={base_dir}, week_label={week_label}")

        # 加载本周数据
        current_files = {
            'traffic': f'traffic_weekly_{week_label}.json',
            'activation': f'activation_weekly_{week_label}.json',
            'engagement': f'engagement_weekly_{week_label}.json',
            'retention': f'retention_weekly_{week_label}.json',
            'revenue': f'revenue_weekly_{week_label}.json'
        }

        for key, filename in current_files.items():
            file_path = base_path / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # 如果文件包含 'data' 字段，提取它
                    if isinstance(loaded, dict) and 'data' in loaded:
                        data['current'][key] = loaded['data']
                        # 保存元数据中的 latest_week
                        if 'query' in loaded and 'latest_week' in loaded['query']:
                            data[f'{key}_latest_week'] = loaded['query']['latest_week']
                    else:
                        data['current'][key] = loaded
                    self.logger.info(f"✅ 加载本周数据: {filename} ({len(data['current'][key])} 行)")
            else:
                self.logger.warning(f"⚠️  本周文件不存在: {filename}")

        # 加载上周数据（如果提供）
        if previous_week_label:
            previous_files = {
                'traffic': f'traffic_weekly_{previous_week_label}.json',
                'activation': f'activation_weekly_{previous_week_label}.json',
                'engagement': f'engagement_weekly_{previous_week_label}.json',  # 使用对应的周文件
                'retention': f'retention_weekly_{previous_week_label}.json',
                'revenue': f'revenue_weekly_{previous_week_label}.json'
            }

            for key, filename in previous_files.items():
                file_path = base_path / filename
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        loaded = json.load(f)
                        # 如果文件包含 'data' 字段，提取它
                        if isinstance(loaded, dict) and 'data' in loaded:
                            data['previous'][key] = loaded['data']
                            # 保存元数据中的 latest_week
                            if 'query' in loaded and 'latest_week' in loaded['query']:
                                data[f'{key}_previous_latest_week'] = loaded['query']['latest_week']
                        else:
                            data['previous'][key] = loaded
                        self.logger.info(f"✅ 加载上周数据: {filename} ({len(data['previous'][key])} 行)")
                else:
                    self.logger.warning(f"⚠️  上周文件不存在: {filename}")
                    # 如果上周文件不存在，但有本周数据，则使用本周数据作为上周数据
                    # 这样 extractor 可以从同一个文件中筛选不同周的数据
                    if key in data['current']:
                        data['previous'][key] = data['current'][key]
                        self.logger.info(f"   使用本周数据作为{key}的上周数据（将从同一文件中筛选不同周）")

                        # 尝试从 metadata 计算上周的标签
                        current_latest_week_key = f'{key}_latest_week'
                        if current_latest_week_key in data:
                            from datetime import datetime, timedelta
                            try:
                                current_week = data[current_latest_week_key]
                                # 尝试解析为日期并减去7天
                                week_date = datetime.strptime(current_week, '%Y%m%d')
                                prev_date = week_date - timedelta(days=7)
                                prev_week_label = prev_date.strftime('%Y%m%d')
                                data[f'{key}_previous_latest_week'] = prev_week_label
                                self.logger.info(f"   计算上周数据周标签: {prev_week_label}")
                            except:
                                self.logger.warning(f"   无法解析当前周标签 {data[current_latest_week_key]}")
                    else:
                        self.logger.warning(f"   ⚠️  本周也没有{key}数据")

        # 加载维度数据
        dimension_files = {
            'revenue_by_sku': f'revenue_by_sku_{week_label}.json',
            'revenue_by_country': f'revenue_by_country_{week_label}.json',
            'revenue_by_tier': f'revenue_by_tier_{week_label}.json'
        }

        for key, filename in dimension_files.items():
            file_path = base_path / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # 如果文件包含 'data' 字段，提取它
                    if isinstance(loaded, dict) and 'data' in loaded:
                        data['dimension'][key] = loaded['data']
                    else:
                        data['dimension'][key] = loaded
                    self.logger.info(f"✅ 加载维度数据: {filename}")

        # 汇总加载情况
        self.logger.info(f"数据加载完成: 本周{len(data['current'])}个部分, 上周{len(data['previous'])}个部分, 维度{len(data['dimension'])}个部分")

        return data

    def save_processed_data(self, data: Dict, output_path: str):
        """
        保存处理后的数据

        Args:
            data: 处理后的数据
            output_path: 输出文件路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"✅ 处理后的数据已保存到: {output_file}")

    # 默认值方法
    def _get_default_traffic_metrics(self) -> Dict:
        """获取默认流量指标"""
        return {
            'total_guests': 0,
            'total_registers': 0,
            'conversion_rate': 0,
            'guests_wow': '+0.0%',
            'guests_trend': '→',
            'registers_wow': '+0.0%',
            'registers_trend': '→',
            'conversion_wow': '+0.0%',
            'conversion_trend': '→',
            'notes': []
        }

    def _get_default_activation_metrics(self) -> Dict:
        """获取默认激活指标"""
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
            'incomplete_data': False
        }

    def _get_default_engagement_metrics(self) -> Dict:
        """获取默认活跃指标"""
        return {
            'total_wau': 0,
            'wow': '+0.0',
            'driver': '新老用户',
            'new_wau': 0,
            'new_wow': '+0.0',
            'old_wau': 0,
            'old_wow': '+0.0',
            'historical_avg': 0
        }

    def _get_default_retention_metrics(self) -> Dict:
        """获取默认留存指标"""
        return {
            'new_rate': 0,
            'new_last': 0,
            'new_trend': '',
            'old_rate': 0,
            'old_last': 0,
            'old_trend': '',
            'new_12w_avg': 0,
            'old_12w_avg': 0
        }

    def _get_default_revenue_metrics(self) -> Dict:
        """获取默认收入指标"""
        return {
            'total': 0,
            'change_abs': 0,
            'trend': '→',
            'change_rate': 0,
            'renewal_change': '0',
            'renewal_rate': 0,
            'new_change': '0',
            'new_rate': 0,
            'ai_summary': '数据暂未加载',
            'normal_change': '0',
            'type_analysis': '',
            'users_analysis': '',
            'arpu_analysis': '',
            'sku_analysis': '',
            'country_analysis': '',
            'tier_analysis': ''
        }


if __name__ == '__main__':
    # 测试代码
    print("测试数据处理器\n")

    processor = DataProcessor()

    # 模拟数据
    current_data = {
        'traffic': [
            {'渠道': 'paid ads', '新访客数': 57945, '新访客注册数': 24337},
            {'渠道': 'organic search', '新访客数': 59749, '新访客注册数': 5954}
        ],
        'engagement_new_old_users': [
            {'周': '20260126', '用户类型（新老）': '新注册', '本周工具WAU': 27570},
            {'周': '20260126', '用户类型（新老）': '老用户', '本周工具WAU': 31014}
        ]
    }

    previous_data = {
        'traffic': [
            {'渠道': 'paid ads', '新访客数': 27510, '新访客注册数': 11552},
            {'渠道': 'organic search', '新访客数': 72948, '新访客注册数': 7275}
        ],
        'engagement_new_old_users': [
            {'周': '20260119', '用户类型（新老）': '新注册', '本周工具WAU': 19288},
            {'周': '20260119', '用户类型（新老）': '老用户', '本周工具WAU': 30552}
        ]
    }

    historical_data = {
        'engagement_historical': [
            {'周': '20260119', 'WAU': 49840, '新用户WAU': 19288, '老用户WAU': 30552},
            {'周': '20260112', 'WAU': 49102, '新用户WAU': 18372, '老用户WAU': 30730}
        ]
    }

    # 处理所有数据
    results = processor.process_all_sections(
        current_data=current_data,
        previous_data=previous_data,
        historical_data=historical_data
    )

    # 显示结果
    print("\n处理结果:")
    print(f"流量: {results['traffic']['total_guests']:,} 访客")
    print(f"活跃: {results['engagement']['total_wau']:,} WAU")
