# fmm 桌宠补完计划 · Fmm DesktopPet

这是一只 **芙眠眠nemu** 桌宠，基于已有的 Python / PySide6 源码修改。先把日常用着不顺手的地方修好，再慢慢加功能。

芙眠眠nemu是 B 站助眠区的 UP 主，很推荐她的助眠内容，感兴趣可以搜搜看。

## 现在能做什么

- 放在桌面上，点击会开心，能拖着走，也会自己眨眼、走动和睡觉。
- 右键调整大小，范围 80%～200%；也可以按住 Ctrl 滚动滚轮。
- 切换像素清晰或平滑显示，开关自主走动，记住上次的位置和大小。
- 替换 PNG 动作素材后，可以在菜单里重新加载。

目前还没修好：走路时会变小，拖到任务栏边缘还不能吸附，呆毛里也有背景残留。现有动作不多，后面还会继续补。

## 怎么打开

新电脑第一次运行，需要先装 Python 3.10+，再双击 `setup.bat`。

**平时双击根目录的 `run.bat` 就行。** 如果桌宠已经开着，先右键退出，再启动，避免开出好几只。菜单里也可以调整大小、睡觉和重载素材。

更多操作见 [源码使用说明](deskpet/deskpet/README.md)。

## 接下来要改什么

| 版本 | 内容 | 进度 |
|---|---|---|
| v0.0 | 保存原作者的源码和素材 | 已留档 |
| v0.1 | 修启动和基础交互，加入缩放、像素显示 | 已完成，正在试用 |
| v0.2 | 修走路变小，加入任务栏吸附 | 下一步 |
| v0.3 | 清理图片背景，补走路、睡觉等动作 | 待做 |
| 以后 | 助眠音乐台、播放器联动、小控件和养宠机制 | 慢慢来 |

要改的东西记在 [开发计划](docs/ROADMAP.md) 和 [下一版方案](docs/PHASE_2_PROPOSAL.md) 里，已经改好的记在 [更新记录](CHANGELOG.md) 里。

## 代码和素材

`main` 放目前能用的版本，改功能时另开分支。每完成一段就提交，试过没问题再留一个版本，方便改坏了退回来。原版源码也保留着。

[开发与回退说明](docs/DEVELOPMENT.md) · [Issues](https://github.com/Jacky-zhengH/Fmm_DesktopPet/issues) · [Milestones](https://github.com/Jacky-zhengH/Fmm_DesktopPet/milestones) · [Actions](https://github.com/Jacky-zhengH/Fmm_DesktopPet/actions)

角色参考图放在 `image/`，之前的分析和演示放在 `analysis/`。运行环境、个人设置和打包文件不放进源码仓库。
