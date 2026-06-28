# -*- coding: utf-8 -*-
"""
测试中国养猪网数据爬取
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

logger = get_logger("test_zhuwang")


def test_zhuwang():
    """测试中国养猪网数据爬取"""
    
    gateway = DataGateway()
    
    # 测试1：猪价页面
    print("\n" + "="*60)
    print("测试：中国养猪网猪价页面")
    print("="*60)
    try:
        url = "https://zhujia.zhuwang.com.cn/piglocal.shtml"
        html = gateway.get_html(url)
        print(f"页面长度: {len(html)} 字符")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 打印页面标题
        title = soup.find('title')
        if title:
            print(f"\n页面标题: {title.get_text()}")
        
        # 找全国价格
        print("\n找全国价格...")
        all_text = soup.get_text()
        lines = all_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and ('全国' in line or '外三元' in line or '内三元' in line) and len(line) < 100:
                print(f"  {line}")
        
        # 找分省价格
        print("\n找分省价格...")
        tables = soup.find_all('table')
        print(f"找到 {len(tables)} 个表格")
        
        for i, table in enumerate(tables[:3]):
            rows = table.find_all('tr')
            print(f"\n表格{i} ({len(rows)}行):")
            for row in rows[:5]:
                cells = row.find_all(['td', 'th'])
                cell_texts = [c.get_text(strip=True) for c in cells]
                if any(cell_texts):
                    print(f"  {' | '.join(cell_texts)}")
                
    except Exception as e:
        print(f"失败: {e}")
        import traceback
        traceback.print_exc()
    
    gateway.close()


if __name__ == "__main__":
    test_zhuwang()
