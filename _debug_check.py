# -*- coding: utf-8 -*-
"""调试：检查数据库表格间数据一致性"""
import sqlite3

conn = sqlite3.connect('data/hog_data.db')
c = conn.cursor()

print("=" * 60)
print("1. pig_price 2026-06-29 概要")
print("=" * 60)
c.execute("SELECT COUNT(*), ROUND(AVG(price),2), MIN(price), MAX(price) FROM pig_price WHERE date='2026-06-29'")
row = c.fetchone()
print(f"  记录数={row[0]}, 均价={row[1]}, 最低={row[2]}, 最高={row[3]}")

print()
print("=" * 60)
print("2. daily_snapshot 最近7天 (关键字段比对)")
print("=" * 60)
c.execute("""
    SELECT date, pig_price, lh_futures, corn_price, soybean_meal_price,
           piglet_price_3way, piglet_price_crossbred, pig_grain_ratio, pig_feed_ratio
    FROM daily_snapshot ORDER BY date DESC LIMIT 7
""")
cols = [d[0] for d in c.description]
print(f"  {' | '.join(cols)}")
for r in c.fetchall():
    print(f"  {r}")

print()
print("=" * 60)
print("3. daily_monitor 最近7天 (7字段汇聚表)")
print("=" * 60)
c.execute("SELECT * FROM daily_monitor ORDER BY date DESC LIMIT 7")
cols = [d[0] for d in c.description]
print(f"  {' | '.join(cols)}")
for r in c.fetchall():
    print(f"  {r}")

print()
print("=" * 60)
print("4. market_daily 最近7天 (前端主数据源)")
print("=" * 60)
c.execute("SELECT * FROM market_daily ORDER BY date DESC LIMIT 7")
cols = [d[0] for d in c.description]
print(f"  {' | '.join(cols)}")
for r in c.fetchall():
    print(f"  {r}")

print()
print("=" * 60)
print("5. futures_data 最近7天")
print("=" * 60)
c.execute("SELECT * FROM futures_data ORDER BY date DESC LIMIT 7")
cols = [d[0] for d in c.description]
print(f"  {' | '.join(cols)}")
for r in c.fetchall():
    print(f"  {r}")

print()
print("=" * 60)
print("6. piglet_price 最近7天")
print("=" * 60)
c.execute("SELECT date, category, price FROM piglet_price ORDER BY date DESC LIMIT 7")
for r in c.fetchall():
    print(f"  {r}")

print()
print("=" * 60)
print("7. hog_cost_history 最近3天")
print("=" * 60)
c.execute("SELECT * FROM hog_cost_history ORDER BY date DESC LIMIT 3")
cols = [d[0] for d in c.description]
print(f"  {' | '.join(cols)}")
for r in c.fetchall():
    print(f"  {r}")

print()
print("=" * 60)
print("8. hog_supply_history 最近3天")
print("=" * 60)
c.execute("SELECT * FROM hog_supply_history ORDER BY date DESC LIMIT 3")
cols = [d[0] for d in c.description]
print(f"  {' | '.join(cols)}")
for r in c.fetchall():
    print(f"  {r}")

conn.close()
