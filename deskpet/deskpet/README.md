# 桌宠

透明无边框窗口 + 置顶。像素风女仆装角色「芙眠眠」，全套真实素材（待机/眨眼/睡觉/走路×2/开心）。

## 玩法

| 操作 | 效果 |
|---|---|
| 左键点击 | 互动：开心跳跃（睡觉中则唤醒） |
| 左键拖动 | 抓起移动（>_< 表情） |
| 右键 | 菜单：睡觉(叫醒) / 退出 |
| 放置不管 | 随机眨眼、呼吸；随机漫游走动；90 秒无交互自动睡觉（Zzz） |

## 运行

```
run.bat          # 双击（无控制台窗口）
# 或
python main.py   # 需已安装 PySide6
```

## 目录结构

```
main.py            入口，装配应用
pet/
  sprites.py       素材库：图片加载 / 组合式占位图（带缓存与回退链）
  character.py     状态机：idle/walk/sleep/happy/drag + 漫游
  window.py        透明窗口、拖动 vs 点击识别、行走移动、Zzz 绘制、右键菜单
assets/sprites/    图片素材目录 ← 换皮只动这里
```

## 如何替换 / 添加图片素材

把 PNG（建议透明背景）放进 `assets/sprites/`，**文件名与状态名一致，重启即生效，代码零改动**：

| 文件名 | 用途 |
|---|---|
| `idle.png`  | 待机 |
| `walk_0.png`、`walk_1.png` | 走路序列帧（素材朝左；往右走由程序自动镜像，`WALK_SPRITE_FACING` 可配） |
| `sleep.png` | 睡觉 |
| `happy.png` | 开心互动 |
| `blink.png` | 眨眼（叠加在 idle/walk 上） |

- **序列帧**：任何状态都支持 `<状态>_0.png`、`<状态>_1.png`… 连续编号自动轮播（~7.5fps）；有序列帧的状态自动关闭程序化动效（呼吸/眨眼），眨眼帧可画进序列里
- **叠加变体**：`walk_blink.png` 可提供走路眨眼专用图；缺失时自动回退 `blink.png` → 占位图
- 素材统一缩放到 200×200（`sprites.py` 顶部 `CANVAS_SIZE` 可改）
- 素材缺失时按名字关键词自动组合绘制占位图，永不因缺图崩溃

## 如何扩展新动作

以"跳舞"为例：

1. `character.py` 的 `State` 加 `DANCE = "dance"`
2. `_tick()` 里挂迁移逻辑（何时进入/退出）
3. `current_sprite()` 里返回 `self.sprites.get("dance")`
4. `assets/sprites/` 放 `dance.png`（或 `dance_0.png`… 序列帧）

行为参数（漫游频率、入睡时间、移动速度等）都在
`character.py` 顶部常量区，直接改数值即可调手感。
