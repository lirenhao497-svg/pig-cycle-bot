#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
猪周期 - 实盘监控 (v2.0 定稿版)
策略：signal_a_muyuan + (pgr>7.0 或 pgr<5.0) → 清仓避险
历史：11/12笔盈利，92.3%胜率，平均避开+6.89%下跌

信号触发 → Bark推送写入 daily_trade_log + cycle_stage
"""
import sqlite3
import datetime

BARK_URL = "https://api.day.app/pxQmPaqfrDSgwRsCNxptUC/"
DB = r'C:\Users\ll\.doubao\chats\2026-06-25\new-chat\pig_cycle_bot\data\hog_data.db'


def get_latest_signal(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT date, pig_grain_ratio, signal_a_muyuan,
               stock_muyuan, pgr_golden_cross, muyuan_above_ma20, muyuan_vol_contract
        FROM market_daily_signals_v2
        WHERE date = (SELECT MAX(date) FROM market_daily_signals_v2)
    """)
    return cur.fetchone()


def get_extra_prices(conn, date_str):
    cur = conn.cursor()
    cur.execute("SELECT stock_wens, hog_futures FROM market_daily WHERE date=?", (date_str,))
    return cur.fetchone() or (None, None)


def get_yr_stats(conn, year):
    cur = conn.cursor()
    cur.execute("SELECT signal_a_muyuan, pig_grain_ratio FROM market_daily_signals_v2 WHERE date>=? ORDER BY date",
                (f"{year}-01-01",))
    rows = cur.fetchall()
    total = len(rows)
    triggered = sum(1 for sig, pgr in rows if sig and pgr and (pgr > 7.0 or pgr < 5.0))
    return total, triggered, total - triggered


def pgr_desc(pgr):
    if pgr is None: return "无数据", ""
    if pgr < 4.0:   return "深度亏损", "🔴"
    elif pgr < 5.0: return "极端低位", "🟠"
    elif pgr < 6.0: return "偏弱",     "🟡"
    elif pgr < 7.0: return "中性",     "🟢"
    else:           return "高位",     "🔵"


def ensure_log_table(conn):
    cur = conn.cursor()
    cur.execute("""
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
        )
    """)
    conn.commit()


def push_bark(title, body, max_len=400):
    import requests
    if len(body) > max_len:
        body = body[:max_len] + "..."
    url = BARK_URL.rstrip("/")
    params = {"title": title, "body": body, "group": "猪周期",
              "sound": "alert", "icon": "https://cdn-icons-png.flaticon.com/128/3094/3094966.png"}
    try:
        resp = requests.get(url, params=params, timeout=10)
        return resp
    except Exception as e:
        print(f"  Bark 推送失败: {e}")
        return None


def make_report(date_str, pgr, signal_a, price, wenshi, futures,
                interval_label, need_action, mo):
    """生成报告 + Bark 内容。need_action: 是否执行清仓避险"""
    desc, emoji = pgr_desc(pgr)
    pgr_line = f"猪粮比 {pgr:.2f}（{desc}）" if pgr is not None else "猪粮比 无数据"

    # 价格行
    parts = []
    if price is not None: parts.append(f"牧原 {price:.2f}")
    if wenshi is not None: parts.append(f"温氏 {wenshi:.2f}")
    if futures is not None: parts.append(f"期货 {futures:.0f}")
    price_str = " | ".join(parts) if parts else "--"

    now = datetime.datetime.now()
    yr = now.year
    total_d, trig_d, wait_d = get_yr_stats(None, yr)
    yr_line = f"\n{yr}年: 已避险{trig_d}次 | 空仓{wait_d}天"

    # 月份标签
    mo_advice = ""
    if mo == 4 or mo == 12:
        mo_advice = " ★ 本窗口为最佳窗口"
    elif mo == 8:
        mo_advice = " ⚠ 8月需严格过滤(前20日涨>8%才操作)"

    if need_action:
        title = f"🚨 猪周期：清仓避险"
        body = (
            f"📊 猪周期日报 | {date_str}{mo_advice}\n\n"
            f"🚨 清仓避险信号！\n"
            f" {pgr_line}\n"
            f" signal_a_muyuan：True\n\n"
            f"📈 关键价格\n {price_str}\n\n"
            f"💡 操作：卖出牧原/温氏/畜牧ETF\n"
            f"      转现金/国债/货币基金\n"
            f"      持有20天或直到信号解除\n\n"
            f"📊 历史表现\n"
            f" 胜率：92.3%（11/12）| 平均：+6.89%\n"
            f" 最大亏损：-1.06% | 夏普：4.35{yr_line}\n\n"
            f"⚠️ 夏季做多/春节后做空等已验证无效，请勿尝试"
        )
        advice = (
            f"【清仓避险】{date_str}\n"
            f"{pgr_line}\n"
            f"signal_a_muyuan：True\n"
            f"操作：卖出持仓，转货币基金，持有20天或信号解除\n"
            f"历史胜率：92.3%（{yr}年已触发{trig_d}次）"
        )

    elif signal_a and pgr is not None and 5.0 <= pgr <= 7.0:
        title = f"⚠️ 猪周期：信号触发但震荡陷阱"
        body = (
            f"📊 猪周期日报 | {date_str}\n\n"
            f"⚠️ signal_a 触发但猪粮比在震荡陷阱\n"
            f" {pgr_line}（5.0~7.0 区间）\n"
            f" 策略G在该区间不做操作\n\n"
            f"📈 关键价格\n {price_str}\n\n"
            f"💡 建议：空仓观望，等待极端位置{yr_line}\n\n"
            f"⚠️ 夏季做多/春节后做空等已验证无效，请勿尝试"
        )
        advice = (
            f"【震荡陷阱】{date_str}\n"
            f"{pgr_line}\n"
            f"signal_a_muyuan：True（5.0-7.0 观望区间）\n"
            f"建议：空仓等待"
        )

    else:
        title = f"🟢 猪周期：无信号"
        body = (
            f"📊 猪周期日报 | {date_str}\n\n"
            f"🟢 无信号，空仓等待\n"
            f" {pgr_line}\n\n"
            f"📈 关键价格\n {price_str}\n\n"
            f"💡 建议：无操作，继续等待{yr_line}\n\n"
            f"⚠️ 夏季做多/春节后做空等已验证无效，请勿尝试"
        )
        if pgr is not None:
            advice = (
                f"【无信号】{date_str}\n"
                f"猪粮比：{pgr}（{desc}）\n"
                f"signal_a_muyuan：{signal_a}\n"
                f"建议：空仓等待"
            )
        else:
            advice = f"【无信号】{date_str}\n猪粮比：无数据\n建议：空仓等待"

    return title, body, advice


