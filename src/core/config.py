#!/usr/bin/env python3
"""
配置管理模块

从环境变量和配置文件加载配置
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Optional
from src.logger import get_logger
from src.models.types import WeekParams, ColumnMappings

logger = get_logger('core.config')


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径，默认为 config/config.yaml
        """
        self.config_file = config_file or Path(__file__).parent.parent.parent / 'config' / 'config.yaml'
        self._config = {}
        self._load_config()

    def _load_config(self) -> None:
        """从文件加载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning(f"⚠️ 配置文件不存在: {self.config_file}，使用默认配置")
            self._config = self.get_default_config()

    def get(self, key: str, default=None):
        """
        获取配置项（支持嵌套键，如 'metabase.database_id'）

        Args:
            key: 配置键，支持点分隔的嵌套键
            default: 默认值

        Returns:
            配置值或默认值
        """
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def get_api_config(self) -> Dict:
        """
        获取 API 配置

        注意：API Token 从环境变量读取，不从配置文件读取

        Returns:
            dict: API 配置字典
        """
        return {
            'metabase_base_url': self.get('metabase.base_url', 'https://kmb.qunhequnhe.com/'),
            'metabase_api_key': os.getenv('METABASE_API_KEY', ''),  # 从环境变量读取
            'metabase_username': self.get('metabase.username', 'bigdata'),
            'metabase_database_id': self.get('metabase.database_id', 2),
            'metabase_query_timeout': self.get('metabase.query_timeout', 300),
            'confluence_base_url': self.get('confluence.api_url', ''),
            'confluence_page_id': self.get('confluence.page_id', ''),
            'confluence_username': os.getenv('CONFLUENCE_USERNAME', ''),
            'confluence_password': os.getenv('CONFLUENCE_PASSWORD', ''),
        }

    def get_column_mappings(self) -> ColumnMappings:
        """
        获取列名映射配置

        Returns:
            ColumnMappings: 列名映射字典
        """
        mappings = self.get('column_mappings', {})
        if not mappings:
            # 使用默认映射
            return {
                'traffic': {
                    'columns': ['新访客数', '新访客注册数', '新访客注册转化率'],
                    'sum_fields': ['新访客数', '新访客注册数']
                },
                'revenue': {
                    'columns': ['Total_Amt', 'NewSubscribe_Amt', 'Renewal_Amt'],
                    'sum_fields': ['Total_Amt']
                },
                'engagement': {
                    'columns': ['新用户WAU', '老用户WAU'],
                    'sum_fields': []
                },
                'retention': {
                    'columns': ['新用户留存', '老用户留存'],
                    'sum_fields': []
                }
            }
        return mappings

    def get_sql_files_config(self) -> Dict:
        """
        获取 SQL 文件配置

        Returns:
            dict: SQL 文件配置
        """
        return self.get('sql_files', {})

    def get_week_config(self) -> Dict:
        """
        获取日期配置

        Returns:
            dict: 日期配置
        """
        return self.get('date', {})

    def get_logging_config(self) -> Dict:
        """
        获取日志配置

        Returns:
            dict: 日志配置
        """
        return {
            'level': self.get('logging.level', 'INFO'),
            'file': self.get('logging.file', 'logs/weekly_report.log'),
            'max_bytes': self.get('logging.max_bytes', 10485760),  # 10MB
            'backup_count': self.get('logging.backup_count', 5)
        }

    def get_revenue_md_config(self) -> Dict:
        """
        获取收入 MD 文档配置

        Returns:
            dict: 收入 MD 配置
        """
        return {
            'skip_md_prompt_in_scheduled': self.get('revenue_md.skip_md_prompt_in_scheduled', False),
            'default_search_path': self.get('revenue_md.default_search_path', '')
        }

    def get_schedule_config(self) -> Dict:
        """
        获取调度配置

        Returns:
            dict: 调度配置
        """
        return {
            'enabled': self.get('schedule.enabled', True),
            'time': self.get('schedule.time', 'Wed 10:00'),
            'timezone': self.get('schedule.timezone', 'Asia/Shanghai')
        }

    def get_default_config(self) -> Dict:
        """
        获取默认配置

        Returns:
            dict: 默认配置字典
        """
        return {
            'metabase': {
                'database_id': 2,
                'base_url': 'https://kmb.qunhequnhe.com/',
                'username': 'bigdata',
                'query_timeout': 300
            },
            'confluence': {
                'page_id': 81397518314,
                'page_url': 'https://cf.qunhequnhe.com/pages/viewpage.action?pageId=81397518314',
                'api_url': 'https://cf.qunhequnhe.com'
            },
            'sql_files': {
                'traffic': {
                    'name': '流量/投放',
                    'file': '01_traffic_weekly.sql',
                    'section_key': 'traffic_acquisition'
                },
                'activation': {
                    'name': '激活/注册',
                    'file': '02_activation_ready.sql',
                    'section_key': 'activation_funnel'
                },
                'engagement': {
                    'name': '活跃-新老用户',
                    'file': '03_engagement_new_old_users.sql',
                    'section_key': 'engagement'
                },
                'retention': {
                    'name': '留存',
                    'file': '04_retention.sql',
                    'section_key': 'retention'
                },
                'revenue': {
                    'name': '收入',
                    'file': '05_revenue.sql',
                    'section_key': 'revenue'
                }
            },
            'date': {
                'mode': 'auto'
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/weekly_report.log',
                'max_bytes': 10485760,
                'backup_count': 5
            },
            'column_mappings': {}
        }


if __name__ == "__main__":
    # 测试配置管理器
    print("测试配置管理器\n")

    config = ConfigManager()

    # 测试获取配置
    print(f"Metabase Database ID: {config.get('metabase.database_id')}")
    print(f"日志级别: {config.get_logging_config()['level']}")

    # 测试 API 配置
    api_config = config.get_api_config()
    print(f"\nMetabase Base URL: {api_config['metabase_base_url']}")
    print(f"Metabase Database ID: {api_config['metabase_database_id']}")
    print(f"API Key (from env): {'*' * 10 if api_config['metabase_api_key'] else 'Not set'}")

    # 测试列名映射
    mappings = config.get_column_mappings()
    print(f"\n列名映射: {list(mappings.keys())}")
