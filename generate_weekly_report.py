#!/usr/bin/env python3
"""
一键生成周报脚本

完整的周报生成流程：
1. 加载JSON数据文件
2. 提取所有指标
3. 生成MD报告
4. 保存报告

使用方法:
    python generate_weekly_report.py --week 20260203 --prev-week 20260127
    python generate_weekly_report.py --week 20260203  # 不指定上周，自动计算
"""

import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.data_processor import DataProcessor
from src.metrics_extractor import MetricsExtractor
from generate_report import WeeklyReportGenerator
from src.logger import get_logger


def calculate_previous_week(week_label: str) -> str:
    """
    根据本周标签计算上周标签

    Args:
        week_label: 本周标签 (YYYYMMDD 格式)

    Returns:
        str: 上周标签
    """
    try:
        week_date = datetime.strptime(week_label, '%Y%m%d')
        prev_date = week_date - timedelta(days=7)
        return prev_date.strftime('%Y%m%d')
    except ValueError:
        logger.warning(f"⚠️  无法解析周标签 {week_label}，假设上周为 7 天前")
        return str(int(week_label) - 7)


def calculate_week_end_date(week_label: str) -> str:
    """
    根据周标签计算周结束日期

    Args:
        week_label: 周标签 (YYYYMMDD 格式，通常是周日)

    Returns:
        str: YYYY-MM-DD 格式的日期
    """
    try:
        week_date = datetime.strptime(week_label, '%Y%m%d')
        return week_date.strftime('%Y-%m-%d')
    except ValueError:
        return week_label


