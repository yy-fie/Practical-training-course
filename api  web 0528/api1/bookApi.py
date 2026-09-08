from fastapi import FastAPI, HTTPException, Query
from typing import List
from database import get_db_connection
from schemas import Book, BookList, BookCreate

def register_book_routes(app: FastAPI):
    """注册图书相关的API路由"""

    @app.post("/api/books", response_model=Book, status_code=201)
    def create_book(book: BookCreate):
        """
        添加新图书
        
        - **bookName**: 图书名称
        - **bookCategory**: 图书类别
        - **bookTag**: 图书标签
        - **Authors**: 作者
        - **Price**: 价格
        - **Url**: 网址
        - **Pic**: 图片
        - **Isbn**: ISBN
        - **description**: 图书简介
        - **mulu**: 目录
        - **publishDate**: 出版日期
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            insert_query = """
                INSERT INTO Book (bookName, bookCategory, bookTag, Authors, Price, Url, Pic, Isbn, description, mulu, publishDate) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, (
                book.bookName,
                book.bookCategory,
                book.bookTag,
                book.Authors,
                book.Price,
                book.Url,
                book.Pic,
                book.Isbn,
                book.description,
                book.mulu,
                book.publishDate
            ))
            
            connection.commit()
            
            select_query = "SELECT TOP 1 bookId, bookName, bookCategory, bookTag, Authors, Price, Url, Pic, Isbn, description, mulu, publishDate FROM Book ORDER BY bookId DESC"
            cursor.execute(select_query)
            row = cursor.fetchone()
            
            if row:
                columns = [column[0] for column in cursor.description]
                book_dict = dict(zip(columns, row))
                return Book(**book_dict)
            else:
                raise HTTPException(status_code=500, detail="创建图书失败")
            
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"创建图书失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.delete("/api/booksDelete", status_code=200)
    def delete_books(book_ids: List[int] = Query(..., description="要删除的图书ID列表")):
        """
        批量删除指定ID的图书
        
        - **book_ids**: 要删除的图书ID列表
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            if not book_ids:
                raise HTTPException(status_code=400, detail="请提供至少一个图书ID")
            
            placeholders = ','.join(['?'] * len(book_ids))
            check_query = f"SELECT COUNT(*) FROM Book WHERE bookId IN ({placeholders})"
            cursor.execute(check_query, book_ids)
            existing_count = cursor.fetchone()[0]
            
            if existing_count != len(book_ids):
                raise HTTPException(status_code=404, detail=f"部分图书ID不存在，无法删除")
            
            delete_query = f"DELETE FROM Book WHERE bookId IN ({placeholders})"
            cursor.execute(delete_query, book_ids)
            
            connection.commit()
            
            return {"msg": f"成功删除 {len(book_ids)} 个图书", "status": 200, "deleted_count": len(book_ids)}
            
        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"批量删除图书失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.delete("/api/books/{book_id}", status_code=204)
    def delete_book(book_id: int):
        """
        删除指定ID的图书
        
        - **book_id**: 要删除的图书ID
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            check_query = "SELECT COUNT(*) FROM Book WHERE bookId = ?"
            cursor.execute(check_query, (book_id,))
            count = cursor.fetchone()[0]
            
            if count == 0:
                raise HTTPException(status_code=404, detail=f"图书ID {book_id} 不存在，无法删除")
            
            delete_query = "DELETE FROM Book WHERE bookId = ?"
            cursor.execute(delete_query, (book_id,))
            
            connection.commit()
            
            return {"msg":"删除成功","status":204}
            
        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"删除图书失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.put("/api/books/{book_id}", response_model=Book)
    def update_book(book_id: int, book: BookCreate):
        """
        更新指定ID的图书信息（完整更新）
        
        - **book_id**: 要更新的图书ID
        - **bookName**: 图书名称
        - **bookCategory**: 图书类别
        - **bookTag**: 图书标签
        - **Authors**: 作者
        - **Price**: 价格
        - **Url**: 网址
        - **Pic**: 图片
        - **Isbn**: ISBN
        - **description**: 图书简介
        - **mulu**: 目录
        - **publishDate**: 出版日期
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            check_query = "SELECT COUNT(*) FROM Book WHERE bookId = ?"
            cursor.execute(check_query, (book_id,))
            count = cursor.fetchone()[0]
            
            if count == 0:
                raise HTTPException(status_code=404, detail=f"图书ID {book_id} 不存在，无法更新")
            
            update_query = """
                UPDATE Book 
                SET bookName = ?, 
                    bookCategory = ?, 
                    bookTag = ?,
                    Authors = ?,
                    Price = ?,
                    Url = ?,
                    Pic = ?,
                    Isbn = ?,
                    description = ?,
                    mulu = ?,
                    publishDate = ?
                WHERE bookId = ?
            """
            cursor.execute(update_query, (
                book.bookName,
                book.bookCategory,
                book.bookTag,
                book.Authors,
                book.Price,
                book.Url,
                book.Pic,
                book.Isbn,
                book.description,
                book.mulu,
                book.publishDate,
                book_id
            ))
            
            connection.commit()
            
            select_query = "SELECT bookId, bookName, bookCategory, bookTag, Authors, Price, Url, Pic, Isbn, description, mulu, publishDate FROM Book WHERE bookId = ?"
            cursor.execute(select_query, (book_id,))
            row = cursor.fetchone()
            
            if row:
                columns = [column[0] for column in cursor.description]
                book_dict = dict(zip(columns, row))
                return Book(**book_dict)
            else:
                raise HTTPException(status_code=500, detail="更新后查询失败")
            
        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail=f"更新图书失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/books", response_model=BookList)
    def get_books(
        page: int = Query(default=1, ge=1, description="页码，从1开始"), 
        rows: int = Query(default=10, ge=1, le=100, description="每页记录数"),
        bookCategory: str = Query(default=None, description="图书类别（可选）"),
        bookTag: str = Query(default=None, description="图书标签（可选）"),
        bookName: str = Query(default=None, description="图书名称（可选，支持模糊搜索）"),
        Authors: str = Query(default=None, description="作者（可选，支持模糊搜索）"),
        min_price: float = Query(default=None, ge=0, description="最低价格（可选）"),
        max_price: float = Query(default=None, ge=0, description="最高价格（可选）"),
        isbn: str = Query(default=None, description="ISBN（可选，支持模糊搜索）"),
        sort_by: str = Query(default=None, description="排序字段和方式：支持单个或多个排序条件，格式为 '字段 asc/desc'，多个条件用逗号分隔。例如：'Price desc,publishDate desc' 或 'bookName asc'。支持的字段：bookName(图书名称), Price(价格), publishDate(出版日期)，默认为bookId升序")
       
    ):
        """
        查询 Book 表的图书记录（支持分页、类别过滤、标签过滤、图书名称搜索、价格区间搜索、ISBN搜索和排序）
        
        - **page**: 页码，从1开始，默认第1页
        - **rows**: 每页记录数量，默认10条，最大100条
        - **bookCategory**: 图书类别（可选），如果提供则只返回该类别的图书
        - **bookTag**: 图书标签（可选），如果提供则只返回该标签的图书
        - **bookName**: 图书名称（可选），支持模糊搜索
        - **Authors**: 作者（可选），支持模糊搜索
        - **min_price**: 最低价格（可选），如果提供则只返回价格大于等于此值的图书
        - **max_price**: 最高价格（可选），如果提供则只返回价格小于等于此值的图书
        
        - **isbn**: ISBN（可选），支持模糊搜索
        - **sort_by**: 排序字段和方式，支持单个或多个排序条件。格式为 '字段 asc/desc'，多个条件用逗号分隔。
                     例如：'Price desc,publishDate desc' 表示先按价格降序，价格相同时按出版日期降序；
                     'bookName asc' 表示按书名升序。
                     支持的字段：bookName(图书名称), Price(价格), publishDate(出版日期)。
                     默认为 bookId 升序
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            start_row = (page - 1) * rows + 1
            end_row = page * rows
            
            # 确定排序规则（支持多条件排序）
            order_clause = "ORDER BY bookId ASC"
            if sort_by:
                # 分割多个排序条件
                sort_conditions = [s.strip() for s in sort_by.split(',')]
                order_parts = []
                
                for sort_condition in sort_conditions:
                    sort_parts = sort_condition.lower().split()
                    if len(sort_parts) == 2 and sort_parts[1] in ["asc", "desc"]:
                        field = sort_parts[0].lower()
                        order_direction = sort_parts[1].upper()
                        
                        if field == "bookname":
                            order_parts.append(f"bookName {order_direction}")
                        elif field == "price":
                            order_parts.append(f"Price {order_direction}")
                        elif field == "publishdate":
                            order_parts.append(f"publishDate {order_direction}")
                
                # 如果有有效的排序条件，构建 ORDER BY 子句
                if order_parts:
                    order_clause = "ORDER BY " + ", ".join(order_parts)
            
            # 构建 WHERE 条件和参数列表
            where_conditions = []
            params = []
            
            if bookCategory:
                where_conditions.append("LTRIM(RTRIM(bookCategory)) = LTRIM(RTRIM(?))")
                params.append(bookCategory)
            
            if bookTag:
                where_conditions.append("LTRIM(RTRIM(bookTag)) = LTRIM(RTRIM(?))")
                params.append(bookTag)
            
            if bookName:
                where_conditions.append("bookName LIKE ?")
                params.append(f"%{bookName}%")
            
            if Authors:
                where_conditions.append("Authors LIKE ?")
                params.append(f"%{Authors}%")
            
            if min_price is not None:
                where_conditions.append("Price >= ?")
                params.append(min_price)
            
            if max_price is not None:
                where_conditions.append("Price <= ?")
                params.append(max_price)
            
            if isbn:
                where_conditions.append("Isbn LIKE ?")
                params.append(f"%{isbn}%")
            
            # 构建计数查询
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)
                count_query = f"SELECT COUNT(*) FROM Book{where_clause}"
                cursor.execute(count_query, params)
            else:
                count_query = "SELECT COUNT(*) FROM Book"
                cursor.execute(count_query)
            
            total_count = cursor.fetchone()[0]
            
            # 构建数据查询
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)
                query = f"""
                SELECT * FROM (
                    SELECT ROW_NUMBER() OVER ({order_clause}) AS RowNum, 
                        bookId, bookName, bookCategory, bookTag, Authors, Price, Url, Pic, Isbn, description, mulu, publishDate 
                    FROM Book{where_clause}
                ) AS RankedBooks
                WHERE RowNum BETWEEN ? AND ?
                """
                cursor.execute(query, params + [start_row, end_row])
            else:
                query = f"""
                SELECT * FROM (
                    SELECT ROW_NUMBER() OVER ({order_clause}) AS RowNum, 
                        bookId, bookName, bookCategory, bookTag, Authors, Price, Url, Pic, Isbn, description, mulu, publishDate 
                    FROM Book
                ) AS RankedBooks
                WHERE RowNum BETWEEN ? AND ?
                """
                cursor.execute(query, (start_row, end_row))
            
            columns = [column[0] for column in cursor.description]
            rows_data = cursor.fetchall()
            
            books = []
            for row in rows_data:
                book_dict = dict(zip(columns, row))
                book_dict.pop('RowNum', None)
                books.append(Book(**book_dict))
            
            return BookList(
                total=total_count,
                rows=books
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/books/category")
    def get_books_by_category(
        bookCategory: str = Query(..., min_length=1, description="图书类别"),
        page: int = Query(default=1, ge=1, description="页码，从1开始"),
        page_size: int = Query(default=10, ge=1, le=100, description="每页记录数")
    ):
        """
        根据类别查询图书，支持分页
        
        - **bookCategory**: 图书类别（精确匹配）
        - **page**: 页码，从1开始
        - **page_size**: 每页记录数，默认10条，最大100条
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            count_query = "SELECT COUNT(*) FROM Book WHERE bookCategory = ?"
            cursor.execute(count_query, (bookCategory,))
            total_count = cursor.fetchone()[0]
            
            if total_count == 0:
                return {
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0,
                    "books": []
                }
            
            offset = (page - 1) * page_size
            start_row = offset + 1
            end_row = offset + page_size

            data_query = """
                SELECT * FROM (
                    SELECT ROW_NUMBER() OVER (ORDER BY bookId) AS RowNum,
                           bookId, bookName, bookCategory, bookTag, Authors, Price, Url, Pic, Isbn, description, mulu, publishDate 
                    FROM Book 
                    WHERE bookCategory = ?
                ) AS SubQuery
                WHERE RowNum > ? AND RowNum <= ?
            """
            cursor.execute(data_query, (bookCategory, start_row, end_row))
            
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            
            books = []
            for row in rows:
                book_dict = dict(zip(columns, row))
                book_dict.pop('RowNum', None)
                books.append(Book(**book_dict))
            
            total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
            
            return {
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "books": books
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/books/tag")
    def get_books_by_tag(
        bookTag: str = Query(..., min_length=1, description="图书标签"),
        page: int = Query(default=1, ge=1, description="页码，从1开始"),
        page_size: int = Query(default=10, ge=1, le=100, description="每页记录数")
    ):
        """
        根据标签查询图书，支持分页
        
        - **bookTag**: 图书标签（精确匹配）
        - **page**: 页码，从1开始
        - **page_size**: 每页记录数，默认10条，最大100条
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            count_query = "SELECT COUNT(*) FROM Book WHERE bookTag = ?"
            cursor.execute(count_query, (bookTag,))
            total_count = cursor.fetchone()[0]
            
            if total_count == 0:
                return {
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0,
                    "books": []
                }
            
            offset = (page - 1) * page_size
            start_row = offset + 1
            end_row = offset + page_size

            data_query = """
                SELECT * FROM (
                    SELECT ROW_NUMBER() OVER (ORDER BY bookId) AS RowNum,
                           bookId, bookName, bookCategory, bookTag, Authors, Price, Url, Pic, Isbn, description, mulu, publishDate 
                    FROM Book 
                    WHERE bookTag = ?
                ) AS SubQuery
                WHERE RowNum > ? AND RowNum <= ?
            """
            cursor.execute(data_query, (bookTag, start_row, end_row))
            
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            
            books = []
            for row in rows:
                book_dict = dict(zip(columns, row))
                book_dict.pop('RowNum', None)
                books.append(Book(**book_dict))
            
            total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
            
            return {
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "books": books
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/books/search")
    def search_books(keyword: str = Query(..., min_length=1, description="搜索关键词")):
        """
        根据关键词搜索图书
        
        - **keyword**: 搜索关键词（支持图书名称、类别、标签、作者模糊搜索）
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            search_pattern = f"%{keyword}%"
            query = """
                SELECT TOP 20 bookId, bookName, bookCategory, bookTag, Authors, Price, Url, Pic, Isbn, description, mulu, publishDate 
                FROM Book 
                WHERE bookName LIKE ?
                   OR bookCategory LIKE ?
                   OR bookTag LIKE ?
                   OR Authors LIKE ?
                ORDER BY bookId
            """
            cursor.execute(query, (search_pattern, search_pattern, search_pattern, search_pattern))
            
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            
            books = []
            for row in rows:
                book_dict = dict(zip(columns, row))
                books.append(Book(**book_dict))
            
            return {
                "total": len(books),
                "keyword": keyword,
                "books": books
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/books/categories")
    def get_all_categories():
        """
        获取所有图书类别名称（去重）
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            query = "SELECT DISTINCT bookCategory FROM Book WHERE bookCategory IS NOT NULL ORDER BY bookCategory"
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

    @app.get("/api/books/tags")
    def get_all_tags():
        """
        获取所有图书标签名称（去重）
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            query = "SELECT DISTINCT bookTag FROM Book WHERE bookTag IS NOT NULL ORDER BY bookTag"
            cursor.execute(query)
            
            rows = cursor.fetchall()
            
            tags = [row[0] for row in rows if row[0]]
            
            return {
                "total": len(tags),
                "tags": tags
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/books/{book_id}", response_model=Book)
    def get_book_by_id(book_id: int):
        """
        根据 ID 查询单个图书
        
        - **book_id**: 图书ID
        """
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            query = "SELECT bookId, bookName, bookCategory, bookTag, Authors, Price, Url, Pic, Isbn, description, mulu, publishDate FROM Book WHERE bookId = ?"
            cursor.execute(query, (book_id,))
            
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail=f"图书ID {book_id} 不存在")
            
            columns = [column[0] for column in cursor.description]
            book_dict = dict(zip(columns, row))
            
            return Book(**book_dict)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
