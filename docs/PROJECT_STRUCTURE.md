# 项目目录

程序在 `app/`，双击根目录 `run.bat` 测试。目录整理不改变当前 0.1.3 的运行功能。

```text
fmm/
├─ app/                      程序本体
│  ├─ main.py                启动入口
│  ├─ pet/                   行为、界面、布局、设置
│  └─ assets/                程序实际使用的动画参数和 PNG
├─ image/                    美术素材
│  ├─ references/            角色母图、问题示例、UI 概念图
│  ├─ repaired/0.1.4/        六张已处理的候选 PNG，待审图后接入
│  ├─ review/                按版本保存效果对照，每轮保留最终对照与动画
│  └─ work/0.1.4/            PS 工作稿及手工导出，仅本地保存
├─ tools/                    开发工具
│  ├─ art/                   素材处理、照片裁切、视频拆帧
│  ├─ diagnostics/           素材检查、界面预览
│  ├─ release/               EXE 构建和发布包生成
│  └─ github/                仓库管理、原始源码导入
├─ tests/                    自动检查
├─ requirements/             运行、打包、素材工具的依赖
├─ docs/                     功能指引、开发说明、目录说明、路线图
│  ├─ plans/                 当前版本的具体方案
│  ├─ art/                   美术工作流与提示词
│  └─ releases/              各版发布说明
├─ analysis/                 检查数据；0.1.4/ 为当前检查，history/ 为旧数据
├─ dist/                     当前已发布的 EXE、ZIP、源码包、指引、校验值
├─ deskpet/                  中文便携 EXE、本地定制安装及旧入口兼容
├─ .local/                   本机归档、定制源码及维护记录
└─ .venv/                    Python 环境，不能直接搬动或随源码上传
```

`build/` 是打包时自动创建的临时目录；旧编译缓存已清理，独有的实验脚本和构建凭证在 `.local/archive/experiments/`。历史安装包统一在 `.local/archive/releases/`，原始源码 ZIP 在 `.local/archive/source/`。

## 素材放哪里

- **看修复结果**：`image/repaired/0.1.4/`。六张图均为 512×512 透明 PNG。
- **看修改前后**：`image/review/0.1.4/comparison.png`；走路循环是同目录 `walk_preview.gif`。
- **继续用 PS 编辑**：`image/work/0.1.4/` 中的 `blink.psd`、`happy.psd` 和四张手工导出。文件只改位置和名称，内容未改。
- **查处理记录**：`analysis/0.1.4/repaired_assets.json`。
- **程序当前加载**：`app/assets/sprites/`。候选素材尚未替换进去，EXE 也没有重新打包。

## 以后怎样保持整洁

效果图统一放 `image/review/版本号/`；同一轮保留一张最终对照和必要的动画预览，旧的重复试图删掉。大量生图废稿和临时输出留 `.local/`。PSD 与手工工作图放 `image/work/`，最终素材通过审图再进入 `app/assets/`。

日常问题直接在对话里解释；已有功能写 `QUICK_GUIDE.md`，开发方向写 `ROADMAP.md`，具体阶段只维护一份方案，发布说明写 `releases/`。不再为每次问答另建 MD。已经提交过的旧说明和效果图可以从 Git 历史找回。

## Git 与本机文件

Git 保存源码、测试、开发工具、依赖定义、必要文档、角色参考、修复候选和最终对照。`.local/`、`image/work/`、`.venv/`、个人设置、日志、`build/`、`dist/`、EXE/ZIP 不上传。

`deskpet/deskpet/` 只保留旧命令的转发层和源码版 `.user/` 存档，没有第二份实现。源码设置仍位于 `deskpet/deskpet/.user/`；中文便携版的设置在 `deskpet/.user/`。本地定制版及它的存档继续独立保留，定制源码工作树不搬动、不上传。

中文便携版保留 `deskpet/芙眠眠桌宠便携版.exe`；发布用版本名 EXE 留在 `dist/`，删除了安装目录内相同内容的额外副本。它们分别是日常安装和发布产物。
