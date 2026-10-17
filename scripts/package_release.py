"""Build, smoke-test and archive a portable Windows release (does not publish)."""
import argparse
import hashlib
import os
import shutil
import tempfile
from pathlib import Path
import runpy
import subprocess
import sys
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent.parent
INFO = runpy.run_path(str(ROOT / 'deskpet' / 'deskpet' / 'pet' / 'version.py'))
NAME = INFO['PACKAGE_NAME']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-build', action='store_true', help='validate an already built EXE')
    args = parser.parse_args()
    if not args.skip_build:
        subprocess.run([sys.executable, str(ROOT / 'scripts' / 'build_windows.py')], check=True, cwd=ROOT)
    directory = ROOT / 'dist'
    executable = directory / (NAME + '.exe')
    if not executable.is_file():
        raise SystemExit('Build the EXE before packaging.')
    # Fail before archiving if the bundled images are absent or personal files leaked in.
    from PyInstaller.archive.readers import CArchiveReader
    names = [name.replace('\\', '/') for name in CArchiveReader(str(executable)).toc]
    expected = ['assets/sprites/' + path.name for path in (ROOT / 'deskpet' / 'deskpet' / 'assets' / 'sprites').glob('*.png')]
    if not expected or not all(name in names for name in expected):
        raise SystemExit('The EXE is missing character sprites.')
    if any(Path(name).name.lower() in ('icuuc.dll', 'icudt78.dll') for name in names):
        raise SystemExit('A conflicting ICU DLL was bundled; rebuild with a clean PATH.')
    if any('/.user/' in '/' + name or name.endswith(('.log', 'settings.json')) for name in names):
        raise SystemExit('Personal files were found in the EXE.')
    # Exercise only the EXE in a fresh directory, with Python/Qt development paths removed.
    validation = ROOT / 'build' / 'portable-validation'
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
        package.writestr(NAME + '/使用说明.txt', '\ufeff' + (ROOT / 'docs' / 'PORTABLE.md').read_text(encoding='utf-8'))
    checksum = directory / (NAME + '-SHA256SUMS.txt')
    digests = []
    for path in (executable, archive):
        with path.open('rb') as stream:
            digests.append(hashlib.file_digest(stream, 'sha256').hexdigest() + '  ' + path.name + '\n')
    checksum.write_text(''.join(digests), encoding='ascii')
    for path in (executable, archive, checksum):
        print(f'{path.name}: {path.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
