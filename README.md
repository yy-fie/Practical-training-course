# Practical-training-course

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