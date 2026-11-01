# 美术素材

| 目录 | 内容 |
|---|---|
| `references/` | 角色母图、呆毛问题示例、手绘 UI 图 |
| `repaired/0.1.4/` | 修复交付记录，处理清单为 `processing.json` |
| `review/0.1.4/` | 一张完整对照、一份走路 GIF，检查数据在 `audit/` |
| `work/0.1.4/` | 两份 PSD、四张手修图，仅本机保存 |

**六张修复图已接入标准版源码。** 实际运行图在 `app/assets/sprites/`，双击根目录 `run.bat` 查看；已发布的 0.1.3 EXE 尚未重新打包。

母图 `references/fmm_master_reference.jpg` 是用户提供的 1280×1280 JPG，原始字节保留。呆毛拱起空隙应透明；头饰、眼睛和头发高光要保留，不能全局去白。

PS 工作稿为 `blink.psd`、`happy.psd`，手工导出为 `idle_manual.png`、`blink_manual.png`、`sleep_manual.png`、`happy_partial.png`。原始补发生成输出只留两张，位于本机 `.local/art/0.1.4/`。

后续效果对照统一放 `review/版本/`，同一轮更新最终对照，清理重复试图。认可后的素材才进入运行目录。

行走两帧的复修对照已更新到 `review/0.1.4/comparison.png`，循环见同目录 `walk_preview.gif`。本轮先清原有浅粉外圈，再统一待机参考色板；详细参数、输入提交与输出哈希见 `repaired/0.1.4/processing.json` 的 `walk_correction`。可用 `tools/art/repair_walk_sprites.py` 从记录的 Git 提交重新生成独立候选，工具会拒绝覆盖运行目录。

[素材工作流](../docs/art/WORKFLOW_0_1_4.md) · [提示词](../docs/art/PROMPTS_0_1_4.md) · [项目结构](../docs/PROJECT_STRUCTURE.md)
