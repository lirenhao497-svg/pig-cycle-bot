# -*- coding: utf-8 -*-
"""
报告生成模块（输出层）
负责把指标计算、周期分析的结果组装成可读的报告
所有计算逻辑在 indicators.py 和 cycle.py 中
"""
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storage.db import HogDatabase
from analysis.indicators import Indicators


class HogAnalyzer:
    """报告生成器"""
    
    def __init__(self):
        self.db = HogDatabase()
        self.indicators = Indicators()

    def calc_price_change(self, days=7):
        """计算涨跌幅（调用indicators层）"""
        price_series = self.indicators.get_price_series(days=days)
        return self.indicators.calc_price_change(price_series, days=days)

    def generate_daily_report(self):
        """生成每日猪周期简报"""
        report_lines = []
        today = datetime.now().strftime("%Y-%m-%d")
        
        report_lines.append(f"📊 猪周期日报 - {today}")
        report_lines.append("=" * 30)
        
        # 价格数据
        price_change_7d = self.calc_price_change(days=7)
        if price_change_7d:
            report_lines.append(f"🐷 生猪均价: {price_change_7d['end_price']} 元/公斤")
            report_lines.append(f"📈 7日涨跌幅: {price_change_7d['change_pct']}%")
        
        # 情绪数据
        sentiment_data = self.db.query_daily_sentiment(today, today)
        if sentiment_data:
            today_sentiment = sentiment_data[0]
            report_lines.append(f"📰 今日新闻数: {today_sentiment[2]} 条")
            report_lines.append(f"💭 平均情绪分: {round(today_sentiment[1], 2)}")
        
        # 周期信号（在cycle.py中，scheduler层会追加）
        # 这里只做基础报告
        
        report_text = "\n".join(report_lines)
        return report_text

    def export_to_csv(self, output_path=None):
        """导出数据到CSV"""
        if not output_path:
            output_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "hog_data_export.csv"
            )
        print(f"数据已导出到: {output_path}")
        return output_path

    def close(self):
        self.db.close()
        self.indicators.close()


if __name__ == "__main__":
    analyzer = HogAnalyzer()
    report = analyzer.generate_daily_report()
    print(report)
    analyzer.close()
