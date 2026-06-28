# -*- coding: utf-8 -*-
"""
猪周期周报 - 自动化图表生成脚本

运行: python weekly_report.py
输出目录: 可视化/YYYYMMDD/ 下的4张PNG

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
import matplotlib.ticker as mticker

# ── 路径配置 ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "hog_data.db")
OUTPUT_ROOT = r"C:\Users\ll\.doubao\chats\2026-06-25\new-chat\可视化"
TODAY = datetime.now().strftime("%Y%m%d")
OUTPUT_DIR = os.path.join(OUTPUT_ROOT, TODAY)

# matplotlib 中文字体
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


# ── 数据读取 ─────────────────────────────────────────────
def load_data() -> dict:
    """从 market_daily + daily_snapshot 读取所有数据，返回 dict of DataFrames"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # 1. market_daily —— 期货、指数、个股、猪粮比、猪料比、利润
    market = pd.read_sql(
        """SELECT date, hog_futures, index_xumu,
                  stock_muyuan, stock_wens, stock_xinxiwang, stock_haida,
                  pig_grain_ratio, pig_feed_ratio, profit_self
           FROM market_daily
           ORDER BY date""",
        conn, parse_dates=["date"], index_col="date"
    )

    # 2. daily_snapshot —— 猪价、玉米、豆粕、仔猪等补充信息
    snap = pd.read_sql(
        """SELECT date, pig_price, corn_price, soybean_meal_price,
                  piglet_price_3way, piglet_price_crossbred
           FROM daily_snapshot
           ORDER BY date""",
        conn, parse_dates=["date"], index_col="date"
    )

    # 3. industry_monthly —— 能繁母猪存栏
    sow = pd.read_sql(
        "SELECT month, sow_inventory FROM industry_monthly ORDER BY month",
        conn, parse_dates=["month"], index_col="month"
    )

    conn.close()
    return {"market": market, "snap": snap, "sow": sow}


# ── 图1: 期货 + 指数长期走势（双Y轴）──────────────────
def plot_futures_index(market: pd.DataFrame, today_str: str, out_path: str):
    fig, ax1 = plt.subplots(figsize=(14, 6))

    data = market.dropna(subset=["hog_futures"]).copy()
    if data.empty:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return

    ax1.plot(data.index, data["hog_futures"], color="#E74C3C", linewidth=1.5, label="生猪期货（元/公斤）")
    ax1.set_ylabel("生猪期货（元/公斤）", color="#E74C3C", fontsize=11)
    ax1.tick_params(axis="y", labelcolor="#E74C3C")

    ax2 = ax1.twinx()
    idx_data = data.dropna(subset=["index_xumu"])
    if not idx_data.empty:
        ax2.plot(idx_data.index, idx_data["index_xumu"], color="#3498DB", linewidth=1.5, alpha=0.85, label="畜牧养殖指数")
    ax2.set_ylabel("畜牧养殖指数", color="#3498DB", fontsize=11)
    ax2.tick_params(axis="y", labelcolor="#3498DB")

    # 标题
    ax1.set_title(f"生猪期货 vs 畜牧养殖指数（长期走势）\n数据截止: {today_str}", fontsize=13, pad=12)
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # 图例合并
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=10)

    ax1.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  图1 已保存")


