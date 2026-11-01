# 开发与打包

`main` 是已测试基线。新改动关联 Issue，在独立分支完成，通过测试和 PR 后合并。版本使用 0.1.x、0.2.x；何时进入 1.0.x 由用户决定。历史功能与版本变化见 [CHANGELOG](../CHANGELOG.md)。

## 日常运行与检查

新电脑安装 Python 3.10+ 后运行根目录 `setup.bat`。平时双击根目录 `run.bat`，它使用本机 `.venv` 和 `app/main.py`。

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe app/main.py --smoke-test
```

测试使用 Qt 离屏环境和临时存档；启动检查运行事件循环后退出，不保存用户设置。多屏、混合 DPI 和长期运行仍需实际试用。

源码存档在 `.local/profiles/user-source/`，标准便携版存档在 EXE 旁的 `.user/`。两者分别保留，实际目录见 [PROJECT_STRUCTURE](PROJECT_STRUCTURE.md)。源码已接入本轮六张修复图；已发布的 0.1.3 EXE 尚未重新打包。

## 标准版打包

版本号只在 `app/pet/version.py` 定义。先更新 `docs/QUICK_GUIDE.md` 和 `docs/releases/版本.md`，提交源码并完成测试，再执行：

```powershell
.venv/Scripts/python.exe -m pip install -r requirements/build.txt
.venv/Scripts/python.exe tools/release/package_release.py
```

默认输出到 `versions/user/`，生成 EXE、便携 ZIP、源码 ZIP、功能指引和 SHA256SUMS 五件套。源码 ZIP 来自当前 Git 提交；两个 ZIP 都含同一份功能指引。打包工具核对源码树与 EXE、素材完整性及个人文件排除，再将 EXE 复制到隔离目录，清除外部 Python/Qt 路径后验证启动。

缓存与构建凭证写入 `.local/build/`。目录或打包实验可用 `--output-dir .local/package-check`，完成后删除实验结果。`--skip-build` 只接受构建记录与当前源码树、EXE 哈希完全匹配的成品；结构调整后需要重新完整构建。

发布顺序：用户验收 → 保存源码并完成测试/打包 → 推送功能分支，等待 CI → 合并 PR → 在 main 对同一代码树重新归档 → 创建新的注释标签与 Release，使用对应版本说明并上传五件套。已接受的标签不改写，不自动推进到下一阶段。

## 开发检查点

后续只维护标准用户版。较大改动按能够单独检查、回退的小块推进，每完成一块就测试、提交并推送功能分支，不等到整版完成才上传。相关的小修可以合并成一次清楚的提交。

每次运行改动关联 Issue 和 PR，CI 通过后再合并 `main`。合并完成的临时分支及时清理；尚有独立改动的分支先核对内容，历史提交与已发布标签保留。当前处于 0.1.4 开发过程，合并检查点不等于发布新版本。

## 回退

```powershell
git log --oneline --decorate
git show v0.0.0-original:deskpet/deskpet/main.py
git revert <commit>
```

需要完整旧代码时可另建 worktree；不要覆盖当前工作目录或移动旧标签。原作者便携 EXE、源码 ZIP 另留在 `.local/original/`。
