# -*- coding: utf-8 -*-
"""
能繁母猪存栏数据录入命令

用法:
    python update_sow.py 2026-06 3050
    python update_sow.py 2026-06 3050 --source moa
    
参数:
    月份 (YYYY-MM 格式)
    存栏量 (万头)
    --source 数据来源（默认 moa）
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from storage.db import HogDatabase
from datetime import datetime


def main():
    if len(sys.argv) < 3:
        print("用法: python update_sow.py <YYYY-MM> <存栏量(万头)> [--source 来源]")
        print("示例: python update_sow.py 2026-06 3050")
        sys.exit(1)

    month = sys.argv[1]
    try:
        inventory = float(sys.argv[2])
    except ValueError:
        print(f"存栏量必须是数字，收到: {sys.argv[2]}")
        sys.exit(1)

    source = "moa"
    if "--source" in sys.argv:
        idx = sys.argv.index("--source")
        if idx + 1 < len(sys.argv):
            source = sys.argv[idx + 1]

    # 验证月份格式
    try:
        datetime.strptime(month + "-01", "%Y-%m-%d")
    except ValueError:
        print(f"月份格式错误，应为 YYYY-MM，收到: {month}")
        sys.exit(1)

    db = HogDatabase()

    latest = db.get_latest_sow_inventory()
    if latest:
        print(f"当前最新: {latest['month']} -> {latest['sow_inventory']} 万头")

    ok = db.save_sow_inventory(month, inventory, source)
    if ok:
        print(f"已录入: {month} -> {inventory} 万头 (来源: {source})")
        print(f"共 {db.cur.execute('SELECT COUNT(*) FROM industry_monthly').fetchone()[0]} 条记录")
    else:
        print("录入失败")
        sys.exit(1)

    db.close()


if __name__ == "__main__":
    main()
