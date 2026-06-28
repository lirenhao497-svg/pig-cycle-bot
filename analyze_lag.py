# -*- coding: utf-8 -*-
"""
滞后相关性分析脚本
分析生猪产业链指标与养殖股价格的滞后相关关系

日度数据：
  猪粮比(pig_grain_ratio) → 牧原/温氏/畜牧指数
  猪料比(pig_feed_ratio) → 牧原/温氏/畜牧指数
  期货(hog_futures) → 牧原/温氏/畜牧指数

月度数据：
  能繁母猪存栏(sow_inventory) → 个股月均价
"""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# ── 配置 ──
DB = Path(__file__).parent / "data" / "hog_data.db"
MIN_SAMPLES = 30  # 最小样本数

conn = sqlite3.connect(str(DB))
cur = conn.cursor()

def corr_with_lag(df, x_col, y_col, lags):
    """计算 x 滞后 lags 天与 y 的 Pearson 相关系数"""
    results = []
    df_sorted = df.sort_values("date").reset_index(drop=True)
    for lag in lags:
        if lag > 0:
            # X 滞后 lag 期：移 X 向后 lag 行
            x = df_sorted[x_col].shift(-lag)
            y = df_sorted[y_col]
        else:
            x = df_sorted[x_col]
            y = df_sorted[y_col]
        
        mask = x.notna() & y.notna()
        n = mask.sum()
        if n < MIN_SAMPLES:
            results.append({"滞后": lag, "样本": n, "相关性": None, 
                            "p值": None, "说明": f"样本不足{n}<{MIN_SAMPLES}"})
            continue
        
        from scipy.stats import pearsonr
        corr, p = pearsonr(x[mask], y[mask])
        results.append({"滞后": lag, "样本": n, "相关性": round(corr, 3),
                        "p值": round(p, 4)})
    return results


def print_results(items, title):
    """打印格式化的结果表格"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    header = f"{'自变量→因变量':<30} {'滞后':>5} {'相关性':>8} {'p值':>7} {'样本':>5}"
    print(header)
    print("-" * 60)
    
    best_by_pair = {}
    for item in items:
        key = f"{item['x']}→{item['y']}"
        if key not in best_by_pair:
            best_by_pair[key] = item
        else:
            # 找绝对值最大的相关性
            if item.get("相关性") is not None:
                cur_best = best_by_pair[key].get("相关性") or 0
                if abs(item["相关性"]) > abs(cur_best):
                    best_by_pair[key] = item
    
    for item in items:
        label = f"{item['x']} → {item['y']}"
        lag = item["滞后"]
        corr = item.get("相关性")
        pv = item.get("p值")
        n = item["样本"]
        note = item.get("说明", "")
        
        if corr is not None:
            flag = " ★" if abs(corr) >= 0.3 else ""
            print(f"  {label:<28} {lag:>5} {corr:>8.3f} {pv if pv is not None else '':>7} {n:>5}{flag}")
        else:
            print(f"  {label:<28} {lag:>5} {'—':>8} {'—':>7} {n:>5}  ⚠️{note}")

    print()
    print("  最强滞后（|r|≥0.3 标记 ★）：")
    for key, item in sorted(best_by_pair.items()):
        if item.get("相关性") is not None and abs(item["相关性"]) >= 0.3:
            print(f"    {key:<30} 滞后={item['滞后']}天  r={item['相关性']:.3f}")
    print()


# ═══════════════════════════════════════════════
# 1. 日度滞后分析
# ═══════════════════════════════════════════════

print("=" * 60)
print("  滞后相关性分析")
print("  " + datetime.now().strftime("%Y-%m-%d %H:%M"))
print("=" * 60)

# 读取 market_daily
df = pd.read_sql_query("""
    SELECT date, pig_grain_ratio, pig_feed_ratio, hog_futures,
           index_xumu, stock_muyuan, stock_wens
    FROM market_daily
    WHERE date >= '2022-01-04'
    ORDER BY date ASC