def generate_report(
    base_dir: str,
    week_label: str,
    prev_week_label: Optional[str] = None,
    output_dir: Optional[str] = None,
    report_date: Optional[str] = None
) -> str:
    """
    生成完整的周报

    Args:
        base_dir: 数据文件基础目录
        week_label: 本周标签
        prev_week_label: 上周标签（可选，不提供则自动计算）
        output_dir: 报告输出目录（可选）
        report_date: 报告日期（可选，默认为今天）

    Returns:
        str: 生成的报告文件路径
    """
    global logger
    logger = get_logger('generate_report')

    logger.info("=" * 70)
    logger.info("🚀 开始生成周报")
    logger.info("=" * 70)

    # 如果未提供上周标签，自动计算
    if prev_week_label is None:
        prev_week_label = calculate_previous_week(week_label)
        logger.info(f"📅 自动计算上周标签: {prev_week_label}")

    # 如果未提供报告日期，使用今天
    if report_date is None:
        report_date = datetime.now().strftime('%Y-%m-%d')

    # 计算周结束日期
    week_end_date = calculate_week_end_date(week_label)

    logger.info(f"📊 报告参数:")
    logger.info(f"   - 报告日期: {report_date}")
    logger.info(f"   - 数据周: {week_label} (截止 {week_end_date})")
    logger.info(f"   - 对比周: {prev_week_label}")
    logger.info(f"   - 数据目录: {base_dir}")

    # 步骤1: 加载数据
    logger.info("\n" + "=" * 70)
    logger.info("📂 步骤1: 加载数据文件")
    logger.info("=" * 70)

    processor = DataProcessor()
    loaded_data = processor.load_data_from_files(
        base_dir=base_dir,
        week_label=week_label,
        previous_week_label=prev_week_label
    )

    # 检查数据完整性
    required_sections = ['traffic', 'activation', 'engagement', 'retention', 'revenue']
    missing_sections = [s for s in required_sections if s not in loaded_data['current']]

    if missing_sections:
        logger.warning(f"⚠️  以下部分的数据文件缺失: {', '.join(missing_sections)}")
        logger.warning("⚠️  将使用默认值填充这些部分")

    # 步骤2: 提取指标
    logger.info("\n" + "=" * 70)
    logger.info("📈 步骤2: 提取所有指标")
    logger.info("=" * 70)

    metrics = processor.process_all_sections(
        current_data=loaded_data['current'],
        previous_data=loaded_data['previous'],
        dimension_data=loaded_data.get('dimension', {}),
        metadata=loaded_data  # 传递完整的 loaded_data 以获取元数据
    )

    # 步骤3: 生成报告
    logger.info("\n" + "=" * 70)
    logger.info("📝 步骤3: 生成MD报告")
    logger.info("=" * 70)

    generator = WeeklyReportGenerator()

    report_content = generator.generate_report(
        report_date=report_date,
        week_label=week_label,
        week_end_date=week_end_date,
        traffic_data=metrics.get('traffic', {}),
        activation_data=metrics.get('activation', {}),
        engagement_data=metrics.get('engagement', {}),
        retention_data=metrics.get('retention', {}),
        revenue_data=metrics.get('revenue', {})
    )

    # 步骤4: 保存报告
    if output_dir is None:
        output_dir = base_dir

    output_filename = f'weekly_report_{week_label}.md'
    output_path = Path(output_dir) / output_filename

    generator.save_report(report_content, str(output_path))

    # 完成摘要
    logger.info("\n" + "=" * 70)
    logger.info("✅ 周报生成完成!")
    logger.info("=" * 70)

    logger.info(f"\n📊 报告摘要:")
    if 'traffic' in metrics:
        logger.info(f"   流量: {metrics['traffic'].get('total_guests', 0):,} 访客, {metrics['traffic'].get('total_registers', 0):,} 注册")
    if 'engagement' in metrics:
        logger.info(f"   活跃: {metrics['engagement'].get('total_wau', 0):,} WAU")
    if 'retention' in metrics:
        logger.info(f"   留存: 新用户 {metrics['retention'].get('new_rate', 0)}%, 老用户 {metrics['retention'].get('old_rate', 0)}%")
    if 'revenue' in metrics:
        logger.info(f"   收入: ${metrics['revenue'].get('total', 0):,}")

    logger.info(f"\n📄 报告已保存到: {output_path}")
    logger.info(f"📏 报告大小: {len(report_content):,} 字符")

    return str(output_path)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='一键生成Coohom周报',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 生成20260203周的报告（自动计算上周）
  python generate_weekly_report.py --week 20260203

  # 生成20260203周的报告（指定上周）
  python generate_weekly_report.py --week 20260203 --prev-week 20260127

  # 指定输出目录
  python generate_weekly_report.py --week 20260203 --output ./reports

  # 指定数据目录
  python generate_weekly_report.py --week 20260203 --data-dir /path/to/data
        '''
    )

    parser.add_argument(
        '--week', '-w',
        required=True,
        help='本周标签 (YYYYMMDD 格式，例如 20260203)'
    )

    parser.add_argument(
        '--prev-week', '-p',
        required=False,
        help='上周标签 (YYYYMMDD 格式，不提供则自动计算)'
    )

    parser.add_argument(
        '--data-dir', '-d',
        default='/Users/sunsirui/Documents/coohom PLG/kmb/Our analytics/weekly_report_automation/output',
        help='数据文件目录 (默认: ./output)'
    )

    parser.add_argument(
        '--output', '-o',
        help='报告输出目录 (默认与数据目录相同)'
    )

    parser.add_argument(
        '--report-date', '-r',
        help='报告日期 (YYYY-MM-DD 格式，默认为今天)'
    )

    args = parser.parse_args()

    try:
        output_path = generate_report(
            base_dir=args.data_dir,
            week_label=args.week,
            prev_week_label=args.prev_week,
            output_dir=args.output,
            report_date=args.report_date
        )

        print(f"\n✅ 报告生成成功: {output_path}")
        return 0

    except FileNotFoundError as e:
        print(f"\n❌ 文件未找到: {e}")
        return 1

    except json.JSONDecodeError as e:
        print(f"\n❌ JSON解析错误: {e}")
        return 1

    except Exception as e:
        print(f"\n❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import json
    logger = None  # 将在 generate_report 中初始化
    sys.exit(main())
