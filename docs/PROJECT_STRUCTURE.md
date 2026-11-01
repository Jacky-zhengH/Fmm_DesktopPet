# 项目目录

根目录只保留实际维护需要的内容：

```text
fmm/
├─ app/                 标准版程序、动画参数和运行 PNG
├─ tests/               自动检查
├─ tools/               art / diagnostics / release / github
├─ requirements/        运行、素材工具、打包依赖
├─ image/               参考、修图记录、对照、PS 工作稿
├─ docs/                指引、开发、计划、美术流程、发布记录
├─ versions/user/       标准版 EXE、发布包及自己的 .user，Git 忽略
├─ .local/              本机存档、原始备份和临时构建
├─ .venv/               本机 Python 环境
├─ .git/、.github/      Git 历史与自动检查
└─ run.bat / setup.bat  日常源码测试 / 首次配置
```

旧 `deskpet/` 转发层、重复的 `dist/` 和历史 `analysis/` 已移除。程序统一按 `app/` 中的标准用户版开发。此前本地定制版的活跃安装与源码副本已移除，历史提交和标签保留。

## 运行与存档

| 用途 | 启动位置 | 设置位置 |
|---|---|---|
| 用户版 | `versions/user/Fmm-DesktopPet-v0.1.3.exe` | `versions/user/.user/` |
| 日常开发测试 | 根目录 `run.bat` | `.local/profiles/user-source/` |

源码版和便携版各自保留存档。根目录 `run.bat` 已使用本轮接入的六张修复图；`versions/user/` 中仍是此前已发布的 0.1.3 EXE，尚未重新打包。标准构建工具默认输出到 `versions/user/`。

## 美术位置

- `image/references/`：母图、问题示例和手绘 UI 图。
- `image/repaired/0.1.4/`：修复交付记录，处理清单为 `processing.json`。
- `image/review/0.1.4/`：最终前后对照、走路 GIF；原图检查数据在 `audit/`。
- `image/work/0.1.4/`：两份 PSD、四张手工修图，仅本机保存。
- `app/assets/sprites/`：程序实际加载的六张修复图；此处是运行素材的正式位置。

## 本机资料与清理规则

`.local/original/` 保存原作者 EXE 和源码 ZIP；`.local/art/0.1.4/` 只保留补发时两张独有的原始生成图；`.local/releases/` 保存必要的已发布构建记录；`.local/build/` 在打包时自动创建，可重建。

不再堆积旧中间包、无用下载、重复效果图和一次性说明。历史源码、已提交的旧文档和效果图从 Git 找回，已发布标签与 GitHub Release 不变。效果对照统一放 `image/review/版本/`；PS 工作稿放 `image/work/版本/`。每个阶段维护一份方案，普通问答直接在对话里说明。

Git 保存源码、测试、开发工具、依赖、必要文档、原角色参考、候选和最终对照。`.local/`、`.venv/`、`versions/`、`image/work/`、个人设置与日志均不上传。Git 元数据、自动检查、测试和依赖属于项目必需内容。