""", conn)

print(f"\n📊 market_daily: {len(df)} 行（{df['date'].min()} ~ {df['date'].max()}）")

# 日度滞后天数
DAILY_LAGS = [0, 5, 10, 20, 40, 60]

pairs_daily = [
    ("pig_grain_ratio", "stock_muyuan", "猪粮比→牧原"),
    ("pig_grain_ratio", "stock_wens",   "猪粮比→温氏"),
    ("pig_grain_ratio", "index_xumu",   "猪粮比→畜牧指数"),
    ("pig_feed_ratio",  "stock_muyuan", "猪料比→牧原"),
    ("pig_feed_ratio",  "stock_wens",   "猪料比→温氏"),
    ("hog_futures",     "stock_muyuan", "期货→牧原"),
    ("hog_futures",     "stock_wens",   "期货→温氏"),
    ("hog_futures",     "index_xumu",   "期货→畜牧指数"),
]

print("\n📈 日度滞后相关性")
for x_col, y_col, label in pairs_daily:
    sub_df = df[[x_col, y_col, "date"]].dropna(subset=[x_col, y_col])
    n = len(sub_df)
    if n < MIN_SAMPLES:
        print(f"\n  {label}: 有效数据 {n} 条 < {MIN_SAMPLES}，跳过")
        continue
    
    results = corr_with_lag(sub_df, x_col, y_col, DAILY_LAGS)
    for r in results:
        corr_str = f"{r['相关性']:.3f}" if r['相关性'] is not None else "—"
        p_str = f"{r['p值']:.4f}" if r.get('p值') is not None else "—"
        flag = " ★" if r.get('相关性') is not None and abs(r['相关性']) >= 0.3 else ""
        print(f"  {label:<22} 滞后{r['滞后']:>3}天  r={corr_str}  p={p_str}  n={r['样本']}{flag}")

print()

# ═══════════════════════════════════════════════
# 2. 月度滞后分析
# ═══════════════════════════════════════════════

print("📅 月度滞后相关性（能繁母猪→月均股价）")

# 从 market_daily 计算月均股价
df["month"] = df["date"].str[:7] + "-01"

monthly_avg = df.groupby("month").agg({
    "stock_muyuan": "mean",
    "stock_wens": "mean",
    "index_xumu": "mean",
}).reset_index()

monthly_avg.columns = ["month", "muyuan_avg", "wens_avg", "xumu_avg"]

# 读取 industry_monthly
df_sow = pd.read_sql_query("""
    SELECT month, sow_inventory FROM industry_monthly
    ORDER BY month ASC
""", conn)

# 合并
df_monthly = pd.merge(df_sow, monthly_avg, on="month", how="inner")
print(f"\n  月度合并数据: {len(df_monthly)} 行（{df_monthly['month'].min()} ~ {df_monthly['month'].max()}）")

MONTHLY_LAGS = [0, 1, 3, 6, 9, 12]

from scipy.stats import pearsonr

for y_col, label in [("muyuan_avg", "母猪→牧原"), ("wens_avg", "母猪→温氏"), ("xumu_avg", "母猪→畜牧指数")]:
    x_vals = df_monthly["sow_inventory"].values
    y_vals_all = df_monthly[y_col].values
    dates = df_monthly["month"].values
    n_total = len(df_monthly)
    
    if n_total < MIN_SAMPLES:
        print(f"\n  {label}: 有效数据 {n_total} 条 < {MIN_SAMPLES}，跳过")
        continue
    
    for lag in MONTHLY_LAGS:
        if lag == 0:
            x = x_vals
            y = y_vals_all
        else:
            x = x_vals[:-lag]
            y = y_vals_all[lag:]
        
        mask = ~(np.isnan(x) | np.isnan(y))
        n = mask.sum()
        if n < MIN_SAMPLES:
            print(f"  {label:<20} 滞后{lag:>2}月  样本不足{n}<{MIN_SAMPLES}，跳过")
            continue
        
        corr, p = pearsonr(x[mask], y[mask])
        flag = " ★" if abs(corr) >= 0.3 else ""
        print(f"  {label:<20} 滞后{lag:>2}月  r={corr:.3f}  p={p:.4f}  n={n}{flag}")

print()

# ═══════════════════════════════════════════════
# 3. 日度综合最优总结
# ═══════════════════════════════════════════════

print("📋 分析总结")
print("-" * 50)

# 读取 daily_snapshot 统计
cur.execute("SELECT COUNT(*) FROM market_daily WHERE pig_grain_ratio IS NOT NULL")
grain_n = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM market_daily WHERE hog_futures IS NOT NULL")
fut_n = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM market_daily WHERE stock_muyuan IS NOT NULL")
stock_n = cur.fetchone()[0]

print(f"  猪粮比数据: {grain_n} 交易日")
print(f"  期货数据:   {fut_n} 交易日")
print(f"  个股数据:   {stock_n} 交易日")
print(f"  母猪存栏:   {len(df_sow)} 个月")

print(f"\n💡 说明：")
print(f"  - 「★」标记 |r| ≥ 0.3 的较强相关")
print(f"  - 正相关表示自变量涨价→滞后N期后因变量跟涨")
print(f"  - 需积累更多数据后结论会更可靠")
print(f"  - 数据来源：AKShare / 搜猪网 / 农业农村部")

conn.close()
print("\n✅ 分析完成")
