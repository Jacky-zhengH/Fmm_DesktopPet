# 美术素材

| 目录 | 内容 |
|---|---|
| `references/` | 角色母图、呆毛问题示例、手绘 UI 图 |
| `repaired/0.1.4/` | 六张修复候选，处理记录为 `processing.json` |
| `review/0.1.4/` | 一张完整对照、一份走路 GIF，检查数据在 `audit/` |
| `work/0.1.4/` | 两份 PSD、四张手修图，仅本机保存 |

**修复候选尚未接入程序。** 实际运行图在 `app/assets/sprites/`，两版 EXE 各自使用内置素材。

母图 `references/fmm_master_reference.jpg` 是用户提供的 1280×1280 JPG，原始字节保留。呆毛拱起空隙应透明；头饰、眼睛和头发高光要保留，不能全局去白。

PS 工作稿为 `blink.psd`、`happy.psd`，手工导出为 `idle_manual.png`、`blink_manual.png`、`sleep_manual.png`、`happy_partial.png`。原始补发生成输出只留两张，位于本机 `.local/art/0.1.4/`。

后续效果对照统一放 `review/版本/`，同一轮更新最终对照，清理重复试图。认可后的素材才进入运行目录。

[素材工作流](../docs/art/WORKFLOW_0_1_4.md) · [提示词](../docs/art/PROMPTS_0_1_4.md) · [项目结构](../docs/PROJECT_STRUCTURE.md)
