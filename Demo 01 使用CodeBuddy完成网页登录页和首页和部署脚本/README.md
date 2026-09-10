# Demo 01 · 网页登录页 + 首页 + 部署脚本（对接 FastAPI 登录）

对应实训讲义 2.2 与任务 7：

- 两个原始静态分析页（`station_monthly_analysis.html`、
  `station_monthly_analysis_by_month.html`）已按“css/js/html 三分离”重构，
  样式进 `css/`，脚本进 `js/`（原件保留在 `原始文件备份/`）；
- 新增登录页 `login.html`（数字验证码 + 调用 FastAPI `POST /api/users/login`
  校验 UsersInfo 手机号/邮箱 + 密码）；
- 登录成功 → 跳转首页 `home.html`，首页左侧导航两个分析页，左下角
  显示 UsersInfo.realName 真实姓名；
- 登录状态使用 Session（sessionStorage）保存，退出时清除；
- 提供 `运行环境脚本.bat`、`一键启动脚本.bat`、`停止网站.bat`。

## 运行

1. 先启动后端：Demo 02 FastAPI 项目 `api1` 目录运行「启动FastAPI接口项目.bat」
   （http://127.0.0.1:9001）；
2. 本目录双击「一键启动脚本.bat」→ 打开 http://127.0.0.1:8000/login.html；
3. 用 AI 数据库 UsersInfo 表的手机号 + loginPassword 登录。

## 关键代码

- `js/api.js`：登录接口调用封装（apiLogin）
- `js/login.js`：验证码绘制与校验、调用接口、写入 sessionStorage、跳转首页
- `js/home.js`：读取 sessionStorage → 未登录回登录页；已登录左下角显示真实姓名
