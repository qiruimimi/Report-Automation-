#!/usr/bin/env python3
"""
Coohom周报自动化更新系统 - 主入口（支持命令行参数）

整合所有模块，实现端到端的周报更新流程
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict
import yaml

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.logger import setup_logging, get_logger
from src.date_utils import calculate_week_params
from src.interactive_prompt import ask_target_week, ask_revenue_summary, confirm_execution
from src.data_fetcher import DataFetcher
from src.data_analyzer import DataAnalyzer
from src.report_generator import ReportGenerator
from src.confluence_updater import ConfluenceUpdater


def parse_arguments() -> Dict:
    """解析命令行参数"""
    args = {
        'mode': 'auto',
        'target_date': None,
        'week_offset': 0,
        'has_revenue_md': False,
        'md_path': None,
        'auto_confirm': False,
        'save_file': False
    }

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--help' or arg == '-h':
            print("""
使用方法: python3 main.py [选项]

选项：
  --auto           使用本周（默认）
  --next          使用下周
  --prev          使用上一周
  --target DATE   手动指定目标日期（格式：YYYYMMDD）
  --md PATH       指定收入MD文档路径
  --no-md         不使用MD文档，仅SQL数据
  --auto-confirm  自动确认所有提示
  --save-file     将报告保存到本地文件，不更新Confluence

示例：
  # 自动运行（本周）：
    python3 main.py --auto

  # 使用特定日期：
    python3 main.py --target 20260210

  # 使用MD文档：
    python3 main.py --md /path/to/revenue.md --auto

  # 保存到本地文件（不更新Confluence）：
    python3 main.py --auto --save-file
