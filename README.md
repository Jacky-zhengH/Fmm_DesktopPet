# fmm 桌宠补完计划 · Fmm DesktopPet

给 **芙眠眠nemu** 做的一只小桌宠，在现有的 Python / PySide6 版本上慢慢修改。

芙眠眠nemu是 B 站助眠区的一位 UP 主，很推荐她的助眠内容，感兴趣可以去 B 站搜搜看。

## 现在能做什么

- 放在桌面上，点击会开心，能拖着走，也会自己眨眼、走动和睡觉。
- 右键调整大小，范围 80%～200%；也可以按住 Ctrl 滚动滚轮。
- 切换像素清晰或平滑显示，开关自主走动，记住上次的位置和大小。
- 替换 PNG 动作素材后，可以在菜单里重新加载。

目前还有些小毛病：走路会变小，不能贴住任务栏，呆毛里面还有没抠干净的背景。动作也比较少，会先修这些，再继续补。

## 怎么打开

新电脑第一次运行，需要先装 Python 3.10+，再双击 `setup.bat`。

**平时双击根目录的 `run.bat` 就行。** 如果桌宠已经开着，先右键退出，再启动，避免开出好几只。菜单里也可以调整大小、睡觉和重载素材。

更多操作见 [源码使用说明](deskpet/deskpet/README.md)。

## 接下来想做的

| 版本 | 内容 | 进度 |
|---|---|---|
| v0.0 | 保存原作者的源码和素材 | 已留档 |
| v0.1 | 修启动和基础交互，加入缩放、像素显示 | 已完成，正在试用 |
| v0.2 | 修走路变小，加入任务栏吸附 | 下一步 |
| v0.3 | 清理图片背景，补走路、睡觉等动作 | 待做 |
| 以后 | 助眠音乐台、播放器联动、小控件和养宠机制 | 慢慢来 |

详细安排见 [开发计划](docs/ROADMAP.md) 和 [下一版的修改方案](docs/PHASE_2_PROPOSAL.md)。改过什么会记在 [更新记录](CHANGELOG.md) 里。

## 代码和素材

`main` 放目前能用的版本，改功能时另开分支。每完成一段就提交，试过没问题再留一个版本，方便改坏了退回来。原版源码也保留着。

[开发与回退说明](docs/DEVELOPMENT.md) · [Issues](https://github.com/Jacky-zhengH/Fmm_DesktopPet/issues) · [Milestones](https://github.com/Jacky-zhengH/Fmm_DesktopPet/milestones) · [Actions](https://github.com/Jacky-zhengH/Fmm_DesktopPet/actions)

角色参考图放在 `image/`，之前的分析和演示放在 `analysis/`。运行环境、个人设置和打包文件留在本地。
