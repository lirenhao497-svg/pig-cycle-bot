# -*- coding: utf-8 -*-
"""
全局配置文件
所有API密钥、路径、参数统一在这里管理
"""
import os

# ========== 路径配置 ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "hog_data.db")

# ========== 数据源API配置 ==========
# 农业农村部农产品平台（无需key，直接请求）
MOA_BASE_URL = "https://ncpscxx.moa.gov.cn"

# 大商所API（注册后填入）
DCE_API_KEY = ""
DCE_API_SECRET = ""

# 新闻情绪NLP配置（百度/阿里云，可选）
NLP_API_KEY = ""
NLP_API_SECRET = ""

# ========== 爬虫参数 ==========
REQUEST_INTERVAL = 2  # 请求间隔（秒），避免被封
# 设为 "random" 则从UA池随机选择，降低被识别概率
USER_AGENT = "random"

# ========== 微信通知配置（可选） ==========
WECHAT_WEBHOOK = ""  # 企业微信机器人webhook
