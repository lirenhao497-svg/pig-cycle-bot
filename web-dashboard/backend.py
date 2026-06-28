#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
猪周期量化系统 - FastAPI 后端
提供 9 个 /api 接口供前端仪表盘使用
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
import json

# 基于 backend.py 所在位置，指向上一级目录的 data/hog_data.db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "data", "hog_data.db"))
app = FastAPI(title="猪周期量化系统API", version="2.0")

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "https://pig-cycle-dashboard.vercel.app"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    兜底建表：数据库文件或表不存在时自动创建核心表结构。
    Railway 部署时会调用此函数，确保表存在。
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS market_daily (
            date TEXT PRIMARY KEY,
            pig_grain_ratio REAL,
            pig_feed_ratio REAL,
            hog_futures REAL,
            index_xumu REAL,
            stock_muyuan REAL,
            stock_wens REAL,
            stock_xinxiwang REAL,
            stock_haida REAL,
            profit_self INTEGER
        );

        CREATE TABLE IF NOT EXISTS market_daily_signals_v2 (
            date TIMESTAMP PRIMARY KEY,
            pig_grain_ratio REAL,
            pig_feed_ratio REAL,
            hog_futures REAL,
            index_xumu REAL,
            stock_muyuan REAL,
            stock_wens REAL,
            stock_xinxiwang REAL,
            stock_haida REAL,
            profit_self REAL,
            pgr_ma5 REAL,
            pgr_ma10 REAL,
            pgr_ma20 REAL,
            pgr_ma5_above_ma20 INTEGER,
            pgr_golden_cross INTEGER,
            pgr_death_cross INTEGER,
            pgr_ma5_rising INTEGER,
            pgr_up_1d INTEGER,
            pgr_up_3d INTEGER,
            pgr_up_5d INTEGER,
            pgr_below_5_0_consec INTEGER,
            pgr_below_5_5_consec INTEGER,
            pgr_below_6_0_consec INTEGER,
            pgr_below_6_5_consec INTEGER,
            muyuan_ma5 REAL,
            muyuan_ma20 REAL,
            muyuan_ma60 REAL,
            muyuan_golden_cross INTEGER,
            muyuan_death_cross INTEGER,
            muyuan_above_ma20 INTEGER,
            wens_ma5 REAL,
            wens_ma20 REAL,
            wens_ma60 REAL,
            wens_golden_cross INTEGER,
            wens_death_cross INTEGER,
            wens_above_ma20 INTEGER,
            xumu_ma5 REAL,
            xumu_ma20 REAL,
            xumu_ma60 REAL,
            xumu_golden_cross INTEGER,
            xumu_death_cross INTEGER,
            xumu_above_ma20 INTEGER,
            muyuan_ret_20d REAL,
            muyuan_atr20 REAL,
            muyuan_atr60 REAL,
            muyuan_vol_contract INTEGER,
            muyuan_vol_contract_strict INTEGER,
            wens_atr20 REAL,
            wens_atr60 REAL,
            wens_vol_contract INTEGER,
            wens_vol_contract_strict INTEGER,
            xumu_atr20 REAL,
            xumu_atr60 REAL,
            xumu_vol_contract INTEGER,
            xumu_vol_contract_strict INTEGER,
            futures_ma5 REAL,
            futures_ma20 REAL,
            futures_ret_5d REAL,
            futures_golden_cross INTEGER,
            futures_death_cross INTEGER,
            signal_a_muyuan INTEGER,
            signal_b_wens INTEGER,
            signal_c_xumu INTEGER
        );

        CREATE TABLE IF NOT EXISTS cycle_stage (
            date TEXT PRIMARY KEY,
            pgr REAL,
            stage TEXT,
            stage_label TEXT,
            signal_a INTEGER,
            l1_active INTEGER,
            bull_count INTEGER
        );

        CREATE TABLE IF NOT EXISTS daily_trade_log (
            date TEXT PRIMARY KEY,
            pig_grain_ratio REAL,
            signal_a_muyuan INTEGER,
            interval_label TEXT,
            action TEXT,
            advice TEXT,
            position_pct INTEGER,
            stop_loss_pct INTEGER,
            stock_price REAL,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS sim_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT NOT NULL,
            entry_price REAL NOT NULL,
            pgr REAL,
            exit_planned TEXT,
            exit_date TEXT,
            exit_price REAL,
            profit_pct REAL,
            status TEXT DEFAULT 'open',
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS l1_watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT,
            pgr REAL,
            muyuan_price REAL,
            consec_55 REAL,
            status TEXT DEFAULT 'watching',
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS daily_snapshot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            pig_price REAL,
            lh_futures REAL,
            corn_price REAL,
            soybean_meal_price REAL,
            max_price REAL,
            max_price_province TEXT,
            min_price REAL,
            min_price_province TEXT,
            price_spread REAL,
            piglet_price_3way REAL,
            piglet_price_crossbred REAL,
            pig_grain_ratio REAL,
            pig_feed_ratio REAL
        );

        CREATE TABLE IF NOT EXISTS piglet_price (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT '三元',
            price REAL NOT NULL,
            UNIQUE(date, category)
        );
    """)

    conn.commit()
    conn.close()
    print(f"[init_db] 数据库就绪: {DB_PATH}")

# ========== 杈呭姪鍑芥暟 ==========
def compute_status(row):
    """璁＄畻褰撳墠淇″彿鐘舵€?"""
    pgr = row['pig_grain_ratio']
    sig_a = bool(row.get('pgr_golden_cross', 0)) and bool(row.get('muyuan_above_ma20', 0)) and bool(row.get('muyuan_vol_contract', 0))
    trigger = sig_a and (pgr > 7.0 or pgr < 5.0)
    if trigger:
        stage_text = '高价位' if pgr > 7.0 else '低价位'
        return "清仓避险", f"猪粮比{pgr:.2f}触发{stage_text}信号"
    elif sig_a:
        return "观望", "signal_a 触发但猪粮比在震荡区间"
    return "空仓", None


def get_cycle_stage_label(pgr):
    if pgr < 4.0: return "深度亏损"
    elif pgr < 5.0: return "极端低位"
    elif pgr < 6.0: return "偏弱"
    elif pgr < 7.0: return "中性"
    return "高位"

# ========== API 鎺ュ彛 ==========
@app.get("/api/latest")
def api_latest():
    conn = get_db()
    cur = conn.cursor()

    # 1) 鏈€鏂颁氦鏄撴棩鏁版嵁
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

    # 2) 鐚倝浠锋牸 & 浠旂尓浠锋牸
    cur.execute("SELECT pig_price FROM daily_snapshot WHERE date = ?", (latest_date,))
    snap = cur.fetchone()
    d['pig_price'] = snap['pig_price'] if snap else None

    # piglet_price 琛? category='澶栦笁鍏? 鏄厓/澶达紝category='涓夊厓' 涔熸槸鍏?澶?    # 鍓嶇 Dashboard 闇€瑕佷粩鐚环鏍煎厓/kg锛岃繖閲岀敤 category='澶栦笁鍏? 鐨勪环鏍?    cur.execute("SELECT price FROM piglet_price WHERE category=? AND date = ? ORDER BY id DESC LIMIT 1", ('澶栦笁鍏?, latest_date))
    piglet = cur.fetchone()
    d['piglet_price'] = piglet['price'] if piglet else None

    # 3) 鍛ㄦ湯/鑺傚亣鏃ュ洖閫€锛氬鏋?muyuan_close 涓?null锛屾煡涓婁竴涓氦鏄撴棩
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

    # 4) 娑ㄨ穼骞咃細瀵规瘮鍓嶄竴涓氦鏄撴棩
    # 鍥為€€鍚庯紝鍓嶄竴涓氦鏄撴棩搴斾负鍥為€€鏃ユ湡鐨勫墠涓€涓氦鏄撴棩
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

@app.on_event("startup")
def on_startup():
    init_db()


if __name__ == '__main__':
    import uvicorn
    print('馃惙 鐚懆鏈熼噺鍖栫郴缁?API 宸插惎鍔? http://localhost:8000')
    print('   Swagger 鏂囨。: http://localhost:8000/docs')
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

