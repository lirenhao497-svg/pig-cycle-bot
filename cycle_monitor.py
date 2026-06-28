#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
监控增强模块 cycle_monitor.py
L1 观察清单 + 右侧反转面板 + 周期阶段
供 daily_trade_monitor.py 和 scheduler.py 调用
"""
import sqlite3
import datetime

DB = r'C:\Users\ll\.doubao\chats\2026-06-25\new-chat\pig_cycle_bot\data\hog_data.db'


def init_tables(conn):
    cur = conn.cursor()
    # L1 观察清单
    cur.execute("""
        CREATE TABLE IF NOT EXISTS l1_watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT,
            pgr REAL,
            muyuan_price REAL,
            consec_55 REAL,
            status TEXT DEFAULT 'watching',
            created_at TEXT,
            updated_at TEXT
        )
    """)
    # 周期阶段
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cycle_stage (
            date TEXT PRIMARY KEY,
            pgr REAL,
            stage TEXT,
            stage_label TEXT,
            signal_a INTEGER,
            l1_active INTEGER,
            bull_count INTEGER  -- 右侧反转满足条件数 0-4
        )
    """)
    conn.commit()


def get_latest_signal(conn):
    cur = conn.cursor()
    cur.execute('SELECT date, pig_grain_ratio, signal_a_muyuan, stock_muyuan, '
                 '"pgr_below_5.5_consec", stock_wens, hog_futures '
                 'FROM market_daily_signals_v2 '
                 'WHERE date = (SELECT MAX(date) FROM market_daily_signals_v2)')
    r = cur.fetchone()
    if not r:
        cur.execute("""
            SELECT date, pig_grain_ratio, signal_a_muyuan, stock_muyuan,
                   0 as pgr_below_5.5_consec, NULL, NULL
            FROM market_daily_signals_v2
            WHERE date = (SELECT MAX(date) FROM market_daily_signals_v2)
        """)
        r = cur.fetchone()
    return r


def get_pgr_ma20(conn):
    """取最近20日猪粮比"""
    cur = conn.cursor()
    cur.execute("""
        SELECT pig_grain_ratio FROM market_daily
        WHERE pig_grain_ratio IS NOT NULL
        ORDER BY date DESC LIMIT 20
    """)
    rows = [r[0] for r in cur.fetchall()]
    if len(rows) >= 20:
        return sum(rows)/20
    return None


def get_sow_inventory(conn):
    """最新能繁母猪存栏"""
    cur = conn.cursor()
    cur.execute("SELECT month, sow_inventory FROM industry_monthly ORDER BY month DESC LIMIT 2")
    rows = cur.fetchall()
    return rows if len(rows) >= 2 else []


def get_ma60(conn, col):
    """60日均价"""
    cur = conn.cursor()
    cur.execute(f"SELECT {col} FROM market_daily WHERE {col} IS NOT NULL ORDER BY date DESC LIMIT 60")
    vals = [r[0] for r in cur.fetchall()]
    return sum(vals)/len(vals) if len(vals) >= 60 else None


# ============================================================
# 1. L1 观察清单
# ============================================================
def update_l1_watchlist(conn):
    cur = conn.cursor()
    r = get_latest_signal(conn)
    if not r:
        return
    raw_date, pgr, signal_a, price, consec55, *_ = r
    date_str = str(raw_date)[:10]
    pgr = round(pgr, 2) if pgr else None
    price = round(price, 2) if price else None
    consec55 = int(consec55) if consec55 else 0
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # L1 条件：pgr < 4.0 AND consec55 > 30
    if pgr is not None and pgr < 4.0 and consec55 > 30:
        # 检查是否已有未完成观察
        cur.execute("""
            SELECT id, entry_date FROM l1_watchlist
            WHERE status='watching' ORDER BY entry_date DESC LIMIT 1
        """)
        existing = cur.fetchone()
        if not existing:
            cur.execute("""
                INSERT INTO l1_watchlist (entry_date, pgr, muyuan_price, consec_55, status, created_at, updated_at)
                VALUES (?,?,?,?,'watching',?,?)
            """, (date_str, pgr, price, consec55, now, now))
            conn.commit()
            print(f'  L1观察: 新增 {date_str}  pgr={pgr} 牧原={price}')

    # 更新已有watch条目
    cur.execute("""
        SELECT id, entry_date, pgr, created_at FROM l1_watchlist WHERE status='watching'
    """)
    for row in cur.fetchall():
        w_id, w_date, w_pgr_old, created = row
        # 计算持有天数
        try:
            e = datetime.datetime.strptime(w_date, '%Y-%m-%d')
            t = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            days = (t - e).days
        except:
            days = 0

        if days >= 90:
            # 检查在此期间是否突破5.5
            cur.execute("""
                SELECT MAX(pig_grain_ratio) FROM market_daily
                WHERE date BETWEEN ? AND ? AND pig_grain_ratio IS NOT NULL
            """, (w_date, date_str))
            max_pgr = cur.fetchone()[0]
            new_status = 'potential_bottom' if max_pgr and max_pgr >= 5.5 else 'failed'
            cur.execute("""
                UPDATE l1_watchlist SET status=?, updated_at=? WHERE id=?
            """, (new_status, now, w_id))
            conn.commit()
            print(f'  L1观察 #{w_id} ({w_date}->{date_str}, {days}天): {new_status}  max_pgr={max_pgr}')


