# -*- coding: utf-8 -*-
"""
生猪价格爬虫 - 正大猪博士数据源
数据源：https://www.cpcti.com/
特点：数据更新及时、有分省价格、有饲料价格、HTML结构清晰
"""
import sys
import os
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fetch.base import DataGateway
from models.schema import PigPrice, FeedPrice
from utils.logger import get_logger

logger = get_logger("pig_price_cpcti")


class PigPriceCpctiFetcher(DataGateway):
    """正大猪博士 - 生猪价格爬虫"""
    
    def __init__(self):
        super().__init__()
        self.source_name = "正大猪博士"
        self.base_url = "https://www.cpcti.com/"

    def fetch_daily_price(self) -> List[PigPrice]:
        """
        抓取每日分省生猪价格
        返回：PigPrice列表
        """
        logger.info(f"开始抓取 {self.source_name} 生猪价格数据...")
        
        try:
            html = self.get_html(self.base_url)
            soup = BeautifulSoup(html, 'html.parser')
            
            # 找到分省价格表格
            tables = soup.find_all('table')
            if not tables:
                logger.error("未找到价格表格")
                return []
            
            # 第一个表格是分省价格
            price_table = tables[0]
            rows = price_table.find_all('tr')
            
            today = datetime.now()
            price_list = []
            
            for row in rows[1:]:  # 跳过表头
                cells = row.find_all('td')
                if len(cells) >= 2:
                    province = cells[0].get_text(strip=True)
                    price_str = cells[1].get_text(strip=True)
                    
                    # 解析价格
                    try:
                        price = float(price_str)
                        if province and price > 0:
                            pig_price = PigPrice(
                                date=today,
                                province=province,
                                price=price
                            )
                            price_list.append(pig_price)
                    except ValueError:
                        continue
            
            logger.info(f"成功抓取 {len(price_list)} 条分省价格数据")
            return price_list
            
        except Exception as e:
            logger.error(f"抓取生猪价格失败: {e}")
            return []

    def get_national_avg(self, price_list: List[PigPrice]) -> float:
        """计算全国均价"""
        if not price_list:
            return 0.0
        total = sum(p.price for p in price_list)
        return round(total / len(price_list), 2)
    
    def get_price_stats(self, price_list: List[PigPrice]) -> dict:
        """
        计算价格统计信息
        返回：{max_price, max_province, min_price, min_province, spread}
        """
        if not price_list:
            return {}
        
        # 找最高价
        max_p = max(price_list, key=lambda x: x.price)
        # 找最低价
        min_p = min(price_list, key=lambda x: x.price)
        
        return {
            "max_price": max_p.price,
            "max_province": max_p.province,
            "min_price": min_p.price,
            "min_province": min_p.province,
            "spread": round(max_p.price - min_p.price, 2)
        }

    def fetch_feed_price(self) -> Optional[FeedPrice]:
        """
        抓取饲料价格（玉米、豆粕）
        从详细页面抓取，数据更准确
        """
        logger.info(f"开始抓取 {self.source_name} 饲料价格数据...")
        
        try:
            # 用详细页面，数据更全更清晰
            detail_url = "https://www.cpcti.com/province/0/city/0"
            html = self.get_html(detail_url)
            soup = BeautifulSoup(html, 'html.parser')
            
            corn_price = None
            soybean_meal_price = None
            
            # 查找所有价格卡片
            cards = soup.find_all('div', class_='price-card')
            
            for card in cards:
                label_elem = card.find('div', class_='price-label')
                value_elem = card.find('div', class_='price-value')
                
                if not label_elem or not value_elem:
                    continue
                
                label = label_elem.get_text(strip=True)
                value_str = value_elem.get_text(strip=True)
                
                try:
                    value = float(value_str)
                    # 单位是元/吨，转换为元/公斤
                    price_kg = round(value / 1000, 3)
                    
                    if '玉米' in label and '14%' in label:
                        corn_price = price_kg
                    elif '豆粕' in label and '43%' in label:
                        soybean_meal_price = price_kg
                except ValueError:
                    continue
            
            if corn_price and soybean_meal_price:
                feed_data = FeedPrice(
                    date=datetime.now(),
                    corn_price=corn_price,
                    soybean_meal_price=soybean_meal_price
                )
                logger.info(f"饲料价格：玉米{corn_price}元/公斤，豆粕{soybean_meal_price}元/公斤")
                return feed_data
            else:
                logger.warning(f"未提取到完整的饲料价格数据：玉米={corn_price}，豆粕={soybean_meal_price}")
                return None
                
        except Exception as e:
            logger.error(f"抓取饲料价格失败: {e}")
            return None

    def close(self):
        super().close()
        logger.info(f"{self.source_name} 爬虫会话已关闭")


if __name__ == "__main__":
    fetcher = PigPriceCpctiFetcher()
    
    # 测试抓取猪价
    prices = fetcher.fetch_daily_price()
    if prices:
        print(f"\n成功抓取 {len(prices)} 条分省价格：")
        for p in prices[:5]:
            print(f"  {p.province}: {p.price} 元/公斤")
        print(f"  ...")
        
        avg = fetcher.get_national_avg(prices)
        print(f"\n全国均价: {avg} 元/公斤")
    
    # 测试抓取饲料价格
    feed = fetcher.fetch_feed_price()
    if feed:
        print(f"\n饲料价格:")
        print(f"  玉米: {feed.corn_price} 元/公斤")
        print(f"  豆粕: {feed.soybean_meal_price} 元/公斤")
    
    fetcher.close()
