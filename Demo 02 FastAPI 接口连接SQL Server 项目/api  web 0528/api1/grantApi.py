# -*- coding: utf-8 -*-
"""分级授权（授权决策权）+ 时间受限授权 + 授权台账

规则：
- 超级管理员(4)：可授予全部角色，全院范围；
- 学院管理员(5)：可授予其下级角色，全院范围；
- 系管理员(2)：可授予其下级角色，仅限本院系用户；
- 时间受限：授权可设结束时间，到期自动失效并把用户角色回退为原角色；
- 可提前撤销；全程记录授权台账（谁在何时给谁授了什么）。
"""

from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Depends

from database import get_db_connection
from permissionApi import require_permission, descendant_role_ids, load_user


def _grantable_roles(cursor, me):
    """当前用户可授予的角色列表"""
    if me["roleId"] == 4:
        cursor.execute("SELECT roleId, roleName FROM RoleInfo ORDER BY roleId")
    else:
        ids = descendant_role_ids(me["roleId"])
        if not ids:
            return []
        marks = ",".join(["?"] * len(ids))
        cursor.execute(
            "SELECT roleId, roleName FROM RoleInfo WHERE roleId IN (%s) ORDER BY roleId" % marks,
            ids,
        )
    return [{"roleId": r[0], "roleName": r[1]} for r in cursor.fetchall()]


def _expire_grants(cursor):
    """把已到期的授权置为 expired，并回退用户角色"""
    cursor.execute(
        "SELECT grantId, userId, roleId, originalRoleId FROM RoleGrant "
        "WHERE status = 'active' AND endTime IS NOT NULL AND endTime <= GETDATE()"
    )
    rows = cursor.fetchall()
    for grant_id, user_id, role_id, original_role_id in rows:
        cursor.execute("SELECT roleId FROM UsersInfo WHERE userId = ?", (user_id,))
        current = cursor.fetchone()
        if current and current[0] == role_id and original_role_id is not None:
            cursor.execute(
                "UPDATE UsersInfo SET roleId = ? WHERE userId = ?", (original_role_id, user_id)
            )
        cursor.execute("UPDATE RoleGrant SET status = 'expired' WHERE grantId = ?", (grant_id,))
    return len(rows)


