# fmm project workflow

- Preserve the private GitHub repository `Jacky-zhengH/Fmm_DesktopPet`; do not change visibility.
- Keep `main` as the tested baseline. Initial repository import is allowed on main; subsequent runtime changes use a focused `fix/`, `feat/`, or `phase/` branch, associated Issue and PR.
- Commit completed units with clear messages; never force-push shared history or rewrite accepted release tags.
- Each accepted stage has an annotated version tag, CHANGELOG entry and validation notes. Tagging is done after required tests and user acceptance, not merely because a milestone exists.
- Before changing runtime behavior, establish a clean checkpoint for existing user changes. Do not discard unrelated changes.
- The common manual test entry is the root `run.bat`. The old portable EXE is a preserved local artifact.
- Run `.venv/Scripts/python.exe -m unittest discover -s deskpet/deskpet/tests -v` for relevant runtime changes. On CI use the selected Python interpreter directly.
- Keep `.venv`, `.user`, logs, credentials, build output and desktop screenshots out of Git. Keep source PNGs and intentionally provided character references versioned.
- Do not modify original character art while fixing layout math. Asset changes require explicit before/after visual review.
- Record planned work separately from implemented behavior; update README/roadmap when the implementation changes.
