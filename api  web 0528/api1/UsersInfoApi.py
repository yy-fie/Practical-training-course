from fastapi import FastAPI, HTTPException, Query
from typing import List
from database import get_db_connection
from schemas import User, UserList, UserCreate


def register_user_routes(app: FastAPI):
    """注册用户相关的API路由"""

    @app.post("/api/users", response_model=User, status_code=201)
    def create_user(user: UserCreate):
        """
        添加新用户
        
        - **realName**: 真实姓名
        - **phone**: 手机号
        - **roleId**: 角色ID
        - **departmentId**: 部门ID
        - **gender**: 性别
        - **nativePlace**: 籍贯
        - **politicalStatus**: 政治面貌
        - **loginPassword**: 登录密码
        - **idCard**: 身份证号
        - **email**: 邮箱
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            insert_query = """
                INSERT INTO UsersInfo (realName, phone, roleId, departmentId, gender, nativePlace, politicalStatus, loginPassword, idCard, email) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, (
                user.realName,
                user.phone,
                user.roleId,
                user.departmentId,
                user.gender,
                user.nativePlace,
                user.politicalStatus,
                user.loginPassword,
                user.idCard,
                user.email
            ))
            
            connection.commit()
            
            select_query = "SELECT TOP 1 userId, realName, phone, roleId, departmentId, gender, nativePlace, politicalStatus, loginPassword, idCard, email FROM UsersInfo ORDER BY userId DESC"
            cursor.execute(select_query)
            row = cursor.fetchone()
            
            if row:
                columns = [column[0] for column in cursor.description]
                user_dict = dict(zip(columns, row))
                return User(**user_dict)
            else:
                raise HTTPException(status_code=500, detail="创建用户失败")
            
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"创建用户失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.delete("/api/usersDelete", status_code=200)
    def delete_users(user_ids: List[int] = Query(..., description="要删除的用户ID列表")):
        """
        批量删除指定ID的用户
        
        - **user_ids**: 要删除的用户ID列表
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            if not user_ids:
                raise HTTPException(status_code=400, detail="请提供至少一个用户ID")
            
            placeholders = ','.join(['?'] * len(user_ids))
            check_query = f"SELECT COUNT(*) FROM UsersInfo WHERE userId IN ({placeholders})"
            cursor.execute(check_query, user_ids)
            existing_count = cursor.fetchone()[0]
            
            if existing_count != len(user_ids):
                raise HTTPException(status_code=404, detail=f"部分用户ID不存在，无法删除")
            
            delete_query = f"DELETE FROM UsersInfo WHERE userId IN ({placeholders})"
            cursor.execute(delete_query, user_ids)
            
            connection.commit()
            
            return {"msg": f"成功删除 {len(user_ids)} 个用户", "status": 200, "deleted_count": len(user_ids)}
            
        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"批量删除用户失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.delete("/api/users/{user_id}", status_code=204)
    def delete_user(user_id: int):
        """
        删除指定ID的用户
        
        - **user_id**: 要删除的用户ID
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            check_query = "SELECT COUNT(*) FROM UsersInfo WHERE userId = ?"
            cursor.execute(check_query, (user_id,))
            count = cursor.fetchone()[0]
            
            if count == 0:
                raise HTTPException(status_code=404, detail=f"用户ID {user_id} 不存在，无法删除")
            
            delete_query = "DELETE FROM UsersInfo WHERE userId = ?"
            cursor.execute(delete_query, (user_id,))
            
            connection.commit()
            
            return {"msg":"删除成功","status":204}
            
        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"删除用户失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.put("/api/users/{user_id}", response_model=User)
    def update_user(user_id: int, user: UserCreate):
        """
        更新指定ID的用户信息（完整更新）
        
        - **user_id**: 要更新的用户ID
        - **realName**: 真实姓名
        - **phone**: 手机号
        - **roleId**: 角色ID
        - **departmentId**: 部门ID
        - **gender**: 性别
        - **nativePlace**: 籍贯
        - **politicalStatus**: 政治面貌
        - **loginPassword**: 登录密码
        - **idCard**: 身份证号
        - **email**: 邮箱
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            check_query = "SELECT COUNT(*) FROM UsersInfo WHERE userId = ?"
            cursor.execute(check_query, (user_id,))
            count = cursor.fetchone()[0]
            
            if count == 0:
                raise HTTPException(status_code=404, detail=f"用户ID {user_id} 不存在，无法更新")
            
            update_query = """
                UPDATE UsersInfo 
                SET realName = ?, 
                    phone = ?, 
                    roleId = ?,
                    departmentId = ?,
                    gender = ?,
                    nativePlace = ?,
                    politicalStatus = ?,
                    loginPassword = ?,
                    idCard = ?,
                    email = ?
                WHERE userId = ?
            """
            cursor.execute(update_query, (
                user.realName,
                user.phone,
                user.roleId,
                user.departmentId,
                user.gender,
                user.nativePlace,
                user.politicalStatus,
                user.loginPassword,
                user.idCard,
                user.email,
                user_id
            ))
            
            connection.commit()
            
            select_query = "SELECT userId, realName, phone, roleId, departmentId, gender, nativePlace, politicalStatus, loginPassword, idCard, email FROM UsersInfo WHERE userId = ?"
            cursor.execute(select_query, (user_id,))
            row = cursor.fetchone()
            
            if row:
                columns = [column[0] for column in cursor.description]
                user_dict = dict(zip(columns, row))
                return User(**user_dict)
            else:
                raise HTTPException(status_code=500, detail="更新后查询失败")
            
        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"更新用户失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/users", response_model=UserList)
    def get_users(
        page: int = Query(default=1, ge=1, description="页码，从1开始"), 
        rows: int = Query(default=10, ge=1, le=100, description="每页记录数"),
        realName: str = Query(default=None, description="真实姓名（可选，支持模糊搜索）"),
        phone: str = Query(default=None, description="手机号（可选，支持模糊搜索）"),
        email: str = Query(default=None, description="邮箱（可选，支持模糊搜索）"),
        roleId: int = Query(default=None, description="角色ID（可选）"),
        departmentId: int = Query(default=None, description="部门ID（可选）"),
        gender: str = Query(default=None, description="性别（可选）"),
        sort_by: str = Query(default=None, description="排序字段和方式：支持单个或多个排序条件，格式为 '字段 asc/desc'，多个条件用逗号分隔。例如：'realName asc' 或 'userId desc'。支持的字段：realName(姓名), phone(手机), email(邮箱)，默认为userId升序")
    ):
        """
        查询 UsersInfo 表的用户记录（支持分页、姓名搜索、手机搜索、邮箱搜索和排序）
        
        - **page**: 页码，从1开始，默认第1页
        - **rows**: 每页记录数量，默认10条，最大100条
        - **realName**: 真实姓名（可选），支持模糊搜索
        - **phone**: 手机号（可选），支持模糊搜索
        - **email**: 邮箱（可选），支持模糊搜索
        - **roleId**: 角色ID（可选）
        - **departmentId**: 部门ID（可选）
        - **gender**: 性别（可选）
        - **sort_by**: 排序字段和方式，支持单个或多个排序条件。格式为 '字段 asc/desc'，多个条件用逗号分隔。
                     例如：'realName asc' 表示按姓名升序；
                     'roleId asc,realName desc' 表示先按角色ID升序，再按姓名降序。
                     支持的字段：realName(姓名), phone(手机), email(邮箱)。
                     默认为 userId 升序
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            start_row = (page - 1) * rows + 1
            end_row = page * rows
            
            # 确定排序规则（支持多条件排序）
            order_clause = "ORDER BY userId ASC"
            if sort_by:
                # 分割多个排序条件
                sort_conditions = [s.strip() for s in sort_by.split(',')]
                order_parts = []
                
                for sort_condition in sort_conditions:
                    sort_parts = sort_condition.lower().split()
                    if len(sort_parts) == 2 and sort_parts[1] in ["asc", "desc"]:
                        field = sort_parts[0].lower()
                        order_direction = sort_parts[1].upper()
                        
                        if field == "realname":
                            order_parts.append(f"realName {order_direction}")
                        elif field == "phone":
                            order_parts.append(f"phone {order_direction}")
                        elif field == "email":
                            order_parts.append(f"email {order_direction}")
                
                # 如果有有效的排序条件，构建 ORDER BY 子句
                if order_parts:
                    order_clause = "ORDER BY " + ", ".join(order_parts)
            
            # 构建 WHERE 条件和参数列表
            where_conditions = []
            params = []
            
            if realName:
                where_conditions.append("realName LIKE ?")
                params.append(f"%{realName}%")
            
            if phone:
                where_conditions.append("phone LIKE ?")
                params.append(f"%{phone}%")
            
            if email:
                where_conditions.append("email LIKE ?")
                params.append(f"%{email}%")
            
            if roleId is not None:
                where_conditions.append("roleId = ?")
                params.append(roleId)
            
            if departmentId is not None:
                where_conditions.append("departmentId = ?")
                params.append(departmentId)
            
            if gender:
                where_conditions.append("gender = ?")
                params.append(gender)
            
            # 构建计数查询
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)
                count_query = f"SELECT COUNT(*) FROM UsersInfo{where_clause}"
                cursor.execute(count_query, params)
            else:
                count_query = "SELECT COUNT(*) FROM UsersInfo"
                cursor.execute(count_query)
            
            total_count = cursor.fetchone()[0]
            
            # 构建数据查询
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)
                query = f"""
                SELECT * FROM (
                    SELECT ROW_NUMBER() OVER ({order_clause}) AS RowNum, 
                        userId, realName, phone, roleId, departmentId, gender, nativePlace, politicalStatus, loginPassword, idCard, email 
                    FROM UsersInfo{where_clause}
                ) AS RankedUsers
                WHERE RowNum BETWEEN ? AND ?
                """
                cursor.execute(query, params + [start_row, end_row])
            else:
                query = f"""
                SELECT * FROM (
                    SELECT ROW_NUMBER() OVER ({order_clause}) AS RowNum, 
                        userId, realName, phone, roleId, departmentId, gender, nativePlace, politicalStatus, loginPassword, idCard, email 
                    FROM UsersInfo
                ) AS RankedUsers
                WHERE RowNum BETWEEN ? AND ?
                """
                cursor.execute(query, (start_row, end_row))
            
            columns = [column[0] for column in cursor.description]
            rows_data = cursor.fetchall()
            
            users = []
            for row in rows_data:
                user_dict = dict(zip(columns, row))
                user_dict.pop('RowNum', None)
                users.append(User(**user_dict))
            
            return UserList(
                total=total_count,
                rows=users
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/users/search")
    def search_users(keyword: str = Query(..., min_length=1, description="搜索关键词")):
        """
        根据关键词搜索用户
        
        - **keyword**: 搜索关键词（支持姓名、手机、邮箱、身份证号模糊搜索）
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            search_pattern = f"%{keyword}%"
            query = """
                SELECT TOP 20 userId, realName, phone, roleId, departmentId, gender, nativePlace, politicalStatus, loginPassword, idCard, email 
                FROM UsersInfo 
                WHERE realName LIKE ?
                   OR phone LIKE ?
                   OR email LIKE ?
                   OR idCard LIKE ?
                ORDER BY userId
            """
            cursor.execute(query, (search_pattern, search_pattern, search_pattern, search_pattern))
            
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            
            users = []
            for row in rows:
                user_dict = dict(zip(columns, row))
                users.append(User(**user_dict))
            
            return {
                "total": len(users),
                "keyword": keyword,
                "users": users
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/users/{user_id}", response_model=User)
    def get_user_by_id(user_id: int):
        """
        根据 ID 查询单个用户
        
        - **user_id**: 用户ID
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            query = "SELECT userId, realName, phone, roleId, departmentId, gender, nativePlace, politicalStatus, loginPassword, idCard, email FROM UsersInfo WHERE userId = ?"
            cursor.execute(query, (user_id,))
            
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail=f"用户ID {user_id} 不存在")
            
            columns = [column[0] for column in cursor.description]
            user_dict = dict(zip(columns, row))
            
            return User(**user_dict)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.post("/api/users/login", response_model=User)
    def login_user(username: str = Query(..., description="用户名（手机号或邮箱）"), password: str = Query(..., description="登录密码")):
        """
        用户登录接口
        
        - **username**: 用户名（支持手机号或邮箱）
        - **password**: 登录密码
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            query = """
                SELECT userId, realName, phone, roleId, departmentId, gender, nativePlace, politicalStatus, loginPassword, idCard, email 
                FROM UsersInfo 
                WHERE (phone = ? OR email = ?) AND loginPassword = ?
            """
            cursor.execute(query, (username, username, password))
            
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=401, detail="用户名或密码错误")
            
            columns = [column[0] for column in cursor.description]
            user_dict = dict(zip(columns, row))
            
            return User(**user_dict)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
