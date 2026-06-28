# -*- coding: utf-8 -*-
"""
生猪期货数据爬虫
数据源：东方财富网API

输出：FuturesData 统一数据模型
"""
import sys
import os
from datetime import datetime
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fetch.base import DataGateway
from models.schema import FuturesData
from utils.logger import get_logger

logger = get_logger("futures")


class FuturesFetcher(DataGateway):
    """生猪期货数据爬虫"""
    
    def __init__(self):
        super().__init__()
        # 东方财富网期货列表API（比单股接口更稳定）
        self.api_url = "https://push2.eastmoney.com/api/qt/clist/get"
        # 大商所市场代码
        self.market = "m:114"
        # 需要的字段
        self.fields = "f12,f13,f14,f2,f3,f4,f5,f6,f7,f15,f16,f17,f18"
        # 字段说明：
        # f12: 代码
        # f13: 市场
        # f14: 名称
        # f2: 最新价
        # f3: 涨跌幅（%）
        # f4: 涨跌额
        # f5: 成交量（手）
        # f6: 成交额（元）
        # f7: 振幅
        # f15: 最高
        # f16: 最低
        # f17: 今开
        # f18: 昨收
    
    def fetch_main_contract(self) -> Optional[FuturesData]:
        """
        抓取生猪主力合约数据
        返回：FuturesData 对象，失败返回 None
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"抓取生猪期货主力合约数据...")
        
        params = {
            "pn": "1",
            "pz": "200",  # 取足够多的合约，确保能找到生猪
            "po": "1",
            "np": "1",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2",
            "invt": "2",
            "fid": "f3",
            "fs": self.market,
            "fields": self.fields,
        }
        
        try:
            data = self.get_json(self.api_url, params=params)
            
            if not data or data.get("rc") != 0 or not data.get("data"):
                logger.error(f"API返回异常：{data}")
                return None
            
            # 从列表中找生猪主力合约
            target = None
            for item in data["data"]["diff"]:
                name = item.get("f14", "")
                # 优先找"生猪主连"或"生猪主力"
                if "生猪主连" in name or "生猪主力" in name:
                    target = item
                    break
            
            # 如果没找到主连，找任意生猪相关的
            if not target:
                for item in data["data"]["diff"]:
                    name = item.get("f14", "")
                    if "生猪" in name:
                        target = item
                        break
            
            if not target:
                logger.error("未找到生猪期货合约")
                return None
            
            # 解析数据
            futures_data = FuturesData(
                date=datetime.now(),
                contract=target.get("f14", "LH主力"),
                open_price=target.get("f17"),
                high_price=target.get("f15"),
                low_price=target.get("f16"),
                close_price=target.get("f2"),
                volume=target.get("f5"),
                amount=target.get("f6"),
                prev_close=target.get("f18"),
                change=target.get("f4"),
                change_pct=target.get("f3"),
            )
            
            logger.info(f"期货数据抓取成功：{futures_data.contract} 最新 {futures_data.close_price} "
                       f"涨跌 {futures_data.change} ({futures_data.change_pct}%)")
            
            return futures_data
            
        except Exception as e:
            logger.error(f"抓取期货数据失败: {e}")
            return None
    
    def get_price(self) -> Optional[float]:
        """
        快捷获取主力合约最新价
        返回：价格（元/吨），失败返回 None
        """
        data = self.fetch_main_contract()
        return data.close_price if data else None
    
    def close(self):
        super().close()


if __name__ == "__main__":
    fetcher = FuturesFetcher()
    result = fetcher.fetch_main_contract()
    if result:
        print(f"合约：{result.contract}")
        print(f"最新价：{result.close_price}")
        print(f"开盘价：{result.open_price}")
        print(f"最高价：{result.high_price}")
        print(f"最低价：{result.low_price}")
        print(f"昨收：{result.prev_close}")
        print(f"涨跌：{result.change}")
        print(f"涨跌幅：{result.change_pct}%")
        print(f"成交量：{result.volume}手")
        print(f"成交额：{result.amount}元")
    else:
        print("抓取失败")
    fetcher.close()
