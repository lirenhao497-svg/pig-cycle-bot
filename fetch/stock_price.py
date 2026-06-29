# -*- coding: utf-8 -*-
"""
股票价格爬虫
使用 AKShare 获取 A 股日K行情（牧原002714、温氏300498）
每天18:00执行（A股15:00收盘后）
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import akshare as ak
import pandas as pd
from datetime import datetime


STOCKS = [
    {"code": "002714", "name": "牧原股份"},
    {"code": "300498", "name": "温氏股份"},
]


def fetch_stock_day(symbol: str, date_str: str = None):
    """
    获取单只股票指定日期的日K数据。
    返回 dict 或 None（当天无数据）。
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")
    
    # AKShare 一次性请求全量数据太慢，但指定单日请求很快
    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=date_str,
        end_date=date_str,
        adjust=""
    )
    
    if df.empty:
        return None
    
    row = df.iloc[-1]  # 取最新一条（如果有期货夜盘会多出第二天）
    return {
        "date": str(row["日期"])[:10],
        "code": symbol,
        "name": str(row["股票代码"]),
        "open": float(row["开盘"]),
        "close": float(row["收盘"]),
        "high": float(row["最高"]),
        "low": float(row["最低"]),
        "volume": int(row["成交量"]),
        "amount": float(row["成交额"]),
        "amplitude": float(row["振幅"]),
        "change_pct": float(row["涨跌幅"]),
        "change_amount": float(row["涨跌额"]),
        "turnover": float(row["换手率"]),
    }


def fetch_all_stocks(date_str: str = None):
    """获取所有配置的股票数据"""
    results = []
    for stock in STOCKS:
        try:
            data = fetch_stock_day(stock["code"], date_str)
            if data:
                results.append(data)
                print(f"  ✅ {stock['name']} ({stock['code']}): {data['close']} 元")
            else:
                print(f"  ⚠️ {stock['name']} ({stock['code']}): 当日无数据（非交易日）")
        except Exception as e:
            print(f"  ❌ {stock['name']} ({stock['code']}) 爬取失败: {e}")
    return results