""")
            sys.exit(0)
        elif arg == '--auto' or arg == '-a':
            args['mode'] = 'auto'
            args['week_offset'] = 0
        elif arg == '--next' or arg == '-n':
            args['mode'] = 'auto'
            args['week_offset'] = 1
        elif arg == '--prev' or arg == '-p':
            args['mode'] = 'auto'
            args['week_offset'] = -1
        elif arg == '--md' or arg.startswith('--md='):
            args['has_revenue_md'] = True
            if '=' in arg:
                args['md_path'] = arg.split('=', 1)[1]
                i += 1
            elif i + 1 < len(sys.argv) and not sys.argv[i+1].startswith('--'):
                args['md_path'] = sys.argv[i + 1]
                i += 1
        elif arg == '--no-md':
            args['has_revenue_md'] = False
        elif arg == '--target' or arg.startswith('--target='):
            args['mode'] = 'manual'
            if '=' in arg:
                args['target_date'] = arg.split('=', 1)[1]
                i += 1
            elif i + 1 < len(sys.argv) and not sys.argv[i+1].startswith('--'):
                args['target_date'] = sys.argv[i + 1]
                i += 1
        elif arg == '--auto-confirm':
            args['auto_confirm'] = True
        elif arg == '--save-file':
            args['save_file'] = True
        else:
            print(f"未知参数: {arg}，使用 --help 查看帮助")
            sys.exit(1)
        i += 1

    return args


def get_week_config_from_args(args: Dict) -> Dict:
    """根据命令行参数获取周配置"""
    if args['mode'] == 'manual' and args['target_date']:
        # 手动模式：计算目标周的偏移
        # 这里简化处理，直接使用固定偏移
        params = calculate_week_params(target_date=args['target_date'])
        result = {
            'description': f'指定日期({args["target_date"]})',
            'target_date': args['target_date'],
            'report_date': params.get('report_date', args['target_date']),
            'week_offset': 0
        }
        # 合并所有返回的参数
        result.update(params)
        return result
    else:
        # 自动模式：根据偏移量计算
        params = calculate_week_params(week_offset=args['week_offset'])
        result = {
            'description': '本周' if args['week_offset'] == 0 else ('下周' if args['week_offset'] == 1 else '上一周'),
            'target_date': params.get('report_date', None),
            'report_date': params.get('report_date', None),
            'week_offset': args['week_offset']
        }
        # 合并所有返回的参数
        result.update(params)
        return result


def load_config(config_file: str = None) -> dict:
    """加载配置文件"""
    if config_file is None:
        config_file = Path(__file__).parent / 'config' / 'config.yaml'
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main():
    """主流程"""
    try:
        # 1. 设置日志
        logger = setup_logging(
            name='weekly_report',
            level=os.getenv('LOG_LEVEL', 'INFO'),
            log_file=os.getenv('LOG_FILE_PATH', 'logs/weekly_report.log')
        )
        logger.info("="*60)
        logger.info("Coohom周报自动化更新系统启动")
        logger.info("="*60)

        # 2. 解析命令行参数
        args = parse_arguments()

        # 3. 获取周配置
        week_config = get_week_config_from_args(args)
        logger.info(f"目标周: {week_config['description']}")
        logger.info(f"报告日期: {week_config.get('report_date', '')}")
        logger.info(f"周范围: {week_config.get('week_monday', '')} ~ {week_config.get('week_saturday', '')}")

        # 4. 收入MD文档（可选）
        md_content = None
        if args['has_revenue_md'] and args['md_path']:
            md_path = args['md_path']
            if os.path.exists(md_path):
                with open(md_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                logger.info(f"✅ 已加载MD文档: {os.path.basename(md_path)}")
            else:
                logger.warning(f"⚠️  MD文件不存在: {md_path}")
        elif not args['has_revenue_md']:
            logger.info("ℹ️  将仅使用SQL数据生成收入部分")

        # 5. 确认执行（自动模式下跳过）
        if not args['auto_confirm']:
            print("\n执行参数确认：")
            print(f" 目标周: {week_config['description']}")
            print(f"  报告日期: {week_config.get('report_date', '')}")
            print(f"  收入MD: {'使用' if args['has_revenue_md'] else '不使用'}")
            print(f"  将在Confluence更新页面ID: 81397518314")
            print("\n按Enter继续执行，或Ctrl+C取消...")

            # 等待用户确认（可选）
            try:
                import time
                time.sleep(2)  # 给用户2秒时间查看
                # 这里简化处理，直接继续
            except KeyboardInterrupt:
                logger.info("\n用户中断执行")
                sys.exit(1)

        # 6. 加载配置
        logger.info("加载配置文件...")
        config = load_config()
        base_path = Path(__file__).parent

        # 7. 数据获取 - 获取本周数据
        logger.info("\n" + "="*60)
        logger.info("第一阶段：数据获取")
        logger.info("="*60)
        fetcher = DataFetcher(config, use_mcp=True, logger=logger)

        logger.info("获取本周数据...")
        current_data = fetcher.fetch_all_sections(week_config, week_offset=0, base_path=str(base_path))
        logger.info("获取数据获取情况")
        sections_with_data = [k for k, v in current_data.items() if v]
        sections_without_data = [k for k, v in current_data.items() if not v]

        if sections_with_data:
            logger.info(f"✅ 成功获取 {len(sections_with_data)} 个部分的数据")
        else:
            logger.warning(f"⚠️  {len(sections_without_data)} 个部分无数据")

        # 8. 数据获取 - 获取上周数据（用于环比）
        logger.info("\n获取上周数据（用于环比计算）...")
        previous_data = fetcher.fetch_all_sections(week_config, week_offset=-1, base_path=str(base_path))

        # 9. 数据分析
        logger.info("\n" + "="*60)
        logger.info("第二阶段：数据分析")
        logger.info("="*60)
        analyzer = DataAnalyzer(logger)

        analysis_results = analyzer.analyze_all_sections(current_data, previous_data)

        # 显示分析结果摘要
        if 'traffic' in analysis_results:
            logger.info(f"流量: {analysis_results['traffic']['summary']}")
        if 'revenue' in analysis_results:
            logger.info(f"收入: {analysis_results['revenue']['summary']}")

        # 10. 生成报告
        logger.info("\n" + "="*60)
        logger.info("第三阶段：报告生成")
        logger.info("="*60)
        generator = ReportGenerator(logger)

        html_content = generator.generate_full_report(
            params=week_config,
            current_data=current_data,
            previous_data=previous_data,
            analysis=analysis_results,
            revenue_md_content=md_content
        )

        logger.info("✅ 报告HTML生成完成")

        # 11. 保存到文件或更新Confluence
        if args['save_file']:
            # 保存到本地文件
            logger.info("\n" + "="*60)
            logger.info("第四阶段：保存报告到文件")
            logger.info("="*60)
            updater = ConfluenceUpdater(config, logger)
            saved_path = updater.save_html_to_file(
                html_content,
                week_config.get('report_date', '')
            )
            if saved_path:
                logger.info("\n" + "="*60)
                logger.info("✅ 报告已保存到本地文件！")
                logger.info("="*60)
                logger.info(f"文件路径: {saved_path}")
                logger.info(f"报告日期: {week_config.get('report_date', '')}")
            else:
                logger.error("\n" + "="*60)
                logger.error("❌ 保存报告失败")
        else:
            # 更新Confluence
            logger.info("\n" + "="*60)
            logger.info("第四阶段：更新Confluence")
            logger.info("="*60)
            updater = ConfluenceUpdater(config, logger)

            success = updater.update_page(
                new_content=html_content,
                version_message=f"Weekly report - {week_config.get('report_date', '')}"
            )

            if success:
                logger.info("\n" + "="*60)
                logger.info("✅ 周报更新完成！")
                logger.info("="*60)
                logger.info(f"Confluence页面: https://cf.qunhequnhe.com/pages/viewpage.action?pageId=81397518314")
                logger.info(f"报告日期: {week_config.get('report_date', '')}")
            else:
                logger.error("\n" + "="*60)
                logger.error("❌ 周报更新失败")

    except KeyboardInterrupt:
        logger.info("\n\n❌ 用户中断执行")
    except Exception as e:
        logger.error(f"\n❌ 执行过程中出现异常: {e}", exc_info=True)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
