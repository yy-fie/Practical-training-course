"""应用第一阶段增量迁移；既有权限映射不会被重置。"""
from pathlib import Path
import json
from datetime import datetime
from database import get_db_connection, DATABASE


def apply_migration():
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        for table in ('UsersInfo', 'RoleInfo', 'Permission', 'RolePermission', 'RoleGrant'):
            cursor.execute('SELECT OBJECT_ID(?)', ('dbo.' + table,))
            if cursor.fetchone()[0] is None:
                raise RuntimeError('缺少 ' + table + ' 表，请先按构建说明初始化数据库与 RBAC 表')
        # 备份旧临时角色写回状态，供审核一次性恢复。
        cursor.execute("SELECT DISTINCT u.userId,u.roleId FROM UsersInfo u "
                       "JOIN RoleGrant g ON g.userId=u.userId WHERE g.status='active'")
        rows = [dict(userId=r[0], roleId=r[1]) for r in cursor.fetchall()]
        directory = Path(__file__).resolve().parents[3] / '.local'
        directory.mkdir(exist_ok=True)
        if rows:
            backup = directory / ('grant-base-backup-' + datetime.now().strftime('%Y%m%d%H%M%S') + '.json')
            backup.write_text(json.dumps({'database': DATABASE, 'users': rows}, indent=2), encoding='utf-8')
        cursor.execute(Path(__file__).with_name('auth_schema.sql').read_text(encoding='utf-8'))
        while cursor.nextset():
            pass
        connection.commit()
        print('第一阶段迁移完成：' + DATABASE)
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == '__main__':
    apply_migration()
