#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
猪周期量化系统 - FastAPI 后端
提供 9 个 /api 接口供前端仪表盘使用
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional

DB = r'C:\Users\ll\.doubao\chats\2026-06-25\new-chat\pig_cycle_bot\data\hog_data.db'
app = FastAPI(title="猪周期量化系统 API", version="2.0")

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn

# ========== 辅助函数 ==========
def compute_status(row):
    """计算当前信号状态"""
    pgr = row['pig_grain_ratio']
    sig_a = bool(row.get('pgr_golden_cross', 0)) and bool(row.get('muyuan_above_ma20', 0)) and bool(row.get('muyuan_vol_contract', 0))
    trigger = sig_a and (pgr > 7.0 or pgr < 5.0)
    if trigger:
        return "清仓避险", f"猪粮比{pgr:.2f}触发{'高位' if pgr>7.0 else '低位'}信号"
    elif sig_a:
        return "观望", "signal_a 触发但猪粮比在震荡区间"
    return "空仓", None

def get_cycle_stage_label(pgr):
    if pgr < 4.0: return "深度亏损"
    elif pgr < 5.0: return "极端低位"
    elif pgr < 6.0: return "偏弱"
    elif pgr < 7.0: return "中性"
    return "高位"

# ========== API 接口 ==========
@app.get("/api/latest")
def api_latest():
    conn = get_db()
    cur = conn.cursor()

    # 1) 最新交易日数据
    cur.execute("""
        SELECT date, pig_grain_ratio, stock_muyuan as muyuan_close,
               stock_wens as wenshi_close, hog_futures as futures_close,
               index_xumu as hog_index_close
        FROM market_daily
        WHERE date = (SELECT MAX(date) FROM market_daily)
    """)
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(404)
    d = dict(row)
    latest_date = d['date']

    # 2) 猪肉价格 & 仔猪价格
    cur.execute("SELECT pig_price FROM daily_snapshot WHERE date = ?", (latest_date,))
    snap = cur.fetchone()
    d['pig_price'] = snap['pig_price'] if snap else None

    # piglet_price 表: category='外三元' 是元/头，category='三元' 也是元/头
    # 前端 Dashboard 需要仔猪价格元/kg，这里用 category='外三元' 的价格
    cur.execute("SELECT price FROM piglet_price WHERE category=? AND date = ? ORDER BY id DESC LIMIT 1", ('外三元', latest_date))
    piglet = cur.fetchone()
    d['piglet_price'] = piglet['price'] if piglet else None

    # 3) 周末/节假日回退：如果 muyuan_close 为 null，查上一个交易日
    d['muyuan_close_is_fallback'] = False
    d['hog_index_close_is_fallback'] = False
    fallback_date = None

    if d['muyuan_close'] is None:
        cur.execute("""
            SELECT date, stock_muyuan FROM market_daily
            WHERE stock_muyuan IS NOT NULL
            ORDER BY date DESC LIMIT 1
        """)
        fb = cur.fetchone()
        if fb:
            d['muyuan_close'] = fb['stock_muyuan']
            d['muyuan_close_is_fallback'] = True
            fallback_date = fb['date']

    if d['hog_index_close'] is None:
        cur.execute("""
            SELECT date, index_xumu FROM market_daily
            WHERE index_xumu IS NOT NULL
            ORDER BY date DESC LIMIT 1
        """)
        fb = cur.fetchone()
        if fb:
            d['hog_index_close'] = fb['index_xumu']
            d['hog_index_close_is_fallback'] = True
            if not fallback_date:
                fallback_date = fb['date']

    d['fallback_date'] = fallback_date

    # 4) 涨跌幅：对比前一个交易日
    # 回退后，前一个交易日应为回退日期的前一个交易日
    ref_date = fallback_date if fallback_date else latest_date
    cur.execute("""
        SELECT stock_muyuan, hog_futures, index_xumu, pig_grain_ratio
        FROM market_daily WHERE date = (SELECT MAX(date) FROM market_daily WHERE date < ?)
    """, (ref_date,))
    prev = cur.fetchone()
    conn.close()

    if prev:
        d['muyuan_change'] = round((d['muyuan_close'] - prev[0]) / prev[0] * 100, 2) if prev[0] and d['muyuan_close'] else None
        d['futures_change'] = round((d['futures_close'] - prev[1]) / prev[1] * 100, 2) if prev[1] and d['futures_close'] else None
        d['index_change'] = round((d['hog_index_close'] - prev[2]) / prev[2] * 100, 2) if prev[2] and d['hog_index_close'] else None
        d['pgr_change'] = round(d['pig_grain_ratio'] - prev[3], 2) if prev[3] and d['pig_grain_ratio'] else None
    return d

