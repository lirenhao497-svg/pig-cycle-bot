# -*- coding: utf-8 -*-
"""
测试正大猪博士数据爬取
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

logger = get_logger("test_cpcti")


def test_cpcti():
    """测试正大猪博士数据爬取"""
    
    gateway = DataGateway()
    
    print("\n" + "="*60)
    print("测试：正大猪博士猪价页面")
    print("="*60)
    try:
        url = "https://www.cpcti.com/"
        html = gateway.get_html(url)
        print(f"页面长度: {len(html)} 字符")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 打印页面标题
        title = soup.find('title')
        if title:
            print(f"\n页面标题: {title.get_text()}")
        
        # 找价格数据
        print("\n找价格相关内容...")
        all_text = soup.get_text()
        lines = all_text.split('\n')
        count = 0
        for line in lines:
            line = line.strip()
            if line and len(line) < 80 and ('生猪' in line or '玉米' in line or '豆粕' in line or '价格' in line or '全国' in line):
                print(f"  {line}")
                count += 1
                if count > 30:
                    break
        
        # 找表格
        print("\n找表格...")
        tables = soup.find_all('table')
        print(f"找到 {len(tables)} 个表格")
        
        for i, table in enumerate(tables[:5]):
            rows = table.find_all('tr')
            print(f"\n表格{i} ({len(rows)}行):")
            for row in rows[:8]:
                cells = row.find_all(['td', 'th'])
                cell_texts = [c.get_text(strip=True) for c in cells]
                if any(cell_texts):
                    print(f"  {' | '.join(cell_texts)}")
        
        # 试试找分省数据
        print("\n找分省数据...")
        divs = soup.find_all('div', class_=lambda x: x and 'price' in x.lower() if x else False)
        print(f"找到 {len(divs)} 个price相关div")
        
        for div in divs[:5]:
            text = div.get_text(strip=True)
            if text:
                print(f"  {text[:100]}")
                
    except Exception as e:
        print(f"失败: {e}")
        import traceback
        traceback.print_exc()
    
    gateway.close()


if __name__ == "__main__":
    test_cpcti()
