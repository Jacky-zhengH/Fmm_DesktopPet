# fmm 桌宠补完计划 · Fmm DesktopPet

以 **芙眠眠nemu** 的角色形象为参考，在已有 Python / PySide6 桌宠源码之上持续补完的个人私有项目。

芙眠眠nemu是 B 站助眠区 UP 主，项目源于对她的助眠内容和角色形象的喜爱；也推荐在 B 站搜索「芙眠眠nemu」了解她的内容。

## 当前功能

- 透明置顶桌宠，点击互动、拖动、随机眨眼和走动、睡觉/唤醒。
- 大小面板实时预览，80%～200% 范围；Ctrl+滚轮快捷缩放，普通滚轮不误触。
- 像素清晰与平滑显示切换，自主走动开关，位置/大小保存。
- PNG 序列帧、独立动作 FPS 和素材重载。
- 时间驱动的动作与睡眠，14 项回归检查。

已知问题：走路时人物可见尺寸变小；任务栏吸附尚未实现；部分呆毛空隙残留白色背景；走路仅两帧，尚无独立睡姿。

## 打开测试

首次在新电脑克隆后，准备 Python 3.10+ 并双击 `setup.bat`。当前开发电脑已配置独立环境。

**日常统一双击根目录 `run.bat`。** 已有桌宠时先右键退出，再启动。右键可调整大小、睡觉、重载素材和退出。旧便携 EXE 保留本地，不作为新版测试入口。

更多操作见 [源码使用说明](deskpet/deskpet/README.md)。

## 开发路径

| 阶段 | 主要内容 | 状态 |
|---|---|---|
| v0.0 原始归档 | 原作者源码与素材留档 | Git 原始回退点 |
| v0.1 基础补完 | 启动、交互、时序、缩放、像素显示 | 已完成基础测试与用户验收 |
| v0.2 视觉定位与任务栏 | 统一角色可见大小和脚底锚点、任务栏吸附 | 方案阶段 |
| v0.3 素材与动作 | 背景残留、独立睡姿、完整步态、动作扩展 | 待制作 |
| 后续 | 助眠音乐台、外部播放器联动、智能控件与养成 | 待设计与验证 |

详细见 [开发路径](docs/ROADMAP.md)、[下一阶段方案](docs/PHASE_2_PROPOSAL.md)、[变更记录](CHANGELOG.md)。

## 版本管理

`main` 保留已测试基线；后续使用 Issue → 分支 → PR → 测试 → 阶段验收 → Tag/Release。原始代码与每个验收版本均有回退点。源码、PNG 和角色参考纳入版本管理，环境、个人设置、日志和 EXE 不随源码提交。

[开发与回退说明](docs/DEVELOPMENT.md) · [Issues](https://github.com/Jacky-zhengH/Fmm_DesktopPet/issues) · [Milestones](https://github.com/Jacky-zhengH/Fmm_DesktopPet/milestones) · [Actions](https://github.com/Jacky-zhengH/Fmm_DesktopPet/actions)

参考素材放在 `image/`；历史分析与诊断在 `analysis/`。
