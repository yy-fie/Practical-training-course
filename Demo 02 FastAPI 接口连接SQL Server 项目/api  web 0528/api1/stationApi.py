from fastapi import FastAPI, HTTPException, Query
from typing import List
from database import get_db_connection
from schemas import Station, StationList, StationCreate, TripStatsList, TripStats

def register_station_routes(app: FastAPI):
    """注册站点相关的API路由"""

    @app.post("/api/stations", response_model=Station, status_code=201)
    def create_station(station: StationCreate):
        """
        添加新站点
        
        - **station_name**: 站点名称
        - **line**: 线路
        - **district**: 区域
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            insert_query = """
                INSERT INTO stations (station_name, line, district) 
                OUTPUT INSERTED.station_id
                VALUES ( ?, ?, ?)
            """
            cursor.execute(insert_query, (
               
                station.station_name,
                station.line,
                station.district
            ))
            
            created_id = cursor.fetchone()[0]
            connection.commit()
            
            select_query = "SELECT station_id, station_name, line, district FROM stations WHERE station_id=?"
            cursor.execute(select_query, (created_id,))
            row = cursor.fetchone()
            
            if row:
                columns = [column[0] for column in cursor.description]
                station_dict = dict(zip(columns, row))
                return Station(**station_dict)
            else:
                raise HTTPException(status_code=500, detail="创建站点失败")
            
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"创建站点失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.delete("/api/stationsDelete", status_code=200)
    def delete_stations(station_ids: List[int] = Query(..., description="要删除的站点ID列表")):
        """
        批量删除指定ID的站点
        
        - **station_ids**: 要删除的站点ID列表
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            if not station_ids:
                raise HTTPException(status_code=400, detail="请提供至少一个站点ID")
            
            placeholders = ','.join(['?'] * len(station_ids))
            check_query = f"SELECT COUNT(*) FROM stations WHERE station_id IN ({placeholders})"
            cursor.execute(check_query, station_ids)
            existing_count = cursor.fetchone()[0]
            
            if existing_count != len(station_ids):
                raise HTTPException(status_code=404, detail=f"部分站点ID不存在，无法删除")
            
            delete_query = f"DELETE FROM stations WHERE station_id IN ({placeholders})"
            cursor.execute(delete_query, station_ids)
            
            connection.commit()
            
            return {"msg": f"成功删除 {len(station_ids)} 个站点", "status": 200, "deleted_count": len(station_ids)}
            
        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"批量删除站点失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.delete("/api/stations/{station_id}", status_code=204)
    def delete_station(station_id: int):
        """
        删除指定ID的站点
        
        - **station_id**: 要删除的站点ID
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            check_query = "SELECT COUNT(*) FROM stations WHERE station_id = ?"
            cursor.execute(check_query, (station_id,))
            count = cursor.fetchone()[0]
            
            if count == 0:
                raise HTTPException(status_code=404, detail=f"站点ID {station_id} 不存在，无法删除")
            
            delete_query = "DELETE FROM stations WHERE station_id = ?"
            cursor.execute(delete_query, (station_id,))
            
            connection.commit()
            
            return {"msg":"删除成功","status":204}
            
        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"删除站点失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.put("/api/stations/{station_id}", response_model=Station)
    def update_station(station_id: int, station: StationCreate):
        """
        更新指定ID的站点信息（完整更新）
        
        - **station_id**: 要更新的站点ID
        - **station_name**: 站点名称
        - **line**: 线路
        - **district**: 区域
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            check_query = "SELECT COUNT(*) FROM stations WHERE station_id = ?"
            cursor.execute(check_query, (station_id,))
            count = cursor.fetchone()[0]
            
            if count == 0:
                raise HTTPException(status_code=404, detail=f"站点ID {station_id} 不存在，无法更新")
            
            update_query = """
                UPDATE stations 
                SET station_name = ?, 
                    line = ?, 
                    district = ?
                WHERE station_id = ?
            """
            cursor.execute(update_query, (
                station.station_name,
                station.line,
                station.district,
                station_id
            ))
            
            connection.commit()
            
            select_query = "SELECT station_id, station_name, line, district FROM stations WHERE station_id = ?"
            cursor.execute(select_query, (station_id,))
            row = cursor.fetchone()
            
            if row:
                columns = [column[0] for column in cursor.description]
                station_dict = dict(zip(columns, row))
                return Station(**station_dict)
            else:
                raise HTTPException(status_code=500, detail="更新后查询失败")
            
        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"更新站点失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/stations", response_model=StationList)
    def get_stations(
        page: int = Query(default=1, ge=1, description="页码，从1开始"), 
        rows: int = Query(default=10, ge=1, le=100, description="每页记录数"),
        line: str = Query(default=None, description="线路名称（可选）"),
        district: str = Query(default=None, description="区域名称（可选）"),
        station_name: str = Query(default=None, description="站点名称（可选，支持模糊搜索）"),
        sort_by: str = Query(default=None, description="排序字段和方式：station_name asc(站点名称升序), station_name desc(站点名称降序)，默认为station_id升序")
    ):
        """
        查询 stations 表的站点记录（支持分页、线路过滤、区域过滤、站点名称搜索和排序）
        
        - **page**: 页码，从1开始，默认第1页
        - **rows**: 每页记录数量，默认10条，最大100条
        - **line**: 线路名称（可选），如果提供则只返回该线路的站点
        - **district**: 区域名称（可选），如果提供则只返回该区域的站点
        - **station_name**: 站点名称（可选），支持模糊搜索
        - **sort_by**: 排序字段和方式，支持 "station_name asc" 或 "station_name desc"，默认为 station_id 升序
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            start_row = (page - 1) * rows + 1
            end_row = page * rows
            
            # 确定排序规则
            order_clause = "ORDER BY station_id ASC"
            if sort_by:
                sort_parts = sort_by.strip().lower().split()
                if len(sort_parts) == 2 and sort_parts[0] == "station_name" and sort_parts[1] in ["asc", "desc"]:
                    order_direction = sort_parts[1].upper()
                    order_clause = f"ORDER BY station_name {order_direction}"
            
            # 构建 WHERE 条件和参数列表
            where_conditions = []
            params = []
            
            if line:
                where_conditions.append("line = ?")
                params.append(line)
            
            if district:
                where_conditions.append("district = ?")
                params.append(district)
            
            if station_name:
                where_conditions.append("station_name LIKE ?")
                params.append(f"%{station_name}%")
            
            # 构建计数查询
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)
                count_query = f"SELECT COUNT(*) FROM stations{where_clause}"
                cursor.execute(count_query, params)
            else:
                count_query = "SELECT COUNT(*) FROM stations"
                cursor.execute(count_query)
            
            total_count = cursor.fetchone()[0]
            
            # 构建数据查询
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)
                query = f"""
                SELECT * FROM (
                    SELECT ROW_NUMBER() OVER ({order_clause}) AS RowNum, 
                        station_id, station_name, line, district 
                    FROM stations{where_clause}
                ) AS RankedStations
                WHERE RowNum BETWEEN ? AND ?
                """
                cursor.execute(query, params + [start_row, end_row])
            else:
                query = f"""
                SELECT * FROM (
                    SELECT ROW_NUMBER() OVER ({order_clause}) AS RowNum, 
                        station_id, station_name, line, district 
                    FROM stations
                ) AS RankedStations
                WHERE RowNum BETWEEN ? AND ?
                """
                cursor.execute(query, (start_row, end_row))
            
            columns = [column[0] for column in cursor.description]
            rows_data = cursor.fetchall()
            
            stations = []
            for row in rows_data:
                station_dict = dict(zip(columns, row))
                station_dict.pop('RowNum', None)
                stations.append(Station(**station_dict))
            
            return StationList(
                total=total_count,
                rows=stations
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/stations/line")
    def get_stations_by_line(
        line: str = Query(..., min_length=1, description="线路名称"),
        page: int = Query(default=1, ge=1, description="页码，从1开始"),
        page_size: int = Query(default=100000,description="每页记录数")
    ):
        """
        根据线路查询站点，支持分页
        
        - **line**: 线路名称（精确匹配）
        - **page**: 页码，从1开始
        - **page_size**: 每页记录数，默认10条，最大100条
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            count_query = "SELECT COUNT(*) FROM stations WHERE line = ?"
            cursor.execute(count_query, (line,))
            total_count = cursor.fetchone()[0]
            
            if total_count == 0:
                return {
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0,
                    "stations": []
                }
            
            offset = (page - 1) * page_size
            start_row = offset + 1
            end_row = offset + page_size

            data_query = """
                SELECT * FROM (
                    SELECT ROW_NUMBER() OVER (ORDER BY station_id) AS RowNum,
                           station_id, station_name, line, district 
                    FROM stations 
                    WHERE line = '%s'
                ) AS SubQuery
                WHERE RowNum > %s AND RowNum <= %s
            """ % (line, start_row, end_row)


            cursor.execute(data_query)
            
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            
            stations = []
            for row in rows:
                station_dict = dict(zip(columns, row))
                station_dict.pop('RowNum', None)
                stations.append(Station(**station_dict))
            
            total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
            
            return {
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "stations": stations
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/stations/district")
    def get_stations_by_district(
        district: str = Query(..., min_length=1, description="区域名称"),
        page: int = Query(default=1, ge=1, description="页码，从1开始"),
        page_size: int = Query(default=10, ge=1, le=100, description="每页记录数")
    ):
        """
        根据区域查询站点，支持分页
        
        - **district**: 区域名称（精确匹配）
        - **page**: 页码，从1开始
        - **page_size**: 每页记录数，默认10条，最大100条
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            count_query = "SELECT COUNT(*) FROM stations WHERE district = ?"
            cursor.execute(count_query, (district,))
            total_count = cursor.fetchone()[0]
            
            if total_count == 0:
                return {
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0,
                    "stations": []
                }
            
            offset = (page - 1) * page_size
            start_row = offset + 1
            end_row = offset + page_size

            data_query = """
                SELECT * FROM (
                    SELECT ROW_NUMBER() OVER (ORDER BY station_id) AS RowNum,
                           station_id, station_name, line, district 
                    FROM stations 
                    WHERE district = ?
                ) AS SubQuery
                WHERE RowNum > ? AND RowNum <= ?
            """
            cursor.execute(data_query, (district, start_row, end_row))
            
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            
            stations = []
            for row in rows:
                station_dict = dict(zip(columns, row))
                station_dict.pop('RowNum', None)
                stations.append(Station(**station_dict))
            
            total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
            
            return {
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "stations": stations
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/stations/search")
    def search_stations(keyword: str = Query(..., min_length=1, description="搜索关键词")):
        """
        根据关键词搜索站点
        
        - **keyword**: 搜索关键词（支持站点名称、线路、区域模糊搜索）
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            search_pattern = f"%{keyword}%"
            query = """
                SELECT TOP 20 station_id, station_name, line, district 
                FROM stations 
                WHERE station_name LIKE ?
                   OR line LIKE ?
                   OR district LIKE ?
                ORDER BY station_id
            """
            cursor.execute(query, (search_pattern, search_pattern, search_pattern))
            
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            
            stations = []
            for row in rows:
                station_dict = dict(zip(columns, row))
                stations.append(Station(**station_dict))
            
            return {
                "total": len(stations),
                "keyword": keyword,
                "stations": stations
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/stations/trip-stats")
    def get_station_trip_stats(station_name: str = Query(..., min_length=1, description="站点名称")):
        """
        查询指定站点各月份的乘车金额和乘车人数统计
        
        - **station_name**: 站点名称（出站名）
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            query = """
                SELECT 乘车月份, SUM(乘车金额) as 总金额, COUNT(*) as 乘车次数 
                FROM tripsInfo 
                WHERE 出站名 = ?
                GROUP BY 乘车月份 
                ORDER BY 乘车月份
            """
            cursor.execute(query, (station_name,))
            
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            
            trip_stats = []
            for row in rows:
                stats_dict = dict(zip(columns, row))
                trip_stats.append(TripStats(**stats_dict))
            
            return TripStatsList(
                total=len(trip_stats),
                station_name=station_name,
                data=trip_stats
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()


    




    @app.get("/api/stations/lines")
    def get_all_lines():
        """
        获取所有线路名称（去重）
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            query = "SELECT DISTINCT line FROM stations ORDER BY line"
            cursor.execute(query)
            
            rows = cursor.fetchall()
            
            lines = [row[0] for row in rows]
            
            return {
                "total": len(lines),
                "lines": lines
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/stations/districts")
    def get_all_districts():
        """
        获取所有行政区名称（去重）
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            query = "SELECT DISTINCT district FROM stations ORDER BY district"
            cursor.execute(query)
            
            rows = cursor.fetchall()
            
            districts = [row[0] for row in rows]
            
            return {
                "total": len(districts),
                "districts": districts
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/stations/{station_id}", response_model=Station)
    def get_station_by_id(station_id: int):
        """
        根据 ID 查询单个站点
        
        - **station_id**: 站点ID
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            query = "SELECT station_id, station_name, line, district FROM stations WHERE station_id = ?"
            cursor.execute(query, (station_id,))
            
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail=f"站点ID {station_id} 不存在")
            
            columns = [column[0] for column in cursor.description]
            station_dict = dict(zip(columns, row))
            
            return Station(**station_dict)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

