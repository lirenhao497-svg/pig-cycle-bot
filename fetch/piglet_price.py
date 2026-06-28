# -*- coding: utf-8 -*-
"""
仔猪价格爬虫
数据源：AKShare -> 搜猪网
频率：日度（但仔猪价格可能间隔较久，非每日更新）
单位：元/头

两个接口：
1. spot_hog_three_way_soozhu  — 三元仔猪  (225~280 元/头)
2. spot_hog_crossbred_soozhu  — 外三元仔猪 (1400~2100 元/头)

接口特点：
- 调用一次返回所有历史数据（AKShare已缓存的，目前约15天）
- 非常稳定（搜猪网数据源，⭐⭐⭐）
"""
import sys
import os
from datetime import datetime, timedelta
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.db import HogDatabase
from models.schema import PigletPrice
from utils.logger import get_logger

logger = get_logger("piglet_price")


class PigletPriceFetcher:
    """
    仔猪价格爬虫
    使用 AKShare 调用搜猪网接口，无需额外认证
    """

    def __init__(self):
        self.source_name = "AKShare-搜猪网"

    def _fetch_by_func(self, func_name: str, category: str) -> list[PigletPrice]:
        """
        通用：调用AKShare接口获取仔猪价格
        func_name: akshare 上的函数名，如 spot_hog_three_way_soozhu
        category: 品种名，如 "三元" / "外三元"
        """
        try:
            import akshare as ak
            df = getattr(ak, func_name)()
            if df is None or df.empty:
                logger.warning(f"{func_name} 返回空数据")
                return []

            results = []
            for _, row in df.iterrows():
                date_str = str(row["日期"])
                price = float(row["价格"])
                date = datetime.strptime(date_str, "%Y-%m-%d")
                results.append(PigletPrice(date=date, price=price, category=category))

            logger.info(f"{func_name} 成功获取 {len(results)} 条 {category}仔猪价格")
            return results

        except ImportError:
            logger.error("AKShare 未安装，请先 pip install akshare")
            return []
        except AttributeError:
            logger.error(f"AKShare 无 {func_name} 接口")
            return []
        except Exception as e:
            logger.error(f"{func_name} 抓取失败: {e}")
            return []

    def fetch_latest_3way(self) -> Optional[PigletPrice]:
        """获取最新三元仔猪价格"""
        rows = self._fetch_by_func("spot_hog_three_way_soozhu", "三元")
        return rows[-1] if rows else None

    def fetch_latest_crossbred(self) -> Optional[PigletPrice]:
        """获取最新外三元仔猪价格"""
        rows = self._fetch_by_func("spot_hog_crossbred_soozhu", "外三元")
        return rows[-1] if rows else None

    def fetch_latest(self, category: str = "三元") -> Optional[PigletPrice]:
        """
        获取指定品种的最新仔猪价格
        兼容旧接口
        """
        if category == "外三元":
            return self.fetch_latest_crossbred()
        return self.fetch_latest_3way()

    def fetch_all_history(self) -> list[PigletPrice]:
        """
        抓取所有品种的所有历史数据
        返回：PigletPrice 列表（包含三元 + 外三元）
        """
        results = []
        results += self._fetch_by_func("spot_hog_three_way_soozhu", "三元")
        results += self._fetch_by_func("spot_hog_crossbred_soozhu", "外三元")
        logger.info(f"全量抓取完成，共 {len(results)} 条仔猪价格")
        return results

    def close(self):
        pass
