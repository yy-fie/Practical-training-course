"""所有 API 验证 Bearer 会话；旧用户接口复用管理接口的数据范围规则。"""
import re
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from authApi import authenticate_request
from permissionApi import current_user

PUBLIC_PATHS = {'/', '/docs', '/docs/oauth2-redirect', '/redoc', '/openapi.json',
                '/api/auth/login', '/api/auth/refresh', '/api/users/login'}
PERSONAL_FIELDS = {'realName', 'phone', 'gender', 'nativePlace', 'politicalStatus', 'email', 'idCard'}


def require_code(me, code):
    if code not in me['permissions']:
        raise HTTPException(403, '没有权限：需要 ' + code)


def check_legacy_scope(me, user_id):
    from adminUserApi import _target_in_scope, TEACHER_ROLE, STUDENT_ROLE
    target = _target_in_scope(me, user_id, 'descendant', allow_self=False)
    if me['roleId'] == TEACHER_ROLE and (target[2] != STUDENT_ROLE or target[3] != me['departmentId']):
        raise HTTPException(403, '教师只能操作本系学生')


def register_access_control(app):
    @app.middleware('http')
    async def access_control(request: Request, call_next):
        path = request.url.path.rstrip('/') or '/'
        method = request.method.upper()
        if method == 'OPTIONS' or path in PUBLIC_PATHS or not path.startswith('/api/'):
            return await call_next(request)
        try:
            uid = await run_in_threadpool(authenticate_request, request)
            me = await run_in_threadpool(current_user, uid)
            request.state.me = me
            if path.startswith('/api/admin/') or path.startswith('/api/me/') or path == '/api/auth/logout':
                return await call_next(request)
            user_match = re.fullmatch(r'/api/users/(\d+)(/password)?', path)
            if user_match:
                target_id = int(user_match.group(1))
                if user_match.group(2):
                    if target_id != uid:
                        raise HTTPException(403, '只能修改本人密码，请使用管理员重置接口')
                    require_code(me, 'password:self')
                elif method == 'GET' and target_id == uid:
                    pass
                elif method == 'PUT' and target_id == uid:
                    require_code(me, 'profile:self')
                    payload = await request.json()
                    if not isinstance(payload, dict) or set(payload) - PERSONAL_FIELDS:
                        raise HTTPException(403, '个人信息接口不可修改角色、院系或密码')
                else:
                    code = {'GET': 'user:list', 'PUT': 'user:edit', 'DELETE': 'user:delete'}.get(method)
                    if code:
                        require_code(me, code)
                        await run_in_threadpool(check_legacy_scope, me, target_id)
                    if method == 'PUT':
                        payload = await request.json()
                        if not isinstance(payload, dict) or set(payload) - PERSONAL_FIELDS:
                            raise HTTPException(403, '调整角色请使用授权接口')
            elif path in ('/api/users', '/api/users/search'):
                if method == 'GET':
                    require_code(me, 'user:list')
                    if me['roleId'] in (2, 3):
                        raise HTTPException(403, '请使用 /api/admin/users 查询管理范围内的用户')
                elif method == 'POST':
                    require_code(me, 'user:edit')
                    payload = await request.json()
                    from permissionApi import descendant_role_ids
                    allowed = await run_in_threadpool(descendant_role_ids, me['roleId'])
                    if not isinstance(payload, dict) or payload.get('roleId') not in allowed:
                        raise HTTPException(403, '只能新增下级角色的用户')
                    if me['roleId'] in (2, 3) and payload.get('departmentId') != me['departmentId']:
                        raise HTTPException(403, '只能新增本系用户')
            elif path == '/api/usersDelete' and method == 'DELETE':
                require_code(me, 'user:delete')
                for target in request.query_params.getlist('user_ids'):
                    try:
                        target_id = int(target)
                    except ValueError:
                        raise HTTPException(422, '用户 ID 必须为整数')
                    await run_in_threadpool(check_legacy_scope, me, target_id)
            elif re.match(r'^/api/(stations|books|buildings|floors|majors)', path):
                code = {'GET': 'analysis:view', 'POST': 'user:edit', 'PUT': 'user:edit',
                        'DELETE': 'user:delete'}.get(method)
                if code:
                    require_code(me, code)
            return await call_next(request)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={'detail': exc.detail}, headers=exc.headers)
        except (ValueError, TypeError):
            return JSONResponse(status_code=422, content={'detail': '请求参数格式错误'})
