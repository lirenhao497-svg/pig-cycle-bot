"""
Railway 部署入口点
将 sys.path 指向 web-dashboard 子目录以正确导入 backend 模块
"""
import sys
import os

# 将 web-dashboard 目录加入模块搜索路径
dashboard_dir = os.path.join(os.path.dirname(__file__), "web-dashboard")
sys.path.insert(0, dashboard_dir)

# 导入并启动 FastAPI 应用
from backend import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend:app", host="0.0.0.0", port=port, reload=False)