# ── 图2: 四只个股归一化对比（2022年初=100）──────────
def plot_stock_compare(market: pd.DataFrame, today_str: str, out_path: str):
    stocks = {
        "stock_muyuan": "牧原股份",
        "stock_wens": "温氏股份",
        "stock_xinxiwang": "新希望",
        "stock_haida": "海大集团",
    }

    fig, ax = plt.subplots(figsize=(14, 6))

    data = market.copy()
    # 仅保留2022年起的行情数据
    data = data[data.index >= "2022-01-01"].copy()
    if data.empty:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return

    colors = {"stock_muyuan": "#E74C3C", "stock_wens": "#3498DB",
              "stock_xinxiwang": "#2ECC71", "stock_haida": "#F39C12"}

    for col, name in stocks.items():
        series = data[col].dropna()
        if series.empty:
            continue
        # 归一化: 2022年首个非空值 = 100
        first_val = series.iloc[0]
        if first_val and first_val > 0:
            normalized = series / first_val * 100
            ax.plot(normalized.index, normalized.values,
                    label=name, color=colors[col], linewidth=1.3, alpha=0.85)

    ax.axhline(y=100, color="gray", linestyle="--", linewidth=0.7, alpha=0.5)
    ax.set_title(f"养殖板块个股归一化对比（2022年初 = 100）\n数据截止: {today_str}", fontsize=13, pad=12)
    ax.set_ylabel("相对值 (2022=100)", fontsize=11)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")
    ax.legend(loc="best", fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  图2 已保存")


# ── 图3: 猪粮比 ────────────────────────────────────────
def plot_pig_grain_ratio(market: pd.DataFrame, today_str: str, out_path: str):
    fig, ax = plt.subplots(figsize=(14, 6))

    data = market.dropna(subset=["pig_grain_ratio"]).copy()
    if data.empty:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return

    ax.plot(data.index, data["pig_grain_ratio"], color="#8E44AD", linewidth=2,
            marker="o", markersize=4, label="猪粮比")

    # 盈亏平衡线 6.0
    ax.axhline(y=6.0, color="#E74C3C", linestyle="--", linewidth=1.5, alpha=0.7, label="盈亏平衡线 (6.0)")

    # 填充亏损区
    ax.fill_between(data.index, data["pig_grain_ratio"], 6.0,
                     where=(data["pig_grain_ratio"] < 6.0),
                     color="#E74C3C", alpha=0.08, label="亏损区")

    ax.set_title(f"猪粮比走势\n数据截止: {today_str}", fontsize=13, pad=12)
    ax.set_ylabel("猪粮比", fontsize=11)
    ax.set_ylim(bottom=0)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")
    ax.legend(loc="best", fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  图3 已保存")


# ── 图4: 自繁利润柱状图 ────────────────────────────────
def plot_profit(market: pd.DataFrame, today_str: str, out_path: str):
    fig, ax = plt.subplots(figsize=(14, 6))

    data = market.dropna(subset=["profit_self"]).copy()
    if data.empty:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return

    # 按盈亏分色：红亏绿盈
    colors = ["#E74C3C" if v < 0 else "#2ECC71" for v in data["profit_self"]]

    ax.bar(data.index, data["profit_self"], color=colors, width=0.6, edgecolor="white", linewidth=0.5)

    # 零线
    ax.axhline(y=0, color="gray", linewidth=0.8)

    # 在每个柱子上标数值
    for idx, val in zip(data.index, data["profit_self"]):
        y_pos = val - 3 if val >= 0 else val + 3
        ax.text(idx, y_pos, f"{int(val)}", ha="center", va="bottom" if val >= 0 else "top",
                fontsize=7, color="#E74C3C" if val < 0 else "#2ECC71", alpha=0.8)

    ax.set_title(f"自繁自养利润（元/头）\n数据截止: {today_str}", fontsize=13, pad=12)
    ax.set_ylabel("利润（元/头）", fontsize=11)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  图4 已保存")


# ── 主入口 ──────────────────────────────────────────────
def main():
    print(f"\n{'='*50}")
    print(f"猪周期周报 - 图表生成")
    print(f"{'='*50}")

    # 读取数据
    print("\n读取数据...")
    data = load_data()
    market = data["market"]
    print(f"    market_daily: {len(market)} 行 ({market.index.min().date()} ~ {market.index.max().date()})")

    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"\n输出目录: {OUTPUT_DIR}")

    today_display = market.index.max().strftime("%Y-%m-%d")
    date_tag = market.index.max().strftime("%Y%m%d")

    # 生成4张图
    print(f"\n开始生成图表（数据截止: {today_display}）...")

    plot_futures_index(market, today_display, os.path.join(OUTPUT_DIR, f"{date_tag}_1_期货指数.png"))
    plot_stock_compare(market, today_display, os.path.join(OUTPUT_DIR, f"{date_tag}_2_个股对比.png"))
    plot_pig_grain_ratio(market, today_display, os.path.join(OUTPUT_DIR, f"{date_tag}_3_猪粮比.png"))
    plot_profit(market, today_display, os.path.join(OUTPUT_DIR, f"{date_tag}_4_利润.png"))

    print(f"\n{'='*50}")
    print(f"图表已保存到 {OUTPUT_DIR}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
