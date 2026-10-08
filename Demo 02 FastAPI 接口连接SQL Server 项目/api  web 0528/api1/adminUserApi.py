# -*- coding: utf-8 -*-
"""用户管理接口（权限码 + 数据范围 + 角色层级）

权限码：
  user:list   查看用户列表（数据范围：系管理员=本系；教师=本系学生）
  user:edit   编辑用户信息（系管理员=本系；教师=本系学生）
  user:reset  重置密码（自己 + 直接下一层；系管理员限本系）
  user:delete 删除用户（仅下一层及以下；系管理员限本系）
  role:assign 调整用户角色（仅下一层及以下；系管理员限本系）

请求头：Authorization: Bearer <访问令牌>
"""

from fastapi import FastAPI, HTTPException, Query, Depends

from database import get_db_connection
from schemas import User, UserList
from permissionApi import require_permission, subordinate_role_ids, descendant_role_ids, load_user
from security import hash_password
from authApi import revoke_user_sessions

DEPT_SCOPE_ROLE = 2   # 系管理员：按院系隔离
TEACHER_ROLE = 3      # 教师：只看/改本系学生
STUDENT_ROLE = 1


def _target_in_scope(me, target_user_id, mode, allow_self=True):
    """mode: 'self_child'（自己+直接下一层）或 'descendant'（下一层及以下）"""
    target = load_user(target_user_id)
    if not target:
        raise HTTPException(status_code=404, detail="用户ID %d 不存在" % target_user_id)

    target_role = target[2]
    target_dept = target[3]
    if allow_self and target_user_id == me['userId']:
        return target

    if mode == "self_child":
        allowed = set(subordinate_role_ids(me["roleId"]))
        if allow_self and target_user_id == me['userId']:
            allowed.add(target_role)
    else:
        allowed = set(descendant_role_ids(me["roleId"]))

    if target_role not in allowed:
        raise HTTPException(status_code=403, detail="超出可管理范围：只能操作本人/下级角色范围的用户")

    if me["roleId"] == DEPT_SCOPE_ROLE and target_dept != me["departmentId"]:
        raise HTTPException(status_code=403, detail="只能操作本系用户")
    if me['roleId'] == TEACHER_ROLE and target_dept != me['departmentId']:
        raise HTTPException(status_code=403, detail="只能操作本系学生")

    return target


