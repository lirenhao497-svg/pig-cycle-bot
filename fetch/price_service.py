# -*- coding: utf-8 -*-
"""
生猪价格统一服务（多数据源降级）

分析层只调用这个接口，不知道数据来自哪里。

数据源优先级：
1. 正大猪博士（主源，分省数据全）
2. 搜猪网（备用源，只有全国均价）

工程原则：永远不要依赖单一数据源
"""
import sys
import os
from datetime import datetime
from typing import List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fetch.pig_price import PigPriceCpctiFetcher
from fetch.pig_price_soozhu import PigPriceSoozhuFetcher
from models.schema import PigPrice
from utils.logger import get_logger

logger = get_logger("price_service")


class PigPriceService:
    """
    生猪价格统一服务
    封装多数据源降级逻辑
    """
    
    def __init__(self):
        # 数据源列表，按优先级排序
        self.sources = [
            ("正大猪博士", PigPriceCpctiFetcher),
            ("搜猪网", PigPriceSoozhuFetcher),
        ]
        self.active_source = None
        self.fetcher = None

    def _try_fetch(self) -> List[PigPrice]:
        """
        尝试从各个数据源抓取，自动降级
        返回：PigPrice列表
        """
        for source_name, fetcher_class in self.sources:
            try:
                logger.info(f"尝试数据源: {source_name}")
                fetcher = fetcher_class()
                prices = fetcher.fetch_daily_price()
                
                if prices:
                    logger.info(f"数据源 {source_name} 抓取成功，共 {len(prices)} 条")
                    self.active_source = source_name
                    self.fetcher = fetcher
                    return prices
                else:
                    logger.warning(f"数据源 {source_name} 返回空数据，尝试下一个")
                    
            except Exception as e:
                logger.error(f"数据源 {source_name} 抓取失败: {e}，尝试下一个")
                continue
        
        logger.error("所有数据源都失败了！")
        return []

    def get_daily_prices(self) -> List[PigPrice]:
        """
        获取每日分省价格
        返回：PigPrice列表
        """
        return self._try_fetch()

    def get_national_price(self) -> Optional[float]:
        """
        获取全国均价（统一接口）
        分析层只需要调用这个方法
        """
        prices = self._try_fetch()
        if not prices:
            return None
        
        # 如果只有一条"全国"的数据，直接返回
        if len(prices) == 1 and prices[0].province == "全国":
            return prices[0].price
        
        # 否则计算均价
        total = sum(p.price for p in prices)
        return round(total / len(prices), 2)

    def get_price_stats(self, prices: List[PigPrice] = None) -> dict:
        """
        获取价格统计（最高、最低、价差）
        如果没有传prices，会自动抓取
        """
        if prices is None:
            prices = self._try_fetch()
        
        if not prices:
            return {}
        
        # 如果只有全国数据，没有分省，就返回空统计
        if len(prices) == 1 and prices[0].province == "全国":
            return {
                "avg_price": prices[0].price,
                "has_province_data": False
            }
        
        # 有分省数据，计算统计
        max_p = max(prices, key=lambda x: x.price)
        min_p = min(prices, key=lambda x: x.price)
        avg = round(sum(p.price for p in prices) / len(prices), 2)
        
        return {
            "avg_price": avg,
            "max_price": max_p.price,
            "max_province": max_p.province,
            "min_price": min_p.price,
            "min_province": min_p.province,
            "spread": round(max_p.price - min_p.price, 2),
            "province_count": len(prices),
            "has_province_data": True
        }

    def get_active_source(self) -> str:
        """获取当前使用的数据源名称"""
        return self.active_source or "未知"
    
    def get_feed_price(self):
        """
        获取饲料价格（玉米、豆粕）
        只有部分数据源支持，不支持则返回None
        """
        if not self.fetcher:
            # 如果还没初始化，先尝试抓取猪价（顺便初始化fetcher）
            self._try_fetch()
        
        if self.fetcher and hasattr(self.fetcher, 'fetch_feed_price'):
            try:
                return self.fetcher.fetch_feed_price()
            except Exception as e:
                logger.error(f"获取饲料价格失败: {e}")
                return None
        
        return None

    def close(self):
        """关闭所有资源"""
        if self.fetcher:
            self.fetcher.close()
        logger.info("PigPriceService已关闭")


if __name__ == "__main__":
    service = PigPriceService()
    
    print("\n" + "="*50)
    print("测试：生猪价格统一服务")
    print("="*50)
    
    # 测试获取全国均价
    price = service.get_national_price()
    if price:
        print(f"\n全国均价: {price} 元/公斤")
        print(f"数据源: {service.get_active_source()}")
    else:
        print("\n获取失败")
    
    # 测试获取完整统计
    stats = service.get_price_stats()
    if stats:
        print(f"\n价格统计:")
        print(f"  均价: {stats.get('avg_price')} 元/公斤")
        if stats.get('has_province_data'):
            print(f"  最高价: {stats['max_price']} 元/公斤 ({stats['max_province']})")
            print(f"  最低价: {stats['min_price']} 元/公斤 ({stats['min_province']})")
            print(f"  价差: {stats['spread']} 元/公斤")
            print(f"  覆盖省份: {stats['province_count']} 个")
    
    service.close()
