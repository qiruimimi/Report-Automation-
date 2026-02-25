#!/usr/bin/env python3
"""
MCP客户端模块

统一的Metabase MCP客户端封装
"""

import subprocess
import json
from typing import Dict, List, Optional, Any
from src.logger import get_logger
from src.retry_handler import RetryHandler, RetryConfig


class MetabaseMCPClient:
    """
    Metabase MCP客户端

    提供统一的Metabase MCP工具调用接口，支持重试和错误处理
    """

    def __init__(
        self,
        database_id: int = 2,
        max_retries: int = 3,
        timeout: int = 300,
        logger=None
    ):
        """
        初始化MCP客户端

        Args:
            database_id: Metabase数据库ID
            max_retries: 最大重试次数
            timeout: 查询超时时间（秒）
            logger: 日志记录器
        """
        self.database_id = database_id
        self.timeout = timeout
        self.logger = logger or get_logger('mcp_client')

        # 创建重试处理器
        retry_config = RetryConfig.DATABASE_CONFIG
        retry_config['max_retries'] = max_retries
        self.retry_handler = RetryHandler(
            logger=logger,
            **retry_config
        )

    def execute_sql_query(
        self,
        sql: str,
        parameters: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        执行SQL查询

        Args:
            sql: SQL查询语句
            parameters: SQL参数（可选）

        Returns:
            List[Dict]: 查询结果

        Raises:
            Exception: 查询失败时抛出异常
        """
        self.logger.debug(f"执行SQL查询，长度: {len(sql)} 字符")

        def _execute():
            # 使用subprocess调用MCP工具
            cmd = [
                'mcp', 'call', 'mcp__metabase__execute_sql_query',
                '--',
                json.dumps({
                    'database_id': self.database_id,
                    'query': sql,
                    'parameters': parameters or []
                })
            ]

            self.logger.debug(f"执行命令: {' '.join(cmd[:3])}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            # 检查执行结果
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or '未知错误'
                raise RuntimeError(f"MCP调用失败: {error_msg}")

            # 解析返回结果
            try:
                response = json.loads(result.stdout)
                if 'data' in response:
                    return response['data']
                elif 'error' in response:
                    raise RuntimeError(f"MCP错误: {response['error']}")
                else:
                    # 可能是直接返回数据
                    if isinstance(response, list):
                        return response
                    return []
            except json.JSONDecodeError as e:
                raise RuntimeError(f"无法解析MCP响应: {e}\n响应: {result.stdout[:200]}")

        # 使用重试机制执行
        return self.retry_handler.retry(_execute)

    def get_card_query_results(
        self,
        card_id: int
    ) -> List[Dict]:
        """
        获取Card查询结果

        Args:
            card_id: Metabase Card ID

        Returns:
            List[Dict]: 查询结果
        """
        self.logger.debug(f"获取Card查询结果, card_id: {card_id}")

        def _get_results():
            cmd = [
                'mcp', 'call', 'mcp__metabase__get_card_query_results',
                '--',
                json.dumps({'card_id': card_id})
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or '未知错误'
                raise RuntimeError(f"MCP调用失败: {error_msg}")

            response = json.loads(result.stdout)
            if 'data' in response:
                return response['data']
            elif isinstance(response, list):
                return response
            return []

        return self.retry_handler.retry(_get_results)

    def execute_card(
        self,
        card_id: int,
        parameters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        执行Card查询（带参数）

        Args:
            card_id: Metabase Card ID
            parameters: 查询参数（可选）

        Returns:
            List[Dict]: 查询结果
        """
        self.logger.debug(f"执行Card查询, card_id: {card_id}, parameters: {parameters}")

        def _execute_card():
            # 先获取Card内容，然后执行查询
            # 这里简化为直接调用execute_sql_query
            # 实际实现可能需要先调用get_card_by_id获取SQL
            self.logger.warning(
                f"execute_card功能未完全实现，"
                f"建议使用execute_sql_query直接执行SQL"
            )
            return []

        return self.retry_handler.retry(_execute_card)

    # 批量操作方法

    def execute_multiple_queries(
        self,
        queries: List[Dict[str, str]],
        parallel: bool = True
    ) -> Dict[str, List[Dict]]:
        """
        执行多个SQL查询

        Args:
            queries: 查询列表，格式: [{'name': 'query_name', 'sql': 'SELECT ...'}]
            parallel: 是否并行执行

        Returns:
            Dict: 查询结果字典 {'query_name': [results]}
        """
        self.logger.info(f"执行 {len(queries)} 个查询 {'并行' if parallel else '串行'}")

        results = {}

        if parallel:
            # 并行执行（简化版，实际应使用多线程/多进程）
            for query_info in queries:
                name = query_info.get('name', f'query_{len(results)}')
                try:
                    results[name] = self.execute_sql_query(query_info['sql'])
                except Exception as e:
                    self.logger.error(f"查询 {name} 失败: {e}")
                    results[name] = []
        else:
            # 串行执行
            for query_info in queries:
                name = query_info.get('name', f'query_{len(results)}')
                try:
                    results[name] = self.execute_sql_query(query_info['sql'])
                except Exception as e:
                    self.logger.error(f"查询 {name} 失败: {e}")
                    results[name] = []

        return results

    # 配置方法

    def set_database_id(self, database_id: int) -> None:
        """
        设置数据库ID

        Args:
            database_id: 数据库ID
        """
        self.database_id = database_id
        self.logger.debug(f"设置数据库ID: {database_id}")

    def set_timeout(self, timeout: int) -> None:
        """
        设置查询超时时间

        Args:
            timeout: 超时时间（秒）
        """
        self.timeout = timeout
        self.logger.debug(f"设置超时时间: {timeout} 秒")


class MetabaseQueryHelper:
    """
    Metabase查询辅助类

    提供常用的查询构建和执行辅助方法
    """

    def __init__(self, client: MetabaseMCPClient):
        """
        初始化查询辅助类

        Args:
            client: MetabaseMCPClient实例
        """
        self.client = client

    def query_with_date_range(
        self,
        sql: str,
        start_date: str,
        end_date: str,
        date_column: str = 'ds'
    ) -> List[Dict]:
        """
        执行带日期范围的查询

        Args:
            sql: SQL模板（包含{{start_date}}和{{end_date}}占位符）
            start_date: 开始日期
            end_date: 结束日期
            date_column: 日期列名

        Returns:
            List[Dict]: 查询结果
        """
        # 替换SQL中的日期占位符
        sql_with_dates = sql.replace('{{start_ds}}', f"'{start_date}'")
        sql_with_dates = sql_with_dates.replace('{{end_ds}}', f"'{end_date}'")

        return self.client.execute_sql_query(sql_with_dates)

    def query_single_value(
        self,
        sql: str,
        default: Any = None
    ) -> Any:
        """
        执行查询并返回单个值

        Args:
            sql: SQL查询
            default: 默认值

        Returns:
            Any: 查询结果的第一行第一列的值，或默认值
        """
        results = self.client.execute_sql_query(sql)
        if results and len(results) > 0:
            first_row = results[0]
            first_key = list(first_row.keys())[0] if first_row else None
            if first_key:
                return first_row[first_key]
        return default


if __name__ == "__main__":
    # 测试代码
    print("测试Metabase MCP客户端\n")

    # 创建客户端
    client = MetabaseMCPClient(
        database_id=2,
        max_retries=3,
        timeout=30
    )

    # 测试简单查询
    test_sql = "SELECT 1 AS test_value LIMIT 1"
    print("执行测试查询...")

    try:
        results = client.execute_sql_query(test_sql)
        print(f"查询结果: {results}")
    except Exception as e:
        print(f"查询失败（预期，因为MCP可能不可用）: {e}")

    # 测试批量查询
    queries = [
        {'name': 'query1', 'sql': 'SELECT 1 AS q1 LIMIT 1'},
        {'name': 'query2', 'sql': 'SELECT 2 AS q2 LIMIT 1'}
    ]

    try:
        batch_results = client.execute_multiple_queries(queries, parallel=False)
        print(f"\n批量查询结果: {batch_results}")
    except Exception as e:
        print(f"批量查询失败: {e}")
