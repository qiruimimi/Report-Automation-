#!/usr/bin/env python3
"""
Metabase API 客户端

功能：
1. 从 Metabase 执行 SQL 查询
2. 支持查询历史和缓存
3. 统一的错误处理
"""
import requests
from typing import Dict, List, Optional
from src.logger import get_logger
from src.api import APIClient

logger = get_logger('api.metabase')


class MetabaseAPIClient(APIClient):
    """Metabase API 客户端"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()

    def fetch_section_data(
        self,
        section: str,
        sql_file: str,
        params: dict
    ) -> List[Dict]:
        """
        通过 API 获取某部分数据

        Args:
            section: 部分名称 (traffic, activation, engagement, retention, revenue)
            sql_file: SQL 文件名
            params: 日期参数等

        Returns:
            List[Dict]: 查询结果
        """
        # 读取 SQL 文件
        sql_path = Path(__file__).parent.parent / 'sql' / sql_file
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_template = f.read()

        # 替换参数
        processed_sql = sql_template.format(**params)

        # 调用 API 执行
        try:
            response = self.session.post(
                f"{self.base_url}/api/query",
                json={
                    'api_key': self.api_key,
                    'database': params.get('database_id'),
                    'query': processed_sql,
                    'parameters': {'format': 'json'}
                },
                timeout=30
            )
            response.raise_for_status()

            result = response.json().get('data', [])
            logger.info(f"✅ {section} 数据获取成功: {len(result)} 条记录")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ {section} API 请求失败: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ {section} 数据获取异常: {e}")
            raise