# fmm 桌宠补完计划 · Fmm DesktopPet

这是一只 **芙眠眠nemu** 桌宠，基于已有的 Python / PySide6 源码修改。先把日常用着不顺手的地方修好，再慢慢加功能。

芙眠眠nemu是 B 站助眠区的 UP 主，很推荐她的助眠内容，感兴趣可以搜搜看。

目前有点击互动、拖动与边缘吸附、缩放、睡眠、弧形气泡菜单、时钟和定时提醒。喂食仍是概念演示，尚未加入养成存档。具体操作见 [简易功能指引](docs/QUICK_GUIDE.md)。

## 怎么打开

直接使用可从私有仓库的 [Release](https://github.com/Jacky-zhengH/Fmm_DesktopPet/releases/latest) 下载 `Fmm-DesktopPet-v0.1.3.exe` 或便携 ZIP，无需安装 Python。

开发时仍双击根目录 **`run.bat`**。新电脑先安装 Python 3.10+，运行一次 `setup.bat`。源码设置独立保存在 `.local/profiles/user-source/`，便携版在 EXE 旁的 `.user/`。

## 文件放哪里

- `app/`：当前标准版的程序与运行素材。
- `tools/`、`tests/`、`requirements/`：开发工具、自动检查和依赖。
- `image/`：参考图、修复候选、最终对照和本地 PS 工作稿。
- `docs/`：功能指引、开发说明、阶段方案与发布记录。
- `versions/`：本机程序包，用户版与 Fmm 定制版分开放置，不提交 Git。

0.1.4 正在修素材，再补拎起轻晃、连续点击生气、边缘探头和动作管理。六张修复候选已完成，尚未审定接入；当前运行版仍为 0.1.3。

[目录与两个版本的位置](docs/PROJECT_STRUCTURE.md) · [开发与回退](docs/DEVELOPMENT.md) · [后续方向](docs/ROADMAP.md) · [0.1.4 方案](docs/plans/0.1.4.md) · [更新记录](CHANGELOG.md)

第一阶段使用 0.1.x，下一阶段再用 0.2.x；何时进入 1.0.x，由用户决定。源码每完成一段就提交并测试，已发布标签保留，方便回退。
