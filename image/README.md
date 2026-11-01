# 美术素材

| 目录 | 内容 |
|---|---|
| `references/` | 角色母图、呆毛白底问题示例、手绘 UI 概念图 |
| `repaired/0.1.4/` | 六张去白边、走路右侧补发后的候选 PNG |
| `review/0.1.4/` | 一张完整前后对照、一份两帧走路预览 |
| `work/0.1.4/` | 两份 PSD、四张手工修图，仅本机保存，不上传 |

**修复候选尚未接入程序。** 当前运行图仍在 `app/assets/sprites/`，EXE 使用自身内置图。

母图 `references/fmm_master_reference.jpg` 是用户提供的 1280×1280 JPG，原始字节保留。呆毛拱起的空隙应透明；头饰、眼睛和头发上的白色属于角色，不能全局删除。`ahoge_white_region_reference.jpg` 是问题示例，`ui_0_1_2_concept.jpg` 是菜单手绘图。

PS 工作稿现名 `blink.psd`、`happy.psd`；手工导出为 `idle_manual.png`、`blink_manual.png`、`sleep_manual.png`、`happy_partial.png`。闭眼与睡眠暂时同图，仍保留各自文件名。若 PS 还打开旧路径的文档，请从新位置重新打开后继续编辑。

修图处理记录在 `analysis/0.1.4/repaired_assets.json`。原始生图输出和中间稿已归入本机 `.local/archive/art/0.1.4/`。后续对照图统一放 `review/版本号/`，同一轮用最终结果替换冗余试图。

[素材工作流](../docs/art/WORKFLOW_0_1_4.md) · [提示词](../docs/art/PROMPTS_0_1_4.md) · [整个项目的目录说明](../docs/PROJECT_STRUCTURE.md)
