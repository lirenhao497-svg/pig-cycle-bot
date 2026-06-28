# -*- coding: utf-8 -*-
"""
数据网关（DataGateway）
整个系统的请求入口，稳定性核心

统一处理：
- Session复用
- 超时
- 指数退避重试
- 请求间隔（防封）
- User-Agent
- 日志记录
"""
import requests
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USER_AGENT, REQUEST_INTERVAL
from utils.logger import get_logger

logger = get_logger("gateway")


class DataGateway:
    """数据网关基类"""
    
    def __init__(self, max_retries: int = 3, timeout: int = 10):
        self.session = requests.Session()
        self.max_retries = max_retries
        self.timeout = timeout
        self.request_interval = REQUEST_INTERVAL
        
        # 默认请求头
        self.session.headers.update({
            "User-Agent": self._get_ua(),
            "Accept": "text/html,application/json,text/plain,*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
        })
        
        logger.info(f"DataGateway初始化完成，重试次数={max_retries}，超时={timeout}s")

    def _get_ua(self) -> str:
        """获取User-Agent"""
        if USER_AGENT == "random":
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        return USER_AGENT

    def _sleep(self):
        """请求间隔（防封IP）"""
        if self.request_interval > 0:
            time.sleep(self.request_interval)

    def get(self, url: str, params: dict = None) -> requests.Response:
        """
        统一GET请求
        自动重试（指数退避）+ 请求间隔 + 日志
        """
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                self._sleep()
                logger.debug(f"请求 [{attempt}/{self.max_retries}]: {url}")
                
                resp = self.session.get(url, params=params, timeout=self.timeout)
                resp.raise_for_status()
                
                logger.debug(f"请求成功: {url} (状态码={resp.status_code})")
                return resp
                
            except requests.RequestException as e:
                last_error = e
                logger.warning(f"请求失败 [{attempt}/{self.max_retries}]: {url} - {e}")
                
                if attempt < self.max_retries:
                    # 指数退避：2s, 4s, 8s...
                    wait_time = 2 ** attempt
                    logger.info(f"{wait_time}秒后重试...")
                    time.sleep(wait_time)
        
        # 所有重试都失败
        logger.error(f"请求最终失败 ({self.max_retries}次重试): {url} - {last_error}")
        raise last_error

    def get_html(self, url: str, params: dict = None) -> str:
        """获取HTML文本（自动识别编码）"""
        resp = self.get(url, params=params)
        resp.encoding = resp.apparent_encoding
        return resp.text

    def get_json(self, url: str, params: dict = None) -> dict:
        """获取JSON数据"""
        resp = self.get(url, params=params)
        return resp.json()

    def close(self):
        """关闭会话"""
        self.session.close()
        logger.info("DataGateway会话已关闭")


# 兼容旧代码
BaseFetcher = DataGateway
