"""Import original ZIP as a Git tree, without replacing live project files."""
from pathlib import Path, PurePosixPath
import subprocess
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent.parent


def git(*args, data=None, check=True):
    result = subprocess.run(["git", *args], cwd=ROOT, input=data, capture_output=True, check=check)
    return result.stdout.decode("utf-8", errors="replace").strip()


def tree_sha(tree):
    entries = []
    for name, value in tree.items():
        if isinstance(value, dict):
            mode, kind, sha = "040000", "tree", tree_sha(value)
        else:
            mode, kind, sha = "100644", "blob", value
        entries.append(f"{mode} {kind} {sha}\t{name}".encode("utf-8") + b"\0")
    return git("mktree", "-z", data=b"".join(entries))


if not (ROOT / ".git").exists():
    git("init", "--initial-branch=main")
existing = git("rev-parse", "--verify", "HEAD", check=False)
if existing:
    raise SystemExit("Repository already has commits; original import will not rewrite them.")
root_tree = {}
with ZipFile(ROOT / "analysis" / "source_before_phase1.zip") as archive:
    for info in archive.infolist():
        path = PurePosixPath(info.filename.replace("\\", "/"))
        if info.is_dir():
            continue
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise ValueError("Unsafe archive path")
        target = root_tree
        for part in ("deskpet", "deskpet", *path.parts[:-1]):
            target = target.setdefault(part, {})
        target[path.name] = git("hash-object", "-w", "--stdin", data=archive.read(info))
sha = git("commit-tree", tree_sha(root_tree), "-m", "chore: preserve original desktop pet source")
git("update-ref", "refs/heads/main", sha)
git("symbolic-ref", "HEAD", "refs/heads/main")
git("read-tree", "HEAD")
git("tag", "-a", "v0.0.0-original", "-m", "Original desktop pet source and sprites preserved before modifications")
print("Original source checkpoint:", sha)
