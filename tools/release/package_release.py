"""Build, smoke-test and archive a portable Windows release (does not publish)."""
import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
import runpy
import subprocess
import sys
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[2]
INFO = runpy.run_path(str(ROOT / 'app' / 'pet' / 'version.py'))
NAME = INFO['PACKAGE_NAME']
VERSION = INFO['VERSION']


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def source_revision():
    # Source and EXE must describe the same saved code; ignored local data is never archived.
    if subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--'], cwd=ROOT).returncode:
        raise SystemExit('Commit tracked changes before packaging source and EXE together.')
    return tuple(subprocess.check_output(['git', 'rev-parse', ref], cwd=ROOT, text=True).strip()
                 for ref in ('HEAD', 'HEAD^{tree}'))


def source_archive(path, revision, guide):
    prefix = NAME + '-source/'
    subprocess.run(['git', 'archive', '--format=zip', '--prefix=' + prefix,
                    '--output=' + str(path), revision], cwd=ROOT, check=True)
    with ZipFile(path, 'a', compression=ZIP_DEFLATED, compresslevel=6) as package:
        package.writestr(prefix + '功能指引.txt', guide)
        package.writestr(prefix + '版本信息.txt', f'{NAME}\nSource commit: {revision}\n'.encode('utf-8-sig'))
        for name in package.namelist():
            parts = Path(name).parts
            if (any(part in ('.git', '.venv', '.user', '.local', 'versions', 'ForFmm', '__pycache__', 'build', 'dist') for part in parts)
                    or parts[1:3] == ('image', 'work')
                    or Path(name).name.startswith('.env')
                    or name.lower().endswith(('.exe', '.dll', '.pyd', '.log'))):
                raise SystemExit('Unexpected local/build data in source archive: ' + name)
        required = ('run.bat', 'setup.bat', 'app/main.py',
                    'app/pet/version.py', 'requirements/base.txt', 'tests/test_runtime.py',
                    'tools/release/build_windows.py', 'tools/release/package_release.py',
                    'docs/QUICK_GUIDE.md', '功能指引.txt')
        if not all(prefix + name in package.namelist() for name in required):
            raise SystemExit('Source archive is missing a required entry point or guide.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-build', action='store_true', help='validate an already built EXE')
    parser.add_argument('--output-dir', type=Path, default=Path('versions/user'), help='standard build output folder relative to the project')
    args = parser.parse_args()
    directory = (ROOT / args.output_dir).resolve()
    if directory.is_relative_to(ROOT / 'versions' / 'fmm') or directory.is_relative_to(ROOT / '.local' / 'for-fmm-source'):
        raise SystemExit('The standard packager cannot write into the local custom version.')
    revision, tree = source_revision()
    notes_path = ROOT / 'docs' / 'releases' / (VERSION + '.md')
    if not notes_path.is_file():
        raise SystemExit('Add version-specific release notes with current features before packaging.')
    notes = notes_path.read_text(encoding='utf-8')
    if not all(heading in notes for heading in ('## 当前功能', '## 本次更新', '## 下载与运行')):
        raise SystemExit('Release notes must describe current features, changes and downloads.')
    guide_text = (ROOT / 'docs' / 'QUICK_GUIDE.md').read_text(encoding='utf-8')
    guide = (NAME + '\n\n' + guide_text).encode('utf-8-sig')
    executable = directory / (NAME + '.exe')
    build_record = ROOT / '.local' / 'build' / 'portable-build.json'
    if not args.skip_build:
        subprocess.run([sys.executable, str(ROOT / 'tools' / 'release' / 'build_windows.py'),
                        '--output-dir', str(directory)], check=True, cwd=ROOT)
        build_record.write_text(json.dumps({'tree': tree, 'exe_sha256': digest(executable)}), encoding='utf-8')
    if not executable.is_file():
        raise SystemExit('Build the EXE before packaging.')
    if not build_record.is_file():
        raise SystemExit('No source/build record. Run a full package build first.')
    built = json.loads(build_record.read_text(encoding='utf-8'))
    if built != {'tree': tree, 'exe_sha256': digest(executable)}:
        raise SystemExit('EXE does not match this source tree. Run a full package build.')
    # Fail before archiving if the bundled images are absent or personal files leaked in.
    from PyInstaller.archive.readers import CArchiveReader
    names = [name.replace('\\', '/') for name in CArchiveReader(str(executable)).toc]
    expected = ['assets/sprites/' + path.name for path in (ROOT / 'app' / 'assets' / 'sprites').glob('*.png')]
    if not expected or not all(name in names for name in expected):
        raise SystemExit('The EXE is missing character sprites.')
    if any(Path(name).name.lower() in ('icuuc.dll', 'icudt78.dll') for name in names):
        raise SystemExit('A conflicting ICU DLL was bundled; rebuild with a clean PATH.')
    if any('/.user/' in '/' + name or name.endswith(('.log', 'settings.json')) for name in names):
        raise SystemExit('Personal files were found in the EXE.')
    # Exercise only the EXE in a fresh directory, with Python/Qt development paths removed.
    validation = ROOT / '.local' / 'build' / 'portable-validation'
    validation.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='独立运行-', dir=validation) as folder:
        isolated = Path(folder)
        copied = isolated / executable.name
        shutil.copy2(executable, copied)
        env = {key: value for key, value in os.environ.items()
               if not key.upper().startswith(('PYTHON', 'PYSIDE', 'QT_', 'VIRTUAL_ENV'))}
        windows = Path(os.environ.get('SystemRoot', 'C:/Windows'))
        env['PATH'] = str(windows / 'System32') + os.pathsep + str(windows)
        subprocess.run([str(copied), '--smoke-test'], cwd=isolated, env=env, check=True, timeout=90)
        log = isolated / '.user' / 'runtime.log'
        if not log.is_file() or 'Source build started' not in log.read_text(encoding='utf-8'):
            raise SystemExit('The isolated EXE did not finish application startup.')
    print('Isolated EXE startup passed without external Python/Qt paths.', flush=True)
    archive = directory / (NAME + '.zip')
    with ZipFile(archive, 'w', compression=ZIP_DEFLATED, compresslevel=6) as package:
        package.write(executable, arcname=NAME + '/' + executable.name)
        package.writestr(NAME + '/功能指引.txt', guide)
    source = directory / (NAME + '-source.zip')
    source_archive(source, revision, guide)
    guide_path = directory / (NAME + '-Guide.txt')
    guide_path.write_bytes(guide)
    (ROOT / '.local' / 'build' / 'release-notes.md').write_text(notes, encoding='utf-8')
    if source_revision() != (revision, tree):
        raise SystemExit('Source changed during packaging; rerun from a saved checkpoint.')
    checksum = directory / (NAME + '-SHA256SUMS.txt')
    digests = []
    artifacts = (executable, archive, source, guide_path)
    for path in artifacts:
        digests.append(digest(path) + '  ' + path.name + '\n')
    checksum.write_text(''.join(digests), encoding='ascii')
    for path in (*artifacts, checksum):
        print(f'{path.name}: {path.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
