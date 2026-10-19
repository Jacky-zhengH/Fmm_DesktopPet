# 项目目录与整理记录

正式源码已从两层 `deskpet/deskpet` 移到 `app/`。根目录仍双击 `run.bat`，现有便携版及个人设置继续使用原位置。

```text
fmm/
├─ app/                 正式程序：main.py、pet/、assets/
├─ tests/               Qt、状态、布局、素材工具测试
├─ tools/               图片处理和视频拆帧工具
├─ requirements/        base.txt、build.txt、tools.txt
├─ scripts/             打包、校验和 GitHub 管理工具
├─ docs/                功能指引、开发说明和版本记录
├─ image/               用户提供的角色参考图
├─ analysis/            历史分析、对照图及诊断脚本
├─ deskpet/             本机便携安装、旧入口兼容和个人设置
├─ .local/              仅本地的定制源码、发布操作记录
├─ build/               可重建的编译缓存、临时检查产物
└─ dist/                构建结果；archive/ 保存历史成品
```

## 哪些路径保持兼容

| 用途 | 正式位置 | 旧位置如何处理 |
|---|---|---|
| 启动程序 | `run.bat` / `app/main.py` | `deskpet/deskpet/run.bat` 和 `main.py` 只转发 |
| 程序模块 | `app/pet/` | 旧 `pet` 包路径转发，旧版本文件只导出正式版本值 |
| 运行图片 | `app/assets/sprites/` | 六张原图原样移动，内容不改 |
| 动画参数 | `app/assets/animations.json` | 打包及工具路径同步更新 |
| 测试 | `tests/` | 原 unittest 命令仍转发到同一套测试 |
| 素材工具 | `tools/` | 旧工具路径保留 CLI 和导入兼容入口 |
| 依赖 | `requirements/` | 旧依赖文件只引用新文件，不再重复定义版本 |
| 源码操作说明 | `docs/SOURCE.md` | 旧 README 只提示新位置 |

源码个人设置仍在 `deskpet/deskpet/.user/`，EXE 设置仍在各自 EXE 旁的 `.user/`。这次不迁移存档，避免升级后位置、大小等偏好被重置。ForFmm 仍独立安装在 `deskpet/ForFmm/`，其源码工作目录移到 `.local/for-fmm-source/`，不随清理 build 丢失。

## 重复文件怎样处理

- 移除了无内容的“双击run.bat运行”提示文件。
- `blink.png` 和 `sleep.png` 当前内容相同，但分别是眨眼、睡眠的状态素材，保留两者以维持现有效果。
- 当前版本名 EXE 与中文兼容 EXE 是有意保留的两个启动入口；dist 是打包产物，archive 是回退副本，不当作源码重复删除。
- 旧版安装目录里与 archive 完全一致的 0.1.2 EXE，核对 SHA256 后归入 archive；旧诊断包和 0.1.2 发布文件也已归档。
- 运行环境、缓存、个人设置、定制源码和二进制均不提交 Git。原角色图、参考图和历史分析对照图继续保留。

## 验证与边界

新、旧 unittest 入口运行同一套回归；启动脚本、旧命令、素材工具和打包路径都需验证。测试包使用 `scripts/package_release.py --output-dir dist/layout-validation`，避免覆盖已发布成品。

本次是源码结构整理，运行版本仍为 0.1.3；不移动旧版本标签，不覆盖现有 Release 的源码和 EXE。后续新发行包从新结构构建。

旧版手动上传的源码 ZIP 已在本地校验留档后撤下。GitHub 自动生成的标签源码归档、历史提交仍受仓库读取权限控制；不能把“删除一个 Release 附件”当作撤销历史代码访问。仓库继续保持私有。
