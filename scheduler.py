# -*- coding: utf-8 -*-
"""
定时任务调度器
统一管理所有定时任务
"""
import sys
import os
import time
import urllib.parse
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fetch.price_service import PigPriceService
from fetch.futures import FuturesFetcher
from fetch.piglet_price import PigletPriceFetcher
from fetch.piglet_price_cpcti import PigletPriceCpctiFetcher
from storage.db import HogDatabase
from models.schema import DailySnapshot, MarketDailyRow
from config import DB_PATH
from fetch.stock_price import fetch_all_stocks
from daily_trade_monitor import run_trade_monitor
from simulate_trading import run_simulate_trading
from cycle_monitor import run_cycle_monitor
from utils.logger import get_logger

logger = get_logger("scheduler")


class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        # 确保控制台能输出中文和emoji
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

        self.db = HogDatabase()
        self.price_service = PigPriceService()
        self.futures_fetcher = FuturesFetcher()
        self.piglet_fetcher = PigletPriceFetcher()
        self.piglet_fetcher_cpcti = PigletPriceCpctiFetcher()

    def task_daily_price(self):
        """每日任务:抓取价格数据并存库"""
        print(f"\n{'='*50}")
        print(f"  [1/5] 抓取生猪价格数据")
        print(f"{'='*50}")

        start_time = time.time()

        # 使用统一价格服务(自动降级)
        prices = self.price_service.get_daily_prices()
        source = self.price_service.get_active_source()

        if not prices:
            print("  ❌ 所有数据源都失败了!")
            logger.error("所有数据源抓取失败")
            return False

        print(f"  ✅ 数据源:{source}")
        print(f"  ✅ 成功抓取 {len(prices)} 条价格数据")

        # 存入分省价格表
        success_count = 0
        for p in prices:
            if self.db.insert_pig_price(p):
                success_count += 1

        print(f"  ✅ 成功写入数据库 {success_count} 条")

        # 计算统计信息
        stats = self.price_service.get_price_stats(prices)

        # 抓取饲料价格(玉米、豆粕)
        print(f"\n{'='*50}")
        print(f"  [2/5] 抓取饲料价格数据")
        print(f"{'='*50}")

        feed_price = self.price_service.get_feed_price()
        corn_price = None
        soybean_meal_price = None

        if feed_price:
            corn_price = feed_price.corn_price
            soybean_meal_price = feed_price.soybean_meal_price
            print(f"  ✅ 玉米:{corn_price} 元/公斤")
            print(f"  ✅ 豆粕:{soybean_meal_price} 元/公斤")
            # 存入饲料价格独立表
            self.db.insert_feed_price(datetime.now(), corn_price, soybean_meal_price)

            # 计算猪粮比
            if corn_price and corn_price > 0:
                pig_grain_ratio = round(stats.get('avg_price', 0) / corn_price, 2)
                print(f"  📊 猪粮比:{pig_grain_ratio} : 1")
        else:
            print("  ⚠️  饲料价格抓取失败")

        # 记录数据源状态
        duration = time.time() - start_time
        self.db.log_source_status(
            source_name=source,
            data_type="pig_price",
            success=True,
            duration=duration,
            records_count=len(prices)
        )

        # 展示结果
        print(f"\n  📊 今日数据:")
        print(f"     全国均价:{stats.get('avg_price')} 元/公斤")
        if stats.get('has_province_data'):
            print(f"     最高价:{stats['max_price']} 元/公斤({stats['max_province']})")
            print(f"     最低价:{stats['min_price']} 元/公斤({stats['min_province']})")
            print(f"     价差:{stats['spread']} 元/公斤")
            print(f"     覆盖省份:{stats['province_count']} 个")

        # 保存统计信息,供后面的snapshot用
        self._last_stats = stats
        self._last_corn_price = corn_price
        self._last_meal_price = soybean_meal_price

        # 先保存每日快照(不含期货价格,期货成功后再更新)
        snapshot = DailySnapshot(
            date=datetime.now(),
            pig_price=stats.get('avg_price'),
            max_price=stats.get('max_price'),
            max_price_province=stats.get('max_province'),
            min_price=stats.get('min_price'),
            min_price_province=stats.get('min_province'),
            price_spread=stats.get('spread'),
            corn_price=corn_price,
            soybean_meal_price=soybean_meal_price
        )
        self.db.save_daily_snapshot(snapshot)

        return True

    def task_daily_futures(self):
        """每日任务:抓取期货数据"""
        print(f"\n{'='*50}")
        print(f"  [3/5] 抓取生猪期货数据")
        print(f"{'='*50}")

        start_time = time.time()

        futures_data = self.futures_fetcher.fetch_main_contract()

        if not futures_data:
            print("  ❌ 期货数据抓取失败!")
            logger.error("期货数据抓取失败")
            self._last_futures_price = None
            return False

        # 存入数据库
        self.db.insert_futures(futures_data)

        duration = time.time() - start_time
        self.db.log_source_status(
            source_name="东方财富网",
            data_type="futures",
            success=True,
            duration=duration,
            records_count=1
        )

        print(f"  ✅ 合约:{futures_data.contract}")
        print(f"  ✅ 最新价:{futures_data.close_price} 元/吨")
        print(f"  📈 涨跌:{futures_data.change}({futures_data.change_pct}%)")
        print(f"  📊 成交量:{futures_data.volume} 手")

        # 保存期货价格,供snapshot用
        self._last_futures_price = futures_data.close_price

        # 计算猪粮比和猪料比
        pig_grain_ratio = None
        pig_feed_ratio = None
        pig_price = self._last_stats.get('avg_price')
        if pig_price and self._last_corn_price and self._last_corn_price > 0:
            pig_grain_ratio = round(pig_price / self._last_corn_price, 2)
        corn = self._last_corn_price or 0
        meal = self._last_meal_price or 0
        feed_cost = corn * 0.6 + meal * 0.25
        if pig_price and feed_cost > 0:
            pig_feed_ratio = round(pig_price / feed_cost, 2)

        # 更新每日快照中的期货和比值字段(仅更新,不覆盖已有数据)
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.db.update_daily_snapshot_futures(
            date_str=today_str,
            lh_futures=futures_data.close_price,
            pig_grain_ratio=pig_grain_ratio,
            pig_feed_ratio=pig_feed_ratio
        )

        return True

    def task_piglet_price(self):
        """每日任务:抓取仔猪价格(搜猪网,三元+外三元)"""
        print(f"\n{'='*50}")
        print(f"  [猪仔] 抓取仔猪价格数据")
        print(f"{'='*50}")

        start_time = time.time()
        inserted_any = False

        # 1. 三元仔猪
        piglet_3way = self.piglet_fetcher.fetch_latest_3way()
        if piglet_3way:
            self.db.insert_piglet_price(piglet_3way)
            print(f"  ✅ 三元仔猪:{piglet_3way.date.strftime('%Y-%m-%d')} → {piglet_3way.price} 元/头")
            inserted_any = True

        # 2. 外三元仔猪
        piglet_cross = self.piglet_fetcher.fetch_latest_crossbred()
        if piglet_cross:
            self.db.insert_piglet_price(piglet_cross)
            print(f"  ✅ 外三元仔猪:{piglet_cross.date.strftime('%Y-%m-%d')} → {piglet_cross.price} 元/头")
            inserted_any = True

        duration = time.time() - start_time

        if not inserted_any:
            print("  ❌ 仔猪价格抓取失败!")
            logger.error("仔猪价格全部抓取失败")
            self.db.log_source_status(
                source_name="AKShare-搜猪网",
                data_type="piglet_price",
                success=False,
                error_msg="两个接口都返回空",
                duration=duration
            )
            return False

        # 记录状态
        self.db.log_source_status(
            source_name="AKShare-搜猪网",
            data_type="piglet_price",
            success=True,
            duration=duration,
            records_count=2 if piglet_3way and piglet_cross else 1
        )

        # 更新每日快照(加入仔猪价格)
        latest_snapshot = self.db.get_latest_snapshot()
        if latest_snapshot:
            piglet_price_3way = piglet_3way.price if piglet_3way else None
            piglet_price_cross = piglet_cross.price if piglet_cross else None
            pig_price = latest_snapshot.get("pig_price")
            corn_price = latest_snapshot.get("corn_price")
            meal_price = latest_snapshot.get("soybean_meal_price")
            pig_grain_ratio = latest_snapshot.get("pig_grain_ratio")
            pig_feed_ratio = latest_snapshot.get("pig_feed_ratio")
            # 如果之前的快照里没算上比值,在这里补算
            if pig_grain_ratio is None and pig_price and corn_price and corn_price > 0:
                pig_grain_ratio = round(pig_price / corn_price, 2)
            if pig_feed_ratio is None and pig_price:
                feed_cost = (corn_price or 0) * 0.6 + (meal_price or 0) * 0.25
                if feed_cost > 0:
                    pig_feed_ratio = round(pig_price / feed_cost, 2)
            snapshot = DailySnapshot(
                date=datetime.strptime(latest_snapshot["date"], "%Y-%m-%d"),
                pig_price=pig_price,
                lh_futures=latest_snapshot.get("lh_futures"),
                max_price=latest_snapshot.get("max_price"),
                max_price_province=latest_snapshot.get("max_price_province"),
                min_price=latest_snapshot.get("min_price"),
                min_price_province=latest_snapshot.get("min_price_province"),
                price_spread=latest_snapshot.get("price_spread"),
                corn_price=corn_price,
                soybean_meal_price=meal_price,
                piglet_price_3way=piglet_price_3way,
                piglet_price_crossbred=piglet_price_cross,
                pig_grain_ratio=pig_grain_ratio,
                pig_feed_ratio=pig_feed_ratio
            )
            self.db.save_daily_snapshot(snapshot)

        # 3. 正大猪博士仔猪(元/公斤)
        print(f"  🆕 正大猪博士仔猪(元/公斤)")
        cpcti_rows = self.piglet_fetcher_cpcti.fetch_all()
        cpcti_inserted = 0
        cpcti_latest = None
        for item in cpcti_rows:
            self.db.insert_piglet_price(item)
            cpcti_inserted += 1
            if cpcti_latest is None or item.date > cpcti_latest.date:
                cpcti_latest = item
        print(f"  ✅ 正大仔猪:{cpcti_inserted} 条(含历史)")
        if cpcti_latest:
            print(f"     最新:{cpcti_latest.date.strftime('%Y-%m-%d')} → {cpcti_latest.price} 元/公斤")

        # 统计
        total_3way = self.db.get_piglet_total_records("三元")
        total_cross = self.db.get_piglet_total_records("外三元")
        total_cpcti = self.db.get_piglet_total_records("仔猪(正大)")
        print(f"  📊 三元仔猪 {total_3way} 条 | 外三元 {total_cross} 条 | 正大仔猪 {total_cpcti} 条")

        # 仔猪价格报警检查(三元仔猪)
        self._check_piglet_alert(piglet_3way)

        return True

    def task_daily_stock(self):
        """每日任务：抓取A股股票数据（牧原002714、温氏300498）"""
        print(f"\n{'='*50}")
        print(f"  [股票] 抓取股票行情数据")
        print(f"{'='*50}")

        start_time = time.time()
        today = datetime.now().strftime("%Y-%m-%d")
        today_compact = datetime.now().strftime("%Y%m%d")

        results = fetch_all_stocks(today_compact)

        if not results:
            print("  ⚠️ 今日无股票数据（非交易日或API无响应）")
            self.db.log_source_status(
                source_name="东方财富-股票",
                data_type="stock",
                success=False,
                duration=time.time() - start_time
            )
            return False

        # 写入数据库
        inserted = 0
        for r in results:
            ok = self.db.insert_stock_history(
                date_str=r["date"],
                code=r["code"],
                name=r["name"],
                open_price=r["open"],
                close_price=r["close"],
                high=r["high"],
                low=r["low"],
                volume=r["volume"],
                amount=r["amount"],
                amplitude=r["amplitude"],
                change_pct=r["change_pct"],
                change_amount=r["change_amount"],
                turnover=r["turnover"]
            )
            if ok:
                inserted += 1

        # 更新 last stock 价格供 monitor 使用
        if results:
            for r in results:
                if r["code"] == "002714":
                    self._last_stats["stock_muyuan"] = r["close"]
                    break

        duration = time.time() - start_time
        self.db.log_source_status(
            source_name="东方财富-股票",
            data_type="stock",
            success=True,
            duration=duration,
            records_count=inserted
        )

        print(f"  ✅ 股票数据入库：{inserted}/{len(results)} 条")
        return True

    def _check_piglet_alert(self, latest: "PigletPrice"):
        """检查仔猪价格是否跌破20日均线,触发Bark推送"""
        if not latest:
            return

        category = latest.category
        history = self.db.get_piglet_price_history(category, days=20)
        if len(history) < 20:
            # 数据还不够计算20日均线
            return

        prices = [h["price"] for h in history]
        ma20 = sum(prices) / len(prices)
        current = latest.price

        if current < ma20:
            # 触发报警
            pct = round((ma20 - current) / ma20 * 100, 1)
            title = f"仔猪价格跌破20日均线"
            body = (
                f"{category}仔猪 {latest.date.strftime('%Y-%m-%d')}\n"
                f"当前价:{current} 元/头\n"
                f"20日均线:{round(ma20, 1)} 元/头\n"
                f"偏离:-{pct}%"
            )

            bark_key = "pxQmPaqfrDSgwRsCNxptUC"
            url = f"https://api.day.app/{bark_key}/{urllib.parse.quote(title)}"
            try:
                import requests
                requests.get(url, params={"body": body, "group": "猪周期", "sound": "alert", "icon": "https://cdn-icons-png.flaticon.com/128/3094/3094966.png"}, timeout=5)
                print(f"  🔔 Bark报警已发送:{category}仔猪跌破20日均线(-{pct}%)")
                logger.info(f"Bark报警已发送:{category}仔猪 {current}<MA20({round(ma20,1)}), 偏离{pct}%")
            except Exception as e:
                logger.warning(f"Bark报警发送失败: {e}")

    def task_daily_report(self):
        """每日任务:生成简单日报"""
        print(f"\n{'='*50}")
        print(f"  [4/5] 生成每日数据汇总")
        print(f"{'='*50}")

        # 获取最新快照
        latest = self.db.get_latest_snapshot()
        if not latest:
            print("  ⚠️  暂无数据")
            return False

        print(f"  📅 日期:{latest['date']}")
        print(f"  💰 全国生猪均价:{latest['pig_price']} 元/公斤")

        if latest.get('max_price'):
            print(f"  📈 最高价:{latest['max_price']} 元/公斤({latest['max_price_province']})")
            print(f"  📉 最低价:{latest['min_price']} 元/公斤({latest['min_price_province']})")
            print(f"  📊 价差:{latest['price_spread']} 元/公斤")

        # 期货数据
        if latest.get('lh_futures'):
            futures = self.db.get_latest_futures()
            if futures:
                print(f"\n  📈 生猪期货({futures['contract']}):")
                print(f"     最新价:{futures['close_price']} 元/吨")
                print(f"     涨跌:{futures['change']}({futures['change_pct']}%)")
                print(f"     成交量:{futures['volume']} 手")

        # 饲料价格和猪粮比
        if latest.get('corn_price'):
            print(f"\n  🌽 玉米:{latest['corn_price']} 元/公斤")
            print(f"  🫘 豆粕:{latest['soybean_meal_price']} 元/公斤")

            # 猪粮比 + 猪料比(优先从数据库读已算好的值)
            pig_grain_ratio = latest.get("pig_grain_ratio")
            pig_feed_ratio = latest.get("pig_feed_ratio")
            if pig_grain_ratio is None and latest.get('pig_price') and latest['corn_price'] > 0:
                pig_grain_ratio = round(latest['pig_price'] / latest['corn_price'], 2)
            if pig_feed_ratio is None and latest.get('pig_price') and latest['corn_price'] and latest['soybean_meal_price']:
                pig_feed_ratio = round(latest['pig_price'] / (latest['corn_price'] * 0.6 + latest['soybean_meal_price'] * 0.25), 2)

            if pig_grain_ratio:
                print(f"  📐 猪粮比:{pig_grain_ratio} : 1")
                # 判断盈亏
                if pig_grain_ratio >= 6.0:
                    print(f"  💚 猪粮比:高利润")
                elif pig_grain_ratio >= 5.5:
                    print(f"  💚 猪粮比:微利")
                elif pig_grain_ratio >= 5.0:
                    print(f"  🟡 猪粮比:盈亏平衡附近")
                else:
                    print(f"  🔴 猪粮比:深度亏损")
            if pig_feed_ratio:
                print(f"  📐 猪料比:{pig_feed_ratio} : 1")

        # 最近7天趋势
        history_7 = self.db.get_last_7days()
        if len(history_7) >= 2:
            first = history_7[0]['price']
            last = history_7[-1]['price']
            change = round(last - first, 2)
            change_pct = round(change / first * 100, 2)
            direction = "上涨" if change > 0 else "下跌" if change < 0 else "持平"
            print(f"\n  📈 近7天{direction}:{change} 元/公斤({change_pct}%)")

        return True

    def task_data_summary(self):
        """任务:数据积累情况汇总"""
        print(f"\n{'='*50}")
        print(f"  [5/5] 数据积累情况")
        print(f"{'='*50}")

        # 统计总数据量
        self.db.cur.execute("SELECT COUNT(*) FROM pig_price")
        price_count = self.db.cur.fetchone()[0]

        self.db.cur.execute("SELECT COUNT(DISTINCT date) FROM pig_price")
        day_count = self.db.cur.fetchone()[0]

        self.db.cur.execute("SELECT COUNT(*) FROM futures_data")
        futures_count = self.db.cur.fetchone()[0]

        self.db.cur.execute("SELECT COUNT(*) FROM source_status")
        status_count = self.db.cur.fetchone()[0]

        print(f"  📦 分省价格数据:{price_count} 条")
        print(f"  📅 累计天数:{day_count} 天")
        print(f"  📈 期货数据:{futures_count} 条")
        print(f"  📝 抓取记录:{status_count} 次")

        # 数据源健康度
        health = self.db.get_source_health("正大猪博士", days=7)
        print(f"  💚 数据源健康度:{health['success_rate']}(近7天)")

        # 饲料 + 仔猪统计
        self.db.cur.execute("SELECT COUNT(*) FROM feed_price")
        feed_count = self.db.cur.fetchone()[0]
        piglet_3 = self.db.get_piglet_total_records("三元")
        piglet_c = self.db.get_piglet_total_records("外三元")

        print(f"  \U0001f33d 饲料价格:{feed_count} 条")
        print(f"  \U0001f437 仔猪价格:三元{piglet_3}条 + 外三元{piglet_c}条")

        return True

    def _save_daily_monitor(self):
        """将当日数据汇聚到 daily_monitor 表。
        只有当日7个字段全部有效才写入,任一字段为空则跳过(如节假日无股价)。
        """
        from storage.db import HogDatabase
        db = HogDatabase()
        db.init_daily_monitor()

        today = datetime.now().strftime("%Y-%m-%d")
        pig_price_kg = getattr(self, '_last_stats', {}).get('avg_price')

        # 从 daily_snapshot 取猪价 + 比值
        latest = db.get_latest_snapshot()
        if latest and latest.get("date") == today:
            pig_price_kg = pig_price_kg or latest.get("pig_price")
            pig_grain_ratio = latest.get("pig_grain_ratio")
            pig_feed_ratio = latest.get("pig_feed_ratio")
        else:
            pig_grain_ratio = None
            pig_feed_ratio = None

        # 从 market_daily 取期货+个股+指数(单位已是元/公斤)
        hog_futures = None
        stock_muyuan = None
        index_xumu = None
        db.cur.execute(
            "SELECT hog_futures, stock_muyuan, index_xumu FROM market_daily WHERE date=?",
            (today,))
        row = db.cur.fetchone()
        if row:
            hog_futures = row[0]
            stock_muyuan = row[1]
            index_xumu = row[2]

        # 核心规则:任一字段为 None 就跳过
        fields = [pig_price_kg, hog_futures, stock_muyuan,
                  pig_grain_ratio, pig_feed_ratio, index_xumu]
        if any(v is None for v in fields):
            missing = []
            names = ["猪价", "期货", "牧原股价", "猪粮比", "猪料比", "畜牧指数"]
            for name, val in zip(names, fields):
                if val is None:
                    missing.append(name)
            print(f"    daily_monitor: 跳过(缺少: {', '.join(missing)})")
            db.close()
            return

        ok = db.save_daily_monitor(
            date_str=today,
            pig_price_kg=pig_price_kg,
            hog_futures=hog_futures,
            stock_muyuan=stock_muyuan,
            pig_grain_ratio=pig_grain_ratio,
            pig_feed_ratio=pig_feed_ratio,
            index_xumu=index_xumu
        )
        if ok:
            db.cur.execute(
                "SELECT pig_price_head, pig_price_kg, hog_futures, stock_muyuan, "
                "pig_grain_ratio, pig_feed_ratio, index_xumu "
                "FROM daily_monitor WHERE date=?", (today,))
            r = db.cur.fetchone()
            if r:
                print(f"    daily_monitor: 头价={r[0]}, 均重价={r[1]}, 期货={r[2]}, 牧原={r[3]}, "
                      f"猪粮比={r[4]}, 猪料比={r[5]}, 指数={r[6]}")
        db.close()

    def _check_sow_inventory_update(self):
        """检查能繁母猪存栏是否需要更新。每月1号提示录入上月数据。"""
        from storage.db import HogDatabase
        db = HogDatabase()
        now = datetime.now()
        latest = db.get_latest_sow_inventory()

        print(f"\n{'='*50}")
        print(f"  [7/7] 能繁母猪存栏")
        print(f"{'='*50}")

        if latest:
            print(f"  最新: {latest['month']} -> {latest['sow_inventory']} 万头")
        else:
            print(f"  暂无数据")

        if now.day == 1:
            from datetime import timedelta
            last_month = (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
            if not latest or latest["month"] != last_month:
                print(f"  ! 提示:{last_month} 数据待录入")
                print(f"  请运行: python update_sow.py {last_month} <存栏量(万头)>")
        else:
            print(f"  下次检查: {now.year}-{now.month:02d}-01")

        db.close()

    def run_all_daily(self):
        """执行所有每日任务"""
        print("\n" + "="*50)
        print("🐷  猪周期数据系统 - 每日任务")
        print("="*50)
        print(f"⏰ 执行时间:{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # 1. 抓取猪价
            self.task_daily_price()

            # 2. 抓取期货
            self.task_daily_futures()

            # 3. 抓取仔猪价格
            self.task_piglet_price()

            # 4. 抓取股票数据
            print(f"\n{'='*50}")
            print(f"  [4/12] 抓取股票行情")
            print(f"{'='*50}")
            self.task_daily_stock()

            # 5. 生成汇总
            self.task_daily_report()

            # 6. 数据统计
            self.task_data_summary()

            # 7. 汇聚到 daily_monitor 表
            self._save_daily_monitor()

            # 8. 检查能繁母猪存栏是否需要更新
            self._check_sow_inventory_update()

            # 9. 交易监控
            print(f"\n{'='*50}")
            print(f"  [9/12] 实盘交易监控")
            print(f"{'='*50}")
            run_trade_monitor()

            # 10. 模拟盘
            print(f"\n{'='*50}")
            print(f"  [10/12] 模拟盘")
            print(f"{'='*50}")
            run_simulate_trading()

            # 11. 周期监控
            print(f"\n{'='*50}")
            print(f"  [11/12] 周期监控(L1+反转面板+周期阶段)")
            print(f"{'='*50}")
            run_cycle_monitor()

            # 12. 更新 market_daily(让前端看到当天数据)
            self._update_market_daily()

        except Exception as e:
            print(f"\n❌ 执行出错:{e}")
            logger.error(f"每日任务执行出错: {e}", exc_info=True)

        finally:
            self.price_service.close()
            self.futures_fetcher.close()
            self.piglet_fetcher.close()
            self.piglet_fetcher_cpcti.close()
            self.db.close()

        print("\n" + "="*50)
        print("✅  每日任务执行完成")
        print("="*50)
        print(f"💾 数据文件:data/hog_data.db")
        print(f"📋 日志文件:logs/app.log")
        print("="*50 + "\n")

    # ========== market_daily 更新 ==========
    def _update_market_daily(self):
        """
        将当日数据合并写入 market_daily 表,供前端 api/latest 读取。
        只在爬虫完成数据抓取后调用,确保当天数据可见。
        """
        print(f"\n{'='*50}")
        print(f"  [11/11] 更新 market_daily(同步到前端)")
        print(f"{'='*50}")

        import sqlite3
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d")

            # 从 daily_snapshot 取当天数据
            cur.execute("""
                SELECT pig_price, lh_futures, corn_price, soybean_meal_price,
                       pig_grain_ratio, pig_feed_ratio
                FROM daily_snapshot WHERE date = ?
            """, (today,))
            snap = cur.fetchone()

            if not snap:
                print(f"  ⚠️ {today} snapshot 不存在,跳过")
                conn.close()
                return

            pig_price_kg = snap[0]
            lh_futures = snap[1]  # 元/吨
            pig_grain_ratio = snap[4]
            pig_feed_ratio = snap[5]

            # 期货转元/公斤
            hog_futures_kg = round(lh_futures / 1000, 2) if lh_futures else None

            # 从 stock_history 取当天股票数据(盘后才有)
            stock_muyuan = None
            stock_wens = None
            cur.execute("""
                SELECT close FROM stock_history
                WHERE date = ? AND code = '002714'
                LIMIT 1
            """, (today,))
            r = cur.fetchone()
            if r:
                stock_muyuan = r[0]

            cur.execute("""
                SELECT close FROM stock_history
                WHERE date = ? AND code = '300498'
                LIMIT 1
            """, (today,))
            r = cur.fetchone()
            if r:
                stock_wens = r[0]

            # 查询之前 day(最近一个有牧原收盘价的)的 profit_self
            cur.execute("""
                SELECT profit_self FROM market_daily
                WHERE stock_muyuan IS NOT NULL
                ORDER BY date DESC LIMIT 1
            """)
            r = cur.fetchone()
            prev_profit = r[0] if r else None

            # 写入或更新 market_daily
            # 检查是否存在当天记录
            cur.execute("SELECT COUNT(*) FROM market_daily WHERE date = ?", (today,))
            exists = cur.fetchone()[0] > 0

            if exists:
                # 更新只合并非空字段(不覆盖已有股票数据)
                updates = []
                params = []
                if pig_grain_ratio is not None:
                    updates.append("pig_grain_ratio = ?")
                    params.append(pig_grain_ratio)
                if pig_feed_ratio is not None:
                    updates.append("pig_feed_ratio = ?")
                    params.append(pig_feed_ratio)
                if hog_futures_kg is not None:
                    updates.append("hog_futures = ?")
                    params.append(hog_futures_kg)
                if stock_muyuan is not None:
                    updates.append("stock_muyuan = ?")
                    params.append(stock_muyuan)
                if stock_wens is not None:
                    updates.append("stock_wens = ?")
                    params.append(stock_wens)
                if prev_profit is not None:
                    updates.append("profit_self = ?")
                    params.append(prev_profit)

                if updates:
                    params.append(today)
                    cur.execute(f"UPDATE market_daily SET {', '.join(updates)} WHERE date = ?", params)
                    print(f"  ✅ market_daily {today} 已更新: {len(updates)} 个字段")
            else:
                # 插入新行
                cur.execute("""
                    INSERT INTO market_daily
                    (date, pig_grain_ratio, pig_feed_ratio, hog_futures,
                     stock_muyuan, stock_wens, profit_self)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    today, pig_grain_ratio, pig_feed_ratio, hog_futures_kg,
                    stock_muyuan, stock_wens, prev_profit
                ))
                print(f"  ✅ market_daily {today} 已新增")

            # 检查是否需要更新 market_daily_signals_v2
            # 如果当天已有猪粮比但 signals 表没有该日数据,补入
            cur.execute("SELECT COUNT(*) FROM market_daily_signals_v2 WHERE date = ?", (today,))
            sig_exists = cur.fetchone()[0] > 0
            if not sig_exists and pig_grain_ratio is not None:
                # 只插入核心字段,后续由 calculate_signals 补全
                cur.execute("""
                    INSERT OR IGNORE INTO market_daily_signals_v2
                    (date, pig_grain_ratio, hog_futures, stock_muyuan, stock_wens)
                    VALUES (?, ?, ?, ?, ?)
                """, (today, pig_grain_ratio, hog_futures_kg, stock_muyuan, stock_wens))
                print(f"  ✅ market_daily_signals_v2 {today} 已插入基础数据")

            conn.commit()
            conn.close()

            # 打印摘要
            print(f"  📊 猪粮比: {pig_grain_ratio}")
            print(f"  📈 期货: {hog_futures_kg} 元/公斤")
            print(f"  🏢 牧原: {stock_muyuan} 元")
            if stock_wens:
                print(f"  🏢 温氏: {stock_wens} 元")

        except Exception as e:
            logger.error(f"更新 market_daily 失败: {e}")
            print(f"  ❌ 更新 market_daily 失败: {e}")

    def run_forever(self, interval=3600):
        """持续运行模式(每小时检查一次)"""
        print("🚀 启动持续运行模式")
        print(f"⏱️  检查间隔:{interval}秒({interval//3600}小时)")
        print("💡 每天上午9点后自动执行一次")
        print()

        last_run_date = None

        while True:
            try:
                today = datetime.now().strftime("%Y-%m-%d")
                now_hour = datetime.now().hour

                # 每天只跑一次(上午9点后)
                if today != last_run_date and now_hour >= 9:
                    print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 开始执行每日任务")
                    self.run_all_daily()
                    last_run_date = today
                    print(f"\n💤 下次检查:{interval}秒后...")

                time.sleep(interval)

            except KeyboardInterrupt:
                print("\n\n👋 已停止运行")
                break
            except Exception as e:
                print(f"\n❌ 运行出错:{e}")
                logger.error(f"持续运行出错: {e}", exc_info=True)
                time.sleep(60)  # 出错后等1分钟再试


if __name__ == "__main__":
    scheduler = TaskScheduler()

    # 默认执行一次每日任务
    scheduler.run_all_daily()

    # 如果需要持续运行,取消下面注释:
    # scheduler.run_forever()
