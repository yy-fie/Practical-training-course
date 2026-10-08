"""真实 SQL Server + FastAPI 集成验证；仅使用本次创建的隔离数据库。"""
import json
import sys
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import database
from security import hash_password, verify_password, decode_token
from main import app
from fastapi.testclient import TestClient


class RBACIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_db = database.DATABASE
        cls.name = 'AI_CodexTest_' + uuid4().hex[:12]
        database.DATABASE = 'master'
        connection = database.get_db_connection()
        connection.autocommit = True
        connection.execute('CREATE DATABASE [' + cls.name + ']')
        connection.close()
        database.DATABASE = cls.name
        try:
            connection = database.get_db_connection()
            connection.execute('''
            CREATE TABLE RoleInfo(roleId INT PRIMARY KEY,roleName NVARCHAR(50),parentRoleId INT);
            CREATE TABLE UsersInfo(userId INT IDENTITY PRIMARY KEY,realName NVARCHAR(50),phone NVARCHAR(50),
                roleId INT,departmentId INT,gender NVARCHAR(20),nativePlace NVARCHAR(50),politicalStatus NVARCHAR(50),
                loginPassword NVARCHAR(128),idCard NVARCHAR(50),email NVARCHAR(100));
            CREATE TABLE Permission(permId INT IDENTITY PRIMARY KEY,permCode NVARCHAR(100),permName NVARCHAR(100),category NVARCHAR(50));
            CREATE TABLE RolePermission(roleId INT,permId INT,PRIMARY KEY(roleId,permId));
            CREATE TABLE RoleGrant(grantId INT IDENTITY PRIMARY KEY,userId INT,roleId INT,originalRoleId INT,
                grantedBy INT,startTime DATETIME,endTime DATETIME,status NVARCHAR(20) DEFAULT 'active',
                revokedBy INT,revokedAt DATETIME,remark NVARCHAR(200),createdAt DATETIME DEFAULT GETDATE());
            CREATE INDEX IX_RoleGrant_user ON RoleGrant(userId);
            INSERT RoleInfo VALUES(4,N'超级管理员',NULL),(5,N'学院管理员',4),(2,N'系管理员',5),(3,N'教师',2),(1,N'学生',3);
            ''')
            connection.commit()
            connection.execute(Path(__file__).resolve().parents[1].joinpath('auth_schema.sql').read_text(encoding='utf-8'))
            connection.commit()
            # 重复执行迁移也应保留数据。
            connection.execute(Path(__file__).resolve().parents[1].joinpath('auth_schema.sql').read_text(encoding='utf-8'))
            connection.commit()
            connection.close()
        except Exception:
            cls.tearDownClass()
            raise
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        database.DATABASE = 'master'
        connection = database.get_db_connection()
        connection.autocommit = True
        # 数据库名仅由上面的固定前缀和 uuid 生成，永不接受外部输入。
        if not cls.name.startswith('AI_CodexTest_') or len(cls.name) != 25:
            raise RuntimeError('unexpected test database name')
        connection.execute('ALTER DATABASE [' + cls.name + '] SET SINGLE_USER WITH ROLLBACK IMMEDIATE')
        connection.execute('DROP DATABASE [' + cls.name + ']')
        connection.close()
        database.DATABASE = cls.previous_db

    def sql(self, query, params=(), fetch=False):
        self.assertEqual(database.DATABASE, self.name)
        connection = database.get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(query, params)
            result = cursor.fetchall() if fetch else None
            connection.commit()
            return result
        finally:
            cursor.close()
            connection.close()

    def setUp(self):
        self.sql('DELETE AuthSession; DELETE LoginLog; DELETE RoleGrant; DELETE RolePermission; DELETE Permission; DELETE UsersInfo;')
        self.ids = {}
        for name, role, dept in [('root',4,1),('college',5,1),('dept',2,1),('teacher',3,1),('student',1,1),('other',1,2)]:
            self.ids[name] = self.sql(
                'INSERT UsersInfo(realName,phone,roleId,departmentId,loginPassword) '
                'OUTPUT INSERTED.userId VALUES(?,?,?,?,?)', (name,name,role,dept,'123456'), True)[0][0]
        for code in ('analysis:view','profile:self','password:self','user:list','user:edit','user:reset','user:delete','role:assign','permission:manage'):
            pid = self.sql('INSERT Permission(permCode,permName,category) OUTPUT INSERTED.permId VALUES(?,?,?)', (code,code,'操作'), True)[0][0]
            for role in (4,5,2,3,1):
                allowed = role == 4 or (code in ('analysis:view','profile:self','password:self')) or (role in (5,2,3) and code in ('user:list','user:edit')) or (role in (5,2) and code in ('user:reset','user:delete','role:assign'))
                if allowed:
                    self.sql('INSERT RolePermission VALUES(?,?)', (role,pid))

    def login(self, name='root'):
        response = self.client.post('/api/auth/login', json={'username':name,'password':'123456'})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def headers(self, name='root'):
        return {'Authorization':'Bearer ' + self.login(name)['accessToken']}

    def grant(self, headers, target='student', role=3, **kwargs):
        return self.client.post('/api/admin/grants', headers=headers,
                                params=dict(userId=self.ids[target], roleId=role, **kwargs))

    def test_password_hash_and_legacy_upgrade(self):
        encoded = hash_password('123456')
        self.assertTrue(verify_password('123456', encoded))
        self.assertFalse(verify_password('wrong', encoded))
        self.assertNotEqual(encoded, hash_password('123456'))
        data = self.login('student')
        self.assertNotIn('loginPassword', json.dumps(data))
        self.assertNotIn('passwordHash', json.dumps(data))
        stored = self.sql('SELECT passwordHash,loginPassword FROM UsersInfo WHERE userId=?', (self.ids['student'],), True)[0]
        self.assertTrue(verify_password('123456', stored[0]))
        self.assertEqual(stored[1], '')
        self.login('student')

    def test_authentication_tamper_and_user_id_spoof(self):
        self.assertEqual(self.client.get('/api/me/permissions',headers={'X-User-Id':str(self.ids['root'])}).status_code,401)
        self.assertEqual(self.client.get('/api/me/permissions',headers={'Authorization':'Bearer invalid'}).status_code,401)
        self.assertEqual(self.client.post('/api/auth/login',json={'username':'student','password':'wrong'}).status_code,401)
        self.assertEqual(self.sql('SELECT success FROM LoginLog',fetch=True)[0][0],False)
        self.assertEqual(self.client.options('/api/me/permissions',headers={'Origin':'http://localhost:8000','Access-Control-Request-Method':'GET','Access-Control-Request-Headers':'authorization'}).status_code,200)

    def test_refresh_rotation_and_logout_revocation(self):
        data = self.login()
        old = {'refreshToken':data['refreshToken']}
        refreshed = self.client.post('/api/auth/refresh',json=old)
        self.assertEqual(refreshed.status_code,200,refreshed.text)
        self.assertEqual(self.client.post('/api/auth/refresh',json=old).status_code,401)
        headers = {'Authorization':'Bearer '+refreshed.json()['accessToken']}
        self.assertEqual(self.client.post('/api/auth/logout',headers=headers).status_code,200)
        self.assertEqual(self.client.get('/api/me/permissions',headers=headers).status_code,401)
        self.assertEqual(self.client.post('/api/auth/refresh',json={'refreshToken':refreshed.json()['refreshToken']}).status_code,401)

    def test_refresh_token_cannot_be_access_token(self):
        data = self.login()
        self.assertEqual(self.client.get('/api/me/permissions',headers={'Authorization':'Bearer '+data['refreshToken']}).status_code,401)
        self.assertEqual(self.client.post('/api/auth/refresh',json={'refreshToken':data['accessToken']}).status_code,401)

    def test_profile_cannot_escalate_and_scope_is_enforced(self):
        headers = self.headers('student')
        self.assertEqual(self.client.put('/api/users/'+str(self.ids['student']),headers=headers,json={'roleId':4}).status_code,403)
        self.assertEqual(self.client.put('/api/users/'+str(self.ids['student']),headers=headers,json={'realName':'新姓名'}).status_code,200)
        headers = self.headers('teacher')
        self.assertEqual(self.client.get('/api/users',headers=headers).status_code,403)
        self.assertEqual(self.client.put('/api/admin/users/'+str(self.ids['other']),headers=headers,params={'realName':'越权'}).status_code,403)
        response = self.client.get('/api/admin/users',headers=headers)
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual([r['userId'] for r in response.json()['rows']],[self.ids['student']])

    def test_reset_and_self_change_revoke_all_sessions(self):
        student = self.login('college')
        headers = self.headers()
        response = self.client.put('/api/admin/users/'+str(self.ids['college'])+'/reset-password',headers=headers,params={'newPassword':'new123456'})
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(self.client.get('/api/me/permissions',headers={'Authorization':'Bearer '+student['accessToken']}).status_code,401)
        response = self.client.post('/api/auth/login',json={'username':'college','password':'new123456'})
        self.assertEqual(response.status_code,200,response.text)
        headers = {'Authorization':'Bearer '+response.json()['accessToken']}
        response = self.client.put('/api/users/'+str(self.ids['college'])+'/password',headers=headers,json={'oldPassword':'new123456','newPassword':'next123456','confirmPassword':'next123456'})
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(self.client.get('/api/me/permissions',headers=headers).status_code,401)

    def test_new_user_password_is_hashed(self):
        headers = self.headers()
        invalid = self.client.post('/api/users',headers=headers,json={'realName':'short','phone':'short','roleId':1,'departmentId':1,'loginPassword':'123'})
        self.assertEqual(invalid.status_code,400,invalid.text)
        response = self.client.post('/api/users',headers=headers,json={'realName':'new','phone':'new','roleId':1,'departmentId':1,'loginPassword':'123456'})
        self.assertEqual(response.status_code,201,response.text)
        self.login('new')

    def test_disabled_and_deleted_accounts_reject_tokens(self):
        data = self.login('student')
        self.sql('UPDATE UsersInfo SET isActive=0 WHERE userId=?',(self.ids['student'],))
        self.assertEqual(self.client.get('/api/me/permissions',headers={'Authorization':'Bearer '+data['accessToken']}).status_code,401)
        self.assertEqual(self.client.post('/api/auth/refresh',json={'refreshToken':data['refreshToken']}).status_code,401)
        self.assertEqual(self.client.post('/api/auth/login',json={'username':'student','password':'123456'}).status_code,401)

    def test_grant_pending_active_expired_without_ledger_request(self):
        headers = self.headers()
        student_headers = self.headers('student')
        future = self.sql('SELECT DATEADD(day,1,GETDATE()),DATEADD(day,2,GETDATE())',fetch=True)[0]
        response = self.grant(headers,startTime=str(future[0]),endTime=str(future[1]))
        self.assertEqual(response.status_code,200,response.text)
        grant_id = response.json()['grantId']
        self.assertEqual(response.json()['status'],'pending')
        self.assertEqual(self.client.get('/api/me/permissions',headers=student_headers).json()['roleId'],1)
        self.sql('UPDATE RoleGrant SET startTime=DATEADD(minute,-1,GETDATE()) WHERE grantId=?',(grant_id,))
        self.assertEqual(self.client.get('/api/me/permissions',headers=student_headers).json()['roleId'],3)
        self.sql('UPDATE RoleGrant SET endTime=GETDATE() WHERE grantId=?',(grant_id,))
        self.assertEqual(self.client.get('/api/me/permissions',headers=student_headers).json()['roleId'],1)
        self.assertEqual(self.sql('SELECT roleId FROM UsersInfo WHERE userId=?',(self.ids['student'],),True)[0][0],1)
        response = self.client.get('/api/admin/grants',headers=headers,params={'status':'expired'})
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['rows'][0]['status'],'expired')

    def test_grant_overlap_invalid_time_and_authority(self):
        headers = self.headers('college')
        self.assertEqual(self.grant(headers,role=4).status_code,403)
        self.assertEqual(self.grant(headers,target='root').status_code,403)
        self.assertEqual(self.grant(headers,endTime='invalid').status_code,400)
        self.assertEqual(self.grant(headers,endTime='2020-01-01T00:00').status_code,400)
        self.assertEqual(self.grant(headers).status_code,200)
        self.assertEqual(self.grant(headers).status_code,409)
        self.assertEqual(self.grant(self.headers('dept'),target='other').status_code,403)
        self.assertEqual(self.client.put('/api/admin/users/'+str(self.ids['student'])+'/role',headers=headers,params={'roleId':4}).status_code,403)

    def test_adjacent_grant_segments_and_revoke_pending(self):
        headers = self.headers()
        times = self.sql('SELECT DATEADD(day,1,GETDATE()),DATEADD(day,2,GETDATE()),DATEADD(day,3,GETDATE())',fetch=True)[0]
        first = self.grant(headers,startTime=str(times[0]),endTime=str(times[1]))
        second = self.grant(headers,startTime=str(times[1]),endTime=str(times[2]))
        self.assertEqual(first.status_code,200,first.text)
        self.assertEqual(second.status_code,200,second.text)
        response = self.client.put('/api/admin/grants/'+str(first.json()['grantId'])+'/revoke',headers=headers)
        self.assertEqual(response.status_code,200,response.text)
        ledger = self.client.get('/api/admin/grants',headers=headers,params={'status':'pending'}).json()
        self.assertEqual(ledger['total'],1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
