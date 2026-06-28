# -*- coding: utf-8 -*-
"""
测试搜猪网数据爬取
"""
import sys
import os
from bs4 import BeautifulSoup

# 修复Windows控制台编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch.base import DataGateway
from utils.logger import get_logger

logger = get_logger("test_soozhu")


def test_soozhu():
    """测试搜猪网数据爬取"""
    
    gateway = DataGateway()
    
    # 测试1：首页数据
    print("\n" + "="*60)
    print("测试1：搜猪网首页")
    print("="*60)
    try:
        url = "http://www.soozhu.com/"
        html = gateway.get_html(url)
        print(f"页面长度: {len(html)} 字符")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 找全国均价
        print("\n找全国均价...")
        # 试试不同的选择器
        price_elements = soup.find_all(class_=lambda x: x and 'price' in x.lower() if x else False)
        for el in price_elements[:10]:
            text = el.get_text(strip=True)
            if text and len(text) < 50:
                print(f"  找到: {text}")
        
        # 找包含"元/公斤"的文本
        print("\n找包含'元/公斤'的文本...")
        all_text = soup.get_text()
        lines = all_text.split('\n')
        for line in lines:
            line = line.strip()
            if '元/公斤' in line and len(line) < 100:
                print(f"  {line}")
                
    except Exception as e:
        print(f"失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试2：猪价页面
    print("\n" + "="*60)
    print("测试2：搜猪网猪价页面")
    print("="*60)
    try:
        url = "https://www.soozhu.com/z/404/a5/"
        html = gateway.get_html(url)
        print(f"页面长度: {len(html)} 字符")
        
        soup = BeautifulSoup(html, 'html.parser')
        all_text = soup.get_text()
        lines = all_text.split('\n')
        
        print("\n找价格相关内容...")
        count = 0
        for line in lines:
            line = line.strip()
            if line and ('元' in line or '猪' in line or '价' in line) and len(line) < 80:
                print(f"  {line}")
                count += 1
                if count > 30:
                    break
                
    except Exception as e:
        print(f"失败: {e}")
        import traceback
        traceback.print_exc()
    
    gateway.close()


if __name__ == "__main__":
    test_soozhu()