# ============================================================
# 2. 右侧反转面板
# ============================================================
def check_reversal_panel(conn):
    cur = conn.cursor()
    r = get_latest_signal(conn)
    if not r:
        return 0, []

    raw_date, pgr, signal_a, price, consec55, wens, futures = r
    date_str = str(raw_date)[:10]
    pgr = round(pgr, 2) if pgr else None
    signal_a = bool(signal_a)

    conditions = []
    count = 0

    # 条件1: 猪粮比突破5.0且站稳20天
    if pgr is not None and pgr > 5.0:
        # 检查过去20天是否都在5.0以上
        cur.execute("""
            SELECT COUNT(*) FROM market_daily
            WHERE date >= DATE(?, '-19 days') AND date <= ?
              AND pig_grain_ratio > 5.0 AND pig_grain_ratio IS NOT NULL
        """, (date_str, date_str))
        cnt = cur.fetchone()[0]
        if cnt >= 15:
            count += 1
            conditions.append('猪粮比>5.0站稳')
        else:
            conditions.append(f'猪粮比>5.0但未站稳({cnt}/15天)')
    else:
        conditions.append(f'猪粮比{"" if pgr is None else round(pgr,2)}<5.0')

    # 条件2: 能繁母猪存栏环比转正
    sow_data = get_sow_inventory(conn)
    if len(sow_data) >= 2:
        prev, curr = sow_data[1][1], sow_data[0][1]
        if curr and prev and curr > prev:
            count += 1
            conditions.append(f'能繁环比+{curr-prev:.0f}万头')
        else:
            conditions.append(f'能繁环比{curr-prev:.0f}万头(未转正)' if curr and prev else '能繁数据不足')
    else:
        conditions.append('能繁数据不足')

    # 条件3: 牧原站上60日均线
    ma60 = get_ma60(conn, 'stock_muyuan')
    if price is not None and ma60 is not None:
        if price > ma60:
            count += 1
            conditions.append(f'牧原>{ma60:.2f}(站上60日)')
        else:
            conditions.append(f'牧原{price}<{ma60:.2f}(未站上60日)')
    else:
        conditions.append('股价数据不足')

    # 条件4: signal_a触发且pgr在5.0-6.0
    if signal_a and pgr is not None and 5.0 <= pgr <= 6.0:
        count += 1
        conditions.append(f'signal_a+5.0-6.0')
    else:
        conditions.append(f'signal_a={signal_a} pgr={pgr}')

    print(f'\n  右侧反转面板: {count}/4')
    for c in conditions:
        print(f'    - {c}')

    return count, conditions


# ============================================================
# 3. 周期阶段判断
# ============================================================
def get_cycle_stage(pgr, signal_a, l1_active_flag=False):
    if pgr is None:
        return 'unknown', '数据不足'

    if pgr < 4.0:
        stage = 'deep_loss'
        label = '深度亏损期'
        action = '只做空/空仓，不做多'
    elif pgr < 5.0:
        stage = 'extreme_low'
        label = '极端低位'
        action = '策略G做空有效，L1观察中'
    elif pgr < 6.0:
        stage = 'oscillation'
        label = '震荡陷阱'
        action = '多空都不做，等待极端位置'
    elif pgr < 7.0:
        stage = 'weak_neutral'
        label = '中性偏弱'
        action = '观望'
    else:
        stage = 'high_decline'
        label = '高位回落'
        action = '策略G做空'

    return stage, f'{label}（{action}）'


def update_cycle_stage(conn):
    cur = conn.cursor()
    r = get_latest_signal(conn)
    if not r:
        return
    raw_date, pgr, signal_a, price, *_ = r
    date_str = str(raw_date)[:10]
    pgr = round(pgr, 2) if pgr else None
    signal_a = bool(signal_a)

    # 检查 L1 是否在观察中
    cur.execute("SELECT COUNT(*) FROM l1_watchlist WHERE status='watching'")
    l1_active = cur.fetchone()[0] > 0

    # 反转面板
    bull_count, _ = check_reversal_panel(conn)
    stage, stage_label = get_cycle_stage(pgr, signal_a, l1_active)

    cur.execute("""
        INSERT OR REPLACE INTO cycle_stage (date, pgr, stage, stage_label, signal_a, l1_active, bull_count)
        VALUES (?,?,?,?,?,?,?)
    """, (date_str, pgr, stage, stage_label, 1 if signal_a else 0, 1 if l1_active else 0, bull_count))
    conn.commit()

    print(f'\n  周期阶段: {stage_label}')
    print(f'  反转信号: {bull_count}/4')


def run_cycle_monitor():
    conn = sqlite3.connect(DB)
    init_tables(conn)
    update_l1_watchlist(conn)
    update_cycle_stage(conn)
    conn.close()


if __name__ == '__main__':
    run_cycle_monitor()
