# -*- coding: utf-8 -*-
"""
仔猪价格爬虫 - 正大猪博士数据源
从正大猪博士公开API获取仔猪价格，单位：元/公斤

API:
  https://srv-iorder.cpcti.com/app/spot/info?goods_type=5&k_type=qtr
  返回仔猪价格（元/公斤），不分品种

字段说明：
  handle_price - 处理价（元/公斤），与猪价保持相同量纲
  price        - 源价格（元/公斤），和 handle_price 相同
  data_date    - 数据日期

特点：
  - 完全公开，无需认证
  - 约252条历史数据，覆盖2026-03至今
  - 每日更新（可能有1-2天延迟）
  - 免费、稳定
"""
import sys
import os
from datetime import datetime, timedelta
from typing import List, Optional
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schema import PigletPrice
from utils.logger import get_logger

logger = get_logger("piglet_price_cpcti")


class PigletPriceCpctiFetcher:
    """正大猪博士 - 仔猪价格爬虫"""

    def __init__(self):
        self.source_name = "正大猪博士"
        self.api_url = "https://srv-iorder.cpcti.com/app/spot/info"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.cpcti.com/',
        })

    def fetch_all(self, k_type: str = "year") -> List[PigletPrice]:
        """
        获取仔猪价格全部历史数据
        k_type: qtr(季度) / half_year(半年) / year(年) / 3year(3年)
        """
        try:
            params = {"goods_type": 5, "k_type": k_type}
            resp = self.session.get(self.api_url, params=params, timeout=10)
            data = resp.json()

            if data.get("error") != 0 or not data.get("data", {}).get("list"):
                logger.warning(f"正大猪博士仔猪API返回异常: {data.get('msg')}")
                return []

            items = data["data"]["list"]
            results = []
            for item in items:
                date_str = item.get("data_date")
                price = float(item.get("handle_price", 0))
                if date_str and price > 0:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                    results.append(PigletPrice(
                        date=date,
                        price=price,
                        category="仔猪(正大)"
                    ))

            logger.info(f"正大猪博士仔猪API成功获取 {len(results)} 条数据")
            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"正大猪博士仔猪API请求失败: {e}")
            return []
        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"正大猪博士仔猪API数据解析失败: {e}")
            return []

    def fetch_latest(self) -> Optional[PigletPrice]:
        """获取最新一条仔猪价格"""
        rows = self.fetch_all(k_type="qtr")
        return rows[-1] if rows else None

    def close(self):
        self.session.close()
