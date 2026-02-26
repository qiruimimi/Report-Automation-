#!/usr/bin/env python3
"""
数据获取模块（支持 MCP 和 API 两种方式）
"""
import urllib3
import json
import time
import requests
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
from src.logger import get_logger
from src.sql_preprocessor import preprocess_sql_file
from src.mcp_client import MetabaseMCPClient


class DataFetcher:
    """
    数据获取器（支持 MCP 和 API 两种方式）
    """

    def __init__(self, config: Dict = None, logger=None, use_mcp: bool = False):
        """
        初始化数据获取器

        Args:
            config: 配置字典（包含database_id等）
            logger: 日志记录器
            use_mcp: 是否使用MCP工具（默认False，使用API）
        """
        self.config = config or {}
        self.metabase_config = self.config.get('metabase', {})
        self.database_id = self.metabase_config.get('database_id', 2)
        self.base_url = self.metabase_config.get('base_url', '')
        self.username = self.metabase_config.get('username', '')
        self.password = self.metabase_config.get('password', '')

        # API Token 优先从环境变量读取，其次从配置文件读取
        import os
        self.api_token = os.getenv('METABASE_API_KEY') or \
                       self.metabase_config.get('metabase_api_key') or \
                       self.metabase_config.get('api_token', '')
        self.timeout = self.metabase_config.get('query_timeout', 300)
        self.use_mcp = use_mcp
        self.logger = logger or get_logger('data_fetcher')

        # MCP 客户端（当 use_mcp=True 时使用）
        self.mcp_client = None
        if self.use_mcp:
            self.mcp_client = MetabaseMCPClient(
                database_id=self.database_id,
                max_retries=3,
                timeout=self.timeout,
                logger=logger
            )
            self.logger.info("✅ 使用 MCP 方式获取数据")

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

    def _execute_api_query(self, sql_query: str) -> List[Dict]:
        """
        使用 API 方式执行查询

        Args:
            sql_query: SQL查询字符串

        Returns:
            List[Dict]: 查询结果列表
        """
        import time

        try:
            self.logger.info("正在执行Metabase API查询...")

            # 构建API请求URL
            api_url = self.base_url + 'api/dataset'

            # 构建请求头（官方文档使用小写 x-api-key）
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36)',
                'x-api-key': self.api_token,
                'Content-Type': 'application/json'
            }

            # 构建请求数据
            request_data = {
                'database': self.database_id,
                'type': 'native',
                'native': {
                    'query': sql_query
                }
            }

            self.logger.debug(f"API URL: {api_url}")
            self.logger.debug(f"Database ID: {self.database_id}")
            self.logger.debug(f"API Token (前10位): {self.api_token[:10] if self.api_token else 'NOT SET'}...")
            self.logger.debug(f"Headers: x-api-key={self.api_token[:10] if self.api_token else 'NOT SET'}...")

            # 发送POST请求（支持重试机制处理202异步查询）
            response = None
            for attempt in range(5):  # 最多重试5次
                response = requests.post(
                    api_url,
                    headers=headers,
                    data=json.dumps(request_data).encode('utf-8'),
                    timeout=30
                )

                # 检查响应状态
                if response.status_code == 200:
                    # 200表示查询成功完成，数据已就绪
                    break
                elif response.status_code == 202:
                    # 202表示异步查询已接受，检查响应是否已包含数据
                    try:
                        response_data = response.json()
                        # 如果202响应包含完整数据（status=completed），直接使用
                        if response_data.get('status') == 'completed' and 'data' in response_data:
                            self.logger.info(f"202响应已包含完整数据，status={response_data.get('status')}")
                            break
                        # 否则需要等待并重试
                        if attempt < 4:  # 最多重试4次
                            current_delay = 3 * (2 ** attempt)
                            self.logger.warning(f"⚠️ 查询执行中 (202, status={response_data.get('status')})，等待 {current_delay} 秒后重试... ({attempt + 1}/{5})")
                            time.sleep(current_delay)
                            continue
                        self.logger.debug(f"最终202响应内容: {response.text[:200]}")
                        break
                    except json.JSONDecodeError:
                        # 响应不是有效JSON，继续重试
                        if attempt < 4:
                            current_delay = 3 * (2 ** attempt)
                            self.logger.warning(f"⚠️ 202响应无法解析，等待 {current_delay} 秒后重试... ({attempt + 1}/{5})")
                            time.sleep(current_delay)
                            continue
                        break
                else:
                    # 其他状态码表示错误
                    self.logger.error(f"❌ API请求失败，状态码: {response.status_code}")
                    self.logger.error(f"响应内容: {response.text[:500]}")
                    return []

            # 解析JSON响应（此时response变量已包含最后一次的响应）
            response_data = response.json() if response else None
            self.logger.info(f"成功获取响应，status: {response_data.get('status', 'unknown')}")
            self.logger.info(f"响应keys: {list(response_data.keys())}")
            self.logger.info(f"完整响应: {str(response_data)[:500]}")
            if 'data' in response_data:
                self.logger.info(f"data类型: {type(response_data['data'])}")

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

    def _execute_mcp_query(self, sql_query: str) -> List[Dict]:
        """
        使用 MCP 客户端执行查询

        Args:
            sql_query: SQL查询字符串

        Returns:
            List[Dict]: 查询结果列表
        """
        if not self.mcp_client:
            raise RuntimeError("MCP 客户端未初始化，请设置 use_mcp=True")

        try:
            self.logger.info("使用 MCP 客户端执行查询")

            results = self.mcp_client.execute_sql_query(sql_query)
            self.logger.info(f"✅ MCP 查询成功，返回 {len(results)} 行数据")

            # 转换 MCP 返回的数据格式为与 API 一致的格式
            return self._convert_mcp_results(results)

        except Exception as e:
            self.logger.error(f"❌ MCP 查询失败: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return []

    def _convert_mcp_results(self, mcp_results: List) -> List[Dict]:
        """
        转换 MCP 返回的数据格式为与 API 一致的格式

        Args:
            mcp_results: MCP 返回的结果（可能是字符串或字典）

        Returns:
            List[Dict]: 标准格式的查询结果
        """
        if not mcp_results:
            return []

        # MCP 返回的数据可能是字典列表或字符串列表
        if isinstance(mcp_results, dict):
            if 'data' in mcp_results:
                raw_data = mcp_results['data']
                if isinstance(raw_data, list) and raw_data:
                    # MCP 返回的是列表格式，直接使用
                    return raw_data
                elif isinstance(raw_data, dict) and 'rows' in raw_data:
                    rows = raw_data['rows']
                    cols = raw_data.get('cols', [])
                    col_names = [col.get('name') for col in cols] if cols else [f'col_{i}' for i in range(len(rows[0]))]

                    dict_rows = []
                    for row in rows:
                        if isinstance(row, list) and len(row) == len(col_names):
                            dict_rows.append(dict(zip(col_names, row)))
                        else:
                            dict_rows.append(row)
                    return dict_rows
            elif isinstance(mcp_results, list):
                return mcp_results
        else:
            return []

    def execute_metabase_query(self, sql_query: str, max_retries: int = 5) -> List[Dict]:
        """
        通过Metabase API执行SQL查询（已废弃，保留用于向后兼容）

        根据是否使用MCP选择执行方式
        """
        if self.use_mcp and self.mcp_client:
            return self._execute_mcp_query(sql_query)
        else:
            return self._execute_api_query(sql_query)

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
    print("测试数据获取模块（MCP+API 双模式）\n")

    # 创建客户端（使用 API 方式）
    print("1. 测试 API 方式...")
    fetcher = DataFetcher(use_mcp=False)
    params = calculate_week_params(target_date='20260223')
    test_sql = "SELECT 1 AS test_value LIMIT 1"
    result = fetcher.execute_metabase_query(test_sql)
    print(f"API 结果: {result}")

    # 创建客户端（使用 MCP 方式）
    print("\n2. 测试 MCP 方式...")
    try:
        fetcher_mcp = DataFetcher(use_mcp=True)
        result_mcp = fetcher._execute_mcp_query(test_sql)
        print(f"MCP 结果: {result_mcp}")
    except Exception as e:
        print(f"MCP 测试失败: {e}")
