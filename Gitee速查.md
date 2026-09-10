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
- Gitee：https://gitee.com/（你的码云用户名）/Practical-training-course

> 提示：同一本地仓库可同时关联两个远程（origin 指 GitHub，gitee 指码云），一次提交可分别推送。
