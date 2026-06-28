# -*- coding: utf-8 -*-
"""
统一日志模块
所有模块共用一个logger，输出到文件 + 控制台

日志格式：时间 - 级别 - 模块名 - 消息
日志文件：logs/app.log（按天切割）
"""
import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

# 日志目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "app.log")


def get_logger(name: str = "pig_cycle") -> logging.Logger:
    """
    获取logger
    用法：from utils.logger import get_logger; logger = get_logger(__name__)
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # 日志格式
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 1. 文件输出（按天切割，保留30天）
    file_handler = TimedRotatingFileHandler(
        LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    
    # 2. 控制台输出（只显示警告和错误，详细日志看文件）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    console_handler.setLevel(logging.WARNING)  # 控制台只显示警告和错误
    logger.addHandler(console_handler)
    
    return logger


# 全局默认logger
logger = get_logger()
