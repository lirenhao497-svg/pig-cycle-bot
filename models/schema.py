# -*- coding: utf-8 -*-
"""
统一数据模型（第一版 - 极简）
所有模块之间传递的数据都用这些结构

原则：先简单，跑通闭环，再迭代加字段
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PigPrice:
    """生猪现货价格（分省）"""
    date: datetime
    province: str
    price: float          # 元/公斤


@dataclass
class FuturesData:
    """生猪期货数据"""
    date: datetime
    contract: str         # 合约代码，如 LH主力、LH2609
    open_price: float = None    # 开盘价
    high_price: float = None    # 最高价
    low_price: float = None     # 最低价
    close_price: float = None   # 收盘价/最新价
    volume: int = None          # 成交量（手）
    amount: float = None        # 成交额（元）
    prev_close: float = None    # 昨收
    change: float = None        # 涨跌额
    change_pct: float = None    # 涨跌幅（%）
    open_interest: int = None   # 持仓量
    settlement: float = None    # 结算价


@dataclass
class FeedPrice:
    """饲料价格"""
    date: datetime
    corn_price: float            # 玉米价格
    soybean_meal_price: float    # 豆粕价格


@dataclass
class PigletPrice:
    """仔猪价格（搜猪网/头价）"""
    date: datetime
    price: float            # 元/头
    category: str = "三元"   # 品种："三元"(spot_hog_three_way_soozhu) / "外三元"(spot_hog_crossbred_soozhu)


@dataclass
class DailySnapshot:
    """
    每日汇总快照（分析层用）
    把一天的核心数据打包，方便分析和展示
    """
    date: datetime
    pig_price: float = None              # 全国生猪均价
    lh_futures: float = None             # 主力合约收盘价
    corn_price: float = None             # 玉米价格
    soybean_meal_price: float = None     # 豆粕价格
    piglet_price_3way: float = None      # 三元仔猪价格（元/头），用于关联分析
    piglet_price_crossbred: float = None # 外三元仔猪价格（元/头），用于关联分析
    max_price: float = None              # 最高价
    max_price_province: str = None       # 最高价省份
    min_price: float = None              # 最低价
    min_price_province: str = None       # 最低价省份
    price_spread: float = None           # 价差（最高-最低）
    pig_grain_ratio: float = None        # 猪粮比（生猪价/玉米价）
    pig_feed_ratio: float = None         # 猪料比（生猪价/(0.6*玉米+0.25*豆粕)）


@dataclass
class MarketDailyRow:
    """市场日线数据行（对应 market_daily 表）"""
    date: str
    pig_grain_ratio: float = None
    pig_feed_ratio: float = None
    hog_futures: float = None
    index_xumu: float = None
    stock_muyuan: float = None
    stock_wens: float = None
    stock_xinxiwang: float = None
    stock_haida: float = None
    profit_self: int = None
