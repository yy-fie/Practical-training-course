/* 第一阶段增量迁移：保留既有用户、角色、权限和授权记录。 */
SET XACT_ABORT ON;
BEGIN TRANSACTION;

IF COL_LENGTH('dbo.UsersInfo','passwordHash') IS NULL
    ALTER TABLE dbo.UsersInfo ADD passwordHash NVARCHAR(255) NULL;
IF COL_LENGTH('dbo.UsersInfo','isActive') IS NULL
    ALTER TABLE dbo.UsersInfo ADD isActive BIT NOT NULL CONSTRAINT DF_User_active DEFAULT 1;
IF COL_LENGTH('dbo.UsersInfo','isDeleted') IS NULL
    ALTER TABLE dbo.UsersInfo ADD isDeleted BIT NOT NULL CONSTRAINT DF_User_deleted DEFAULT 0;

IF OBJECT_ID('dbo.AuthSession') IS NULL
BEGIN
    CREATE TABLE dbo.AuthSession (
        sessionId NVARCHAR(36) NOT NULL PRIMARY KEY,
        userId INT NOT NULL,
        refreshHash CHAR(64) NOT NULL,
        expiresAt DATETIME2 NOT NULL,
        revokedAt DATETIME2 NULL,
        createdAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
    CREATE INDEX IX_AuthSession_user ON dbo.AuthSession(userId);
END;
IF OBJECT_ID('dbo.LoginLog') IS NULL
BEGIN
    CREATE TABLE dbo.LoginLog (
        logId INT IDENTITY PRIMARY KEY,
        userId INT NULL,
        username NVARCHAR(200) NOT NULL,
        success BIT NOT NULL,
        ipAddress NVARCHAR(64) NULL,
        reason NVARCHAR(200) NULL,
        createdAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END;
IF OBJECT_ID('dbo.RoleGrant') IS NOT NULL AND
   OBJECT_ID('dbo.TrainingMigration') IS NULL
BEGIN
    CREATE TABLE dbo.TrainingMigration (name NVARCHAR(100) PRIMARY KEY, appliedAt DATETIME2 DEFAULT SYSUTCDATETIME());
END;
/* 老代码把临时角色写入用户表。只做一次恢复，后续授权在鉴权时动态计算。 */
IF OBJECT_ID('dbo.RoleGrant') IS NOT NULL
BEGIN
    IF NOT EXISTS(SELECT 1 FROM dbo.TrainingMigration WHERE name='grant-base-role-v1')
    BEGIN
        ;WITH OriginalRoles AS (
            SELECT userId,originalRoleId,ROW_NUMBER() OVER(PARTITION BY userId ORDER BY grantId) AS rn
            FROM dbo.RoleGrant WHERE status='active' AND originalRoleId IS NOT NULL
        )
        UPDATE u SET roleId=o.originalRoleId
        FROM dbo.UsersInfo u JOIN OriginalRoles o ON u.userId=o.userId AND o.rn=1
        WHERE EXISTS(SELECT 1 FROM dbo.RoleGrant g WHERE g.userId=u.userId AND g.status='active' AND g.roleId=u.roleId);
        INSERT INTO dbo.TrainingMigration(name) VALUES('grant-base-role-v1');
    END;
END;
COMMIT TRANSACTION;