def register_grant_routes(app: FastAPI):

    @app.get("/api/admin/grants/scope")
    def grant_scope(me=Depends(require_permission("role:assign"))):
        """当前用户可授予的角色范围（前端下拉用）"""
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            return {"roles": _grantable_roles(cursor, me)}
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/admin/grants")
    def list_grants(
        page: int = Query(default=1, ge=1),
        rows: int = Query(default=10, ge=1, le=100),
        userId: int = Query(default=None),
        status: str = Query(default=None),
        me=Depends(require_permission("role:assign")),
    ):
        """授权台账（按数据范围过滤）"""
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            _expire_grants(cursor)
            connection.commit()

            where = []
            params = []
            if userId is not None:
                where.append("g.userId = ?")
                params.append(userId)
            if status:
                where.append("g.status = ?")
                params.append(status)
            # 系管理员：只看本院系用户的授权
            if me["roleId"] == 2:
                where.append("u.departmentId = ?")
                params.append(me["departmentId"])

            where_clause = (" WHERE " + " AND ".join(where)) if where else ""

            cursor.execute(
                "SELECT COUNT(*) FROM RoleGrant g JOIN UsersInfo u ON u.userId = g.userId" + where_clause,
                params,
            )
            total = cursor.fetchone()[0]

            start_row = (page - 1) * rows + 1
            end_row = page * rows
            cursor.execute(
                """
                SELECT * FROM (
                    SELECT ROW_NUMBER() OVER (ORDER BY g.grantId DESC) AS RowNum,
                           g.grantId, g.userId, u.realName, g.roleId, r.roleName,
                           g.originalRoleId, g.grantedBy, gb.realName AS grantedByName,
                           g.startTime, g.endTime, g.status, g.revokedBy,
                           g.revokedAt, g.remark, g.createdAt
                    FROM RoleGrant g
                    JOIN UsersInfo u  ON u.userId = g.userId
                    LEFT JOIN RoleInfo r  ON r.roleId = g.roleId
                    LEFT JOIN UsersInfo gb ON gb.userId = g.grantedBy
                    """ + where_clause + """
                ) AS T
                WHERE RowNum BETWEEN ? AND ?
                """,
                params + [start_row, end_row],
            )
            columns = [c[0] for c in cursor.description]
            items = []
            for row in cursor.fetchall():
                d = dict(zip(columns, row))
                d.pop("RowNum", None)
                for key in ("startTime", "endTime", "revokedAt", "createdAt"):
                    if d.get(key) is not None:
                        d[key] = str(d[key])
                items.append(d)

            return {"total": total, "page": page, "rows": items}
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.post("/api/admin/grants")
    def create_grant(
        userId: int = Query(..., description="被授权用户ID"),
        roleId: int = Query(..., description="授予的角色ID"),
        endTime: str = Query(default=None, description="失效时间，如 2026-12-31 23:59:59，空=永久"),
        remark: str = Query(default=None, description="备注"),
        me=Depends(require_permission("role:assign")),
    ):
        """授权（支持时间受限）"""
        target = load_user(userId)
        if not target:
            raise HTTPException(status_code=404, detail="用户不存在")
        if me["roleId"] == 2 and target[3] != me["departmentId"]:
            raise HTTPException(status_code=403, detail="系管理员只能给本院系用户授权")

        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            allowed = [r["roleId"] for r in _grantable_roles(cursor, me)]
            if roleId not in allowed:
                raise HTTPException(status_code=403, detail="超出可授予的角色范围")

            cursor.execute("SELECT roleId FROM UsersInfo WHERE userId = ?", (userId,))
            original_role = cursor.fetchone()[0]

            cursor.execute(
                "INSERT INTO RoleGrant (userId, roleId, originalRoleId, grantedBy, startTime, endTime, status, remark) "
                "VALUES (?, ?, ?, ?, GETDATE(), ?, 'active', ?)",
                (userId, roleId, original_role, me["userId"],
                 (endTime or None), remark),
            )
            cursor.execute("UPDATE UsersInfo SET roleId = ? WHERE userId = ?", (roleId, userId))
            connection.commit()
            return {
                "msg": "授权成功",
                "userId": userId,
                "roleId": roleId,
                "originalRoleId": original_role,
                "endTime": endTime,
            }
        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail="授权失败: " + str(e))
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.put("/api/admin/grants/{grant_id}/revoke")
    def revoke_grant(grant_id: int, me=Depends(require_permission("role:assign"))):
        """提前撤销授权（授权人本人、上级或超级管理员）"""
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute(
                "SELECT userId, roleId, originalRoleId, grantedBy, status FROM RoleGrant WHERE grantId = ?",
                (grant_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="授权记录不存在")
            user_id, role_id, original_role, granted_by, status = row
            if status != "active":
                raise HTTPException(status_code=400, detail="该授权已失效，无需撤销")
            if me["roleId"] != 4 and me["userId"] != granted_by:
                raise HTTPException(status_code=403, detail="只能撤销本人发起的授权")

            cursor.execute("SELECT roleId FROM UsersInfo WHERE userId = ?", (user_id,))
            current = cursor.fetchone()
            if current and current[0] == role_id and original_role is not None:
                cursor.execute(
                    "UPDATE UsersInfo SET roleId = ? WHERE userId = ?", (original_role, user_id)
                )
            cursor.execute(
                "UPDATE RoleGrant SET status = 'revoked', revokedBy = ?, revokedAt = GETDATE() WHERE grantId = ?",
                (me["userId"], grant_id),
            )
            connection.commit()
            return {"msg": "已撤销授权", "grantId": grant_id, "userId": user_id}
        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail="撤销失败: " + str(e))
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()