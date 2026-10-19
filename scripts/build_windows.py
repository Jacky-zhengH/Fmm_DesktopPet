"""Build a versioned Windows portable package without copying personal data."""
import argparse
import os
from pathlib import Path
import runpy
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
VERSION_INFO = runpy.run_path(str(ROOT / 'app' / 'pet' / 'version.py'))
VERSION = VERSION_INFO['VERSION']
NAME = VERSION_INFO['PACKAGE_NAME']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--onedir', action='store_true', help='build an unpacked folder for debugging')
    parser.add_argument('--output-dir', type=Path, default=Path('dist'), help='output folder relative to the project')
    args = parser.parse_args()
    directory = (ROOT / args.output_dir).resolve()
    if sys.platform != 'win32':
        raise SystemExit('Build the Windows package on Windows.')
    build = ROOT / 'build'
    build.mkdir(exist_ok=True)
    version_file = build / 'windows_version.txt'
    numbers = tuple(map(int, VERSION.split('.'))) + (0,)
    version_file.write_text(f'''VSVersionInfo(
  ffi=FixedFileInfo(filevers={numbers}, prodvers={numbers}, mask=0x3f,
    flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('FileDescription', 'Fmm DesktopPet'),
    StringStruct('FileVersion', '{VERSION}'),
    StringStruct('InternalName', '{NAME}'),
    StringStruct('OriginalFilename', '{NAME}.exe'),
    StringStruct('ProductName', 'Fmm DesktopPet'),
    StringStruct('ProductVersion', '{VERSION}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])])
''', encoding='utf-8')
    # Avoid collecting unrelated DLLs from tools such as Poppler on the developer PATH.
    windows = Path(os.environ.get('SystemRoot', 'C:/Windows'))
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith(('PYTHON', 'PYSIDE', 'QT_'))}
    env['PATH'] = str(windows / 'System32') + os.pathsep + str(windows)
    subprocess.run([
        sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
        '--onedir' if args.onedir else '--onefile', '--windowed',
        '--name', NAME, '--distpath', str(directory),
        '--workpath', str(build / 'pyinstaller'), '--specpath', str(build),
        '--version-file', str(version_file),
        '--add-data', f"{ROOT / 'app' / 'assets'};assets",
        str(ROOT / 'app' / 'main.py'),
    ], cwd=ROOT, env=env, check=True)
    output = directory / NAME / (NAME + '.exe') if args.onedir else directory / (NAME + '.exe')
    print(output)


if __name__ == '__main__':
    main()
