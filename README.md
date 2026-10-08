# Practical-training-course

## 按讲义完善项目：进度与运行方式

依据 [《计科23级软件项目开发实训讲义》](https://my.feishu.cn/wiki/M5ajwD8wOip1rTk3iA5cv6sjn6d)，在已有 FastAPI + SQL Server + 静态网页项目上增量完善。

### 第一阶段：认证与时间授权基础（已实现）

- 登录采用 JSON 请求体，签发 15 分钟访问 JWT 和 7 天刷新 JWT；数据库记录可撤销会话，刷新令牌每次续期轮换。
- 前端自动携带 Bearer 令牌，访问令牌过期后续期一次并重试；首页和 iframe 共用刷新过程。退出登录在服务端撤销会话。
- 新建、重置、修改密码保存 PBKDF2-SHA256 哈希；旧账号成功登录后逐个迁移，响应不包含密码。修改或重置密码立即撤销该账号所有会话。
- 全部 API 校验登录；停止信任 `X-User-Id`。个人资料接口不能修改角色、院系或密码，旧用户接口也检查权限与管理范围。
- 角色授权支持生效时间、失效时间、待生效/生效中/已过期/已撤销状态及提前撤销。同一用户多个授权区间不可重叠，采用左闭右开区间 `[开始, 结束)`，相邻时间段允许衔接。
- 临时角色按数据库 `GETDATE()` 动态参与每次鉴权，不覆盖用户永久角色，无需定时任务或查看台账才能到期失效。此阶段沿用单个有效角色模型，不支持同一用户同时启用多个临时角色。
- 新增登录日志持久化。日志检索界面和操作日志仍待第四阶段完成。

后端目录：`Demo 02 FastAPI 接口连接SQL Server 项目/api  web 0528/api1`。

```powershell
cd 'Demo 02 FastAPI 接口连接SQL Server 项目/api  web 0528/api1'
python -m pip install -r requirements.txt
python migrate.py
python main.py
```

迁移需要原有 `UsersInfo`、`RoleInfo`、`Permission`、`RolePermission`、`RoleGrant` 表。`auth_schema.sql` 可重复执行，保留既有数据和权限映射；迁移工具会在需要恢复旧临时角色写回状态时，将原角色保存到被 Git 忽略的 `.local/` 目录。不要为了升级重新执行会清空权限映射的旧初始化脚本。

默认连接本机 `AI` 数据库并使用 Windows 身份验证，自动选择已安装的 SQL Server ODBC 驱动。可通过 `DB_SERVER`、`DB_NAME`、`DB_DRIVER` 配置。生产环境设置至少 32 字符的 `JWT_SECRET`；本地未配置时自动在 `.local/jwt-secret` 生成并持久化随机密钥。FastAPI 依赖已与本次验证环境对齐到 `0.124.4`，升级时请重新安装 `requirements.txt`。

前端仍通过 Demo 01 的启动脚本访问 `http://127.0.0.1:8000/login.html`，后端默认端口为 9001。升级后需要重新登录。Swagger 的 Authorize 输入访问令牌，刷新和登出接口见 `/api/auth/*`；旧登录接口保留为兼容入口并标记 deprecated。

集成测试需要本机 SQL Server 的临时数据库创建权限和 `httpx`，仅操作自动生成的 `AI_CodexTest_*` 数据库，结束后删除测试库：

```powershell
python -m pip install httpx
python tests/test_integration.py
```

### 后续实施顺序

小程序 AppID：`wx08f1707cf311bb45`，开发者工具登录及开发权限已确认。已实现账号登录、工作台、站点筛选与分页、站点详情与月度客流、新增站点、个人资料和修改密码七个页面，接入现有 FastAPI 认证和权限接口。运行方式见 `Demo 03 微信小程序/README.md`。轮播分类、真机及上线配置仍待后续完善。

1. 用户管理：启停、逻辑删除、单用户及批量角色授权，完善字段校验。
2. 菜单与角色：目录/菜单/按钮三级树、权限点 CRUD、防环与唯一标识、角色 CRUD 和权限树勾选；支持角色权限的多段限时配置。
3. 日志管理：登录日志分页检索与操作日志审计，记录用户、动作、时间和结果。
4. 业务与小程序：明确业务模块后补齐微信小程序登录、添加/列表、轮播分类和后端联调；通用存储过程与查询接口限制可访问表及字段。
5. 交付材料：需求与数据库设计、测试报告、部署使用手册、实训总结、数据库脚本、源码及讲解视频清单。

以上是分阶段完成的工作清单，当前并未完成全部讲义要求。讲义前面使用 FastAPI，提交示例又列出 Spring Boot + Vue；当前保留已有技术栈，最终是否必须更换应以任课教师的验收要求为准。

大型软件项目实训（CodeBuddy 实战）作品仓库。

## Demo 01 · 使用 CodeBuddy 完成网页登录页和首页和部署脚本

- 两个“地铁站点月度客流分析”静态页面（css/js/html 三分离，ECharts 已本地化，原件在 原始文件备份/）
- login.html：数字验证码 + 调用 FastAPI POST /api/users/login 校验 UsersInfo 手机号/邮箱 + 密码
- home.html：左侧导航两个分析页，右侧 iframe 展示；登录后左下角显示 UsersInfo.realName 真实姓名
- 登录状态使用 Session（sessionStorage），退出时清除
- 提供 运行环境脚本.bat / 一键启动脚本.bat / 停止网站.bat

运行：先启动 Demo 02 后端（端口 9001），再双击本目录「一键启动脚本.bat」，打开 http://127.0.0.1:8000/login.html

## Demo 02 · FastAPI 接口连接 SQL Server 项目

- api  web 0528/api1：FastAPI + pyodbc + SQL Server（AI 数据库）
- 已实现的接口模块：stations / books / buildings / users / floors / majors
- 含 构建方法.md 与 启动/关闭 FastAPI 接口项目.bat
