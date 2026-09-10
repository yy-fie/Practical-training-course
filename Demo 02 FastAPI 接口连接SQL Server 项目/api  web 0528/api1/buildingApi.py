from fastapi import FastAPI, HTTPException, Query
from typing import List
from database import get_db_connection
from schemas import Building, BuildingList, BuildingCreate


def register_building_routes(app: FastAPI):
    """注册建筑相关的API路由"""

    @app.post("/api/buildings", response_model=Building, status_code=201)
    def create_building(building: BuildingCreate):
        """
        添加新建筑
        
        - **buildingName**: 建筑名称
        - **buildingCode**: 建筑代码
        - **buildingAddress**: 建筑地址
        - **buildingDescription**: 建筑描述
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            insert_query = """
                INSERT INTO BuildingInfo (buildingName, buildingCode, buildingAddress, buildingDescription) 
                VALUES (?, ?, ?, ?)
            """
            cursor.execute(insert_query, (
                building.buildingName,
                building.buildingCode,
                building.buildingAddress,
                building.buildingDescription
            ))
            
            connection.commit()
            
            select_query = "SELECT TOP 1 buildingId, buildingName, buildingCode, buildingAddress, buildingDescription FROM BuildingInfo ORDER BY buildingId DESC"
            cursor.execute(select_query)
            row = cursor.fetchone()
            
            if row:
                columns = [column[0] for column in cursor.description]
                building_dict = dict(zip(columns, row))
                return Building(**building_dict)
            else:
                raise HTTPException(status_code=500, detail="创建建筑失败")
            
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"创建建筑失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.delete("/api/buildingsDelete", status_code=200)
    def delete_buildings(building_ids: List[int] = Query(..., description="要删除的建筑ID列表")):
        """
        批量删除指定ID的建筑
        
        - **building_ids**: 要删除的建筑ID列表
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            if not building_ids:
                raise HTTPException(status_code=400, detail="请提供至少一个建筑ID")
            
            placeholders = ','.join(['?'] * len(building_ids))
            check_query = f"SELECT COUNT(*) FROM BuildingInfo WHERE buildingId IN ({placeholders})"
            cursor.execute(check_query, building_ids)
            existing_count = cursor.fetchone()[0]
            
            if existing_count != len(building_ids):
                raise HTTPException(status_code=404, detail=f"部分建筑ID不存在，无法删除")
            
            delete_query = f"DELETE FROM BuildingInfo WHERE buildingId IN ({placeholders})"
            cursor.execute(delete_query, building_ids)
            
            connection.commit()
            
            return {"msg": f"成功删除 {len(building_ids)} 个建筑", "status": 200, "deleted_count": len(building_ids)}
            
        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"批量删除建筑失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.delete("/api/buildings/{building_id}", status_code=204)
    def delete_building(building_id: int):
        """
        删除指定ID的建筑
        
        - **building_id**: 要删除的建筑ID
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            check_query = "SELECT COUNT(*) FROM BuildingInfo WHERE buildingId = ?"
            cursor.execute(check_query, (building_id,))
            count = cursor.fetchone()[0]
            
            if count == 0:
                raise HTTPException(status_code=404, detail=f"建筑ID {building_id} 不存在，无法删除")
            
            delete_query = "DELETE FROM BuildingInfo WHERE buildingId = ?"
            cursor.execute(delete_query, (building_id,))
            
            connection.commit()
            
            return {"msg":"删除成功","status":204}
            
        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"删除建筑失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.put("/api/buildings/{building_id}", response_model=Building)
    def update_building(building_id: int, building: BuildingCreate):
        """
        更新指定ID的建筑信息（完整更新）
        
        - **building_id**: 要更新的建筑ID
        - **buildingName**: 建筑名称
        - **buildingCode**: 建筑代码
        - **buildingAddress**: 建筑地址
        - **buildingDescription**: 建筑描述
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            check_query = "SELECT COUNT(*) FROM BuildingInfo WHERE buildingId = ?"
            cursor.execute(check_query, (building_id,))
            count = cursor.fetchone()[0]
            
            if count == 0:
                raise HTTPException(status_code=404, detail=f"建筑ID {building_id} 不存在，无法更新")
            
            update_query = """
                UPDATE BuildingInfo 
                SET buildingName = ?, 
                    buildingCode = ?, 
                    buildingAddress = ?,
                    buildingDescription = ?
                WHERE buildingId = ?
            """
            cursor.execute(update_query, (
                building.buildingName,
                building.buildingCode,
                building.buildingAddress,
                building.buildingDescription,
                building_id
            ))
            
            connection.commit()
            
            select_query = "SELECT buildingId, buildingName, buildingCode, buildingAddress, buildingDescription FROM BuildingInfo WHERE buildingId = ?"
            cursor.execute(select_query, (building_id,))
            row = cursor.fetchone()
            
            if row:
                columns = [column[0] for column in cursor.description]
                building_dict = dict(zip(columns, row))
                return Building(**building_dict)
            else:
                raise HTTPException(status_code=500, detail="更新后查询失败")
            
        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"更新建筑失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/buildings", response_model=BuildingList)
    def get_buildings(
        page: int = Query(default=1, ge=1, description="页码，从1开始"), 
        rows: int = Query(default=10, ge=1, le=100, description="每页记录数"),
        buildingName: str = Query(default=None, description="建筑名称（可选，支持模糊搜索）"),
        buildingCode: str = Query(default=None, description="建筑代码（可选，支持模糊搜索）"),
        buildingAddress: str = Query(default=None, description="建筑地址（可选，支持模糊搜索）"),
        sort_by: str = Query(default=None, description="排序字段和方式：支持单个或多个排序条件，格式为 '字段 asc/desc'，多个条件用逗号分隔。例如：'buildingName asc' 或 'buildingId desc'。支持的字段：buildingName(建筑名称), buildingCode(建筑代码)，默认为buildingId升序")
    ):
        """
        查询 BuildingInfo 表的建筑记录（支持分页、名称搜索、代码搜索和排序）
        
        - **page**: 页码，从1开始，默认第1页
        - **rows**: 每页记录数量，默认10条，最大100条
        - **buildingName**: 建筑名称（可选），支持模糊搜索
        - **buildingCode**: 建筑代码（可选），支持模糊搜索
        - **buildingAddress**: 建筑地址（可选），支持模糊搜索
        - **sort_by**: 排序字段和方式，支持单个或多个排序条件。格式为 '字段 asc/desc'，多个条件用逗号分隔。
                     例如：'buildingName asc' 表示按建筑名称升序；
                     'buildingCode desc,buildingName asc' 表示先按建筑代码降序，再按名称升序。
                     支持的字段：buildingName(建筑名称), buildingCode(建筑代码)。
                     默认为 buildingId 升序
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            start_row = (page - 1) * rows + 1
            end_row = page * rows
            
            # 确定排序规则（支持多条件排序）
            order_clause = "ORDER BY buildingId ASC"
            if sort_by:
                # 分割多个排序条件
                sort_conditions = [s.strip() for s in sort_by.split(',')]
                order_parts = []
                
                for sort_condition in sort_conditions:
                    sort_parts = sort_condition.lower().split()
                    if len(sort_parts) == 2 and sort_parts[1] in ["asc", "desc"]:
                        field = sort_parts[0].lower()
                        order_direction = sort_parts[1].upper()
                        
                        if field == "buildingname":
                            order_parts.append(f"buildingName {order_direction}")
                        elif field == "buildingcode":
                            order_parts.append(f"buildingCode {order_direction}")
                
                # 如果有有效的排序条件，构建 ORDER BY 子句
                if order_parts:
                    order_clause = "ORDER BY " + ", ".join(order_parts)
            
            # 构建 WHERE 条件和参数列表
            where_conditions = []
            params = []
            
            if buildingName:
                where_conditions.append("buildingName LIKE ?")
                params.append(f"%{buildingName}%")
            
            if buildingCode:
                where_conditions.append("buildingCode LIKE ?")
                params.append(f"%{buildingCode}%")
            
            if buildingAddress:
                where_conditions.append("buildingAddress LIKE ?")
                params.append(f"%{buildingAddress}%")
            
            # 构建计数查询
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)
                count_query = f"SELECT COUNT(*) FROM BuildingInfo{where_clause}"
                cursor.execute(count_query, params)
            else:
                count_query = "SELECT COUNT(*) FROM BuildingInfo"
                cursor.execute(count_query)
            
            total_count = cursor.fetchone()[0]
            
            # 构建数据查询
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)
                query = f"""
                SELECT * FROM (
                    SELECT ROW_NUMBER() OVER ({order_clause}) AS RowNum, 
                        buildingId, buildingName, buildingCode, buildingAddress, buildingDescription 
                    FROM BuildingInfo{where_clause}
                ) AS RankedBuildings
                WHERE RowNum BETWEEN ? AND ?
                """
                cursor.execute(query, params + [start_row, end_row])
            else:
                query = f"""
                SELECT * FROM (
                    SELECT ROW_NUMBER() OVER ({order_clause}) AS RowNum, 
                        buildingId, buildingName, buildingCode, buildingAddress, buildingDescription 
                    FROM BuildingInfo
                ) AS RankedBuildings
                WHERE RowNum BETWEEN ? AND ?
                """
                cursor.execute(query, (start_row, end_row))
            
            columns = [column[0] for column in cursor.description]
            rows_data = cursor.fetchall()
            
            buildings = []
            for row in rows_data:
                building_dict = dict(zip(columns, row))
                building_dict.pop('RowNum', None)
                buildings.append(Building(**building_dict))
            
            return BuildingList(
                total=total_count,
                rows=buildings
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/buildings/search")
    def search_buildings(keyword: str = Query(..., min_length=1, description="搜索关键词")):
        """
        根据关键词搜索建筑
        
        - **keyword**: 搜索关键词（支持建筑名称、代码、地址模糊搜索）
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            search_pattern = f"%{keyword}%"
            query = """
                SELECT TOP 20 buildingId, buildingName, buildingCode, buildingAddress, buildingDescription 
                FROM BuildingInfo 
                WHERE buildingName LIKE ?
                   OR buildingCode LIKE ?
                   OR buildingAddress LIKE ?
                ORDER BY buildingId
            """
            cursor.execute(query, (search_pattern, search_pattern, search_pattern))
            
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            
            buildings = []
            for row in rows:
                building_dict = dict(zip(columns, row))
                buildings.append(Building(**building_dict))
            
            return {
                "total": len(buildings),
                "keyword": keyword,
                "buildings": buildings
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/buildings/{building_id}", response_model=Building)
    def get_building_by_id(building_id: int):
        """
        根据 ID 查询单个建筑
        
        - **building_id**: 建筑ID
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            query = "SELECT buildingId, buildingName, buildingCode, buildingAddress, buildingDescription FROM BuildingInfo WHERE buildingId = ?"
            cursor.execute(query, (building_id,))
            
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail=f"建筑ID {building_id} 不存在")
            
            columns = [column[0] for column in cursor.description]
            building_dict = dict(zip(columns, row))
            
            return Building(**building_dict)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
