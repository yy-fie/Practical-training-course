# -*- coding: utf-8 -*-
"""分级授权（授权决策权）+ 时间受限授权 + 授权台账

规则：
- 超级管理员(4)：可授予全部角色，全院范围；
- 学院管理员(5)：可授予其下级角色，全院范围；
- 系管理员(2)：可授予其下级角色，仅限本院系用户；
- 时间受限：按数据库时刻动态判断，不覆盖用户的永久角色；
- 可提前撤销；全程记录授权台账（谁在何时给谁授了什么）。
"""

from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Depends

from database import get_db_connection
from permissionApi import require_permission, descendant_role_ids, load_user, user_permissions

STATUS_SQL = "CASE WHEN g.status='revoked' THEN 'revoked' WHEN g.status='expired' OR (g.endTime IS NOT NULL AND g.endTime<=GETDATE()) THEN 'expired' WHEN g.startTime>GETDATE() THEN 'pending' ELSE 'active' END"


def parse_time(value, name):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is not None or parsed < datetime(1753, 1, 1) or parsed > datetime(9999, 12, 31, 23, 59, 59, 997000):
            raise ValueError('timezone')
        return parsed
    except ValueError:
        raise HTTPException(400, name + '格式错误，请填写数据库本地时间，例如 2026-12-31 23:59:59')


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
            where = []
            params = []
            if userId is not None:
                where.append("g.userId = ?")
                params.append(userId)
            if status:
                if status not in ('pending', 'active', 'expired', 'revoked'):
                    raise HTTPException(400, '授权状态不合法')
                where.append('(' + STATUS_SQL + ') = ?')
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
                           g.startTime, g.endTime, """ + STATUS_SQL + """ AS status, g.revokedBy,
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
        startTime: str = Query(default=None, description="生效时间，空=立即生效"),
        endTime: str = Query(default=None, description="失效时间，如 2026-12-31 23:59:59，空=永久"),
        remark: str = Query(default=None, description="备注"),
        me=Depends(require_permission("role:assign")),
    ):
        """授权（支持时间受限）"""
        starts = parse_time(startTime, '生效时间')
        ends = parse_time(endTime, '失效时间')
        target = load_user(userId)
        if not target:
            raise HTTPException(status_code=404, detail="用户不存在")
        if me["roleId"] == 2 and target[3] != me["departmentId"]:
            raise HTTPException(status_code=403, detail="系管理员只能给本院系用户授权")
        if userId == me['userId']:
            raise HTTPException(403, '不可给本人发起角色授权')
        effective_target, _ = user_permissions(userId)
        if me['roleId'] != 4:
            descendants = descendant_role_ids(me['roleId'])
            if target[2] not in descendants or effective_target[2] not in descendants:
                raise HTTPException(403, '只能给下级角色范围内的用户授权')
        if remark and len(remark) > 200:
            raise HTTPException(400, '备注不能超过 200 字')

        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            allowed = [r["roleId"] for r in _grantable_roles(cursor, me)]
            if roleId not in allowed:
                raise HTTPException(status_code=403, detail="超出可授予的角色范围")

            cursor.execute("SELECT roleId,departmentId FROM UsersInfo WITH (UPDLOCK,HOLDLOCK) WHERE userId = ?", (userId,))
            locked_target = cursor.fetchone()
            if not locked_target:
                raise HTTPException(404, '用户不存在')
            original_role = locked_target[0]
            if me['roleId'] != 4 and original_role not in descendants:
                raise HTTPException(403, '用户角色已改变，超出管理范围')
            if me['roleId'] == 2 and locked_target[1] != me['departmentId']:
                raise HTTPException(403, '用户院系已改变，超出管理范围')
            cursor.execute('SELECT GETDATE()')
            now = cursor.fetchone()[0]
            starts = starts or now
            # 与现有 DATETIME 列保持同样的精度，避免相邻区间因参数精度不同误判重叠。
            cursor.execute('SELECT CAST(? AS DATETIME), CAST(? AS DATETIME)', (starts, ends))
            starts, ends = cursor.fetchone()
            if ends is not None and (ends <= starts or ends <= now):
                raise HTTPException(400, '失效时间必须晚于生效时间和当前时间')
            cursor.execute(
                "SELECT TOP 1 grantId FROM RoleGrant WITH (UPDLOCK,HOLDLOCK) WHERE userId=? "
                "AND status='active' AND (endTime IS NULL OR endTime>CAST(? AS DATETIME)) "
                "AND (? IS NULL OR startTime IS NULL OR startTime<CAST(? AS DATETIME))",
                (userId, starts, ends, ends))
            if cursor.fetchone():
                raise HTTPException(409, '该用户已有重叠的授权时间段，请先撤销或选择其他时间段')

            cursor.execute(
                "INSERT INTO RoleGrant (userId, roleId, originalRoleId, grantedBy, startTime, endTime, status, remark) "
                "OUTPUT INSERTED.grantId VALUES (?, ?, ?, ?, ?, ?, 'active', ?)",
                (userId, roleId, original_role, me["userId"], starts, ends, remark),
            )
            grant_id = cursor.fetchone()[0]
            connection.commit()
            return {
                "msg": "授权成功",
                "userId": userId,
                "roleId": roleId,
                "originalRoleId": original_role,
                'grantId': grant_id,
                'startTime': str(starts),
                "endTime": str(ends) if ends else None,
                'status': 'pending' if starts > now else 'active',
            }
        except HTTPException:
            if connection:
                connection.rollback()
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
        """提前撤销待生效/生效中的授权（授权人本人或超级管理员）"""
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            # 与创建授权保持相同锁顺序：先用户，再授权。
            cursor.execute('SELECT userId FROM RoleGrant WHERE grantId=?', (grant_id,))
            grant_user = cursor.fetchone()
            if not grant_user:
                raise HTTPException(404, '授权记录不存在')
            cursor.execute('SELECT departmentId FROM UsersInfo WITH (UPDLOCK,HOLDLOCK) WHERE userId=?',
                           (grant_user[0],))
            target = cursor.fetchone()
            cursor.execute(
                "SELECT userId, roleId, originalRoleId, grantedBy, status, endTime, GETDATE() FROM RoleGrant WITH (UPDLOCK,HOLDLOCK) WHERE grantId = ?",
                (grant_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="授权记录不存在")
            user_id, role_id, original_role, granted_by, status, ends, now = row
            if status != "active" or (ends is not None and ends <= now):
                raise HTTPException(status_code=400, detail="该授权已失效，无需撤销")
            if me["roleId"] != 4 and me["userId"] != granted_by:
                raise HTTPException(status_code=403, detail="只能撤销本人发起的授权")

            if me['roleId'] == 2 and target and target[0] != me['departmentId']:
                raise HTTPException(403, '只能撤销本系用户的授权')
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
