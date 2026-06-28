# -*- coding: utf-8 -*-
"""
测试农业农村部API - 找生猪品类
"""
import sys
import os
import requests

# 修复Windows控制台编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch.base import DataGateway
from utils.logger import get_logger

logger = get_logger("test_moa")


def test_moa_api():
    """测试农业农村部API"""
    
    base_url = "https://ncpscxx.moa.gov.cn"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36',
        'Origin': 'https://ncpscxx.moa.gov.cn',
        'Referer': 'https://ncpscxx.moa.gov.cn/',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Content-Type': 'application/json;charset=UTF-8'
    }
    
    gateway = DataGateway()
    gateway.session.headers.update(headers)
    
    # 测试1：获取完整品类列表，找生猪
    print("\n" + "="*60)
    print("测试1：获取品类列表（找生猪）")
    print("="*60)
    try:
        url = base_url + "/product/sys-variety/selectList"
        resp = gateway.session.post(url, json={}, timeout=10)
        data = resp.json()
        
        if data.get('code') == 0:
            varieties = data.get('data', [])
            print(f"共找到 {len(varieties)} 个品类：")
            for v in varieties:
                code = v.get('varietyCode', '')
                name = v.get('varietyName', '')
                pid = v.get('pid', '')
                print(f"  {code:10} {name:15} 父级:{pid}")
                
                # 如果是畜禽类，可能有子分类，继续查
                if '畜' in name or '禽' in name or '猪' in name:
                    print(f"    -> 可能包含生猪，继续查子分类...")
    except Exception as e:
        print(f"失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试2：试试其他可能的价格接口
    print("\n" + "="*60)
    print("测试2：尝试不同的价格接口路径")
    print("="*60)
    
    possible_paths = [
        "/product/price-info/getDailyPrice",
        "/product/price-info/getPrice",
        "/product/price-info/list",
        "/product/price/getDaily",
        "/product/daily-price/list",
        "/api/price/daily",
    ]
    
    for path in possible_paths:
        try:
            url = base_url + path
            resp = gateway.session.post(url, json={"pageNum":1, "pageSize":10}, timeout=5)
            print(f"  {path:40} -> {resp.status_code}")
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    print(f"     返回: {str(data)[:200]}")
                except:
                    print(f"     内容: {resp.text[:200]}")
        except Exception as e:
            print(f"  {path:40} -> 错误: {str(e)[:50]}")
    
    gateway.close()


if __name__ == "__main__":
    test_moa_api()
