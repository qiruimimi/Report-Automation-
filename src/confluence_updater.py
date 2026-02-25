#!/usr/bin/env python3
"""
Confluence更新模块（API版本）

通过requests直接调用Confluence REST API更新页面
"""

import requests
import urllib3
from typing import Dict, Optional
from pathlib import Path

from src.logger import get_logger

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ConfluenceUpdater:
    """Confluence更新器（API版本）"""

    def __init__(self, config: Dict = None, logger=None):
        """
        初始化Confluence更新器

        Args:
            config: 配置字典
            logger: 日志记录器
        """
        self.config = config or {}
        self.confluence_config = self.config.get('confluence', {})
        self.page_id = self.confluence_config.get('page_id', 81397518314)
        self.base_url = self.confluence_config.get('api_url', '')
        self.username = self.confluence_config.get('username', '')
        self.api_token = self.confluence_config.get('api_token', '')
        self.logger = logger or get_logger('confluence_updater')

        # Session for API calls
        self.session = None

    def _get_session(self) -> requests.Session:
        """获取或创建API会话"""
        if self.session is None:
            self.session = requests.Session()

            # 如果有用户名和API token，配置认证
            if self.username and self.api_token:
                # Confluence使用Basic Auth或Bearer Token
                from requests.auth import HTTPBasicAuth
                self.session.auth = HTTPBasicAuth(self.username, self.api_token)
                self.session.headers.update({
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                })
                self.logger.info("✅ Confluence认证配置完成")

        return self.session

    def _build_confluence_api_url(self, path: str) -> str:
        """构建Confluence API URL"""
        # Confluence REST API通常使用 /wiki/rest/api/ 路径
        return f"{self.base_url}/wiki/rest/api/{path}"

    def get_current_page(self) -> Dict:
        """
        获取当前Confluence页面信息

        Returns:
            dict: 页面元数据，包含版本号等
        """
        self.logger.info(f"获取Confluence页面 (Page ID: {self.page_id})...")

        try:
            session = self._get_session()

            # Confluence REST API: GET /wiki/rest/api/content/{id}?expand=version
            url = self._build_confluence_api_url(f"content/{self.page_id}?expand=version")

            response = session.get(url, timeout=30, verify=False)

            if response.status_code != 200:
                self.logger.error(f"获取页面失败: HTTP {response.status_code}")
                self.logger.error(f"响应内容: {response.text[:200]}")
                return {}

            # 解析JSON结果
            data = response.json()

            self.logger.info(f"✅ 成功获取页面，当前版本: {data.get('version', {}).get('number', 'N/A')}")

            return data

        except requests.RequestException as e:
            self.logger.error(f"❌ 获取页面网络异常: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"❌ 获取页面异常: {e}")
            return {}

    def update_page(
        self,
        new_content: str,
        version_message: str = None
    ) -> bool:
        """
        更新Confluence页面

        Args:
            new_content: 新的页面内容（HTML格式）
            version_message: 版本更新消息

        Returns:
            bool: 是否更新成功
        """
        self.logger.info("更新Confluence页面...")

        try:
            session = self._get_session()

            # 先获取当前页面信息
            current_page = self.get_current_page()

            if not current_page:
                self.logger.error("❌ 无法获取当前页面信息")
                return False

            # 获取当前版本号并递增
            current_version = current_page.get('version', {}).get('number', 1)
            new_version = current_version + 1

            if version_message is None:
                from datetime import datetime
                version_message = f"Weekly report update - {datetime.now().strftime('%Y-%m-%d')}"

            # 准备更新数据
            # Confluence REST API使用PUT更新页面
            update_data = {
                'id': str(self.page_id),
                'type': 'page',
                'title': current_page.get('title', 'Coohom平台整体数据'),
                'body': {
                    'storage': {
                        'value': new_content,
                        'representation': 'storage'
                    }
                },
                'version': {
                    'number': new_version,
                    'message': version_message
                }
            }

            url = self._build_confluence_api_url(f"content/{self.page_id}")

            response = session.put(url, json=update_data, timeout=60, verify=False)

            if response.status_code not in [200, 201]:
                self.logger.error(f"更新失败: HTTP {response.status_code}")
                self.logger.error(f"响应内容: {response.text[:200]}")
                return False

            self.logger.info(f"✅ Confluence页面更新成功 (版本: {new_version})")
            return True

        except requests.RequestException as e:
            self.logger.error(f"❌ 更新页面网络异常: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ 更新页面异常: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return False

    def save_html_to_file(
        self,
        html_content: str,
        report_date: str = None
    ) -> str:
        """
        将HTML内容保存到文件

        Args:
            html_content: HTML内容
            report_date: 报告日期（用于文件名）

        Returns:
            str: 保存的文件路径
        """
        try:
            # 确保output目录存在
            output_dir = Path('output')
            output_dir.mkdir(exist_ok=True)

            # 生成文件名
            from datetime import datetime
            date_str = report_date or datetime.now().strftime('%Y%m%d')
            filename = f"confluence_report_{date_str}.html"
            file_path = output_dir / filename

            # 写入文件
            file_path.write_text(html_content, encoding='utf-8')

            self.logger.info(f"✅ HTML已保存到: {filename}")
            return str(file_path)

        except Exception as e:
            self.logger.error(f"❌ 保存HTML文件失败: {e}")
            return ""


if __name__ == "__main__":
    # 测试代码
    print("测试Confluence更新模块（API版本）\n")

    updater = ConfluenceUpdater()

    # 测试获取页面
    print("测试获取Confluence页面:")
    page_info = updater.get_current_page()

    if page_info:
        print(f"✅ 页面标题: {page_info.get('title', 'N/A')}")
        print(f"   版本号: {page_info.get('version', {}).get('number', 'N/A')}")
    else:
        print("❌ 无法获取页面信息")

    # 测试保存HTML到文件
    print("\n测试保存HTML到文件:")
    test_html = "<h1>测试报告</h1><p>这是一个测试内容。</p>"
    saved_path = updater.save_html_to_file(test_html, "20260224")
    print(f"文件路径: {saved_path}")
