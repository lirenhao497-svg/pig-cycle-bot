# -*- coding: utf-8 -*-
"""
SQLite数据库封装

表：
1. pig_price        - 分省生猪价格（元/公斤）
2. futures_data     - 生猪期货（元/吨）
3. feed_price       - 饲料价格（玉米、豆粕，元/公斤）
4. piglet_price     - 仔猪价格（三元/外三元，元/头）
5. daily_snapshot   - 每日汇总快照（分析用，一张表搞定核心指标）
6. source_status    - 数据源监控（运维用）
"""
import sqlite3
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH, DATA_DIR
from models.schema import PigPrice, FuturesData, FeedPrice, PigletPrice, DailySnapshot
from utils.logger import get_logger

logger = get_logger("db")


class HogDatabase:
    def __init__(self):
        # 确保data目录存在
        os.makedirs(DATA_DIR, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self.cur = self.conn.cursor()
        self._init_tables()

    def _init_tables(self):
        """初始化所有表"""
        
        # 表1：分省生猪价格
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS pig_price (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                province TEXT NOT NULL,
                price REAL NOT NULL,
                UNIQUE(date, province)
            )
        """)
        
        # 表2：期货数据
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS futures_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                contract TEXT NOT NULL,
                open_price REAL,
                high_price REAL,
                low_price REAL,
                close_price REAL,
                volume INTEGER,
                amount REAL,
                prev_close REAL,
                change REAL,
                change_pct REAL,
                open_interest INTEGER,
                settlement REAL,
                UNIQUE(date, contract)
            )
        """)
        
        # 兼容旧表：增加新字段
        try:
            self.cur.execute("ALTER TABLE futures_data ADD COLUMN open_price REAL")
        except sqlite3.OperationalError:
            pass
        try:
            self.cur.execute("ALTER TABLE futures_data ADD COLUMN high_price REAL")
        except sqlite3.OperationalError:
            pass
        try:
            self.cur.execute("ALTER TABLE futures_data ADD COLUMN low_price REAL")
        except sqlite3.OperationalError:
            pass
        try:
            self.cur.execute("ALTER TABLE futures_data ADD COLUMN amount REAL")
        except sqlite3.OperationalError:
            pass
        try:
            self.cur.execute("ALTER TABLE futures_data ADD COLUMN prev_close REAL")
        except sqlite3.OperationalError:
            pass
        try:
            self.cur.execute("ALTER TABLE futures_data ADD COLUMN change REAL")
        except sqlite3.OperationalError:
            pass
        try:
            self.cur.execute("ALTER TABLE futures_data ADD COLUMN change_pct REAL")
        except sqlite3.OperationalError:
            pass
        try:
            self.cur.execute("ALTER TABLE futures_data ADD COLUMN open_interest INTEGER")
        except sqlite3.OperationalError:
            pass
        try:
            self.cur.execute("ALTER TABLE futures_data ADD COLUMN settlement REAL")
        except sqlite3.OperationalError:
            pass
        
        # 表3：每日汇总快照（分析用，一张表就能查核心指标）
        self.cur.execute("""
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
                piglet_price_crossbred REAL
            )
        """)
        
        # 兼容旧表：如果是旧版本表，增加新字段
        try:
            self.cur.execute("ALTER TABLE daily_snapshot ADD COLUMN max_price REAL")
        except sqlite3.OperationalError:
            pass  # 字段已存在
        try:
            self.cur.execute("ALTER TABLE daily_snapshot ADD COLUMN max_price_province TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            self.cur.execute("ALTER TABLE daily_snapshot ADD COLUMN min_price REAL")
        except sqlite3.OperationalError:
            pass
        try:
            self.cur.execute("ALTER TABLE daily_snapshot ADD COLUMN min_price_province TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            self.cur.execute("ALTER TABLE daily_snapshot ADD COLUMN price_spread REAL")
        except sqlite3.OperationalError:
            pass
        try:
            self.cur.execute("ALTER TABLE daily_snapshot ADD COLUMN piglet_price_3way REAL")
        except sqlite3.OperationalError:
            pass
        try:
            self.cur.execute("ALTER TABLE daily_snapshot ADD COLUMN piglet_price_crossbred REAL")
        except sqlite3.OperationalError:
            pass
        
        # 表4：数据源监控（运维用，半年后你会感谢自己）
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS source_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT NOT NULL,
                data_type TEXT NOT NULL,
                fetch_time TEXT NOT NULL,
                success INTEGER NOT NULL,
                error_msg TEXT,
                duration REAL,
                records_count INTEGER
            )
        """)
        
        self.conn.commit()
        # 表5：饲料价格（玉米/豆粕，元/公斤）
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS feed_price (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                corn_price REAL,           -- 玉米价格（元/公斤）
                soybean_meal_price REAL     -- 豆粕价格（元/公斤）
            )
        """)
        # 兼容：给旧表加字段
        try:
            self.cur.execute("ALTER TABLE feed_price ADD COLUMN corn_price REAL")
        except sqlite3.OperationalError:
            pass
        try:
            self.cur.execute("ALTER TABLE feed_price ADD COLUMN soybean_meal_price REAL")
        except sqlite3.OperationalError:
            pass
        
        # 表6：仔猪价格（搜猪网，元/头）
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS piglet_price (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT '三元',
                price REAL NOT NULL,
                UNIQUE(date, category)
            )
        """)
        # 兼容旧表：增加category字段
        try:
            self.cur.execute("ALTER TABLE piglet_price ADD COLUMN category TEXT NOT NULL DEFAULT '三元'")
        except sqlite3.OperationalError:
            pass
        try:
            self.cur.execute("DROP INDEX IF EXISTS idx_piglet_price_unique")
        except:
            pass
        try:
            self.cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_piglet_price_unique ON piglet_price(date, category)")
        except:
            pass
        
        self.conn.commit()
        logger.info("数据库初始化完成，6张表已就绪")

    # ========== 生猪价格 ==========
    
    def insert_pig_price(self, data: PigPrice) -> bool:
        """插入一条分省价格数据"""
        try:
            self.cur.execute("""
                INSERT OR REPLACE INTO pig_price (date, province, price)
                VALUES (?, ?, ?)
            """, (
                data.date.strftime("%Y-%m-%d"),
                data.province,
                data.price
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"插入猪价失败: {e}")
            return False

    def get_national_avg(self, date_str: str) -> float:
        """查询指定日期全国均价"""
        self.cur.execute("""
            SELECT AVG(price) FROM pig_price WHERE date = ?
        """, (date_str,))
        result = self.cur.fetchone()
        return result[0] if result and result[0] else 0.0

    def get_price_series(self, days: int = 30) -> list:
        """查询近N天的全国均价序列（用于分析）"""
        self.cur.execute("""
            SELECT date, AVG(price) as avg_price 
            FROM pig_price 
            GROUP BY date 
            ORDER BY date DESC 
            LIMIT ?
        """, (days,))
        return self.cur.fetchall()

    # ========== 期货数据 ==========
    
    def insert_futures(self, data: FuturesData) -> bool:
        """插入期货数据"""
        try:
            self.cur.execute("""
                INSERT OR REPLACE INTO futures_data 
                (date, contract, open_price, high_price, low_price, close_price, 
                 volume, amount, prev_close, change, change_pct, open_interest, settlement)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.date.strftime("%Y-%m-%d"),
                data.contract,
                data.open_price,
                data.high_price,
                data.low_price,
                data.close_price,
                data.volume,
                data.amount,
                data.prev_close,
                data.change,
                data.change_pct,
                data.open_interest,
                data.settlement
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"插入期货数据失败: {e}")
            return False
    
    def get_latest_futures(self, contract: str = "LH主力") -> dict:
        """获取最新的期货数据"""
        self.cur.execute("""
            SELECT * FROM futures_data 
            WHERE contract = ? 
            ORDER BY date DESC 
            LIMIT 1
        """, (contract,))
        row = self.cur.fetchone()
        if row:
            return {
                "date": row[1],
                "contract": row[2],
                "open_price": row[3],
                "high_price": row[4],
                "low_price": row[5],
                "close_price": row[6],
                "volume": row[7],
                "amount": row[8],
                "prev_close": row[9],
                "change": row[10],
                "change_pct": row[11],
                "open_interest": row[12],
                "settlement": row[13]
            }
        return {}

    # ========== 每日快照 ==========
    
    def save_daily_snapshot(self, data: DailySnapshot) -> bool:
        """保存每日汇总快照"""
        try:
            self.cur.execute("""
                INSERT OR REPLACE INTO daily_snapshot 
                (date, pig_price, lh_futures, corn_price, soybean_meal_price,
                 max_price, max_price_province, min_price, min_price_province, price_spread,
                 piglet_price_3way, piglet_price_crossbred,
                 pig_grain_ratio, pig_feed_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.date.strftime("%Y-%m-%d"),
                data.pig_price,
                data.lh_futures,
                data.corn_price,
                data.soybean_meal_price,
                data.max_price,
                data.max_price_province,
                data.min_price,
                data.min_price_province,
                data.price_spread,
                data.piglet_price_3way,
                data.piglet_price_crossbred,
                data.pig_grain_ratio,
                data.pig_feed_ratio
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"保存每日快照失败: {e}")
            return False

    def update_daily_snapshot_futures(self, date_str: str, lh_futures: float,
                                         pig_grain_ratio: float = None,
                                         pig_feed_ratio: float = None) -> bool:
        """
        只更新 daily_snapshot 中指定日期的期货和比值字段，
        不覆盖已有数据（如仔猪价格、饲料价格等）。
        解决两次写入 snapshot 导致 lh_futures 被覆盖为 None 的问题。
        """
        try:
            updates = []
            params = []
            if lh_futures is not None:
                updates.append("lh_futures = ?")
                params.append(lh_futures)
            if pig_grain_ratio is not None:
                updates.append("pig_grain_ratio = ?")
                params.append(pig_grain_ratio)
            if pig_feed_ratio is not None:
                updates.append("pig_feed_ratio = ?")
                params.append(pig_feed_ratio)
            
            if not updates:
                return True
            
            params.append(date_str)
            sql = f"UPDATE daily_snapshot SET {', '.join(updates)} WHERE date = ?"
            self.cur.execute(sql, params)
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"更新 daily_snapshot 期货字段失败: {e}")
            return False

    def get_latest_snapshot(self) -> dict:
        """查询最新的每日快照"""
        self.cur.execute("""
            SELECT * FROM daily_snapshot ORDER BY date DESC LIMIT 1
        """)
        row = self.cur.fetchone()
        if row:
            return {
                "date": row[1],
                "pig_price": row[2],
                "lh_futures": row[3],
                "corn_price": row[4],
                "soybean_meal_price": row[5],
                "max_price": row[6] if len(row) > 6 else None,
                "max_price_province": row[7] if len(row) > 7 else None,
                "min_price": row[8] if len(row) > 8 else None,
                "min_price_province": row[9] if len(row) > 9 else None,
                "price_spread": row[10] if len(row) > 10 else None,
                "piglet_price_3way": row[11] if len(row) > 11 else None,
                "piglet_price_crossbred": row[12] if len(row) > 12 else None
            }
        return {}
    
    def get_latest_price(self) -> float:
        """获取最新全国均价"""
        snapshot = self.get_latest_snapshot()
        return snapshot.get("pig_price", 0.0)
    
    def get_price_history(self, days: int = 30) -> list:
        """
        获取近N天的价格历史序列
        返回：[{"date": "2026-06-25", "price": 9.48}, ...]
        按日期升序排列
        """
        self.cur.execute("""
            SELECT date, pig_price 
            FROM daily_snapshot 
            WHERE pig_price IS NOT NULL
            ORDER BY date DESC 
            LIMIT ?
        """, (days,))
        rows = self.cur.fetchall()
        # 反转成升序
        result = []
        for row in reversed(rows):
            result.append({
                "date": row[0],
                "price": row[1]
            })
        return result
    
    def get_last_7days(self) -> list:
        """最近7天价格序列"""
        return self.get_price_history(7)
    
    def get_last_30days(self) -> list:
        """最近30天价格序列"""
        return self.get_price_history(30)
    
    def get_last_90days(self) -> list:
        """最近90天价格序列"""
        return self.get_price_history(90)

    # ========== 仔猪价格 ==========
    
    def insert_piglet_price(self, data: PigletPrice) -> bool:
        """插入一条仔猪价格数据"""
        try:
            self.cur.execute("""
                INSERT OR REPLACE INTO piglet_price (date, category, price)
                VALUES (?, ?, ?)
            """, (
                data.date.strftime("%Y-%m-%d"),
                data.category,
                data.price
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"插入仔猪价格失败: {e}")
            return False

    def get_latest_piglet_price(self, category: str = "三元") -> dict:
        """获取指定品种的最新仔猪价格"""
        self.cur.execute("""
            SELECT date, category, price FROM piglet_price WHERE category = ? ORDER BY date DESC LIMIT 1
        """, (category,))
        row = self.cur.fetchone()
        if row:
            return {"date": row[0], "category": row[1], "price": row[2]}
        return {}

    def get_piglet_price_history(self, category: str = "三元", days: int = 30) -> list:
        """获取近N天指定品种仔猪价格序列"""
        self.cur.execute("""
            SELECT date, price FROM piglet_price
            WHERE category = ?
            ORDER BY date DESC LIMIT ?
        """, (category, days))
        rows = self.cur.fetchall()
        result = []
        for row in reversed(rows):
            result.append({"date": row[0], "price": row[1]})
        return result

    def get_piglet_total_records(self, category: str = None) -> int:
        """仔猪价格总记录数"""
        if category:
            self.cur.execute("SELECT COUNT(*) FROM piglet_price WHERE category = ?", (category,))
        else:
            self.cur.execute("SELECT COUNT(*) FROM piglet_price")
        return self.cur.fetchone()[0]

    # ========== 饲料价格 ==========
    
    def insert_feed_price(self, date: datetime, corn_price: float = None, soybean_meal_price: float = None) -> bool:
        """插入或更新饲料价格"""
        try:
            self.cur.execute("""
                INSERT OR REPLACE INTO feed_price (date, corn_price, soybean_meal_price)
                VALUES (?, ?, ?)
            """, (
                date.strftime("%Y-%m-%d"),
                corn_price,
                soybean_meal_price
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"插入饲料价格失败: {e}")
            return False

    def get_latest_feed_price(self) -> dict:
        """获取最新饲料价格"""
        self.cur.execute("""
            SELECT date, corn_price, soybean_meal_price FROM feed_price ORDER BY date DESC LIMIT 1
        """)
        row = self.cur.fetchone()
        if row:
            return {"date": row[0], "corn_price": row[1], "soybean_meal_price": row[2]}
        return {}

    def get_feed_price_history(self, days: int = 30) -> list:
        """获取近N天饲料价格序列"""
        self.cur.execute("""
            SELECT date, corn_price, soybean_meal_price FROM feed_price
            ORDER BY date DESC LIMIT ?
        """, (days,))
        rows = self.cur.fetchall()
        result = []
        for row in reversed(rows):
            result.append({"date": row[0], "corn_price": row[1], "soybean_meal_price": row[2]})
        return result

    # ========== 数据源监控（运维用） ==========
    
    def log_source_status(self, source_name: str, data_type: str, 
                          success: bool, error_msg: str = "",
                          duration: float = 0, records_count: int = 0):
        """
        记录数据源抓取状态
        以后哪个源挂了，直接查这张表
        """
        try:
            self.cur.execute("""
                INSERT INTO source_status 
                (source_name, data_type, fetch_time, success, error_msg, duration, records_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                source_name,
                data_type,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                1 if success else 0,
                error_msg,
                round(duration, 2),
                records_count
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"记录数据源状态失败: {e}")

    def get_source_health(self, source_name: str, days: int = 7) -> dict:
        """查询数据源最近N天的健康度（成功率）"""
        self.cur.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(success) as success_count,
                MAX(fetch_time) as last_fetch
            FROM source_status 
            WHERE source_name = ? 
            AND fetch_time >= datetime('now', ?)
        """, (source_name, f"-{days} days"))
        row = self.cur.fetchone()
        if row and row[0] > 0:
            success_rate = round(row[1] / row[0] * 100, 1)
            return {
                "total": row[0],
                "success": row[1],
                "success_rate": f"{success_rate}%",
                "last_fetch": row[2]
            }
        return {"total": 0, "success": 0, "success_rate": "0%", "last_fetch": "无记录"}

    # ========== 每日监控汇聚表（日报用）==========

    def init_daily_monitor(self):
        """创建 daily_monitor 表"""
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS daily_monitor (
                date            TEXT    NOT NULL UNIQUE,
                pig_price_head  REAL,           -- 外三元生猪价格，元/头（标准体重 110kg）
                pig_price_kg    REAL,           -- 生猪均价，元/公斤
                hog_futures     REAL,           -- 生猪期货主力合约，元/公斤
                stock_muyuan    REAL,           -- 牧原股份股价，元
                pig_grain_ratio REAL,           -- 猪粮比
                pig_feed_ratio  REAL,           -- 猪料比
                index_xumu      REAL            -- 中证畜牧指数
            )
        """)
        self.conn.commit()

    def save_daily_monitor(self, date_str: str, pig_price_kg: float = None,
                           hog_futures: float = None, stock_muyuan: float = None,
                           pig_grain_ratio: float = None, pig_feed_ratio: float = None,
                           index_xumu: float = None):
        """
        保存一条每日监控数据。
        pig_price_head 由 pig_price_kg * 110（标准体重）自动计算。
        """
        pig_price_head = round(pig_price_kg * 110, 2) if pig_price_kg else None
        try:
            self.cur.execute("""
                INSERT OR REPLACE INTO daily_monitor
                (date, pig_price_head, pig_price_kg, hog_futures, stock_muyuan,
                 pig_grain_ratio, pig_feed_ratio, index_xumu)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (date_str, pig_price_head, pig_price_kg, hog_futures, stock_muyuan,
                   pig_grain_ratio, pig_feed_ratio, index_xumu))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"保存每日监控数据失败: {e}")
            return False

    def get_daily_monitor(self, days: int = 30) -> list:
        """获取最近N天的每日监控数据"""
        self.cur.execute("""
            SELECT * FROM daily_monitor ORDER BY date DESC LIMIT ?
        """, (days,))
        rows = self.cur.fetchall()
        result = []
        for row in reversed(rows):
            result.append({
                "date": row[0],
                "pig_price_head": row[1],
                "pig_price_kg": row[2],
                "hog_futures": row[3],
                "stock_muyuan": row[4],
                "pig_grain_ratio": row[5],
                "pig_feed_ratio": row[6],
                "index_xumu": row[7]
            })
        return result

    # ========== 能繁母猪存栏（月度）==========

    def save_sow_inventory(self, month: str, inventory: float, source: str = "moa"):
        """
        保存一条能繁母猪存栏数据。
        month: YYYY-MM 格式
        inventory: 万头
        """
        try:
            self.cur.execute("""
                INSERT OR REPLACE INTO industry_monthly (month, sow_inventory, source)
                VALUES (?, ?, ?)
            """, (month, inventory, source))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"保存能繁母猪存栏失败: {e}")
            return False

    def get_sow_inventory_history(self, limit: int = 60) -> list:
        """获取能繁母猪存栏历史"""
        self.cur.execute(
            "SELECT month, sow_inventory, source FROM industry_monthly ORDER BY month DESC LIMIT ?",
            (limit,))
        rows = self.cur.fetchall()
        result = []
        for row in reversed(rows):
            result.append({"month": row[0], "sow_inventory": row[1], "source": row[2]})
        return result

    def insert_stock_history(self, date_str: str, code: str, name: str,
                                open_price: float, close_price: float,
                                high: float, low: float,
                                volume: int, amount: float,
                                amplitude: float, change_pct: float,
                                change_amount: float, turnover: float) -> bool:
        """插入一条股票日K数据"""
        try:
            self.cur.execute("""
                INSERT OR REPLACE INTO stock_history
                (date, 股票代码, open, close, high, low, volume, amount,
                 振幅, 涨跌幅, 涨跌额, turnover, code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                date_str, f"{code}.SZ", open_price, close_price,
                high, low, volume, amount, amplitude, change_pct,
                change_amount, turnover, code
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"插入股票数据失败 {code}: {e}")
            return False

    def get_latest_sow_inventory(self) -> dict:
        """获取最新能繁母猪存栏"""
        self.cur.execute(
            "SELECT month, sow_inventory, source FROM industry_monthly ORDER BY month DESC LIMIT 1")
        row = self.cur.fetchone()
        if row:
            return {"month": row[0], "sow_inventory": row[1], "source": row[2]}
        return {}

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    db = HogDatabase()
    print("数据库初始化成功，三张表已创建")
    print(f"数据库路径: {DB_PATH}")
    db.close()
