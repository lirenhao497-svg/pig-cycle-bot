# -*- coding: utf-8 -*-
"""查看数据库里有什么数据"""
import sys
import os

# 修复Windows控制台编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from storage.db import HogDatabase

db = HogDatabase()

print("=" * 60)
print("🐷  猪周期数据系统 - 数据查看")
print("=" * 60)

# 1. 分省价格表
print("\n📊 【1】分省价格明细")
print("-" * 60)

db.cur.execute("SELECT COUNT(*) FROM pig_price")
count = db.cur.fetchone()[0]

db.cur.execute("SELECT DISTINCT date FROM pig_price ORDER BY date DESC")
dates = db.cur.fetchall()

print(f"   总记录数：{count} 条")
print(f"   覆盖日期：{len(dates)} 天")
print()

# 显示最新一天的所有省份价格
if dates:
    latest_date = dates[0][0]
    print(f"   最新日期：{latest_date}")
    print(f"   各省份价格：")
    print()
    
    db.cur.execute("""
        SELECT province, price 
        FROM pig_price 
        WHERE date = ? 
        ORDER BY price DESC
    """, (latest_date,))
    
    provinces = db.cur.fetchall()
    for i, (province, price) in enumerate(provinces):
        end = "  " if (i + 1) % 4 != 0 else "\n   "
        print(f"   {province:4}：{price:5.2f} 元/公斤", end=end)
    print()

# 2. 每日快照表
print("\n" + "=" * 60)
print("📈 【2】每日价格汇总（历史趋势）")
print("-" * 60)

db.cur.execute("SELECT COUNT(*) FROM daily_snapshot")
count = db.cur.fetchone()[0]
print(f"   累计天数：{count} 天")
print()

db.cur.execute("""
    SELECT date, pig_price, lh_futures, max_price, max_price_province, 
           min_price, min_price_province, price_spread,
           corn_price, soybean_meal_price
    FROM daily_snapshot 
    ORDER BY date DESC
""")
rows = db.cur.fetchall()

print(f"   {'日期':12} {'猪价':>6} {'期货':>6} {'玉米':>6} {'豆粕':>6} {'猪粮比':>6} {'价差':>6}")
print(f"   {'-'*12} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*6}")

for r in rows[:14]:  # 最多显示14天
    date = r[0]
    pig_price = f"{r[1]:.2f}" if r[1] else "-"
    lh_futures = f"{r[2]:.0f}" if r[2] else "-"
    corn_price = f"{r[8]:.2f}" if r[8] else "-"
    meal_price = f"{r[9]:.2f}" if r[9] else "-"
    
    # 计算猪粮比
    if r[1] and r[8] and r[8] > 0:
        ratio = round(r[1] / r[8], 1)
        pig_grain_ratio = f"{ratio}"
    else:
        pig_grain_ratio = "-"
    
    spread = f"{r[7]:.2f}" if r[7] else "-"
    print(f"   {date:12} {pig_price:>6} {lh_futures:>6} {corn_price:>6} {meal_price:>6} {pig_grain_ratio:>6} {spread:>6}")

if len(rows) > 14:
    print(f"   ... 还有 {len(rows) - 14} 天数据")

# 显示最新一天的详细数据
if rows:
    latest = rows[0]
    print()
    print(f"   最新详细数据（{latest[0]}）：")
    print(f"     💰 生猪均价：{latest[1]:.2f} 元/公斤" if latest[1] else "     💰 生猪均价：-")
    print(f"     📈 生猪期货：{latest[2]:.0f} 元/吨" if latest[2] else "     📈 生猪期货：-")
    
    if latest[8]:  # 有玉米价格
        print(f"     🌽 玉米：{latest[8]:.2f} 元/公斤")
        print(f"     🫘 豆粕：{latest[9]:.2f} 元/公斤")
        if latest[1] and latest[8] and latest[8] > 0:
            ratio = round(latest[1] / latest[8], 2)
            print(f"     📐 猪粮比：{ratio} : 1")
            if ratio >= 6.0:
                print(f"     💚 盈利状态：高利润")
            elif ratio >= 5.5:
                print(f"     💚 盈利状态：微利")
            elif ratio >= 5.0:
                print(f"     🟡 盈利状态：盈亏平衡附近")
            else:
                print(f"     🔴 盈利状态：亏损")

# 2.5 期货数据详情
print("\n" + "=" * 60)
print("📊 【3】生猪期货详情")
print("-" * 60)

futures = db.get_latest_futures()
if futures:
    print(f"   合约：{futures['contract']}")
    print(f"   日期：{futures['date']}")
    print()
    print(f"   最新价：{futures['close_price']} 元/吨")
    print(f"   开盘价：{futures['open_price']} 元/吨" if futures['open_price'] else "   开盘价：-")
    print(f"   最高价：{futures['high_price']} 元/吨" if futures['high_price'] else "   最高价：-")
    print(f"   最低价：{futures['low_price']} 元/吨" if futures['low_price'] else "   最低价：-")
    print(f"   昨收：{futures['prev_close']} 元/吨" if futures['prev_close'] else "   昨收：-")
    print(f"   涨跌：{futures['change']}（{futures['change_pct']}%）" if futures['change'] else "   涨跌：-")
    print(f"   成交量：{futures['volume']} 手" if futures['volume'] else "   成交量：-")
    print(f"   成交额：{futures['amount']/1e8:.2f} 亿元" if futures['amount'] else "   成交额：-")
else:
    print("   暂无期货数据")

# 4. 数据源监控表
print("\n" + "=" * 60)
print("💚 【4】数据源运行状态")
print("-" * 60)

db.cur.execute("SELECT COUNT(*) FROM source_status")
count = db.cur.fetchone()[0]
print(f"   总抓取次数：{count} 次")
print()

# 健康度
health = db.get_source_health("正大猪博士", days=7)
print(f"   近7天成功率：{health['success_rate']}")
print()

print(f"   最近5次抓取记录：")
print()
db.cur.execute("""
    SELECT fetch_time, source_name, success, records_count, duration
    FROM source_status 
    ORDER BY id DESC 
    LIMIT 5
""")
rows = db.cur.fetchall()

for r in rows:
    status = "✅ 成功" if r[2] else "❌ 失败"
    duration = f"{r[4]:.1f}秒" if r[4] else "-"
    print(f"   {r[0]} | {r[1]:8} | {status} | {r[3]}条 | 耗时{duration}")

db.close()

print("\n" + "=" * 60)
print(f"💾 数据库文件：data/hog_data.db")
print(f"📋 日志文件：logs/app.log")
print("=" * 60)
