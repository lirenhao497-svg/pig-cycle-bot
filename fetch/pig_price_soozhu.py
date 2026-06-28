# -*- coding: utf-8 -*-
"""
生猪价格爬虫 - 搜猪网数据源（备用源）
数据源：https://www.soozhu.com/z/404/a5/
特点：soozhu指数，只有全国均价，数据更新及时，作为备用源
"""
import sys
import os
import re
from datetime import datetime
from typing import List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fetch.base import DataGateway
from models.schema import PigPrice
from utils.logger import get_logger

logger = get_logger("pig_price_soozhu")


class PigPriceSoozhuFetcher(DataGateway):
    """搜猪网 - 生猪价格爬虫（备用源）"""
    
    def __init__(self):
        super().__init__()
        self.source_name = "搜猪网"
        self.index_url = "https://www.soozhu.com/z/404/a5/"

    def fetch_national_price(self) -> Optional[float]:
        """
        抓取全国均价（soozhu瘦肉猪指数）
        备用源只有全国均价，没有分省数据
        """
        logger.info(f"开始抓取 {self.source_name} 生猪价格数据...")
        
        try:
            html = self.get_html(self.index_url)
            
            # 提取瘦肉猪价格
            pattern = r'瘦肉猪[:：]?\s*(\d+\.?\d*)'
            match = re.search(pattern, html)
            
            if match:
                price = float(match.group(1))
                logger.info(f"成功抓取全国均价: {price} 元/公斤")
                return price
            else:
                logger.warning("未提取到瘦肉猪价格")
                return None
                
        except Exception as e:
            logger.error(f"抓取生猪价格失败: {e}")
            return None

    def fetch_daily_price(self) -> List[PigPrice]:
        """
        兼容接口：返回只有一条"全国"的PigPrice列表
        备用源没有分省数据，用全国代替
        """
        price = self.fetch_national_price()
        if price:
            return [PigPrice(
                date=datetime.now(),
                province="全国",
                price=price
            )]
        return []

    def close(self):
        super().close()
        logger.info(f"{self.source_name} 爬虫会话已关闭")


if __name__ == "__main__":
    fetcher = PigPriceSoozhuFetcher()
    
    price = fetcher.fetch_national_price()
    if price:
        print(f"\n搜猪网瘦肉猪指数: {price} 元/公斤")
    else:
        print("\n抓取失败")
    
    fetcher.close()
