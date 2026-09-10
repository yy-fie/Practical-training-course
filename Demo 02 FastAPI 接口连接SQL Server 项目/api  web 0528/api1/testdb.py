import pyodbc
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')




#  使用 linma进行编程   运行python程序  需要安装扩展插件   Code  Runner      再重启下编辑器
# python -m pip install pyodbc

# print("可用的驱动程序:")
# for driver in pyodbc.drivers():
#     if 'SQL Server' in driver:
#         print(f"  {driver}")


#  *********数据库接口服务***************

# 本地数据库存储着业务数据


# 连接 SQL Server 数据库
try:
    # 修改以下连接参数以匹配你的实际配置
    server = '.'  # 或者是 '(local)'、'127.0.0.1'、'.\\SQLEXPRESS'
    database = 'TTT'
    
    # 使用 Windows 身份验证，无需用户名和密码
    # 创建连接字符串
    conn_str = f'DRIVER={{SQL Server Native Client 11.0}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'

    # 建立连接
    connection = pyodbc.connect(conn_str)
    print("成功连接到数据库！")
    
    # 创建游标对象
    cursor = connection.cursor()
    
    # 查询专业表中的所有记录
    cursor.execute("select  top 10 *  from    stations ")  
    
    # 获取查询结果
    rows = cursor.fetchall()
    
    # 打印结果
    for row in rows:
       print(row)
        
    # 关闭连接
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"连接失败：{e}")