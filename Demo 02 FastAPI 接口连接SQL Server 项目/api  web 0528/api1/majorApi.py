from fastapi import FastAPI, HTTPException, Query
from typing import List
from database import get_db_connection
from schemas import Major, MajorList, MajorCreate


def register_major_routes(app: FastAPI):
    """注册专业(Major)相关的API路由"""

    @app.post("/api/majors", response_model=Major, status_code=201)
    def create_major(major: MajorCreate):
        """
        添加新专业

        - **majorName**: 专业名称
        - **departmentId**: 所属院系ID
        - **majorCode**: 专业代码
        - **category**: 学科门类
        """
        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            insert_query = """
                INSERT INTO Major (majorName, departmentId, majorCode, category)
                VALUES (?, ?, ?, ?)
            """
            cursor.execute(insert_query, (
                major.majorName,
                major.departmentId,
                major.majorCode,
                major.category
            ))

            connection.commit()

            select_query = """
                SELECT TOP 1 majorId, majorName, departmentId, majorCode, category
                FROM Major ORDER BY majorId DESC
            """
            cursor.execute(select_query)
            row = cursor.fetchone()

            if row:
                columns = [column[0] for column in cursor.description]
                major_dict = dict(zip(columns, row))
                return Major(**major_dict)
            else:
                raise HTTPException(status_code=500, detail="创建专业失败")

        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"创建专业失败: {str(e)}")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.delete("/api/majorsDelete", status_code=200)
    def delete_majors(major_ids: List[int] = Query(..., description="要删除的专业ID列表")):
        """
        批量删除指定ID的专业

        - **major_ids**: 要删除的专业ID列表
        """
        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            if not major_ids:
                raise HTTPException(status_code=400, detail="请提供至少一个专业ID")

            placeholders = ','.join(['?'] * len(major_ids))
            check_query = f"SELECT COUNT(*) FROM Major WHERE majorId IN ({placeholders})"
            cursor.execute(check_query, major_ids)
            existing_count = cursor.fetchone()[0]

            if existing_count != len(major_ids):
                raise HTTPException(status_code=404, detail="部分专业ID不存在，无法删除")

            delete_query = f"DELETE FROM Major WHERE majorId IN ({placeholders})"
            cursor.execute(delete_query, major_ids)

            connection.commit()

            return {
                "msg": f"成功删除 {len(major_ids)} 个专业",
                "status": 200,
                "deleted_count": len(major_ids)
            }

        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"批量删除专业失败: {str(e)}")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.delete("/api/majors/{major_id}", status_code=204)
    def delete_major(major_id: int):
        """
        删除指定ID的专业

        - **major_id**: 要删除的专业ID
        """
        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            check_query = "SELECT COUNT(*) FROM Major WHERE majorId = ?"
            cursor.execute(check_query, (major_id,))
            count = cursor.fetchone()[0]

            if count == 0:
                raise HTTPException(status_code=404, detail=f"专业ID {major_id} 不存在，无法删除")

            delete_query = "DELETE FROM Major WHERE majorId = ?"
            cursor.execute(delete_query, (major_id,))

            connection.commit()

            return {"msg": "删除成功", "status": 204}

        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"删除专业失败: {str(e)}")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.put("/api/majors/{major_id}", response_model=Major)
    def update_major(major_id: int, major: MajorCreate):
        """
        更新指定ID的专业信息（完整更新）

        - **major_id**: 要更新的专业ID
        - **majorName**: 专业名称
        - **departmentId**: 所属院系ID
        - **majorCode**: 专业代码
        - **category**: 学科门类
        """
        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            check_query = "SELECT COUNT(*) FROM Major WHERE majorId = ?"
            cursor.execute(check_query, (major_id,))
            count = cursor.fetchone()[0]

            if count == 0:
                raise HTTPException(status_code=404, detail=f"专业ID {major_id} 不存在，无法更新")

            update_query = """
                UPDATE Major
                SET majorName = ?,
                    departmentId = ?,
                    majorCode = ?,
                    category = ?
                WHERE majorId = ?
            """
            cursor.execute(update_query, (
                major.majorName,
                major.departmentId,
                major.majorCode,
                major.category,
                major_id
            ))

            connection.commit()

            select_query = """
                SELECT majorId, majorName, departmentId, majorCode, category
                FROM Major WHERE majorId = ?
            """
            cursor.execute(select_query, (major_id,))
            row = cursor.fetchone()

            if row:
                columns = [column[0] for column in cursor.description]
                major_dict = dict(zip(columns, row))
                return Major(**major_dict)
            else:
                raise HTTPException(status_code=500, detail="更新后查询失败")

        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"更新专业失败: {str(e)}")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/majors", response_model=MajorList)
    def get_majors(
        page: int = Query(default=1, ge=1, description="页码，从1开始"),
        rows: int = Query(default=10, ge=1, le=100, description="每页记录数"),
        departmentId: int = Query(default=None, description="所属院系ID（可选）"),
        majorName: str = Query(default=None, description="专业名称（可选，支持模糊搜索）"),
        majorCode: str = Query(default=None, description="专业代码（可选，支持模糊搜索）"),
        category: str = Query(default=None, description="学科门类（可选，精确匹配）"),
        sort_by: str = Query(
            default=None,
            description="排序字段和方式：支持单个或多个排序条件，格式为 '字段 asc/desc'，"
                        "多个条件用逗号分隔。支持的字段：majorName(专业名称), majorCode(专业代码), "
                        "category(学科门类), departmentName(院系名称)，默认为majorId升序"
        )
    ):
        """
        查询 Major 表的专业记录（支持分页、院系过滤、名称/代码搜索、门类过滤和排序）

        - **page**: 页码，从1开始，默认第1页
        - **rows**: 每页记录数量，默认10条，最大100条
        - **departmentId**: 所属院系ID（可选）
        - **majorName**: 专业名称（可选），支持模糊搜索
        - **majorCode**: 专业代码（可选），支持模糊搜索
        - **category**: 学科门类（可选），精确匹配
        - **sort_by**: 排序字段和方式，支持 'majorName asc/desc'、'departmentName asc/desc' 等，默认为 majorId 升序
        """
        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            start_row = (page - 1) * rows + 1
            end_row = page * rows

            # 确定排序规则（支持多条件排序）
            order_clause = "ORDER BY majorId ASC"
            if sort_by:
                sort_conditions = [s.strip() for s in sort_by.split(',')]
                order_parts = []

                for sort_condition in sort_conditions:
                    sort_parts = sort_condition.lower().split()
                    if len(sort_parts) == 2 and sort_parts[1] in ["asc", "desc"]:
                        field = sort_parts[0].lower()
                        order_direction = sort_parts[1].upper()

                        if field == "majorname":
                            order_parts.append(f"majorName {order_direction}")
                        elif field == "majorcode":
                            order_parts.append(f"majorCode {order_direction}")
                        elif field == "category":
                            order_parts.append(f"category {order_direction}")
                        elif field == "departmentid":
                            order_parts.append(f"departmentId {order_direction}")
                        elif field == "departmentname":
                            order_parts.append(f"departmentName {order_direction}")

                if order_parts:
                    order_clause = "ORDER BY " + ", ".join(order_parts)

            # 构建 WHERE 条件和参数列表（MajorView 含 departmentName）
            where_conditions = []
            params = []

            if departmentId is not None:
                where_conditions.append("departmentId = ?")
                params.append(departmentId)

            if majorName:
                where_conditions.append("majorName LIKE ?")
                params.append(f"%{majorName}%")

            if majorCode:
                where_conditions.append("majorCode LIKE ?")
                params.append(f"%{majorCode}%")

            if category:
                where_conditions.append("LTRIM(RTRIM(category)) = LTRIM(RTRIM(?))")
                params.append(category)

            where_clause = ""
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)

            count_query = f"SELECT COUNT(*) FROM MajorView{where_clause}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]

            query = f"""
                SELECT * FROM (
                    SELECT ROW_NUMBER() OVER ({order_clause}) AS RowNum,
                           majorId, majorName, departmentId, majorCode, category, departmentName
                    FROM MajorView{where_clause}
                ) AS RankedMajors
                WHERE RowNum BETWEEN ? AND ?
            """
            cursor.execute(query, params + [start_row, end_row])

            columns = [column[0] for column in cursor.description]
            rows_data = cursor.fetchall()

            majors = []
            for row in rows_data:
                major_dict = dict(zip(columns, row))
                major_dict.pop('RowNum', None)
                majors.append(Major(**major_dict))

            return MajorList(
                total=total_count,
                rows=majors
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/majors/categories")
    def get_all_major_categories():
        """
        获取所有学科门类名称（去重）
        """
        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            query = """
                SELECT DISTINCT category FROM Major
                WHERE category IS NOT NULL ORDER BY category
            """
            cursor.execute(query)
            rows = cursor.fetchall()

            categories = [row[0] for row in rows if row[0]]

            return {
                "total": len(categories),
                "categories": categories
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/majors/search")
    def search_majors(keyword: str = Query(..., min_length=1, description="搜索关键词")):
        """
        根据关键词搜索专业

        - **keyword**: 搜索关键词（支持专业名称、专业代码、学科门类模糊搜索）
        """
        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            search_pattern = f"%{keyword}%"
            query = """
                SELECT TOP 20 majorId, majorName, departmentId, majorCode, category, departmentName
                FROM MajorView
                WHERE majorName LIKE ?
                   OR majorCode LIKE ?
                   OR category LIKE ?
                ORDER BY majorId
            """
            cursor.execute(query, (search_pattern, search_pattern, search_pattern))

            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()

            majors = []
            for row in rows:
                major_dict = dict(zip(columns, row))
                majors.append(Major(**major_dict))

            return {
                "total": len(majors),
                "keyword": keyword,
                "majors": majors
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/majors/{major_id}", response_model=Major)
    def get_major_by_id(major_id: int):
        """
        根据 ID 查询单个专业

        - **major_id**: 专业ID
        """
        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            query = """
                SELECT majorId, majorName, departmentId, majorCode, category, departmentName
                FROM MajorView WHERE majorId = ?
            """
            cursor.execute(query, (major_id,))

            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail=f"专业ID {major_id} 不存在")

            columns = [column[0] for column in cursor.description]
            major_dict = dict(zip(columns, row))

            return Major(**major_dict)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
