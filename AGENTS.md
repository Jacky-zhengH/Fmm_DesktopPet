# fmm project workflow

- Preserve the private GitHub repository `Jacky-zhengH/Fmm_DesktopPet`; do not change visibility.
- Keep `main` as the tested baseline. Subsequent runtime changes use a focused branch, associated Issue and PR. In addition to `fix/`, `feat/`, or `phase/`, user-named version branches such as `ver0.1.0` are allowed.
- Version families follow the user's stages: first stage is `0.1.x`, next stage is `0.2.x`. The user alone decides when to enter `1.0.x`. A branch named `ver0.1.0` is distinct from the existing immutable `v0.1.0` tag; do not recreate a tag or publish a release without acceptance.
- Commit completed units with clear messages; never force-push shared history or rewrite accepted release tags.
- Each accepted stage has an annotated version tag, CHANGELOG entry and validation notes. Tagging is done after required tests and user acceptance, not merely because a milestone exists.
- Before changing runtime behavior, establish a clean checkpoint for existing user changes. Do not discard unrelated changes.
- The common manual test entry is the root `run.bat`. The old portable EXE is a preserved local artifact.
- Run `.venv/Scripts/python.exe -m unittest discover -s deskpet/deskpet/tests -v` for relevant runtime changes. On CI use the selected Python interpreter directly.
- Keep `.venv`, `.user`, logs, credentials, build output and desktop screenshots out of Git. Keep source PNGs and intentionally provided character references versioned.
- Do not modify original character art while fixing layout math. Asset changes require explicit before/after visual review.
- Record planned work separately from implemented behavior; update README/roadmap when the implementation changes.

- Release titles and portable package names use `Fmm-DesktopPet-vx.x.x`; annotated Git tags keep `vx.x.x`. Read the version from `deskpet/deskpet/pet/version.py`. Back up the original portable EXE before replacing its compatibility entry.
