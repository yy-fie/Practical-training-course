import pyodbc

# 数据库连接配置
SERVER = '.'
DATABASE = 'AI'

def get_db_connection():
    """获取数据库连接"""
    conn_str = f'DRIVER={{SQL Server Native Client 11.0}};SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes;'
    connection = pyodbc.connect(conn_str)
    return connection
