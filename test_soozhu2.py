# -*- coding: utf-8 -*-
"""
测试搜猪网 - 找最新数据页面
"""
import sys
import os
from bs4 import BeautifulSoup
import re

# 修复Windows控制台编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch.base import DataGateway
from utils.logger import get_logger

logger = get_logger("test_soozhu2")


def test_soozhu():
    """测试搜猪网各个页面"""
    
    gateway = DataGateway()
    
    # 测试1：soozhu指数页面
    print("\n" + "="*60)
    print("测试1：soozhu指数页面")
    print("="*60)
    try:
        url = "https://www.soozhu.com/z/404/a5/"
        html = gateway.get_html(url)
        print(f"页面长度: {len(html)}")
        
        soup = BeautifulSoup(html, 'html.parser')
        all_text = soup.get_text()
        
        # 找瘦肉猪价格
        print("\n找瘦肉猪价格...")
        pattern = r'瘦肉猪[:：]?\s*(\d+\.?\d*)'
        matches = re.findall(pattern, all_text)
        for m in matches[:5]:
            print(f"  找到: {m}")
        
        # 找包含"元/公斤"的行
        print("\n找包含价格的行...")
        lines = all_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) < 100 and ('瘦肉猪' in line or '仔猪' in line or '玉米' in line or '豆粕' in line):
                print(f"  {line}")
                
    except Exception as e:
        print(f"失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试2：最新日报页面
    print("\n" + "="*60)
    print("测试2：最新日报页面")
    print("="*60)
    try:
        # 试试找最新日报
        url = "https://www.soozhu.com/article/"
        html = gateway.get_html(url)
        soup = BeautifulSoup(html, 'html.parser')
        
        # 找日报链接
        links = soup.find_all('a')
        print("\n找日报相关链接...")
        count = 0
        for link in links:
            text = link.get_text(strip=True)
            if '生猪日报' in text or '猪价' in text:
                href = link.get('href', '')
                print(f"  {text} -> {href}")
                count += 1
                if count > 10:
                    break
                
    except Exception as e:
        print(f"失败: {e}")
    
    gateway.close()


if __name__ == "__main__":
    test_soozhu()
