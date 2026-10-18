# 开发和版本记录

`main` 放目前能用的版本。改功能时从 main 开一个分支，测试后通过 PR 合并。问题记在 Issue 里，同一版要做的事归到一个 Milestone。

## 已有版本

- `v0.0.0-original`：原作者源码与运行 PNG。
- `v0.1.0`：基础功能验收时的检查点。
- `v0.1.1`：修复走路大小、加入拖放吸附，按用户反馈去掉一键贴边。
- `v0.1.2`：气泡 UI、独立计时器与返程提醒、概念喂食面板，首次打包当前源码的便携 EXE。
- `v0.1.2+build.2`：同一版本的最终修订，补齐透明时钟、日期气泡和边角布局；运行版本及文件名保持 0.1.2。

当前第一阶段统一使用 0.1.x；下一阶段再使用 0.2.x；什么时候进入 1.0.x，由用户决定。

走路大小与吸附修复来自 `ver0.1.0` 分支，关联 Issue #1 / #2；用户同意移除一键贴边后合并，版本记为 `v0.1.1`。已有 `v0.1.0` 标签保留不动。

原作者源码和修改后的源码分别留了提交。EXE、运行环境和个人设置不放进源码仓库；需要保存的安装包放到 Release。

## 平时怎么改

1. 在 Issue 里记下要修什么、希望是什么效果。
2. 开分支，比如 `fix/walk-scale`，每改好一块就提交。
3. 跑自动检查，再双击根目录 run.bat 自己试试。
4. 提 PR，说明改动和测试结果，检查通过后合并。
5. 一版用下来没问题，就更新 CHANGELOG、打标签，需要时再打包。

## 自动检查与打包

`Qt regression` 会在推送 main 或提交 PR 时跑 Windows / Python 3.12 测试。多屏、DPI 和长时间运行仍需要在电脑上试。

需要测试包时，在 Actions 里手动运行 `Windows test package`。它会先测试，再用 PyInstaller 打包、检查素材并尝试启动 EXE。临时产物保留 7 天，已验收的版本再放到私有 Release。

发布名、EXE 与 ZIP 统一为 `Fmm-DesktopPet-vx.x.x`，Git 标签沿用 `vx.x.x`，旧标签不改。同一版本已发布后又获用户确认的重打包，用 `+build.N` 新建注释标签记录构建，不移动旧标签。本次采用 `v0.1.2+build.2`，新 Release 标为最新，原 Release 和附件保留。

版本号只在 `deskpet/deskpet/pet/version.py` 定义；程序显示、Windows 文件属性和打包名都从这里读取。

本机打包：

```powershell
.venv/Scripts/python.exe -m pip install -r deskpet/deskpet/requirements-build.txt
.venv/Scripts/python.exe -m unittest discover -s deskpet/deskpet/tests -v
.venv/Scripts/python.exe scripts/package_release.py
```

`dist/` 会生成 EXE、含使用说明的 ZIP 和 SHA256SUMS 文件。构建时清理开发工具的 DLL 搜索路径，避免混入 Poppler 等工具的同名 DLL。脚本检查素材与个人设置，再把 EXE 单独复制到临时空目录、清除外部 Python/Qt 路径，运行 `--smoke-test`，成功才生成 ZIP。只想排查打包问题时，可运行 `scripts/build_windows.py --onedir`。

发布顺序：用户验收 → 更新说明并完成测试/打包验证 → 推送功能分支并等待 CI → 合并 PR → 在 main 的合并提交上打注释标签 → 创建同名 Release 并上传三个文件。发布内容来自已合并的代码，不把二进制提交进 Git。

本地 `deskpet/芙眠眠桌宠便携版.exe` 更新为新版本，并保留相同内容的版本名 EXE。替换前把原版备份至 `deskpet/archive/芙眠眠桌宠便携版-original.exe`，不覆盖已有备份；个人 `.user` 保留。

新电脑首次运行 setup.bat；当前电脑日常只运行根目录 run.bat。素材工具依赖另见 `requirements-tools.txt`。

## 想看旧代码时

```powershell
git log --oneline --decorate
git show v0.1.0:deskpet/deskpet/pet/window.py
git worktree add --detach ../fmm-v0.1.0 v0.1.0
```

worktree 会另开一个目录，旧版需要单独准备环境。撤销已经提交的错误改动，用 `git revert <commit>`；已经留好的版本标签不要覆盖。

## 开发用演出预览

根目录双击 `preview_event.bat`，无需退出正在运行的桌宠。此工具依赖本项目已有的 `.venv`，打开一只独立的临时芙芙，复用现有气泡与动作；支持重播，默认 12 秒退出。它不读取或写入正式个人设置，不修改系统时间，也不改变已发布的 EXE。

需要长时间查看时：

```powershell
.venv/Scripts/python.exe scripts/preview_event.py --stay-open
```

此工具只用于本地开发验证，不放入普通用户的发布包或功能介绍。
