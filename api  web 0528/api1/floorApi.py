from fastapi import FastAPI, HTTPException, Query
from typing import List
from database import get_db_connection
from schemas import Floor, FloorList, FloorCreate


def register_floor_routes(app: FastAPI):
    """注册楼层(FloorInfo)相关的API路由"""

    @app.post("/api/floors", response_model=Floor, status_code=201)
    def create_floor(floor: FloorCreate):
        """
        添加新楼层

        - **floorName**: 楼层名称
        - **buildingId**: 所属建筑ID
        - **floorDescription**: 楼层描述
        """
        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            insert_query = """
                INSERT INTO FloorInfo (floorName, buildingId, floorDescription)
                VALUES (?, ?, ?)
            """
            cursor.execute(insert_query, (
                floor.floorName,
                floor.buildingId,
                floor.floorDescription
            ))

            connection.commit()

            select_query = """
                SELECT TOP 1 floorId, floorName, buildingId, floorDescription
                FROM FloorInfo ORDER BY floorId DESC
            """
            cursor.execute(select_query)
            row = cursor.fetchone()

            if row:
                columns = [column[0] for column in cursor.description]
                floor_dict = dict(zip(columns, row))
                return Floor(**floor_dict)
            else:
                raise HTTPException(status_code=500, detail="创建楼层失败")

        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"创建楼层失败: {str(e)}")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.delete("/api/floorsDelete", status_code=200)
    def delete_floors(floor_ids: List[int] = Query(..., description="要删除的楼层ID列表")):
        """
        批量删除指定ID的楼层

        - **floor_ids**: 要删除的楼层ID列表
        """
        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            if not floor_ids:
                raise HTTPException(status_code=400, detail="请提供至少一个楼层ID")

            placeholders = ','.join(['?'] * len(floor_ids))
            check_query = f"SELECT COUNT(*) FROM FloorInfo WHERE floorId IN ({placeholders})"
            cursor.execute(check_query, floor_ids)
            existing_count = cursor.fetchone()[0]

            if existing_count != len(floor_ids):
                raise HTTPException(status_code=404, detail="部分楼层ID不存在，无法删除")

            delete_query = f"DELETE FROM FloorInfo WHERE floorId IN ({placeholders})"
            cursor.execute(delete_query, floor_ids)

            connection.commit()

            return {
                "msg": f"成功删除 {len(floor_ids)} 个楼层",
                "status": 200,
                "deleted_count": len(floor_ids)
            }

        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"批量删除楼层失败: {str(e)}")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.delete("/api/floors/{floor_id}", status_code=204)
    def delete_floor(floor_id: int):
        """
        删除指定ID的楼层

        - **floor_id**: 要删除的楼层ID
        """
        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            check_query = "SELECT COUNT(*) FROM FloorInfo WHERE floorId = ?"
            cursor.execute(check_query, (floor_id,))
            count = cursor.fetchone()[0]

            if count == 0:
                raise HTTPException(status_code=404, detail=f"楼层ID {floor_id} 不存在，无法删除")

            delete_query = "DELETE FROM FloorInfo WHERE floorId = ?"
            cursor.execute(delete_query, (floor_id,))

            connection.commit()

            return {"msg": "删除成功", "status": 204}

        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"删除楼层失败: {str(e)}")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.put("/api/floors/{floor_id}", response_model=Floor)
    def update_floor(floor_id: int, floor: FloorCreate):
        """
        更新指定ID的楼层信息（完整更新）

        - **floor_id**: 要更新的楼层ID
        - **floorName**: 楼层名称
        - **buildingId**: 所属建筑ID
        - **floorDescription**: 楼层描述
        """
        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            check_query = "SELECT COUNT(*) FROM FloorInfo WHERE floorId = ?"
            cursor.execute(check_query, (floor_id,))
            count = cursor.fetchone()[0]

            if count == 0:
                raise HTTPException(status_code=404, detail=f"楼层ID {floor_id} 不存在，无法更新")

            update_query = """
                UPDATE FloorInfo
                SET floorName = ?,
                    buildingId = ?,
                    floorDescription = ?
                WHERE floorId = ?
            """
            cursor.execute(update_query, (
                floor.floorName,
                floor.buildingId,
                floor.floorDescription,
                floor_id
            ))

            connection.commit()

            select_query = """
                SELECT floorId, floorName, buildingId, floorDescription
                FROM FloorInfo WHERE floorId = ?
            """
            cursor.execute(select_query, (floor_id,))
            row = cursor.fetchone()

            if row:
                columns = [column[0] for column in cursor.description]
                floor_dict = dict(zip(columns, row))
                return Floor(**floor_dict)
            else:
                raise HTTPException(status_code=500, detail="更新后查询失败")

        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"更新楼层失败: {str(e)}")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/floors", response_model=FloorList)
    def get_floors(
        page: int = Query(default=1, ge=1, description="页码，从1开始"),
        rows: int = Query(default=10, ge=1, le=100, description="每页记录数"),
        buildingId: int = Query(default=None, description="所属建筑ID（可选）"),
        floorName: str = Query(default=None, description="楼层名称（可选，支持模糊搜索）"),
        sort_by: str = Query(
            default=None,
            description="排序字段和方式：支持单个或多个排序条件，格式为 '字段 asc/desc'，"
                        "多个条件用逗号分隔。例如：'floorName asc' 或 'buildingId desc'。"
                        "支持的字段：floorName(楼层名称), buildingId(建筑ID)，默认为floorId升序"
        )
    ):
        """
        查询 FloorInfo 表的楼层记录（支持分页、建筑过滤、名称搜索和排序）

        - **page**: 页码，从1开始，默认第1页
        - **rows**: 每页记录数量，默认10条，最大100条
        - **buildingId**: 所属建筑ID（可选），如果提供则只返回该建筑下的楼层
        - **floorName**: 楼层名称（可选），支持模糊搜索
        - **sort_by**: 排序字段和方式，支持 'floorName asc/desc'、'buildingId asc/desc'，默认为 floorId 升序
        """
        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            start_row = (page - 1) * rows + 1
            end_row = page * rows

            # 确定排序规则（支持多条件排序）
            order_clause = "ORDER BY floorId ASC"
            if sort_by:
                sort_conditions = [s.strip() for s in sort_by.split(',')]
                order_parts = []

                for sort_condition in sort_conditions:
                    sort_parts = sort_condition.lower().split()
                    if len(sort_parts) == 2 and sort_parts[1] in ["asc", "desc"]:
                        field = sort_parts[0].lower()
                        order_direction = sort_parts[1].upper()

                        if field == "floorname":
                            order_parts.append(f"floorName {order_direction}")
                        elif field == "buildingid":
                            order_parts.append(f"buildingId {order_direction}")

                if order_parts:
                    order_clause = "ORDER BY " + ", ".join(order_parts)

            # 构建 WHERE 条件和参数列表
            where_conditions = []
            params = []

            if buildingId is not None:
                where_conditions.append("buildingId = ?")
                params.append(buildingId)

            if floorName:
                where_conditions.append("floorName LIKE ?")
                params.append(f"%{floorName}%")

            # 构建计数查询
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)
                count_query = f"SELECT COUNT(*) FROM FloorInfo{where_clause}"
                cursor.execute(count_query, params)
            else:
                count_query = "SELECT COUNT(*) FROM FloorInfo"
                cursor.execute(count_query)

            total_count = cursor.fetchone()[0]

            # 构建数据查询
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)
                query = f"""
                SELECT * FROM (
                    SELECT ROW_NUMBER() OVER ({order_clause}) AS RowNum,
                        floorId, floorName, buildingId, floorDescription
                    FROM FloorInfo{where_clause}
                ) AS RankedFloors
                WHERE RowNum BETWEEN ? AND ?
                """
                cursor.execute(query, params + [start_row, end_row])
            else:
                query = f"""
                SELECT * FROM (
                    SELECT ROW_NUMBER() OVER ({order_clause}) AS RowNum,
                        floorId, floorName, buildingId, floorDescription
                    FROM FloorInfo
                ) AS RankedFloors
                WHERE RowNum BETWEEN ? AND ?
                """
                cursor.execute(query, (start_row, end_row))

            columns = [column[0] for column in cursor.description]
            rows_data = cursor.fetchall()

            floors = []
            for row in rows_data:
                floor_dict = dict(zip(columns, row))
                floor_dict.pop('RowNum', None)
                floors.append(Floor(**floor_dict))

            return FloorList(
                total=total_count,
                rows=floors
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/floors/building")
    def get_floors_by_building(
        buildingId: int = Query(..., description="所属建筑ID"),
        page: int = Query(default=1, ge=1, description="页码，从1开始"),
        page_size: int = Query(default=10, ge=1, le=100, description="每页记录数")
    ):
        """
        根据建筑ID查询楼层，支持分页

        - **buildingId**: 建筑ID（精确匹配）
        - **page**: 页码，从1开始
        - **page_size**: 每页记录数，默认10条，最大100条
        """
        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            count_query = "SELECT COUNT(*) FROM FloorInfo WHERE buildingId = ?"
            cursor.execute(count_query, (buildingId,))
            total_count = cursor.fetchone()[0]

            if total_count == 0:
                return {
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0,
                    "floors": []
                }

            offset = (page - 1) * page_size
            start_row = offset
            end_row = offset + page_size

            data_query = """
                SELECT * FROM (
                    SELECT ROW_NUMBER() OVER (ORDER BY floorId) AS RowNum,
                           floorId, floorName, buildingId, floorDescription
                    FROM FloorInfo
                    WHERE buildingId = ?
                ) AS SubQuery
                WHERE RowNum > ? AND RowNum <= ?
            """
            cursor.execute(data_query, (buildingId, start_row, end_row))

            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()

            floors = []
            for row in rows:
                floor_dict = dict(zip(columns, row))
                floor_dict.pop('RowNum', None)
                floors.append(Floor(**floor_dict))

            total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0

            return {
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "floors": floors
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/floors/search")
    def search_floors(keyword: str = Query(..., min_length=1, description="搜索关键词")):
        """
        根据关键词搜索楼层

        - **keyword**: 搜索关键词（支持楼层名称、楼层描述模糊搜索）
        """
        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            search_pattern = f"%{keyword}%"
            query = """
                SELECT TOP 20 floorId, floorName, buildingId, floorDescription
                FROM FloorInfo
                WHERE floorName LIKE ?
                   OR floorDescription LIKE ?
                ORDER BY floorId
            """
            cursor.execute(query, (search_pattern, search_pattern))

            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()

            floors = []
            for row in rows:
                floor_dict = dict(zip(columns, row))
                floors.append(Floor(**floor_dict))

            return {
                "total": len(floors),
                "keyword": keyword,
                "floors": floors
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/floors/{floor_id}", response_model=Floor)
    def get_floor_by_id(floor_id: int):
        """
        根据 ID 查询单个楼层

        - **floor_id**: 楼层ID
        """
        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            query = """
                SELECT floorId, floorName, buildingId, floorDescription
                FROM FloorInfo WHERE floorId = ?
            """
            cursor.execute(query, (floor_id,))

            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail=f"楼层ID {floor_id} 不存在")

            columns = [column[0] for column in cursor.description]
            floor_dict = dict(zip(columns, row))

            return Floor(**floor_dict)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
