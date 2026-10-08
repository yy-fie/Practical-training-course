"""密码哈希与 JWT；不在令牌中保存用户资料或权限快照。"""
import base64
import hashlib
import hmac
import os
import secrets
from pathlib import Path
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from fastapi import HTTPException

ACCESS_SECONDS = 900
REFRESH_SECONDS = 7 * 24 * 3600
ITERATIONS = 600000
ISSUER = 'practical-training-api'


def signing_key():
    configured = os.getenv('JWT_SECRET')
    if configured:
        if len(configured) < 32:
            raise RuntimeError('JWT_SECRET 至少需要 32 个字符')
        return configured
    key_file = Path(__file__).resolve().parents[3] / '.local' / 'jwt-secret'
    key_file.parent.mkdir(exist_ok=True)
    try:
        with key_file.open('x', encoding='utf-8') as stream:
            stream.write(secrets.token_urlsafe(48))
    except FileExistsError:
        pass
    return key_file.read_text(encoding='utf-8').strip()


def hash_password(password):
    if not password or len(password) > 128:
        raise HTTPException(400, '密码不能为空或超过 128 位')
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, ITERATIONS)
    return 'pbkdf2_sha256${}${}${}'.format(
        ITERATIONS, base64.b64encode(salt).decode(), base64.b64encode(digest).decode())


def verify_password(password, encoded):
    try:
        algorithm, iterations, salt, expected = encoded.split('$')
        if algorithm != 'pbkdf2_sha256' or not 100000 <= int(iterations) <= 2000000:
            return False
        actual = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),
                                   base64.b64decode(salt, validate=True), int(iterations))
        return hmac.compare_digest(actual, base64.b64decode(expected, validate=True))
    except (ValueError, TypeError, AttributeError):
        return False


def verify_stored_password(password, password_hash, legacy_password):
    if password_hash:
        return verify_password(password, password_hash)
    return bool(legacy_password) and hmac.compare_digest(
        password.encode('utf-8'), str(legacy_password).encode('utf-8'))


def token_hash(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def create_tokens(user_id, session_id, refresh_expires=None):
    now = datetime.now(timezone.utc)
    expires = refresh_expires or now + timedelta(seconds=REFRESH_SECONDS)
    common = {'sub': str(user_id), 'sid': session_id, 'iss': ISSUER, 'iat': now}
    access = jwt.encode(dict(common, typ='access', jti=str(uuid4()),
                             exp=now + timedelta(seconds=ACCESS_SECONDS)), signing_key(), algorithm='HS256')
    refresh = jwt.encode(dict(common, typ='refresh', jti=str(uuid4()), exp=expires),
                         signing_key(), algorithm='HS256')
    return {'accessToken': access, 'refreshToken': refresh,
            'tokenType': 'Bearer', 'expiresIn': ACCESS_SECONDS}


def decode_token(token, token_type):
    try:
        claims = jwt.decode(token, signing_key(), algorithms=['HS256'], issuer=ISSUER,
                            options={'require': ['sub', 'sid', 'typ', 'jti', 'exp', 'iat']})
        if claims['typ'] != token_type or int(claims['sub']) <= 0:
            raise ValueError('token type')
        return claims
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        raise HTTPException(401, '登录信息无效或已过期，请重新登录',
                            headers={'WWW-Authenticate': 'Bearer'})
