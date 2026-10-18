# 开发和版本记录

`main` 放目前能用的版本。改功能时从 main 开一个分支，测试后通过 PR 合并。问题记在 Issue 里，同一版要做的事归到一个 Milestone。

## 已有版本

- `v0.0.0-original`：原作者源码与运行 PNG。
- `v0.1.0`：基础功能验收时的检查点。
- `v0.1.1`：修复走路大小、加入拖放吸附，按用户反馈去掉一键贴边。
- `v0.1.2`：气泡 UI、独立计时器与返程提醒、概念喂食面板，首次打包当前源码的便携 EXE。
- `v0.1.2+build.2`：同一版本的最终修订，补齐透明时钟、日期气泡和边角布局；运行版本及文件名保持 0.1.2。
- `v0.1.2+build.3`：0.1.2 封盘构建，加入功能指引和源码包，保留先前构建。

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

发布名、EXE 与 ZIP 统一为 `Fmm-DesktopPet-vx.x.x`，Git 标签沿用 `vx.x.x`，旧标签不改。同一版本已发布后又获用户确认的重打包，用 `+build.N` 新建注释标签记录构建，不移动旧标签。本次封盘采用 `v0.1.2+build.3`，新 Release 标为最新，原 Release 和附件保留。

版本号只在 `deskpet/deskpet/pet/version.py` 定义；程序显示、Windows 文件属性和打包名都从这里读取。

本机打包：

```powershell
.venv/Scripts/python.exe -m pip install -r deskpet/deskpet/requirements-build.txt
.venv/Scripts/python.exe -m unittest discover -s deskpet/deskpet/tests -v
.venv/Scripts/python.exe scripts/package_release.py
```

`dist/` 固定生成五个文件：单文件 EXE、带指引的便携 ZIP、`-source.zip`、`-Guide.txt` 和 SHA256SUMS。两个 ZIP 都放入 `功能指引.txt`，内容统一来自 `docs/QUICK_GUIDE.md`；源码包用 `git archive` 读取当前已提交的快照，不带 `.git`、环境或个人设置，附源码提交号。源码与 EXE 必须对应同一个 Git 树，`--skip-build` 也会核对构建记录及 EXE 校验值。

每次发布前更新功能指引，并准备 `docs/releases/版本号.md`，必须包含“当前功能”“本次更新”“下载与运行”。脚本将它导出到 `build/release-notes.md`，创建 Release 时原样使用，不用 GitHub 自动生成的提交列表代替。功能指引和发布说明只介绍对外功能，保留未公开内容。

构建时清理开发工具的 DLL 搜索路径，避免混入 Poppler 等工具的同名 DLL。脚本检查素材与个人设置，再把 EXE 单独复制到临时空目录、清除外部 Python/Qt 路径，运行 `--smoke-test`，成功才生成 ZIP。只想排查打包问题时，可运行 `scripts/build_windows.py --onedir`。

发布顺序：用户验收 → 更新说明、提交源码并完成测试/打包验证 → 推送功能分支并等待 CI → 合并 PR → 在 main 对同一代码树用 `--skip-build` 重新归档源码 → 在 main 的合并提交上打注释标签 → 用版本说明创建同名 Release，上传五个文件。发布内容来自已合并的代码，不把二进制提交进 Git。

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

根目录双击 `preview_event.bat`，无需退出正在运行的桌宠。此工具依赖本项目已有的 `.venv`，打开一只独立的临时芙芙，复用源码里的演出流程。她会从左下方走到当前屏幕中央，依次说完四段话，穿插三次原有的跳动爱心和待机呼吸，然后走回起点。支持重播，默认 35 秒退出；重播会从起点重新开始并重新计时。它不读取或写入正式个人设置，不修改系统时间，也不改变已发布的 EXE。

正式流程会保留出发位置、吸附与睡眠状态；途中主动拖动会中断演出，以新的位置为准。演出期间到点的定时提醒会排队，等她回来后再执行。原角色素材保持不变。

本次检查：62 项回归测试通过；Windows 原生事件循环实际运行完整演出，验证四段定时文本、重播、返程与自动退出。个人设置及已发布 EXE 的校验值不变。修正长文本气泡在 Windows 上可能少算一行高度的问题。

需要长时间查看时：

```powershell
.venv/Scripts/python.exe scripts/preview_event.py --stay-open
```

此工具供开发验证，源码包保留开发入口；EXE 便携包不带开发工具，普通功能介绍也不列出它。
