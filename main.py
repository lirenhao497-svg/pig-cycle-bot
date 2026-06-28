# -*- coding: utf-8 -*-
"""
猪周期爬虫 - 主入口
调度统一在 scheduler.py 中
"""
import sys
import os

# 修复Windows控制台编码问题
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from scheduler import TaskScheduler
from storage.db import HogDatabase


def init_project():
    """首次运行：初始化项目结构和数据库"""
    print("🚀 首次运行，初始化猪周期爬虫项目...")
    
    # 确保data目录存在（运行产物，不是代码结构）
    data_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # 初始化数据库
    db = HogDatabase()
    print("✅ SQLite数据库初始化成功")
    print(f"📁 数据库文件: {os.path.join(data_dir, 'hog_data.db')}")
    db.close()
    
    print("\n📋 项目工程结构:")
    print(f"  {BASE_DIR}\\")
    print(f"  ├── main.py          # 主入口")
    print(f"  ├── config.py        # 全局配置")
    print(f"  ├── scheduler.py     # 任务调度")
    print(f"  ├── fetch/           # 数据层（爬虫）")
    print(f"  │   ├── base.py      # 统一请求基类")
    print(f"  │   ├── pig_price.py # 生猪价格")
    print(f"  │   ├── futures.py   # 期货数据")
    print(f"  │   └── feed_price.py# 饲料价格")
    print(f"  ├── storage/         # 数据层（存储）")
    print(f"  │   └── db.py        # SQLite封装")
    print(f"  ├── analysis/        # 逻辑层")
    print(f"  │   ├── indicators.py# 指标计算")
    print(f"  │   ├── cycle.py     # 猪周期逻辑")
    print(f"  │   └── report.py    # 报告输出")
    print(f"  ├── notify/          # 输出层")
    print(f"  │   └── wechat.py    # 微信推送")
    print(f"  └── data/            # 运行产物（自动生成）")
    
    print("\n💡 三层架构说明:")
    print("  ① 数据层 (fetch + storage) - 稳定，很少变")
    print("  ② 逻辑层 (indicators + cycle) - 经常迭代优化")
    print("  ③ 输出层 (report + wechat) - 最容易变")
    
    print("\n💡 下一步操作:")
    print("  1. 编辑 config.py 填入你的API密钥")
    print("  2. 运行 python main.py 执行每日任务")
    print("  3. 逐步完善 fetch/ 下各爬虫的具体解析逻辑")


if __name__ == "__main__":
    # 判断是否首次运行（数据库文件不存在则初始化）
    db_path = os.path.join(BASE_DIR, "data", "hog_data.db")
    if not os.path.exists(db_path):
        init_project()
    else:
        # 正常运行：执行每日任务
        scheduler = TaskScheduler()
        scheduler.run_all_daily()
