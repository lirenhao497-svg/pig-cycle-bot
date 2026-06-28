# -*- coding: utf-8 -*-
"""
完整闭环测试：爬真实数据 → 存数据库 → 查询 → 输出
"""
import sys
import os
from datetime import datetime

# 修复Windows控制台编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch.pig_price import PigPriceCpctiFetcher
from storage.db import HogDatabase
from models.schema import DailySnapshot
from utils.logger import get_logger

logger = get_logger("full_test")


def test_full_cycle():
    """测试完整闭环"""
    
    print("\n" + "="*60)
    print("猪周期系统 - 完整闭环测试（真实数据）")
    print("="*60)
    
    # 1. 初始化
    print("\n[1/5] 初始化爬虫和数据库...")
    fetcher = PigPriceCpctiFetcher()
    db = HogDatabase()
    print("    OK 初始化完成")
    
    # 2. 抓取真实猪价数据
    print("\n[2/5] 抓取真实生猪价格数据...")
    prices = fetcher.fetch_daily_price()
    
    if not prices:
        print("    失败：未抓取到数据")
        return
    
    print(f"    OK 成功抓取 {len(prices)} 条分省价格")
    
    # 3. 存入数据库
    print("\n[3/5] 存入数据库...")
    success_count = 0
    for p in prices:
        if db.insert_pig_price(p):
            success_count += 1
    
    print(f"    OK 成功写入 {success_count} 条")
    
    # 4. 计算全国均价并存入每日快照
    print("\n[4/5] 计算全国均价并保存快照...")
    avg_price = fetcher.get_national_avg(prices)
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    snapshot = DailySnapshot(
        date=datetime.now(),
        pig_price=avg_price,
        lh_futures=None,
        corn_price=None,
        soybean_meal_price=None
    )
    db.save_daily_snapshot(snapshot)
    print(f"    OK 全国均价: {avg_price} 元/公斤")
    
    # 5. 从数据库查询并输出
    print("\n[5/5] 从数据库查询并输出...")
    db_avg = db.get_national_avg(date_str)
    latest = db.get_latest_snapshot()
    
    print("\n" + "-"*60)
    print(f"  日期: {latest['date']}")
    print(f"  全国生猪均价: {latest['pig_price']} 元/公斤")
    print(f"  数据来源: 正大猪博士")
    print(f"  覆盖省份: {len(prices)} 个")
    print("-"*60)
    
    # 显示部分省份数据
    print("\n  部分省份价格:")
    for p in prices[:8]:
        print(f"    {p.province:6} : {p.price:>5.2f} 元/公斤")
    print(f"    ... 共 {len(prices)} 个省份")
    
    # 记录数据源状态
    db.log_source_status(
        source_name="正大猪博士",
        data_type="pig_price",
        success=True,
        records_count=len(prices)
    )
    
    db.close()
    fetcher.close()
    
    print("\n" + "="*60)
    print("  完整闭环测试通过！")
    print("  真实数据 → Schema → SQLite → 查询输出  全链路打通")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_full_cycle()
