"""Manage this private repository using Git's configured credential helper.

Credentials stay in process memory and are never written or printed. No login
or repository visibility settings are changed. Requires existing Git access.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
REPOSITORY = "Jacky-zhengH/Fmm_DesktopPet"


def credential():
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never"}
    result = subprocess.run(["git", "credential", "fill"],
                            input=f"protocol=https\nhost=github.com\npath={REPOSITORY}.git\n\n",
                            text=True, capture_output=True, cwd=ROOT, env=env)
    fields = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    if result.returncode or not fields.get("password"):
        raise SystemExit("Existing GitHub Git credentials are unavailable; no credential data was printed.")
    return fields["password"]


TOKEN = None


def api(method, suffix="", data=None):
    request = urllib.request.Request(
        f"https://api.github.com/repos/{REPOSITORY}{suffix}",
        data=None if data is None else json.dumps(data, ensure_ascii=False).encode("utf-8"),
        method=method,
        headers={"Authorization": "Bearer " + TOKEN, "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "fmm-project-management",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read()
            return json.loads(content) if content else None
    except urllib.error.HTTPError as exc:
        body = json.loads(exc.read().decode("utf-8"))
        raise SystemExit(f"GitHub API {exc.code}: {body.get('message', 'request failed')}") from None


def setup():
    labels = {label["name"] for label in api("GET", "/labels?per_page=100")}
    for name, color in (("bug", "d73a4a"), ("enhancement", "a2eeef"),
                        ("stage:0.2", "7057ff"), ("stage:0.3", "c5def5"), ("assets", "f9d0c4")):
        if name not in labels:
            api("POST", "/labels", {"name": name, "color": color})
    milestones = {item["title"]: item for item in api("GET", "/milestones?state=all&per_page=100")}
    for title, state, description in (
        ("v0.1 · 基础补完", "closed", "源码启动与基础交互，用户已验收，14 项检查通过。"),
        ("v0.2 · 视觉定位与任务栏", "open", "统一可见大小/脚底锚点，任务栏吸附与实机验收。"),
        ("v0.3 · 素材与动作", "open", "封闭背景、统一母版、独立睡姿和完整动作集。")):
        if title not in milestones:
            milestones[title] = api("POST", "/milestones", {"title": title, "state": state, "description": description})
    existing = {item["title"]: item for item in api("GET", "/issues?state=all&per_page=100")}
    specifications = [
        ("[v0.2] 修复行走切换导致人物缩小", "v0.2 · 视觉定位与任务栏", ["bug", "stage:0.2"],
         "当前 idle 可见高度约 179 px，walk 约 139 px；按整张带留白画布缩放导致约 22.3% 的可见高度下降。\n\n方案：按全帧 Alpha bbox 并集计算共享变换、统一可见高度与脚底锚点，保留原始 PNG。\n\n验收：\n- [ ] idle/walk 可见高度差约 5% 内\n- [ ] 动作切换和序列帧不跳位/不抖动\n- [ ] 160/200/300/400 画布不裁切\n- [ ] 原 PNG 哈希不变，附前后对照\n\n详见 docs/PHASE_2_PROPOSAL.md。"),
        ("[v0.2] 实现任务栏上沿吸附与可见脚底锚点", "v0.2 · 视觉定位与任务栏", ["enhancement", "stage:0.2"],
         "当前 availableGeometry + 整窗口边界阻止接近任务栏，图片底部留白还造成悬空。\n\n方案：区分完整屏幕和可用区域，用可见脚底与保留边缘判断吸附；透明留白可越过任务栏边界，不能遮挡任务栏点击。默认目标为站在任务栏上沿。\n\n验收：\n- [ ] 近边缘释放吸附、拖走解除、可关闭\n- [ ] 缩放/换动作/行走保持脚底\n- [ ] 任务栏图标可以点击\n- [ ] 保存/恢复锚点\n- [ ] 实机检查多屏、DPI、自动隐藏与屏幕移除\n\n详见 docs/PHASE_2_PROPOSAL.md。"),
        ("[v0.3] 清理呆毛封闭背景并统一动作素材", "v0.3 · 素材与动作", ["assets", "stage:0.3"],
         "母图呆毛空隙与外部背景同色，现有正面图对应区域却为不透明白色。头饰与高光需保留；走路只有两帧，睡眠图与眨眼图重复。\n\n验收：\n- [ ] 以母图核对封闭背景，保留人物白色细节\n- [ ] 深/浅/棋盘格背景对照\n- [ ] 统一画布、人物比例和脚底基线\n- [ ] 逐步补全步态、独立睡姿、拖动反馈\n- [ ] 素材修改独立提交并附前后图")]
    issues = []
    for title, milestone, labels, body in specifications:
        item = existing.get(title)
        if item is None:
            item = api("POST", "/issues", {"title": title, "milestone": milestones[milestone]["number"],
                                             "labels": labels, "body": body})
        issues.append({"number": item["number"], "title": item["title"], "url": item["html_url"]})
    releases = api("GET", "/releases?per_page=100")
    release = next((r for r in releases if r["tag_name"] == "v0.1.0"), None)
    if release is None:
        release = api("POST", "/releases", {"tag_name": "v0.1.0", "name": "v0.1.0 · 基础补完检查点",
            "body": "保存用户已测试的源码基线，14 项回归检查通过。\n\n包含源码启动、交互、时间驱动、80%～200% 缩放、像素显示和设置保存。\n\n已知行走缩小与任务栏吸附问题归入 v0.2。此 Release 先保存源码快照，尚未附加新版 EXE。",
            "draft": False, "prerelease": False})
    result = {"repository": REPOSITORY, "private": True, "issues": issues,
              "milestones": [{"title": item["title"], "number": item["number"], "url": item["html_url"]} for item in milestones.values()],
              "release": release["html_url"]}
    (ROOT / "analysis" / "github_state.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", action="store_true")
    args = parser.parse_args()
    TOKEN = credential()
    repository = api("GET")
    if not repository.get("private"):
        raise SystemExit("Repository is not private. No mutations performed; visibility was not changed.")
    result = setup() if args.setup else {
        "repository": repository["full_name"], "private": repository["private"],
        "default_branch": repository["default_branch"], "permissions": repository.get("permissions"),
        "size": repository["size"]}
    print(json.dumps(result, ensure_ascii=True, indent=2))
