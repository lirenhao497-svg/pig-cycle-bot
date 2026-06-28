# -*- coding: utf-8 -*-
"""
指标计算模块
负责计算各类技术指标、基本面指标
所有指标都是纯函数，输入数据输出指标值
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storage.db import HogDatabase


class Indicators:
    """指标计算器"""
    
    def __init__(self):
        self.db = HogDatabase()

    def calc_price_change(self, price_list, days=7):
        """
        计算价格涨跌幅
        price_list: [(date, price), ...] 按日期升序排列
        """
        if len(price_list) < days:
            return None
        
        start_price = price_list[0][1]
        end_price = price_list[-1][1]
        
        if start_price and end_price:
            change_pct = (end_price - start_price) / start_price * 100
            return {
                "start_price": start_price,
                "end_price": end_price,
                "change_pct": round(change_pct, 2),
                "days": days
            }
        return None

    def calc_moving_average(self, price_list, window=20):
        """
        计算移动平均线（MA）
        price_list: [(date, price), ...] 按日期升序排列
        """
        if len(price_list) < window:
            return None
        
        ma_values = []
        for i in range(window - 1, len(price_list)):
            window_prices = [p[1] for p in price_list[i-window+1:i+1] if p[1]]
            if window_prices:
                ma = sum(window_prices) / len(window_prices)
                ma_values.append((price_list[i][0], round(ma, 2)))
        
        return ma_values

    def calc_pig_grain_ratio(self, hog_price, feed_price):
        """
        计算猪粮比价
        猪粮比价 = 生猪价格 / 玉米价格
        盈亏平衡点约 5.5:1
        """
        if hog_price and feed_price and feed_price > 0:
            ratio = hog_price / feed_price
            return round(ratio, 2)
        return None

    def calc_breeding_profit(self, hog_price, feed_cost, sow_stock=None):
        """
        估算养殖利润
        简化模型：利润 = 生猪价格 - 饲料成本*料肉比
        料肉比约 2.8~3.0
        """
        feed_ratio = 2.9  # 料肉比
        if hog_price and feed_cost:
            profit = hog_price - feed_cost * feed_ratio
            return round(profit, 2)
        return None

    def calc_sentiment_index(self, sentiment_list):
        """
        计算情绪指数
        sentiment_list: [score1, score2, ...]
        归一化到 0~100 区间
        """
        if not sentiment_list:
            return 50  # 中性
        
        avg_score = sum(sentiment_list) / len(sentiment_list)
        # 将 -10~10 映射到 0~100
        sentiment_index = (avg_score + 10) * 5
        return round(sentiment_index, 1)

    def get_price_series(self, days=90):
        """获取价格时间序列（供指标计算使用）"""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        price_data = self.db.query_price(start_date, end_date, limit=days)
        # 转为 (date, price) 格式并按日期升序
        price_series = [(p[1], p[2]) for p in price_data if p[2]]
        price_series.sort(key=lambda x: x[0])
        return price_series

    def close(self):
        self.db.close()


if __name__ == "__main__":
    ind = Indicators()
    price_series = ind.get_price_series(days=30)
    print(f"获取到 {len(price_series)} 天价格数据")
    
    if price_series:
        change = ind.calc_price_change(price_series, days=7)
        if change:
            print(f"7日涨跌幅: {change['change_pct']}%")
    ind.close()
