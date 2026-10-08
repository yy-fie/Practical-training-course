import os
import pyodbc

# 数据库连接配置
SERVER = os.getenv('DB_SERVER', '.')
DATABASE = os.getenv('DB_NAME', 'AI')

def get_db_connection():
    """获取数据库连接"""
    installed = pyodbc.drivers()
    driver = os.getenv('DB_DRIVER') or next(
        (d for d in ('ODBC Driver 17 for SQL Server', 'ODBC Driver 18 for SQL Server',
                     'SQL Server Native Client 11.0', 'SQL Server') if d in installed), None)
    if not driver:
        raise RuntimeError('未安装 SQL Server ODBC 驱动，请安装 ODBC Driver 17 或设置 DB_DRIVER')
    conn_str = (f'DRIVER={{{driver}}};SERVER={SERVER};DATABASE={DATABASE};'
                'Trusted_Connection=yes;TrustServerCertificate=yes;')
    connection = pyodbc.connect(conn_str, timeout=5)
    return connection
