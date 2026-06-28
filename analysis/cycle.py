# -*- coding: utf-8 -*-
"""
猪周期逻辑模块
核心：判断当前处于猪周期的哪个阶段，给出周期信号
周期四阶段：
  1. 亏损去产能期（价格下跌，产能出清）
  2. 底部磨底期（价格低位，产能持续去化）
  3. 上涨周期（产能不足，价格上涨）
  4. 顶部回落期（产能恢复，价格见顶回落）
"""
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis.indicators import Indicators


class CycleAnalyzer:
    """猪周期分析器"""
    
    # 周期阈值（可根据实际数据调整）
    PIG_GRAIN_RATIO_BREAK_EVEN = 5.5  # 盈亏平衡点
    PIG_GRAIN_RATIO_SEVERE_LOSS = 4.5  # 重度亏损线
    PIG_GRAIN_RATIO_HIGH_PROFIT = 8.0  # 高利润线
    
    def __init__(self):
        self.indicators = Indicators()

    def get_cycle_stage(self):
        """
        判断当前周期阶段
        返回: stage（阶段名称）, signal（信号）, description（描述）
        """
        price_series = self.indicators.get_price_series(days=90)
        
        if len(price_series) < 30:
            return "数据不足", "neutral", "历史数据不足，无法判断周期阶段"
        
        # 计算关键指标
        current_price = price_series[-1][1]
        change_7d = self.indicators.calc_price_change(price_series, days=7)
        change_30d = self.indicators.calc_price_change(price_series, days=30)
        ma20 = self.indicators.calc_moving_average(price_series, window=20)
        
        change_pct_7d = change_7d['change_pct'] if change_7d else 0
        change_pct_30d = change_30d['change_pct'] if change_30d else 0
        current_ma20 = ma20[-1][1] if ma20 else current_price
        
        # 周期判断逻辑（简化版，可后续优化）
        # 1. 价格在20日均线下方，且持续下跌 → 下跌/去产能期
        if current_price < current_ma20 and change_pct_30d < -5:
            if change_pct_7d < -3:
                stage = "快速下跌期"
                signal = "bearish"
                description = "价格快速下跌，产能开始去化，建议观望"
            else:
                stage = "下跌通道"
                signal = "bearish"
                description = "价格处于下跌通道，产能逐步去化"
        
        # 2. 价格低位震荡，跌幅收窄 → 磨底期
        elif current_price < current_ma20 and abs(change_pct_30d) < 5:
            stage = "底部磨底期"
            signal = "neutral"
            description = "价格低位震荡，产能持续去化，关注拐点信号"
        
        # 3. 价格突破均线，持续上涨 → 上涨周期
        elif current_price > current_ma20 and change_pct_30d > 5:
            if change_pct_7d > 3:
                stage = "快速上涨期"
                signal = "bullish"
                description = "价格快速上涨，产能缺口显现，注意追高风险"
            else:
                stage = "上涨通道"
                signal = "bullish"
                description = "价格处于上涨通道，产能恢复需要时间"
        
        # 4. 价格高位，涨幅收窄 → 顶部回落期
        elif current_price > current_ma20 and change_pct_7d < 0:
            stage = "顶部回落期"
            signal = "neutral_bearish"
            description = "价格高位回落，产能逐步恢复，警惕周期见顶"
        
        else:
            stage = "震荡整理"
            signal = "neutral"
            description = "价格震荡整理，方向不明确"
        
        return {
            "stage": stage,
            "signal": signal,
            "description": description,
            "current_price": current_price,
            "change_7d": change_pct_7d,
            "change_30d": change_pct_30d,
            "ma20": current_ma20
        }

    def get_warning_signals(self):
        """获取预警信号列表"""
        warnings = []
        cycle_info = self.get_cycle_stage()
        
        # 价格异动预警
        if abs(cycle_info['change_7d']) > 5:
            direction = "上涨" if cycle_info['change_7d'] > 0 else "下跌"
            warnings.append({
                "level": "warning",
                "type": "price_volatility",
                "message": f"价格7日{direction}超过5%，波动较大"
            })
        
        # 周期拐点预警
        if cycle_info['signal'] in ['bullish', 'bearish'] and cycle_info['stage'] in ['快速上涨期', '快速下跌期']:
            warnings.append({
                "level": "info",
                "type": "cycle_inflection",
                "message": f"进入{cycle_info['stage']}，关注周期节奏"
            })
        
        return warnings

    def close(self):
        self.indicators.close()


if __name__ == "__main__":
    cycle = CycleAnalyzer()
    stage_info = cycle.get_cycle_stage()
    print(f"当前周期阶段: {stage_info['stage']}")
    print(f"信号: {stage_info['signal']}")
    print(f"描述: {stage_info['description']}")
    cycle.close()
