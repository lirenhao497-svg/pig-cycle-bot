# -*- coding: utf-8 -*-
"""
猪周期监控图 - 自动化生成

数据源：daily_monitor 表（仅包含全部字段齐全的有效日期，节假日无股价时不纳入）
有效日期 >= 2 天则画图，否则跳过

运行: python report_generator.py
输出: 可视化\YYYYMMDD\YYYYMMDD_猪周期监控.png

依赖: pip install pandas matplotlib
"""

import os
import sys
import sqlite3
from datetime import datetime

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ── 路径配置 ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "hog_data.db")
OUTPUT_ROOT = r"C:\Users\ll\.doubao\chats\2026-06-25\new-chat\可视化"
TODAY_STR = datetime.now().strftime("%Y%m%d")
OUTPUT_DIR = os.path.join(OUTPUT_ROOT, TODAY_STR)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"{TODAY_STR}_猪周期监控.png")

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


# ── 数据读取 ─────────────────────────────────────────────
def load_valid_data() -> pd.DataFrame:
    """
    从 daily_monitor 表读取数据，同时从 piglet_price 补充仔猪价格。
    daily_monitor 只存全部7个字段都有效的日期（节假日无股价则自动跳过）。
    """
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql(
        """SELECT date, pig_price_kg AS pig_price, pig_price_head,
                  hog_futures, stock_muyuan,
                  pig_grain_ratio, pig_feed_ratio, index_xumu
           FROM daily_monitor
           ORDER BY date""",
        conn, parse_dates=["date"]
    )

    # 从 piglet_price 补充仔猪价格（元/公斤）
    if not df.empty:
        dates = df["date"].dt.strftime("%Y-%m-%d").tolist()
        ph = ",".join(["?" for _ in dates])
        piglet = pd.read_sql(
            f"""SELECT date, category, price / 10.0 AS price_kg
                FROM piglet_price WHERE date IN ({ph})
                ORDER BY date, category""",
            conn, params=dates, parse_dates=["date"]
        )
        if not piglet.empty:
            for cat, col in [("三元", "piglet_3way_kg"), ("外三元", "piglet_cross_kg")]:
                sub = piglet[piglet["category"] == cat][["date", "price_kg"]] \
                    .rename(columns={"price_kg": col})
                df = df.merge(sub, on="date", how="left")

    conn.close()
    return df


