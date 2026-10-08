"""双令牌、可撤销会话、登录日志。刷新令牌轮换采用数据库条件更新。"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from database import get_db_connection
from security import (create_tokens, decode_token, hash_password, token_hash,
                      verify_stored_password, REFRESH_SECONDS)


class LoginInput(BaseModel):
    username: str = Field(..., min_length=1, max_length=200)
    password: str = Field(..., min_length=1, max_length=128)


class RefreshInput(BaseModel):
    refreshToken: str = Field(..., min_length=1, max_length=4096)


def authenticate_request(request):
    scheme, _, token = request.headers.get('Authorization', '').partition(' ')
    if scheme.lower() != 'bearer' or not token:
        raise HTTPException(401, '请先登录', headers={'WWW-Authenticate': 'Bearer'})
    claims = decode_token(token, 'access')
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            'SELECT s.userId FROM AuthSession s JOIN UsersInfo u ON u.userId=s.userId '
            'WHERE s.sessionId=? AND s.userId=? AND s.revokedAt IS NULL '
            'AND s.expiresAt>SYSUTCDATETIME() AND u.isActive=1 AND u.isDeleted=0',
            (claims['sid'], int(claims['sub'])))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(401, '登录已失效，请重新登录')
        request.state.session_id = claims['sid']
        request.state.user_id = row[0]
        return row[0]
    finally:
        cursor.close()
        connection.close()


def revoke_user_sessions(cursor, user_id):
    cursor.execute('UPDATE AuthSession SET revokedAt=SYSUTCDATETIME() '
                   'WHERE userId=? AND revokedAt IS NULL', (user_id,))


def login(data, request):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            'SELECT userId,realName,phone,roleId,departmentId,gender,nativePlace,'
            'politicalStatus,idCard,email,passwordHash,loginPassword,isActive,isDeleted '
            'FROM UsersInfo WHERE phone=? OR email=?', (data.username, data.username))
        columns = [c[0] for c in cursor.description]
        rows = cursor.fetchall()
        row = rows[0] if len(rows) == 1 else None
        user = dict(zip(columns, row)) if row else None
        valid = bool(user and user['isActive'] and not user['isDeleted'] and
                     verify_stored_password(data.password, user['passwordHash'], user['loginPassword']))
        cursor.execute(
            'INSERT INTO LoginLog(userId,username,success,ipAddress,reason) VALUES(?,?,?,?,?)',
            (user['userId'] if user else None, data.username, int(valid),
             request.client.host if request.client else '', '登录成功' if valid else '账号或密码错误，或账号不可用'))
        if not valid:
            connection.commit()
            raise HTTPException(401, '用户名或密码错误，或账号不可用')
        # 仅在该账号验证成功后迁移历史明文密码；不批量改动既有账号。
        if not user['passwordHash']:
            cursor.execute('UPDATE UsersInfo SET passwordHash=?,loginPassword=? WHERE userId=?',
                           (hash_password(data.password), '', user['userId']))
        session_id = str(uuid4())
        tokens = create_tokens(user['userId'], session_id)
        cursor.execute(
            'INSERT INTO AuthSession(sessionId,userId,refreshHash,expiresAt) '
            'VALUES(?,?,?,DATEADD(second,?,SYSUTCDATETIME()))',
            (session_id, user['userId'], token_hash(tokens['refreshToken']), REFRESH_SECONDS))
        connection.commit()
        for field in ('passwordHash', 'loginPassword', 'isActive', 'isDeleted'):
            user.pop(field, None)
        return dict(tokens, user=user)
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def register_auth_routes(app: FastAPI):
    @app.post('/api/auth/login')
    def auth_login(data: LoginInput, request: Request):
        return login(data, request)

    @app.post('/api/auth/refresh')
    def refresh(data: RefreshInput):
        claims = decode_token(data.refreshToken, 'refresh')
        expires = datetime.fromtimestamp(claims['exp'], timezone.utc)
        tokens = create_tokens(int(claims['sub']), claims['sid'], expires)
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                'UPDATE s SET refreshHash=? FROM AuthSession s JOIN UsersInfo u ON u.userId=s.userId '
                'WHERE s.sessionId=? AND s.userId=? AND s.refreshHash=? AND s.revokedAt IS NULL '
                'AND s.expiresAt>SYSUTCDATETIME() AND u.isActive=1 AND u.isDeleted=0',
                (token_hash(tokens['refreshToken']), claims['sid'], int(claims['sub']),
                 token_hash(data.refreshToken)))
            if cursor.rowcount != 1:
                raise HTTPException(401, '刷新令牌已失效，请重新登录')
            connection.commit()
            return tokens
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    @app.post('/api/auth/logout')
    def logout(request: Request):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute('UPDATE AuthSession SET revokedAt=SYSUTCDATETIME() WHERE sessionId=?',
                           (request.state.session_id,))
            connection.commit()
            return {'msg': '已退出登录'}
        finally:
            cursor.close()
            connection.close()
