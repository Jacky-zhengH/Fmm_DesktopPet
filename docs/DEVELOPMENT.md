# 开发和版本记录

`main` 放目前能用的版本。改功能时从 main 开一个分支，测试后通过 PR 合并。问题记在 Issue 里，同一版要做的事归到一个 Milestone。

## 已有版本

- `v0.0.0-original`：原作者源码与运行 PNG。
- `v0.1.0`：目前在用的版本，基础功能已经试过。

当前第一阶段统一使用 0.1.x；下一阶段再使用 0.2.x；什么时候进入 1.0.x，由用户决定。

本次修复在 `ver0.1.0` 分支，关联 Issue #1 / #2。已有 `v0.1.0` 标签保留不动；分支先供测试，不新建标签，不自动合并或发布。

原作者源码和修改后的源码分别留了提交。EXE、运行环境和个人设置不放进源码仓库；需要保存的安装包放到 Release。

## 平时怎么改

1. 在 Issue 里记下要修什么、希望是什么效果。
2. 开分支，比如 `fix/walk-scale`，每改好一块就提交。
3. 跑自动检查，再双击根目录 run.bat 自己试试。
4. 提 PR，说明改动和测试结果，检查通过后合并。
5. 一版用下来没问题，就更新 CHANGELOG、打标签，需要时再打包。

## 自动检查与打包

`Qt regression` 会在推送 main 或提交 PR 时跑 Windows / Python 3.12 测试。多屏、DPI 和长时间运行仍需要在电脑上试。

需要测试包时，在 Actions 里手动运行 `Windows test package`。它会先测试，再用 PyInstaller 打包并尝试启动。临时产物保留 7 天，想长期保存的版本再放到 Release。

新电脑首次运行 setup.bat；当前电脑日常只运行根目录 run.bat。素材工具依赖另见 `requirements-tools.txt`。

## 想看旧代码时

```powershell
git log --oneline --decorate
git show v0.1.0:deskpet/deskpet/pet/window.py
git worktree add --detach ../fmm-v0.1.0 v0.1.0
```

worktree 会另开一个目录，旧版需要单独准备环境。撤销已经提交的错误改动，用 `git revert <commit>`；已经留好的版本标签不要覆盖。
