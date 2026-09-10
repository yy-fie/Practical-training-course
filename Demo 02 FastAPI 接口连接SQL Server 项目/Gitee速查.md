# Gitee（码云）速查

> 实训讲义 2.4：注册码云 → 新建仓库 → 关联本地项目 → 推送代码 → 维护版本。

## 1. 注册与建仓
1) 打开 https://gitee.com/ 注册并登录；
2) 右上角 “+” → 新建仓库；填写仓库名称（如 Practical-training-course）；
3) 不要勾选 “使用 Readme 初始化仓库”（避免与本地已有历史冲突），创建后复制仓库地址。

## 2. 方式一：从 GitHub 导入（最省事）
1) 码云首页 → 新建仓库 → 选择 “导入已有仓库”；
2) 粘贴 GitHub 仓库地址（如 https://github.com/yy-fie/Practical-training-course.git）；
3) 导入完成后，GitHub 的提交历史与文件会完整复制到码云。

## 3. 方式二：本地项目关联码云并推送
```bash
# 在项目文件夹中执行（已初始化 git 的项目）
git remote add gitee https://gitee.com/你的用户名/仓库名.git
git add -A
git commit -m "提交说明"
git push -u gitee main

# 以后同时推送到 GitHub 和码云
git push origin main
git push gitee main
```

## 4. 常用 Git 命令速查
| 目的 | 命令 |
| --- | --- |
| 查看状态 | git status |
| 暂存全部改动 | git add -A |
| 提交 | git commit -m "说明" |
| 查看提交历史 | git log --oneline |
| 查看远程仓库 | git remote -v |
| 拉取更新 | git pull |
| 推送到码云 | git push gitee main |

## 5. 在 CodeBuddy 中关联码云
1) 打开项目文件夹，让 CodeBuddy 执行 “把当前项目关联到 Gitee 仓库”；
2) 按提示输入码云账号、密码与仓库地址；
3) 关联成功后让 CodeBuddy 执行 git add / commit / push，代码即提交到码云；
4) 码云网页端 “仓库 → 提交” 中可查看历史版本。

## 6. 本项目托管地址
- GitHub：https://github.com/yy-fie/Practical-training-course
- Gitee：https://gitee.com/yyyyyis/Practical-training-course

> 提示：同一本地仓库可同时关联两个远程（origin 指 GitHub，gitee 指码云），一次提交可分别推送。

## 7. Git 版本管理工具（CodeBuddy / 替代方案）

### 方式 A：CodeBuddy 中的 GitLG 扩展

1) 打开 CodeBuddy（VS Code 系 IDE）左侧的「扩展 / Extensions」面板；
2) 在搜索框输入 `GitLG`（或 Git Graph / GitLens 等 Git 可视化插件）；
3) 点击 Install 安装；
4) 安装后左侧/状态栏会出现 Git 图标，可查看：
   - 提交历史列表（每次 commit 的信息、作者、时间）；
   - 分支与合并关系图；
   - 单个文件的修改记录与 diff 对比；
   - 右键即可回退/检出某个历史版本。

### 方式 B：不使用 CodeBuddy 时的替代方案

- VS Code：扩展市场安装 **Git Graph** 或 **GitLens**，功能与 GitLG 相同；
- 网页端：码云仓库 → 「提交 / 历史」；GitHub 仓库 → 「Commits」，无需安装任何插件；
- 命令行：使用第 8 节的 `git log` / `git show` / `git blame` 等指令查看历史版本。

## 8. 查看历史版本指令（Git 常用）

```bash
# 1) 简洁查看提交历史
git log --oneline

# 2) 图形化查看分支与提交历史（推荐）
git log --oneline --graph --all --decorate

# 3) 查看最近 5 次提交
git log -5

# 4) 查看某次提交的详细改动
git show <commit-id>

# 5) 查看某个文件的历史修改记录
git log -p -- "api  web 0528/api1/UsersInfoApi.py"

# 6) 比较两次提交之间的差异
git diff <commit1> <commit2>

# 7) 查看某一行代码是谁在哪个版本改的
git blame "api  web 0528/api1/UsersInfoApi.py"

# 8) 查看某次提交改动了哪些文件（统计）
git log --stat

# 9) 按作者 / 时间筛选历史
git log --author="yy-fie"
git log --since="2026-09-01"

# 10) 临时切换到某个历史版本查看（只读查看，不修改当前分支）
git checkout <commit-id>
# 看完回到最新版本
git checkout main
```

> 说明：`<commit-id>` 用第 1 条命令列出的哈希值（如 a5cc2ac）。