def register_admin_user_routes(app: FastAPI):

    @app.get("/api/admin/users", response_model=UserList)
    def admin_get_users(
        page: int = Query(default=1, ge=1),
        rows: int = Query(default=10, ge=1, le=100),
        realName: str = Query(default=None),
        phone: str = Query(default=None),
        roleId: int = Query(default=None),
        departmentId: int = Query(default=None),
        me=Depends(require_permission("user:list")),
    ):
        """用户列表（数据范围由角色决定）"""
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            # 数据范围
            if me["roleId"] == DEPT_SCOPE_ROLE:
                if departmentId is not None and departmentId != me["departmentId"]:
                    raise HTTPException(status_code=403, detail="只能查询本系用户")
                departmentId = me["departmentId"]
            elif me["roleId"] == TEACHER_ROLE:
                if departmentId is not None and departmentId != me["departmentId"]:
                    raise HTTPException(status_code=403, detail="只能查询本系学生")
                departmentId = me["departmentId"]
                if roleId is not None and roleId != STUDENT_ROLE:
                    raise HTTPException(status_code=403, detail="教师只能查看学生")
                roleId = STUDENT_ROLE

            where_conditions = []
            params = []
            if realName:
                where_conditions.append("realName LIKE ?")
                params.append("%" + realName + "%")
            if phone:
                where_conditions.append("phone LIKE ?")
                params.append("%" + phone + "%")
            if roleId is not None:
                where_conditions.append("roleId = ?")
                params.append(roleId)
            if departmentId is not None:
                where_conditions.append("departmentId = ?")
                params.append(departmentId)

            where_clause = ""
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)

            cursor.execute("SELECT COUNT(*) FROM UsersInfo" + where_clause, params)
            total_count = cursor.fetchone()[0]

            start_row = (page - 1) * rows + 1
            end_row = page * rows
            query = """
                SELECT * FROM (
                    SELECT ROW_NUMBER() OVER (ORDER BY userId ASC) AS RowNum,
                           userId, realName, phone, roleId, departmentId, gender,
                           nativePlace, politicalStatus, loginPassword, idCard, email
                    FROM UsersInfo""" + where_clause + """
                ) AS RankedUsers
                WHERE RowNum BETWEEN ? AND ?
            """
            cursor.execute(query, params + [start_row, end_row])

            columns = [c[0] for c in cursor.description]
            users = []
            for row in cursor.fetchall():
                d = dict(zip(columns, row))
                d.pop("RowNum", None)
                users.append(User(**d))

            return UserList(total=total_count, rows=users)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail="查询用户失败: " + str(e))
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.put("/api/admin/users/{user_id}/role")
    def admin_update_role(
        user_id: int,
        roleId: int = Query(..., description="新角色ID"),
        me=Depends(require_permission("role:assign")),
    ):
        """调整用户角色（仅下级角色，且不超出数据范围）"""
        _target_in_scope(me, user_id, "descendant", allow_self=False)
        if roleId not in descendant_role_ids(me['roleId']):
            raise HTTPException(403, '不可授予本人同级或上级角色')
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM RoleInfo WHERE roleId = ?", (roleId,))
            if cursor.fetchone()[0] == 0:
                raise HTTPException(status_code=400, detail="角色ID不合法")
            cursor.execute("UPDATE UsersInfo SET roleId = ? WHERE userId = ?", (roleId, user_id))
            connection.commit()
            return {"msg": "角色修改成功", "userId": user_id, "roleId": roleId}
        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail="修改角色失败: " + str(e))
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.put("/api/admin/users/{user_id}/reset-password")
    def admin_reset_password(
        user_id: int,
        newPassword: str = Query(default="123456", min_length=6, max_length=128),
        me=Depends(require_permission("user:reset")),
    ):
        """重置密码（本人 + 直接下一层；系管理员限本系）"""
        _target_in_scope(me, user_id, "self_child", allow_self=True)
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("UPDATE UsersInfo SET loginPassword = ?, passwordHash=? WHERE userId = ?", ('', hash_password(newPassword), user_id))
            revoke_user_sessions(cursor, user_id)
            connection.commit()
            return {"msg": "密码已重置", "userId": user_id}
        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail="重置密码失败: " + str(e))
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.put("/api/admin/users/{user_id}")
    def admin_update_user(
        user_id: int,
        realName: str = Query(default=None),
        phone: str = Query(default=None),
        gender: str = Query(default=None),
        nativePlace: str = Query(default=None),
        politicalStatus: str = Query(default=None),
        email: str = Query(default=None),
        me=Depends(require_permission("user:edit")),
    ):
        """编辑用户信息（系管理员=本系；教师=本系学生）"""
        target = _target_in_scope(me, user_id, "descendant", allow_self=True)
        if me["roleId"] == TEACHER_ROLE and target[2] != STUDENT_ROLE:
            raise HTTPException(status_code=403, detail="教师只能编辑学生信息")

        fields = []
        params = []
        for name, value in (
            ("realName", realName),
            ("phone", phone),
            ("gender", gender),
            ("nativePlace", nativePlace),
            ("politicalStatus", politicalStatus),
            ("email", email),
        ):
            if value is not None:
                fields.append(name + " = ?")
                params.append(value)
        if not fields:
            raise HTTPException(status_code=400, detail="没有需要更新的字段")
        params.append(user_id)

        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("UPDATE UsersInfo SET " + ", ".join(fields) + " WHERE userId = ?", params)
            connection.commit()
            return {"msg": "用户信息已更新", "userId": user_id}
        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail="更新用户失败: " + str(e))
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.delete("/api/admin/users/{user_id}")
    def admin_delete_user(user_id: int, me=Depends(require_permission("user:delete"))):
        """删除用户（仅下级角色；系管理员限本系）"""
        _target_in_scope(me, user_id, "descendant", allow_self=False)
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("DELETE FROM UsersInfo WHERE userId = ?", (user_id,))
            connection.commit()
            return {"msg": "删除成功", "userId": user_id}
        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail="删除用户失败: " + str(e))
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
