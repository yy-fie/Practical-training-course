# -*- coding: utf-8 -*-
"""权限（RBAC）公共模块与权限管理接口

权限模型：
  Permission(permCode) -- RolePermission(roleId, permId) -- RoleInfo(parentRoleId 角色层级)
  角色层级：4 超级管理员 -> 5 学院管理员 -> 2 系管理员 -> 3 教师 -> 1 学生

调用方式：Authorization: Bearer <访问令牌>，用户身份由会话验证获得。
校验失败：401（会话失效/用户不存在）、403（缺少权限码）
"""

from fastapi import FastAPI, HTTPException, Request, Depends, Body
from typing import List

from database import get_db_connection


def load_user(user_id):
    """返回 (userId, realName, roleId, departmentId)"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT userId, realName, roleId, departmentId FROM UsersInfo WHERE userId = ? AND isActive=1 AND isDeleted=0",
            (user_id,),
        )
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def user_permissions(user_id):
    """返回 (用户行, 权限码集合)"""
    user = load_user(user_id)
    if not user:
        return None, set()
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT TOP 1 roleId FROM RoleGrant WHERE userId=? AND status='active' "
            "AND (startTime IS NULL OR startTime<=GETDATE()) "
            "AND (endTime IS NULL OR GETDATE()<endTime) ORDER BY grantId DESC", (user_id,))
        temporary = cursor.fetchone()
        if temporary:
            user = (user[0], user[1], temporary[0], user[3])
        cursor.execute(
            "SELECT p.permCode FROM Permission p "
            "JOIN RolePermission rp ON rp.permId = p.permId "
            "WHERE rp.roleId = ?",
            (user[2],),
        )
        perms = set(row[0] for row in cursor.fetchall())
        return user, perms
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def current_user(user_id=None):
    """校验登录信息并返回当前用户 + 权限码集合"""
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录")
    user, perms = user_permissions(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="登录用户不存在")
    return {
        "userId": user[0],
        "realName": user[1],
        "roleId": user[2],
        "departmentId": user[3],
        "permissions": perms,
    }


def require_permission(code):
    """依赖：要求当前用户具备指定权限码"""

    def dependency(request: Request):
        me = request.state.me
        if code not in me["permissions"]:
            raise HTTPException(status_code=403, detail="没有权限：需要 " + code)
        return me

    return dependency


def subordinate_role_ids(role_id):
    """直接下级角色ID列表"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT roleId FROM RoleInfo WHERE parentRoleId = ?", (role_id,))
        return [row[0] for row in cursor.fetchall()]
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def descendant_role_ids(role_id):
    """所有下级角色ID（递归）"""
    result = []
    stack = [role_id]
    visited = {role_id}
    while stack:
        current = stack.pop()
        for child in subordinate_role_ids(current):
            if child not in visited:
                visited.add(child)
                result.append(child)
                stack.append(child)
    return result


def register_permission_routes(app: FastAPI):
    """权限查询与维护接口"""

    @app.get("/api/me/permissions")
    def my_permissions(request: Request):
        """当前登录用户的角色与权限码（前端菜单/按钮据此显示）"""
        me = request.state.me
        return {
            "userId": me["userId"],
            "realName": me["realName"],
            "roleId": me["roleId"],
            "departmentId": me["departmentId"],
            "permissions": sorted(me["permissions"]),
        }

    @app.get("/api/admin/roles")
    def list_roles(_me=Depends(require_permission("user:list"))):
        """角色列表（含上级角色，供用户管理的角色下拉/筛选使用）"""
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT roleId, roleName, parentRoleId FROM RoleInfo ORDER BY roleId")
            rows = cursor.fetchall()
            return {
                "total": len(rows),
                "roles": [
                    {"roleId": r[0], "roleName": r[1], "parentRoleId": r[2]}
                    for r in rows
                ],
            }
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/admin/permissions")
    def list_permissions(_me=Depends(require_permission("permission:manage"))):
        """全部权限点（超级管理员）"""
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT permId, permCode, permName, category FROM Permission ORDER BY permId")
            rows = cursor.fetchall()
            return {
                "total": len(rows),
                "permissions": [
                    {"permId": r[0], "permCode": r[1], "permName": r[2], "category": r[3]}
                    for r in rows
                ],
            }
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.get("/api/admin/roles/permissions")
    def role_permission_matrix(_me=Depends(require_permission("permission:manage"))):
        """角色 × 权限 矩阵（超级管理员）"""
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute("SELECT roleId, roleName, parentRoleId FROM RoleInfo ORDER BY roleId")
            roles = [
                {"roleId": r[0], "roleName": r[1], "parentRoleId": r[2]}
                for r in cursor.fetchall()
            ]

            cursor.execute("SELECT permId, permCode, permName, category FROM Permission ORDER BY permId")
            perms = [
                {"permId": r[0], "permCode": r[1], "permName": r[2], "category": r[3]}
                for r in cursor.fetchall()
            ]

            cursor.execute("SELECT roleId, permId FROM RolePermission")
            mapping = {}
            for rid, pid in cursor.fetchall():
                mapping.setdefault(str(rid), []).append(pid)

            return {"roles": roles, "permissions": perms, "mapping": mapping}
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    @app.put("/api/admin/roles/{role_id}/permissions")
    def update_role_permissions(
        role_id: int,
        permCodes: List[str] = Body(..., embed=True),
        _me=Depends(require_permission("permission:manage")),
    ):
        """保存某角色的权限（超级管理员）"""
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute("SELECT COUNT(*) FROM RoleInfo WHERE roleId = ?", (role_id,))
            if cursor.fetchone()[0] == 0:
                raise HTTPException(status_code=404, detail="角色不存在")

            cursor.execute("DELETE FROM RolePermission WHERE roleId = ?", (role_id,))
            if permCodes:
                marks = ",".join(["?"] * len(permCodes))
                cursor.execute(
                    "SELECT permId FROM Permission WHERE permCode IN (%s)" % marks, permCodes
                )
                ids = [r[0] for r in cursor.fetchall()]
                for pid in ids:
                    cursor.execute(
                        "INSERT INTO RolePermission (roleId, permId) VALUES (?, ?)",
                        (role_id, pid),
                    )
            connection.commit()
            return {"msg": "权限已更新", "roleId": role_id, "count": len(permCodes)}
        except HTTPException:
            raise
        except Exception as e:
            if connection:
                connection.rollback()
            raise HTTPException(status_code=500, detail="更新权限失败: " + str(e))
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