# ── 画图 ─────────────────────────────────────────────────
def draw_5_panel_chart(df: pd.DataFrame, out_path: str):
    data_cutoff = df["date"].max().strftime("%Y-%m-%d")

    fig, axes = plt.subplots(5, 1, figsize=(12, 14), sharex=True)
    fig.suptitle(f"猪周期监控图（数据截止: {data_cutoff}）",
                 fontsize=14, fontweight="bold", y=0.98)

    colors = {
        "pig_price": "#2C3E50",
        "piglet_3way_kg": "#E67E22",
        "piglet_cross_kg": "#D35400",
        "hog_futures": "#C0392B",
        "stock_muyuan": "#2980B9",
        "pig_grain_ratio": "#8E44AD",
    }

    # ── 子图1: 外三元生猪价格 ──
    ax1 = axes[0]
    ax1.plot(df["date"], df["pig_price"], color=colors["pig_price"],
             linewidth=2, marker="o", markersize=5, label="外三元生猪价格")
    ax1.set_ylabel("元/公斤", fontsize=10)
    ax1.set_title("(1) 外三元生猪价格", fontsize=11, loc="left")
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(True, alpha=0.25)
    for _, row in df.iterrows():
        ax1.annotate(f"{row['pig_price']:.2f}",
                     (row["date"], row["pig_price"]),
                     textcoords="offset points", xytext=(0, 8),
                     ha="center", fontsize=7, color=colors["pig_price"])

    # ── 子图2: 仔猪价格 ──
    ax2 = axes[1]
    if "piglet_3way_kg" in df.columns:
        ax2.plot(df["date"], df["piglet_3way_kg"], color=colors["piglet_3way_kg"],
                 linewidth=2, marker="o", markersize=5, label="三元仔猪（元/公斤）")
    if "piglet_cross_kg" in df.columns:
        ax2.plot(df["date"], df["piglet_cross_kg"], color=colors["piglet_cross_kg"],
                 linewidth=2, marker="s", markersize=5, label="外三元仔猪（元/公斤）")
    ax2.set_ylabel("元/公斤", fontsize=10)
    ax2.set_title("(2) 仔猪价格", fontsize=11, loc="left")
    ax2.legend(loc="upper left", fontsize=9)
    ax2.grid(True, alpha=0.25)
    if "piglet_3way_kg" in df.columns:
        for _, row in df.iterrows():
            ax2.annotate(f"{row['piglet_3way_kg']:.1f}",
                         (row["date"], row["piglet_3way_kg"]),
                         textcoords="offset points", xytext=(0, 8),
                         ha="center", fontsize=7, color=colors["piglet_3way_kg"])
    if "piglet_cross_kg" in df.columns:
        for _, row in df.iterrows():
            ax2.annotate(f"{row['piglet_cross_kg']:.0f}",
                         (row["date"], row["piglet_cross_kg"]),
                         textcoords="offset points", xytext=(0, -12),
                         ha="center", fontsize=7, color=colors["piglet_cross_kg"])

    # ── 子图3: 生猪期货 ──
    ax3 = axes[2]
    ax3.plot(df["date"], df["hog_futures"], color=colors["hog_futures"],
             linewidth=2, marker="o", markersize=5, label="生猪期货（元/公斤）")
    ax3.set_ylabel("元/公斤", fontsize=10)
    ax3.set_title("(3) 生猪期货价格", fontsize=11, loc="left")
    ax3.legend(loc="upper left", fontsize=9)
    ax3.grid(True, alpha=0.25)
    for _, row in df.iterrows():
        ax3.annotate(f"{row['hog_futures']:.2f}",
                     (row["date"], row["hog_futures"]),
                     textcoords="offset points", xytext=(0, 8),
                     ha="center", fontsize=7, color=colors["hog_futures"])

    # ── 子图4: 牧原股价 ──
    ax4 = axes[3]
    ax4.plot(df["date"], df["stock_muyuan"], color=colors["stock_muyuan"],
             linewidth=2, marker="o", markersize=5, label="牧原股份（元）")
    ax4.set_ylabel("元", fontsize=10)
    ax4.set_title("(4) 牧原股份股价", fontsize=11, loc="left")
    ax4.legend(loc="upper left", fontsize=9)
    ax4.grid(True, alpha=0.25)
    for _, row in df.iterrows():
        ax4.annotate(f"{row['stock_muyuan']:.2f}",
                     (row["date"], row["stock_muyuan"]),
                     textcoords="offset points", xytext=(0, 8),
                     ha="center", fontsize=7, color=colors["stock_muyuan"])

    # ── 子图5: 猪粮比 + 盈亏线 ──
    ax5 = axes[4]
    ax5.plot(df["date"], df["pig_grain_ratio"], color=colors["pig_grain_ratio"],
             linewidth=2, marker="o", markersize=5, label="猪粮比")
    ax5.axhline(y=6.0, color="#E74C3C", linestyle="--", linewidth=1.2,
                alpha=0.7, label="盈亏平衡线 (6.0)")
    ax5.fill_between(df["date"], df["pig_grain_ratio"], 6.0,
                     where=(df["pig_grain_ratio"] < 6.0),
                     color="#E74C3C", alpha=0.06, label="亏损区")
    ax5.set_ylabel("比率", fontsize=10)
    ax5.set_title("(5) 猪粮比", fontsize=11, loc="left")
    ax5.legend(loc="upper left", fontsize=9)
    ax5.grid(True, alpha=0.25)
    for _, row in df.iterrows():
        ax5.annotate(f"{row['pig_grain_ratio']:.2f}",
                     (row["date"], row["pig_grain_ratio"]),
                     textcoords="offset points", xytext=(0, 8),
                     ha="center", fontsize=7, color=colors["pig_grain_ratio"])

    # ── x 轴共用 ──
    ax5.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax5.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    plt.setp(ax5.xaxis.get_majorticklabels(), rotation=45, ha="right")

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ── 主入口 ──────────────────────────────────────────────
def main():
    print(f"\n{'='*50}")
    print(f"猪周期监控图 - 生成")
    print(f"{'='*50}")

    print("\n读取数据...")
    df = load_valid_data()
    print(f"  有效日期: {len(df)} 天")

    if len(df) < 2:
        print(f"\n有效数据不足 2 天，跳过画图。")
        if len(df) == 0:
            print("（daily_monitor 表暂无数据，等数据采集齐全后会自动出现）")
        print(f"\n{'='*50}")
        print(f"跳过: 未生成图片")
        print(f"{'='*50}\n")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"\n有效日期 {len(df)} 天，开始画图...")
    draw_5_panel_chart(df, OUTPUT_FILE)

    print(f"\n{'='*50}")
    print(f"图片已保存到 {OUTPUT_FILE}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
