#!/usr/bin/env python3
"""
数据获取模块（API版本）

通过requests库直接调用Metabase API执行SQL查询
"""

import json
import requests
import time
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from src.logger import get_logger
from src.sql_preprocessor import preprocess_sql_file


class DataFetcher:
    """数据获取器（API版本）"""

    def __init__(self, config: Dict = None, logger=None, use_mcp: bool = False):
        """
        初始化数据获取器

        Args:
            config: 配置字典（包含database_id等）
            logger: 日志记录器
            use_mcp: 是否使用MCP工具（默认True）
        """
        self.config = config or {}
        self.metabase_config = self.config.get('metabase', {})
        self.database_id = self.metabase_config.get('database_id', 2)
        self.base_url = self.metabase_config.get('base_url', '')
        self.username = self.metabase_config.get('username', '')
        self.password = self.metabase_config.get('password', '')
        self.api_token = self.metabase_config.get('api_token', '')
        self.timeout = self.metabase_config.get('query_timeout', 300)
        self.use_mcp = use_mcp
        self.logger = logger or get_logger('data_fetcher')

        # SQL文件映射（从配置文件动态读取）
        sql_config = self.config.get('sql_files', {})
        self.sql_files = {
            'traffic': sql_config.get('traffic', {}).get('file', '01_traffic_weekly.sql'),
            'activation': sql_config.get('activation', {}).get('file', '02_activation_ready.sql'),
            'engagement': sql_config.get('engagement', {}).get('file', '03_engagement_new_old_users.sql'),
            'retention': sql_config.get('retention', {}).get('file', '04_retention.sql'),
            'revenue': sql_config.get('revenue', {}).get('file', '05_revenue.sql'),
        }

        # SQL专属文件夹路径
        self.sql_output_dir = Path(__file__).parent.parent / 'sql_queries'
        self.sql_output_dir.mkdir(parents=True, exist_ok=True)

    def _save_sql_to_md(self, section: str, sql_file: str, processed_sql: str, params: Dict):
        """
        保存SQL内容到md文件（专属文件夹）

        Args:
            section: 部分名称
            sql_file: SQL文件名
            processed_sql: 处理后的SQL
            params: 日期参数
        """
        try:
            report_date = params.get('report_date', datetime.now().strftime('%Y-%m-%d'))
            gen_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            md_file_path = self.sql_output_dir / f"{section}_query_{report_date}.md"

            md_content = f"""# {section.upper()} SQL Query - {report_date}

## 数据参数
"""
            for key, value in params.items():
                if key not in ['week_offset', 'week_monday', 'week_saturday', 'week_sunday', 'last_week_monday',
                          'last_week_saturday', 'last_week_sunday', 'partition_start', 'partition_end',
                          'snapshot_date', 'history_start_date', 'pay_start_date', 'pay_end_date',
                          'report_date', 'description']:
                    md_content += f"- **{key}**: `{value}`\n"

            md_content += f"""

## SQL文件
{sql_file}

## 完整SQL语句
```sql
{processed_sql}
```

---
*生成时间: {gen_time}
"""

            with open(md_file_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            self.logger.info(f"✅ SQL已保存到: {md_file_path}")

        except Exception as e:
            self.logger.warning(f"⚠️ 保存SQL文件失败: {e}")

    def execute_metabase_query(self, sql_query: str, max_retries: int = 5) -> List[Dict]:
        """
        通过Metabase API执行SQL查询

        Args:
            sql_query: SQL查询字符串
            max_retries: 最大重试次数（处理202异步查询）

        Returns:
            list: 查询结果列表
        """
        import time

        try:
            self.logger.info("正在执行Metabase查询...")

            # 构建API请求URL
            api_url = self.base_url + 'api/dataset'

            # 构建请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json',
                'X-API-KEY': self.api_token,
                'Content-Type': 'application/json'
            }

            # 构建cookies
            cookies = {'metabase.DEVICE': self.metabase_config.get('device_id', '')}

            # 构建请求数据
            request_data = {
                'database': self.database_id,
                'type': 'native',
                'native': {
                    'template-tags': {},
                    'query': sql_query
                }
            }

            self.logger.debug(f"API URL: {api_url}")
            self.logger.debug(f"Database ID: {self.database_id}")

            # 发送POST请求（支持重试机制处理202异步查询）
            response_data = None
            for attempt in range(max_retries):
                response = requests.post(
                    api_url,
                    headers=headers,
                    cookies=cookies,
                    json=request_data,
                    timeout=30  # 单次请求超时时间
                )

                # 检查响应状态
                if response.status_code not in (200, 202):
                    self.logger.error(f"❌ API请求失败，状态码: {response.status_code}")
                    self.logger.error(f"响应内容: {response.text[:500]}")
                    return []

                # 对于202状态码（异步查询），重试等待
                if response.status_code == 202:
                    self.logger.debug(f"202响应: {response.text[:200]}")
                    if attempt < max_retries - 1:
                        # 指数退避：3, 6, 12, 24, 48秒
                        current_delay = 3 * (2 ** attempt)
                        self.logger.warning(f"⚠️ 查询执行中 (202)，等待 {current_delay} 秒后重试... ({attempt + 1}/{max_retries})")
                        time.sleep(current_delay)
                        continue
                    else:
                        # 最后一次重试后，直接读取响应
                        self.logger.debug(f"最终响应内容: {response.text[:200]}")

            # 解析JSON响应
            response_data = response.json()
            self.logger.debug(f"成功获取响应，status: {response_data.get('status', 'unknown')}")

            # 处理返回数据
            if 'data' in response_data:
                data_obj = response_data['data']
                if isinstance(data_obj, dict) and 'rows' in data_obj:
                    rows = data_obj['rows']
                    # 如果有列名信息，将列表转换为字典
                    if 'cols' in data_obj:
                        cols = data_obj['cols']
                        col_names = [col.get('name') for col in cols]
                        dict_rows = []
                        for row in rows:
                            if isinstance(row, list) and len(row) == len(col_names):
                                dict_rows.append(dict(zip(col_names, row)))
                            else:
                                dict_rows.append(row)
                        self.logger.info(f"✅ 查询成功，返回 {len(dict_rows)} 行数据")
                        return dict_rows
                elif isinstance(data_obj, list):
                    self.logger.info(f"✅ 查询成功，返回 {len(data_obj)} 行数据")
                    return data_obj
                else:
                    self.logger.warning(f"⚠️ 返回数据格式不符合预期")
                    return []

        except requests.exceptions.Timeout:
            self.logger.error("❌ 查询超时")
            return []
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ API请求异常: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ JSON解析失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"❌ 查询执行异常: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return []

    def fetch_section_data(
        self,
        section: str,
        params: Dict,
        base_path: str = None
    ) -> List[Dict]:
        """
        获取单个部分的数据

        Args:
            section: 部分名称（traffic, activation, engagement, retention, revenue等）
            params: 日期参数字典
            base_path: 项目根目录

        Returns:
            list: 查询结果
        """
        if section not in self.sql_files:
            self.logger.error(f"❌ 未知的section: {section}")
            return []

        sql_file = self.sql_files[section]
        self.logger.info(f"处理 {section} 部分，SQL文件: {sql_file}")

        try:
            # 预处理SQL（替换参数）
            processed_sql = preprocess_sql_file(sql_file, params, base_path)

            # 执行查询
            data = self.execute_metabase_query(processed_sql)

            # 保存SQL内容到md文件（专属文件夹）
            self._save_sql_to_md(section, sql_file, processed_sql, params)

            return data

        except Exception as e:
            self.logger.error(f"❌ 获取 {section} 数据失败: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return []

    def fetch_all_sections(
        self,
        params: Dict,
        week_offset: int = 0,
        base_path: str = None
    ) -> Dict[str, List[Dict]]:
        """
        获取所有部分的数据

        Args:
            params: 日期参数字典
            week_offset: 周偏移量（0=本周, -1=上周）
            base_path: 项目根目录

        Returns:
            dict: 各部分的查询数据
        """
        self.logger.info(f"开始获取所有部分数据（周偏移: {week_offset}）...")

        results = {}

        # 获取各个部分的数据
        sections = [
            'traffic',
            'activation',
            'engagement',
            'retention',
            'revenue'
        ]

        for section in sections:
            results[section] = self.fetch_section_data(section, params, base_path)

        self.logger.info("✅ 数据获取完成")

        return results


if __name__ == "__main__":
    # 测试代码
    from src.date_utils import calculate_week_params

    print("测试数据获取模块（API版本）\\n")

    # 计算本周日期参数
    params = calculate_week_params(target_date='20260223')

    print("测试获取流量数据:")
    fetcher = DataFetcher(use_mcp=False)

    data = fetcher.fetch_section_data('traffic', params)

    if data:
        print(f"✅ 获取到 {len(data)} 行数据")
        if len(data) > 0:
            print(f"第一行数据: {data[0]}")
    else:
        print("❌ 未获取到数据")
