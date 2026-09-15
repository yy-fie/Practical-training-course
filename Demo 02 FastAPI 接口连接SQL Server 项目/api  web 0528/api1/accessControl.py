# -*- coding: utf-8 -*-
"""统一访问控制中间件（让功能逻辑一致）

规则：
1) 旧接口（/api/users、/api/stations 等）同样受权限码约束，避免绕过 /api/admin 的权限体系；
2) 本人接口（/api/users/{id} 的 GET/PUT、/api/users/{id}/password）允许本人操作；
3) /api/admin/*、/api/me/* 由各自依赖校验，这里放行；
4) 公开接口（登录、文档）放行。
"""

import re

from fastapi import Request
from fastapi.responses import JSONResponse

from permissionApi import user_permissions

PUBLIC_PATHS = {"/", "/docs", "/redoc", "/openapi.json", "/api/users/login"}

RULES = [
    (re.compile(r"^/api/users/?$"), {"GET": "user:list", "POST": "user:edit"}),
    (re.compile(r"^/api/users/search"), {"GET": "user:list"}),
    (re.compile(r"^/api/usersDelete"), {"DELETE": "user:delete"}),
    (re.compile(r"^/api/users/(?P<uid>\d+)/password"), {"PUT": "self_or:user:reset"}),
    (
        re.compile(r"^/api/users/(?P<uid>\d+)"),
        {
            "GET": "self_or:user:list",
            "PUT": "self_or:user:edit",
            "DELETE": "user:delete",
        },
    ),
    (
        re.compile(r"^/api/(stations|books|buildings|floors|majors)"),
        {
            "GET": "analysis:view",
            "POST": "user:edit",
            "PUT": "user:edit",
            "DELETE": "user:delete",
        },
    ),
]


def register_access_control(app):
    @app.middleware("http")
    async def access_control(request: Request, call_next):
        path = request.url.path
        method = request.method.upper()

        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)
        if path.startswith("/api/admin") or path.startswith("/api/me"):
            return await call_next(request)

        rule = None
        match = None
        for pattern, methods in RULES:
            m = pattern.match(path)
            if m and method in methods:
                rule = methods[method]
                match = m
                break
        if not rule:
            return await call_next(request)

        x_user_id = request.headers.get("X-User-Id")
        if not x_user_id:
            return JSONResponse(
                status_code=401,
                content={"detail": "未提供登录信息（请求头 X-User-Id）"},
            )
        try:
            user_id = int(x_user_id)
        except ValueError:
            return JSONResponse(status_code=401, content={"detail": "登录信息格式错误"})

        user, perms = user_permissions(user_id)
        if not user:
            return JSONResponse(status_code=401, content={"detail": "登录用户不存在"})

        if rule.startswith("self_or:"):
            code = rule.split(":", 1)[1]
            uid = None
            if match is not None and "uid" in match.groupdict():
                uid = int(match.group("uid"))
            if uid is not None and user[0] == uid:
                return await call_next(request)
            if code not in perms:
                return JSONResponse(status_code=403, content={"detail": "没有权限：需要 " + code})
            return await call_next(request)

        if rule not in perms:
            return JSONResponse(status_code=403, content={"detail": "没有权限：需要 " + rule})
        return await call_next(request)