@app.get("/api/signals")
def api_signals():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM market_daily_signals_v2
        WHERE date = (SELECT MAX(date) FROM market_daily_signals_v2)
    """)
    row = cur.fetchone()
    conn.close()
    if not row: raise HTTPException(404)
    d = dict(row)
    status, reason = compute_status(d)
    return {"date": d['date'], "status": status, "trigger_reason": reason,
            "pgr_golden_cross": bool(d.get('pgr_golden_cross', 0)),
            "muyuan_above_ma20": bool(d.get('muyuan_above_ma20', 0)),
            "muyuan_vol_contract": bool(d.get('muyuan_vol_contract', 0)),
            "pig_grain_ratio": d.get('pig_grain_ratio')}

@app.get("/api/cycle_stage")
def api_cycle_stage():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM cycle_stage ORDER BY date DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    if not row: raise HTTPException(404)
    return dict(row)

@app.get("/api/trade_log")
def api_trade_log(limit: int = 5):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM daily_trade_log ORDER BY date DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.get("/api/strategy_g")
def api_strategy_g():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM sim_positions WHERE status='closed' ORDER BY entry_date")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.get("/api/simulation")
def api_simulation():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM sim_positions WHERE status='open'")
    current = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT * FROM sim_positions WHERE status='closed' ORDER BY entry_date")
    history = [dict(r) for r in cur.fetchall()]
    cur.execute("""
        SELECT COUNT(*), AVG(CASE WHEN profit_pct>0 THEN 1.0 ELSE 0 END)*100 as wr,
               AVG(profit_pct) as avg_ret, MAX(profit_pct) as mx, MIN(profit_pct) as mn
        FROM sim_positions WHERE status='closed'
    """)
    s = cur.fetchone()
    conn.close()
    stats = {"total_trades": s[0], "win_rate": round(s[1], 1) if s[1] else 0,
             "avg_return": round(s[2], 2) if s[2] else 0,
             "max_return": round(s[3], 2) if s[3] else 0,
             "max_loss": round(s[4], 2) if s[4] else 0} if s else {}
    return {"current": current, "history": history, "stats": stats}

@app.get("/api/l1_watchlist")
def api_l1_watchlist():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM l1_watchlist ORDER BY entry_date")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.get("/api/chart_data")
def api_chart_data(start: str = "2022-01-04", end: str = "2026-06-28"):
    conn = get_db()
    df = pd.read_sql(f"""
        SELECT date, pig_grain_ratio, stock_muyuan as muyuan_close,
               stock_wens as wenshi_close, hog_futures as futures_close,
               index_xumu as hog_index_close
        FROM market_daily WHERE date >= '{start}' AND date <= '{end}'
        ORDER BY date
    """, conn)
    conn.close()
    return json.loads(df.to_json(orient='records', force_ascii=False)) if not df.empty else []

@app.get("/api/seasonality")
def api_seasonality():
    conn = get_db()
    df = pd.read_sql("""
        SELECT SUBSTR(date,6,2) as mo, pig_grain_ratio, stock_muyuan as muyuan_close
        FROM market_daily WHERE pig_grain_ratio IS NOT NULL
    """, conn)
    conn.close()
    if df.empty: return {}
    grp = df.groupby('mo')
    return {
        "months": [int(m) for m in grp.groups.keys()],
        "avg_pgr": [round(grp['pig_grain_ratio'].mean().get(str(m).zfill(2), 0), 2) for m in range(1, 13)],
        "avg_muyuan": [round(grp['muyuan_close'].mean().get(str(m).zfill(2), 0), 2) for m in range(1, 13)]
    }

if __name__ == '__main__':
    import uvicorn, json
    print('🐷 猪周期量化系统 API 已启动: http://localhost:8000')
    print('   Swagger 文档: http://localhost:8000/docs')
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
