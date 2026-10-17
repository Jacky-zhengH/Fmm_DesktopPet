# fmm 桌宠 · 源码补完版

Python / PySide6 写的透明桌宠。目前使用这份源码开发，原来的便携 EXE 作为旧版保留。

## 启动

在项目根目录双击 `run.bat`。当前电脑已配置根目录 `.venv`，不需要使用系统默认 Python。

在新电脑上先准备 Python 3.10 或更新版本，再运行根目录 `setup.bat` 安装固定依赖。本项目当前验证环境为 Python 3.12 / PySide6 6.12.0。素材处理工具还需 `requirements-tools.txt`。

命令行（从 fmm 根目录）：

```powershell
.\.venv\Scripts\python.exe deskpet/deskpet/main.py
.\.venv\Scripts\python.exe -m pip install -r deskpet/deskpet/requirements-tools.txt
```

## 操作

| 操作 | 效果 |
|---|---|
| 左键单击 | 开心互动；睡眠中点击仅唤醒 |
| 左键拖动 | 移动宠物；有 drag 图/序列时使用，否则回退待机 |
| 普通滚轮 | 不改变大小，避免误触 |
| Ctrl + 滚轮 | 快捷放大/缩小，每格调整 10% |
| 右键 → 调整大小… | 打开滑条和加减按钮，范围 80%～200%，默认 100% |
| 右键 → 像素清晰显示 | 开关最近邻/平滑显示 |
| 右键 → 自主走动 | 开关漫游 |
| 右键 → 靠近任务栏/屏幕边缘时吸附 | 开关释放拖动后的自动吸附，拖走可解除 |
| 右键 → 重新加载素材 | 重新读 PNG 和 animations.json |
| 右键 → 睡觉/叫醒/退出 | 手动状态切换或结束程序 |

90 秒没有操作会自动睡觉，自主走路不影响计时。窗口周围留了一点空间，方便呼吸和跳动。走路目前只有两帧，图片边缘和动作会在后面继续补。

0.1.1 统一了动作的可见高度和脚底位置。靠近边缘约 24 个逻辑像素、或拖入任务栏区域后释放会吸附；可见人物不会再被整个透明窗口的边界挡在任务栏上方。换动作、调整大小和沿任务栏走动时保持贴边，关闭吸附后可以自由摆放。

大小、位置、显示方式、走动开关保存在源码 `.user/settings.json`；日志在 `.user/runtime.log`。配置损坏会回退默认值。`auto_sleep_seconds` 设为 0 可禁用自动睡眠。

大小面板支持实时预览、恢复默认、确定保存和取消还原。缩放统一限制在 160～400 像素角色画布，旧配置超出范围会自动收回。命令行加 `--size-settings` 可在启动后直接打开面板。

## 素材与动画

运行素材仍在 `assets/sprites/`，根目录 `image/` 是参考素材区，不会自动加载。

- 单图：`idle.png`、`sleep.png`、`happy.png`、`drag.png`、`blink.png`。
- 序列：`idle_0.png`、`idle_1.png`……从 0 连续编号，中途缺号会停止扫描。
- 自动识别现有 idle / walk / sleep / happy / drag 五种状态；新的状态仍需添加行为与触发入口。
- blink 是完整角色替换图，不是独立眼睛图层；走路序列默认不再额外眨眼。
- 图片保留原分辨率，绘制时按比例适配当前大小；建议统一透明画布、人物比例和脚底基线。
- 缺图时会尝试使用备用图片，或显示占位图。替换图片后，在菜单里重新加载即可。

`assets/animations.json` 示例：

```json
{
  "version": 1,
  "states": {
    "walk": {"fps": 8, "loop": true, "facing": -1},
    "happy": {"fps": 12, "loop": false, "procedural": false}
  }
}
```

`facing`：-1 朝左、1 朝右、0 正面；`loop=false` 停在末帧，状态退出仍由行为逻辑控制。序列帧默认关闭额外呼吸/跳动，确有需要时设置 `procedural=true`。

窗口以 16 ms 定时请求更新，目标约 60 次/秒；图片 FPS 独立配置。实际刷新受系统调度影响。两张图快速重复不会变成完整动画，所以原走路先保持约 8 FPS。

现有便携 EXE 使用内置代码和图片，不会读取改过的源码或自动同步外部素材。当前开发请运行源码入口。

## 检查与备份

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s deskpet/deskpet/tests -v
.\.venv\Scripts\python.exe deskpet/deskpet/main.py --smoke-test
```

`--smoke-test` 启动实际 Qt 事件循环约 1.2 秒后退出，不保存用户设置。回归测试使用真实 Qt 离屏环境与合成事件；不能代替多屏/DPI 或长时间桌面验收。

原始源码与素材备份在根目录 `analysis/source_before_phase1.zip`。阶段计划在 `analysis/fmm桌宠补完计划-第一阶段.md`。
