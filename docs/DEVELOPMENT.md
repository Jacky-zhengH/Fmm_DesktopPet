# 开发、版本与回退

仓库为个人私有项目。`main` 保存已验证基线；每项后续修改从 main 建立专门分支，经测试和 PR 后合并。Issue 描述问题及验收，Milestone 表示阶段，Tag 标识验收快照，Release 保存对应的可执行包和说明。

## 当前检查点

- `v0.0.0-original`：原作者源码与运行 PNG。
- `v0.1.0`：用户已测试的源码补完基线。
- `v0.2.0`：计划统一可见尺寸/脚底锚点及任务栏吸附，尚未完成。

首次导入已将原始源码和当前源码分别提交；后续不用依赖覆盖式 ZIP 备份。EXE、环境和个人设置保留本地或放在 Release/构建产物中，不纳入源码提交。

## 常规迭代

1. 建立 Issue，写清实际表现、预期和验收标准，归入阶段 Milestone。
2. 从干净 main 建立 `fix/walk-scale` 等分支，分批提交。
3. 运行自动检查，再从根目录双击 run.bat 实机测试。
4. 创建 PR，记录改动、证据和限制；CI 通过后合并。
5. 用户验收一个阶段后，更新 CHANGELOG 并打版本标签；按需生成 Windows 测试包和 Release。

## 自动检查与打包

`Qt regression` 在 main 推送或 PR 时执行 Windows / Python 3.12 测试；没有运行长时间桌面交互的能力。

`Windows test package` 是手动触发的构建工作流：先运行测试，再通过 PyInstaller 打包整个目录模式的源码程序，并验证打包程序的 `--smoke-test`。构建产物有保留期限；需要长期留存的正式包，验收后放到 Release。默认不自动对外发布。

新电脑首次运行 setup.bat；当前电脑日常只运行根目录 run.bat。素材工具依赖另见 `requirements-tools.txt`。

## 查看旧版而不覆盖正在开发的文件

```powershell
git log --oneline --decorate
git show v0.1.0:deskpet/deskpet/pet/window.py
git worktree add --detach ../fmm-v0.1.0 v0.1.0
```

worktree 是一份独立目录，旧版需要自己的依赖环境。需要撤销已提交的错误改动时优先 `git revert <commit>`，保留可审计历史；不要用 force push 覆盖已验收版本。

Git 分支保护是否可用取决于 GitHub 账户计划；本项目先落实分支/PR/测试习惯，不把未启用的规则写成已经启用。
