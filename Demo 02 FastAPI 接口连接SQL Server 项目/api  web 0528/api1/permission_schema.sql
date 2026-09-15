/* ============================================================
   角色权限（RBAC）数据库迁移脚本
   角色层级：4 超级管理员 -> 5 学院管理员 -> 2 系管理员 -> 3 教师 -> 1 学生
   ============================================================ */
USE AI;
GO

-- 1) 角色表增加“上级角色”字段（用于逐层管理）
IF COL_LENGTH('dbo.RoleInfo', 'parentRoleId') IS NULL
BEGIN
    ALTER TABLE RoleInfo ADD parentRoleId INT NULL;
END;
GO

-- 2) 权限点表
IF OBJECT_ID('dbo.Permission') IS NULL
BEGIN
    CREATE TABLE Permission (
        permId   INT PRIMARY KEY IDENTITY(1,1),
        permCode NVARCHAR(100) NOT NULL UNIQUE,
        permName NVARCHAR(200) NOT NULL,
        category NVARCHAR(50) NULL
    );
END;
GO

-- 3) 角色-权限关联表
IF OBJECT_ID('dbo.RolePermission') IS NULL
BEGIN
    CREATE TABLE RolePermission (
        roleId INT NOT NULL,
        permId INT NOT NULL,
        CONSTRAINT PK_RolePermission PRIMARY KEY (roleId, permId)
    );
END;
GO

-- 4) 设置角色层级
UPDATE RoleInfo SET parentRoleId = NULL WHERE roleId = 4; -- 超级管理员：顶层
UPDATE RoleInfo SET parentRoleId = 4    WHERE roleId = 5; -- 学院管理员
UPDATE RoleInfo SET parentRoleId = 5    WHERE roleId = 2; -- 系管理员
UPDATE RoleInfo SET parentRoleId = 2    WHERE roleId = 3; -- 教师
UPDATE RoleInfo SET parentRoleId = 3    WHERE roleId = 1; -- 学生
GO

-- 5) 权限点
IF NOT EXISTS (SELECT 1 FROM Permission WHERE permCode = 'analysis:view')
    INSERT INTO Permission (permCode, permName, category) VALUES (N'analysis:view',   N'查看客流分析页',            N'菜单');
IF NOT EXISTS (SELECT 1 FROM Permission WHERE permCode = 'profile:self')
    INSERT INTO Permission (permCode, permName, category) VALUES (N'profile:self',    N'修改本人个人信息',          N'操作');
IF NOT EXISTS (SELECT 1 FROM Permission WHERE permCode = 'password:self')
    INSERT INTO Permission (permCode, permName, category) VALUES (N'password:self',   N'修改本人密码',              N'操作');
IF NOT EXISTS (SELECT 1 FROM Permission WHERE permCode = 'user:list')
    INSERT INTO Permission (permCode, permName, category) VALUES (N'user:list',       N'查看用户列表',              N'操作');
IF NOT EXISTS (SELECT 1 FROM Permission WHERE permCode = 'user:edit')
    INSERT INTO Permission (permCode, permName, category) VALUES (N'user:edit',       N'编辑用户信息',              N'操作');
IF NOT EXISTS (SELECT 1 FROM Permission WHERE permCode = 'user:reset')
    INSERT INTO Permission (permCode, permName, category) VALUES (N'user:reset',      N'重置密码（本人/下一层）',   N'操作');
IF NOT EXISTS (SELECT 1 FROM Permission WHERE permCode = 'user:delete')
    INSERT INTO Permission (permCode, permName, category) VALUES (N'user:delete',     N'删除用户',                  N'操作');
IF NOT EXISTS (SELECT 1 FROM Permission WHERE permCode = 'role:assign')
    INSERT INTO Permission (permCode, permName, category) VALUES (N'role:assign',     N'调整用户角色',              N'操作');
IF NOT EXISTS (SELECT 1 FROM Permission WHERE permCode = 'permission:manage')
    INSERT INTO Permission (permCode, permName, category) VALUES (N'permission:manage', N'权限管理（超级管理员）',  N'菜单');
GO

-- 6) 角色权限初始映射
DELETE FROM RolePermission;
GO

-- 学生(1)：分析页 + 本人信息 + 本人密码
INSERT INTO RolePermission (roleId, permId)
SELECT 1, permId FROM Permission WHERE permCode IN ('analysis:view','profile:self','password:self');
GO

-- 教师(3)：+ 查看/编辑本系学生
INSERT INTO RolePermission (roleId, permId)
SELECT 3, permId FROM Permission WHERE permCode IN ('analysis:view','profile:self','password:self','user:list','user:edit');
GO

-- 系管理员(2)：+ 重置密码、删除（限本系）
INSERT INTO RolePermission (roleId, permId)
SELECT 2, permId FROM Permission WHERE permCode IN ('analysis:view','profile:self','password:self','user:list','user:edit','user:reset','user:delete');
GO

-- 学院管理员(5)：+ 调整角色
INSERT INTO RolePermission (roleId, permId)
SELECT 5, permId FROM Permission WHERE permCode IN ('analysis:view','profile:self','password:self','user:list','user:edit','user:reset','user:delete','role:assign');
GO

-- 超级管理员(4)：全部权限
INSERT INTO RolePermission (roleId, permId)
SELECT 4, permId FROM Permission;
GO

-- 7) 查看结果
SELECT r.roleId, r.roleName, r.parentRoleId,
       STUFF((SELECT ',' + p.permCode FROM RolePermission rp
              JOIN Permission p ON p.permId = rp.permId
              WHERE rp.roleId = r.roleId ORDER BY p.permCode
              FOR XML PATH('')), 1, 1, '') AS 权限
FROM RoleInfo r ORDER BY r.roleId;
GO