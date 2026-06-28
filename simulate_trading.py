#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模拟盘脚本 simulate_trading.py
从今天起每日记录 signal_a_muyuan + 猪粮比极端 >7.0/<5.0 的做空信号
每日运行一次，检查是否需要开仓/平仓（虚拟）
"""
import sqlite3
import datetime

DB = r'C:\Users\ll\.doubao\chats\2026-06-25\new-chat\pig_cycle_bot\data\hog_data.db'


def ensure_sim_tables(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sim_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT NOT NULL,
            entry_price REAL NOT NULL,
            pgr REAL,
            exit_planned TEXT,  -- 理论平仓日 (entry + 20交易日)
            exit_date TEXT,
            exit_price REAL,
            profit_pct REAL,
            status TEXT DEFAULT 'open',  -- open / closed
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sim_daily_log (
            date TEXT PRIMARY KEY,
            open_positions INTEGER DEFAULT 0,
            signal_triggered INTEGER DEFAULT 0,
            pgr REAL,
            action TEXT,
            note TEXT,
            created_at TEXT
        )
    """)
    conn.commit()


def count_trading_days(conn, start_date, n):
    """从 start_date 起数 n 个有 stock_muyuan 值的交易日"""
    cur = conn.cursor()
    cur.execute("""
        SELECT date FROM market_daily
        WHERE date > ? AND stock_muyuan IS NOT NULL
        ORDER BY date LIMIT ?
    """, (start_date, n))
    rows = cur.fetchall()
    if len(rows) < n:
        return None
    return rows[-1][0]


def main():
    conn = sqlite3.connect(DB)
    ensure_sim_tables(conn)
    cur = conn.cursor()

    # 读取最新market_daily signals_v2
    cur.execute("""
        SELECT date, pig_grain_ratio, signal_a_muyuan, stock_muyuan
        FROM market_daily_signals_v2
        WHERE date = (SELECT MAX(date) FROM market_daily_signals_v2)
    """)
    r = cur.fetchone()
    if not r:
        print("market_daily_signals_v2 无数据")
        conn.close()
        return

    raw_date, pgr, signal_a, price = r
    date_str = str(raw_date)[:10]
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    open_pos = 0

    # 检查是否有 open 仓
    cur.execute("SELECT COUNT(*) FROM sim_positions WHERE status='open'")
    open_pos = cur.fetchone()[0]

    # 检查是否有信号
    signal_ok = signal_a and pgr is not None and (pgr > 7.0 or pgr < 5.0)

    action = 'wait'
    note = ''
    need_log = 0

    if signal_ok and price is not None:
        # 信号触发，开仓
        exit_planned = count_trading_days(conn, date_str, 20)
        if exit_planned and open_pos == 0:
            cur.execute("""
                INSERT INTO sim_positions
                    (entry_date, entry_price, pgr, exit_planned, status, created_at)
                VALUES (?, ?, ?, ?, 'open', ?)
            """, (date_str, round(price, 2), round(pgr, 2), exit_planned, now))
            conn.commit()
            action = 'short_open'
            need_log = 1
            print(f"【模拟开仓】{date_str}")
            print(f"  做空牧原 @ {price:.2f}")
            print(f"  猪粮比: {pgr}")
            print(f"  计划平仓日: {exit_planned}")
            note = f'做空@{price:.2f}, 目标{exit_planned}'
        elif open_pos > 0:
            action = 'signal_but_occupied'
            need_log = 1
            note = f'信号触发但已有{open_pos}个仓位'
            print(f"【信号触发】但已有 {open_pos} 个持仓中，跳过")
        else:
            action = 'no_exit_planned'
            need_log = 1
            note = '信号触发但20日后无数据'
    else:
        print(f"【无信号】{date_str}, 猪粮比={pgr}, signal_a={signal_a}")

    # 检查是否有到期的平仓
    cur.execute("""
        SELECT id, entry_date, entry_price, exit_planned
        FROM sim_positions
        WHERE status='open' AND exit_planned <= ?
    """, (date_str,))
    for row in cur.fetchall():
        pid, entry_date, entry_price, ep = row
        # 获取当日股价
        cur.execute("SELECT stock_muyuan FROM market_daily_signals_v2 WHERE date=?", (date_str,))
        rr = cur.fetchone()
        if rr and rr[0]:
            exit_price = rr[0]
            profit = (entry_price - exit_price) / entry_price * 100
            cur.execute("""
                UPDATE sim_positions SET
                    exit_date=?, exit_price=?, profit_pct=?, status='closed'
                WHERE id=?
            """, (date_str, round(exit_price, 2), round(profit, 2), pid))
            conn.commit()
            action = 'short_close'
            need_log = 1
            open_pos -= 1
            print(f"\n【模拟平仓】{date_str}")
            print(f"  做空 @ {entry_price:.2f} -> {exit_price:.2f}")
            print(f"  收益: {profit:+.2f}%")
            note = f'平仓@{exit_price:.2f}, 收益{profit:+.2f}%'

    # 写每日日志
    cur.execute("""
        INSERT OR REPLACE INTO sim_daily_log
            (date, open_positions, signal_triggered, pgr, action, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (date_str, open_pos, need_log, round(pgr, 2) if pgr else None, action, note, now))
    conn.commit()

    # 输出汇总
    cur.execute("""
        SELECT COUNT(*), COUNT(CASE WHEN status='open' THEN 1 END),
               COUNT(CASE WHEN status='closed' THEN 1 END),
               ROUND(AVG(CASE WHEN status='closed' THEN profit_pct END), 2)
        FROM sim_positions
    """)
    r = cur.fetchone()
    print(f"\n【模拟盘汇总】")
    print(f"  总交易: {r[0]}")
    print(f"  持仓中: {r[1]}")
    print(f"  已平仓: {r[2]}")
    if r[3]:
        print(f"  平均收益: {r[3]:+.2f}%")

    print(f"\n模拟盘日志已更新  |  {now}")
    conn.close()



def run_simulate_trading():
    """供 scheduler.py 调用的独立入口"""
    main()


if __name__ == '__main__':
    main()
