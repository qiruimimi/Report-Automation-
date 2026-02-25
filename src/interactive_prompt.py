#!/usr/bin/env python3
"""
交互式提示模块（简化版）

处理用户交互，包括目标周选择和收入文档提供
"""

import os
from pathlib import Path
from typing import Optional, Dict


def ask_target_week() -> Dict:
    """
    询问用户目标周（简化版）

    Returns:
        dict: 包含目标周信息的字典
    """
    print("\n" + "="*60)
    print("📊 Coohom周报自动化更新系统")
    print("="*60)

    print("\n请选择目标周：")
    print("  1. 本周（默认）")
    print("  2. 下一周")
    print("  3. 上一周")
    print("  4. 手动指定日期")

    choice = input("\n请输入选项 (1-4, 默认1): ").strip() or "1"

    if choice == "1":
        return {
            'mode': 'auto',
            'target_date': None,
            'week_offset': 0,
            'description': '本周'
        }
    elif choice == "2":
        return {
            'mode': 'auto',
            'target_date': None,
            'week_offset': 1,
            'description': '下一周'
        }
    elif choice == "3":
        return {
            'mode': 'auto',
            'target_date': None,
            'week_offset': -1,
            'description': '上一周'
        }
    elif choice == "4":
        date_str = input("请输入日期 (格式: YYYYMMDD, 如: 20260126): ").strip()
        return {
            'mode': 'manual',
            'target_date': date_str,
            'week_offset': 0,
            'description': f'指定日期({date_str})所在周'
        }
    else:
        print("⚠️  无效选项，将使用本周")
        return {
            'mode': 'auto',
            'target_date': None,
            'week_offset': 0,
            'description': '本周'
        }


def ask_revenue_summary() -> Optional[str]:
    """
    询问用户是否有收入周总结MD文档（简化版）

    Returns:
        str or None: MD文档内容，如果没有则返回None
    """
    print("\n" + "-"*60)
    print("💰 收入部分配置")
    print("-"*60)

    has_md = input("\n本周是否有收入周总结MD文档？ (y/n, 默认n): ").strip().lower() or "n"

    if has_md in ['y', 'yes', '是']:
        while True:
            md_path = input("请输入MD文档路径: ").strip().strip('"').strip("'")
            md_path = md_path.replace('\\', '')

            if os.path.exists(md_path) and md_path.endswith('.md'):
                print(f"✅ 已加载MD文档: {os.path.basename(md_path)}")
                with open(md_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                print(f"❌ 文件不存在或格式错误")
                retry = input("是否继续提供MD文档？ (y/n): ").strip().lower()
                if retry not in ['y', 'yes', '是']:
                    print("⚠️  将仅使用SQL数据生成收入部分")
                    return None

    print("ℹ️  将仅使用SQL查询数据生成收入部分")
    return None


def confirm_execution(params: dict, has_md: bool) -> bool:
    """
    确认执行参数（简化版）

    Args:
        params: 日期参数字典
        has_md: 是否有收入MD文档

    Returns:
        bool: 用户是否确认执行
    """
    print("\n" + "="*60)
    print("📋 执行参数确认")
    print("="*60)

    print(f"\n目标周: {params['description']}")
    print(f"报告日期: {params['report_date']}")
    print(f"周范围: {params['week_monday']} ~ {params['week_saturday']}")

    print(f"\n收入部分:")
    if has_md:
        print(f"  ✅ 使用MD文档 + SQL数据")
    else:
        print(f"  ℹ️  仅使用SQL数据")

    print("\nConfluence页面:")
    print(f"  Page ID: 81397518314")

    confirm = input("\n确认执行？ (y/n, 默认y): ").strip().lower() or "y"

    return confirm in ['y', 'yes', '是']
