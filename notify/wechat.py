# -*- coding: utf-8 -*-
"""
微信通知模块
支持企业微信机器人推送日报、预警消息
"""
import requests
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import WECHAT_WEBHOOK


class WechatNotifier:
    def __init__(self, webhook_url=None):
        self.webhook = webhook_url or WECHAT_WEBHOOK

    def send_text(self, content, mentioned_list=None):
        """
        发送纯文本消息
        content: 消息内容
        mentioned_list: @成员列表，如 ["user1", "@all"]
        """
        if not self.webhook:
            print("未配置企业微信webhook，跳过推送")
            print("消息内容:")
            print(content)
            return False
        
        data = {
            "msgtype": "text",
            "text": {
                "content": content,
                "mentioned_list": mentioned_list or []
            }
        }
        
        try:
            resp = requests.post(self.webhook, json=data, timeout=10)
            result = resp.json()
            if result.get("errcode") == 0:
                print("微信推送成功")
                return True
            else:
                print(f"微信推送失败: {result}")
                return False
        except Exception as e:
            print(f"微信推送异常: {e}")
            return False

    def send_markdown(self, content):
        """发送Markdown格式消息（企业微信支持）"""
        if not self.webhook:
            print("未配置企业微信webhook，跳过推送")
            print("消息内容:")
            print(content)
            return False
        
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
        
        try:
            resp = requests.post(self.webhook, json=data, timeout=10)
            result = resp.json()
            if result.get("errcode") == 0:
                print("微信推送成功")
                return True
            else:
                print(f"微信推送失败: {result}")
                return False
        except Exception as e:
            print(f"微信推送异常: {e}")
            return False

    def send_daily_report(self, report_text):
        """推送每日猪周期报告"""
        return self.send_text(report_text)

    def send_price_alert(self, price, change_pct, direction="down"):
        """价格异动预警推送"""
        if direction == "down":
            emoji = "📉"
            msg = f"{emoji} 价格下跌预警\n当前价格: {price} 元/公斤\n跌幅: {change_pct}%\n建议关注产能变化"
        else:
            emoji = "📈"
            msg = f"{emoji} 价格上涨预警\n当前价格: {price} 元/公斤\n涨幅: {change_pct}%\n建议关注补栏情绪"
        
        return self.send_text(msg)


if __name__ == "__main__":
    notifier = WechatNotifier()
    notifier.send_text("测试消息：猪周期爬虫启动成功")