def main():
    conn = sqlite3.connect(DB)
    ensure_log_table(conn)

    r = get_latest_signal(conn)
    if not r:
        print("market_daily_signals_v2 无数据")
        conn.close()
        return

    raw_date, pgr, signal_a, price, *_ = r
    date_str = str(raw_date)[:10] if raw_date else ""
    price = round(price, 2) if price else None
    pgr = round(pgr, 2) if pgr else None

    wenshi, futures = get_extra_prices(conn, date_str)
    wenshi = round(wenshi, 2) if wenshi else None
    futures = round(futures, 2) if futures else None

    # 提取月份
    try:
        mo = int(raw_date[5:7]) if raw_date else 0
    except:
        mo = 0

    # 判断
    if signal_a and pgr is not None:
        if pgr > 7.0:
            interval_label = "极端高位"; need_action = True
        elif pgr < 5.0:
            interval_label = "极端低位"; need_action = True
        else:
            interval_label = "观望区间"; need_action = False
    elif pgr is not None:
        if pgr > 7.0: interval_label = "极端高位(无信号)"
        elif pgr < 5.0: interval_label = "极端低位(无信号)"
        else: interval_label = "观望区间"
        need_action = False
    else:
        interval_label = "无数据"; need_action = False

    title, body, advice = make_report(
        date_str, pgr, signal_a, price, wenshi, futures,
        interval_label, need_action, mo
    )

    position = 0
    stop = 0
    action = "clear" if need_action else "wait"

    # 控制台
    print(advice)

    # 写入日志
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_row = (
        date_str, pgr, 1 if signal_a else 0,
        f"pgr={pgr}, {interval_label}",
        action, advice, position, stop, price, now
    )
    write_log(conn, log_row)
    print(f"\n日志已写入 daily_trade_log  |  {now}")

    # 周期监控
    print(f"\n{'='*50}")
    print("  周期监控")
    print(f"{'='*50}")
    push_body = body
    try:
        from cycle_monitor import run_cycle_monitor
        run_cycle_monitor()
        cur = conn.cursor()
        cur.execute("SELECT stage, stage_label, bull_count, l1_active FROM cycle_stage WHERE date=?", (date_str,))
        cr = cur.fetchone()
        if cr:
            stage, label, bc, l1 = cr
            l1_txt = " | L1观察" if l1 else ""
            extra = f"\n周期: {label}{l1_txt}\n反转面板: {bc}/4"
            if len(push_body) + len(extra) <= 350:
                push_body += extra
    except Exception as e:
        print(f"  周期监控异常: {e}")

    # Bark 推送
    print(f"\n--- Bark 推送 ---")
    resp = push_bark(title, push_body)
    if resp:
        print(f"  HTTP {resp.status_code}  {resp.json().get('message','')[:40]}")
    print(f"  body: {len(push_body)} 字")
    if need_action:
        print(f"  ⚠️ 请关注手机通知，今日需要操作！")

    conn.close()


def ensure_log_table(conn):
    cur = conn.cursor()
    cur.execute("""
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
        )
    """)
    conn.commit()


def write_log(conn, row):
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO daily_trade_log
            (date, pig_grain_ratio, signal_a_muyuan, interval_label,
             action, advice, position_pct, stop_loss_pct, stock_price, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, row)
    conn.commit()


def get_yr_stats(conn, year):
    if conn is None:
        conn2 = sqlite3.connect(DB)
        cur = conn2.cursor()
        cur.execute("SELECT signal_a_muyuan, pig_grain_ratio FROM market_daily_signals_v2 WHERE date>=? ORDER BY date",
                    (f"{year}-01-01",))
        rows = cur.fetchall()
        total = len(rows)
        triggered = sum(1 for sig, pgr in rows if sig and pgr and (pgr > 7.0 or pgr < 5.0))
        conn2.close()
        return total, triggered, total - triggered
    cur = conn.cursor()
    cur.execute("SELECT signal_a_muyuan, pig_grain_ratio FROM market_daily_signals_v2 WHERE date>=? ORDER BY date",
                (f"{year}-01-01",))
    rows = cur.fetchall()
    total = len(rows)
    triggered = sum(1 for sig, pgr in rows if sig and pgr and (pgr > 7.0 or pgr < 5.0))
    return total, triggered, total - triggered


def run_trade_monitor():
    main()


if __name__ == "__main__":
    main()
