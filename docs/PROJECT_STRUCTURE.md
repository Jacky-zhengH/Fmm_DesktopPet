# 项目目录与两个版本

根目录只保留实际维护需要的内容：

```text
fmm/
├─ app/                 标准版程序、动画参数和运行 PNG
├─ tests/               自动检查
├─ tools/               art / diagnostics / release / github
├─ requirements/        运行、素材工具、打包依赖
├─ image/               参考、候选、对照、PS 工作稿
├─ docs/                指引、开发、计划、美术流程、发布记录
├─ versions/            本机可运行版本，Git 忽略
│  ├─ user/             用户标准版：EXE、发布包及自己的 .user
│  └─ fmm/              Fmm 定制版：EXE、发布包及自己的 .user
├─ .local/              本机存档、定制源码、原始备份和临时构建
├─ .venv/               本机 Python 环境
├─ .git/、.github/      Git 历史与自动检查
└─ run.bat / setup.bat  日常源码测试 / 首次配置
```

旧 `deskpet/` 转发层、重复的 `dist/` 和历史 `analysis/` 已移除。程序源码只有 `app/` 这一份标准实现；本地定制源码保留在独立 Git 工作树 `.local/for-fmm-source/`，不上传。

## 两个版本

| 用途 | 启动位置 | 设置位置 |
|---|---|---|
| 用户版 | `versions/user/Fmm-DesktopPet-v0.1.3.exe` | `versions/user/.user/` |
| Fmm 版 | `versions/fmm/Fmm-DesktopPet-v0.1.3-ForFmm.exe` | `versions/fmm/.user/` |
| 日常开发测试 | 根目录 `run.bat` | `.local/profiles/user-source/` |

三套现有存档分别迁移，未合并覆盖。根目录 `run.bat` 运行当前标准源码；修改源码不会自动改动两版 EXE。标准构建工具默认输出到 `versions/user/`，并拒绝向 Fmm 版目录写入。Fmm 版仅本地保存，GitHub 仍只发布标准版。

## 美术位置

- `image/references/`：母图、问题示例和手绘 UI 图。
- `image/repaired/0.1.4/`：六张修复候选及 `processing.json` 处理记录。
- `image/review/0.1.4/`：最终前后对照、走路 GIF；原图检查数据在 `audit/`。
- `image/work/0.1.4/`：两份 PSD、四张手工修图，仅本机保存。
- `app/assets/sprites/`：程序实际加载的图，尚未替换为修复候选。

## 本机资料与清理规则

`.local/original/` 保存原作者 EXE 和源码 ZIP；`.local/art/0.1.4/` 只保留补发时两张独有的原始生成图；`.local/releases/` 保存必要的已发布构建记录；`.local/build/` 在打包时自动创建，可重建。

不再堆积旧中间包、无用下载、重复效果图和一次性说明。历史源码、已提交的旧文档和效果图从 Git 找回，已发布标签与 GitHub Release 不变。效果对照统一放 `image/review/版本/`；PS 工作稿放 `image/work/版本/`。每个阶段维护一份方案，普通问答直接在对话里说明。

Git 保存源码、测试、开发工具、依赖、必要文档、原角色参考、候选和最终对照。`.local/`、`.venv/`、`versions/`、`image/work/`、个人设置与日志均不上传。Git 元数据、自动检查、测试和依赖属于项目必需内容。
