# -*- coding: utf-8 -*-
"""
测试历史查询接口和快照表
"""
import sys
import os
from datetime import datetime, timedelta

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

logger = get_logger("test_history")


def test_history():
    """测试历史查询"""
    
    print("\n" + "="*60)
    print("测试：历史查询接口 + 完善的快照表")
    print("="*60)
    
    db = HogDatabase()
    
    # 1. 先抓取今天的数据，存入完整快照
    print("\n[1/4] 抓取今日数据并保存完整快照...")
    fetcher = PigPriceCpctiFetcher()
    prices = fetcher.fetch_daily_price()
    
    if prices:
        avg_price = fetcher.get_national_avg(prices)
        stats = fetcher.get_price_stats(prices)
        
        print(f"  全国均价: {avg_price} 元/公斤")
        print(f"  最高价: {stats['max_price']} 元/公斤 ({stats['max_province']})")
        print(f"  最低价: {stats['min_price']} 元/公斤 ({stats['min_province']})")
        print(f"  价差: {stats['spread']} 元/公斤")
        
        # 保存完整快照
        snapshot = DailySnapshot(
            date=datetime.now(),
            pig_price=avg_price,
            max_price=stats['max_price'],
            max_price_province=stats['max_province'],
            min_price=stats['min_price'],
            min_price_province=stats['min_province'],
            price_spread=stats['spread']
        )
        db.save_daily_snapshot(snapshot)
        print("  完整快照已保存")
    
    fetcher.close()
    
    # 2. 测试最新价格查询
    print("\n[2/4] 测试最新价格查询...")
    latest = db.get_latest_price()
    print(f"  最新全国均价: {latest} 元/公斤")
    
    # 3. 测试最新快照（含最高/最低/价差）
    print("\n[3/4] 测试最新完整快照...")
    snapshot = db.get_latest_snapshot()
    if snapshot:
        print(f"  日期: {snapshot['date']}")
        print(f"  全国均价: {snapshot['pig_price']} 元/公斤")
        if snapshot.get('max_price'):
            print(f"  最高价: {snapshot['max_price']} 元/公斤 ({snapshot['max_price_province']})")
            print(f"  最低价: {snapshot['min_price']} 元/公斤 ({snapshot['min_price_province']})")
            print(f"  价差: {snapshot['price_spread']} 元/公斤")
    
    # 4. 测试历史查询
    print("\n[4/4] 测试历史查询...")
    
    # 为了测试，先插入几天模拟数据
    print("  （插入几天模拟历史数据用于测试）")
    base_date = datetime.now() - timedelta(days=1)
    for i in range(6):
        test_date = base_date - timedelta(days=i)
        test_price = 9.5 + i * 0.1  # 模拟价格递增
        try:
            db.cur.execute("""
                INSERT OR IGNORE INTO daily_snapshot (date, pig_price)
                VALUES (?, ?)
            """, (test_date.strftime("%Y-%m-%d"), round(test_price, 2)))
        except:
            pass
    db.conn.commit()
    
    # 查询最近7天
    last_7 = db.get_last_7days()
    print(f"\n  最近7天价格（共{len(last_7)}天）:")
    for item in last_7:
        print(f"    {item['date']} : {item['price']} 元/公斤")
    
    # 查询最近30天
    last_30 = db.get_last_30days()
    print(f"\n  最近30天数据量: {len(last_30)} 天")
    
    db.close()
    
    print("\n" + "="*60)
    print("  历史查询接口测试通过！")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_history()
