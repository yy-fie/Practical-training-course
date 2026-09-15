# 从 fastapi 库导入必要的类和函数
from fastapi import FastAPI, Query  # FastAPI主类、查询参数验证类
from fastapi.middleware.cors import CORSMiddleware  # 跨域资源共享中间件
import sys  # 系统相关功能模块
import io  # 输入输出流处理模块

from stationApi import register_station_routes  # 导入站点API路由注册函数
from bookApi import register_book_routes  # 导入图书API路由注册函数
from buildingApi import register_building_routes  # 导入建筑API路由注册函数
from UsersInfoApi import register_user_routes
from permissionApi import register_permission_routes
from grantApi import register_grant_routes
from accessControl import register_access_control
from adminUserApi import register_admin_user_routes
from floorApi import register_floor_routes  # 导入楼层API路由注册函数
from majorApi import register_major_routes  # 导入专业API路由注册函数

# 设置标准输出编码为UTF-8，解决中文乱码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 创建FastAPI应用实例，配置API基本信息
app = FastAPI(
    title="AI Database API",  # API标题
    description="API接口项目",  # API描述信息
    version="1.0.0"  # API版本号
)

# 添加CORS中间件，允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源的请求
    allow_credentials=True,  # 允许携带认证信息
    allow_methods=["*"],  # 允许所有HTTP方法（GET、POST等）
    allow_headers=["*"],  # 允许所有请求头
)


register_access_control(app)

# 注册路由
register_station_routes(app)
register_book_routes(app)
register_building_routes(app)
register_user_routes(app)
register_permission_routes(app)
register_grant_routes(app)
register_admin_user_routes(app)
register_floor_routes(app)
register_major_routes(app)

# 定义根路径GET接口
@app.get("/")
def read_root():
    """根路径"""
    # 返回欢迎信息和API端点列表
    return {
        "message": "Welcome to AI Database API",  # 欢迎消息
        "description": "API接口项目",  # API描述信息
        "version": "1.0.0",  # API版本号
        "docs": "/docs",  # Swagger文档地址
        "redoc": "/redoc",  # ReDoc文档地址
        "endpoints": {  # 可用的API端点字典
           
            "stations": {  # 站点管理相关接口
                "get_stations": {
                    "method": "GET",
                    "path": "/api/stations",
                    "description": "获取站点列表（支持分页）",
                    "params": ["page", "rows"]
                },
                "create_station": {
                    "method": "POST",
                    "path": "/api/stations",
                    "description": "创建新站点"
                },
                "update_station": {
                    "method": "PUT",
                    "path": "/api/stations/{station_id}",
                    "description": "更新站点信息"
                },
                "delete_station": {
                    "method": "DELETE",
                    "path": "/api/stations/{station_id}",
                    "description": "删除单个站点"
                },
                "delete_stations": {
                    "method": "DELETE",
                    "path": "/api/stationsDelete",
                    "description": "批量删除站点",
                    "params": ["station_ids"]
                },
                "get_station_by_id": {
                    "method": "GET",
                    "path": "/api/stations/{station_id}",
                    "description": "根据ID查询单个站点"
                },
                "get_stations_by_line": {
                    "method": "GET",
                    "path": "/api/stations/line",
                    "description": "按线路查询站点（支持分页）",
                    "params": ["line", "page", "page_size"]
                },
                "get_stations_by_district": {
                    "method": "GET",
                    "path": "/api/stations/district",
                    "description": "按区域查询站点（支持分页）",
                    "params": ["district", "page", "page_size"]
                },
                "search_stations": {
                    "method": "GET",
                    "path": "/api/stations/search",
                    "description": "搜索站点（支持站点名称、线路、区域模糊搜索）",
                    "params": ["keyword"]
                }
            }
        }
    }

if __name__ == "__main__":  # 如果直接运行此文件（而非被导入）
    import uvicorn  # 导入uvicorn服务器
    uvicorn.run(app, host="127.0.0.1", port=9001)  # 
