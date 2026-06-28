# -*- coding: utf-8 -*-
"""
数据库写入测试
验证最小闭环：存数据 → 查数据 → 打印
"""
import sys
import os
from datetime import datetime

# 修复Windows控制台编码问题
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage.db import HogDatabase
from models.schema import PigPrice, FuturesData, FeedPrice, DailySnapshot


def test_db():
    print("=" * 50)
    print("猪周期系统 - 数据库最小闭环测试")
    print("=" * 50)
    
    # 1. 初始化数据库
    print("\n[1/5] 初始化数据库...")
    db = HogDatabase()
    print("    OK 数据库初始化成功，三张表已创建")
    
    # 2. 插入分省猪价数据（模拟）
    print("\n[2/5] 插入分省猪价数据...")
    today = datetime.now()
    test_prices = [
        PigPrice(date=today, province="河南", price=14.52),
        PigPrice(date=today, province="山东", price=14.87),
        PigPrice(date=today, province="四川", price=15.23),
        PigPrice(date=today, province="广东", price=15.68),
        PigPrice(date=today, province="湖南", price=14.95),
        PigPrice(date=today, province="湖北", price=14.76),
    ]
    
    for p in test_prices:
        db.insert_pig_price(p)
    
    print(f"    OK 已插入 {len(test_prices)} 条分省价格数据")
    
    # 3. 查询全国均价
    print("\n[3/5] 查询全国均价...")
    date_str = today.strftime("%Y-%m-%d")
    avg_price = db.get_national_avg(date_str)
    print(f"    日期: {date_str}")
    print(f"    全国均价: {avg_price:.2f} 元/公斤")
    
    # 4. 保存每日快照
    print("\n[4/5] 保存每日汇总快照...")
    snapshot = DailySnapshot(
        date=today,
        pig_price=round(avg_price, 2),
        lh_futures=15350,
        corn_price=2.65,
        soybean_meal_price=3.82
    )
    db.save_daily_snapshot(snapshot)
    print("    OK 每日快照已保存")
    
    # 5. 查询并打印最新快照
    print("\n[5/5] 查询最新快照...")
    latest = db.get_latest_snapshot()
    print("\n" + "-" * 50)
    print(f"  日期: {latest['date']}")
    print(f"  生猪均价: {latest['pig_price']} 元/公斤")
    print(f"  生猪期货: {latest['lh_futures']} 元/吨")
    print(f"  玉米价格: {latest['corn_price']} 元/公斤")
    print(f"  豆粕价格: {latest['soybean_meal_price']} 元/公斤")
    print("-" * 50)
    
    db.close()
    
    print("\n数据库最小闭环测试通过！")
    print("系统已具备：存数据 -> 查数据 -> 输出 能力")
    print("=" * 50)


if __name__ == "__main__":
    test_db()
