/* ============================================================
   分级授权（授权决策权）+ 时间受限授权 + 授权台账
   新增表：RoleGrant
   ============================================================ */
USE AI;
GO

IF OBJECT_ID('dbo.RoleGrant') IS NULL
BEGIN
    CREATE TABLE RoleGrant (
        grantId         INT PRIMARY KEY IDENTITY(1,1),
        userId          INT NOT NULL,              -- 被授权用户
        roleId          INT NOT NULL,              -- 授予的角色
        originalRoleId  INT NULL,                  -- 授权前的原角色（用于到期/撤销回退）
        grantedBy       INT NOT NULL,              -- 授权人 userId
        startTime       DATETIME NULL,             -- 生效时间（空=立即）
        endTime         DATETIME NULL,             -- 失效时间（空=永久）
        status          NVARCHAR(20) NOT NULL DEFAULT 'active',  -- active/revoked/expired
        revokedBy       INT NULL,                  -- 撤销人
        revokedAt       DATETIME NULL,             -- 撤销时间
        remark          NVARCHAR(200) NULL,        -- 备注
        createdAt       DATETIME NOT NULL DEFAULT GETDATE()
    );
    CREATE INDEX IX_RoleGrant_user ON RoleGrant(userId);
    CREATE INDEX IX_RoleGrant_status ON RoleGrant(status);
END;
GO

SELECT TOP 5 * FROM RoleGrant;
GO