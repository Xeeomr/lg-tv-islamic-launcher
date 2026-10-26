"""Native desktop distributions. Packages never contain local TV profiles."""
import os
import json
from pathlib import Path
import platform
import plistlib
import shutil
import subprocess
import sys


def deb_tree(root, frozen, version, destination):
    """Create a relocatable package tree; dpkg-deb handles the archive format."""
    destination = Path(destination)
    if destination.exists():
        shutil.rmtree(destination)
    application = destination / 'opt/clean-your-tv'
    application.parent.mkdir(parents=True)
    shutil.copytree(frozen, application, symlinks=True)
    (application / 'cytv-desktop').chmod(0o755)
    desktop = destination / 'usr/share/applications/cytv.desktop'
    desktop.parent.mkdir(parents=True)
    desktop.write_text('[Desktop Entry]\nType=Application\nName=Clean Your TV\nComment=Set up Clean Your TV on your LG webOS TV\nExec=/opt/clean-your-tv/cytv-desktop\nIcon=cytv\nTerminal=false\nCategories=Utility;\nStartupNotify=true\n', encoding='utf-8')
    icon = destination / 'usr/share/icons/hicolor/256x256/apps/cytv.png'
    icon.parent.mkdir(parents=True)
    shutil.copyfile(root / 'assets/icons/installer-256.png', icon)
    docs = destination / 'usr/share/doc/cytv-desktop'
    docs.mkdir(parents=True)
    shutil.copyfile(root / 'LICENSE', docs / 'copyright')
    shutil.copyfile(root / 'THIRD_PARTY_NOTICES.md', docs / 'THIRD_PARTY_NOTICES.md')
    control = destination / 'DEBIAN/control'
    control.parent.mkdir(parents=True)
    control.write_text(f'''Package: cytv-desktop
Version: {version}
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Clean Your TV <noreply@github.com>
Homepage: https://github.com/Razdva122/clean-your-tv-lg-webos
Depends: libc6 (>= 2.34), libstdc++6, libegl1, libgl1, libopengl0, libglib2.0-0, libdbus-1-3, libfontconfig1, libxkbcommon0, libxkbcommon-x11-0, libxcb-cursor0, libxcb-icccm4, libxcb-keysyms1, libxcb-shape0, libxcb-xinerama0, libxcb-render-util0, libx11-xcb1, libxcb-randr0, libxcb-render0, libxcb-shm0, libxcb-sync1, libxcb-xfixes0, libxcb1, libx11-6, fonts-dejavu-core
Description: Clean Your TV graphical setup wizard
 Install and maintain Root and No-root editions on an LG webOS TV.
 Python and the graphical runtime are included. No terminal is required.
''', encoding='utf-8')
    return destination


def build_desktop(root, payload, environment, version):
    if sys.platform not in ('darwin', 'linux', 'win32'):
        return
    if sys.platform == 'win32' and platform.machine().lower() not in ('amd64', 'x86_64'):
        raise RuntimeError('The Windows desktop package currently targets x64 only.')
    name = 'cytv' if sys.platform == 'darwin' else 'cytv-desktop'
    output = root / 'dist/desktop'
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir', '--windowed',
               '--name', name, '--paths', str(root), '--add-data', str(payload) + os.pathsep + 'payload',
               '--workpath', str(root / 'build/cytv/desktop-freeze'), '--specpath', str(root / 'build/cytv/desktop-spec'),
               '--distpath', str(output)]
    if sys.platform == 'darwin':
        iconset = root / 'build/cytv/cytv.iconset'
        iconset.mkdir(parents=True, exist_ok=True)
        for size in (16, 32, 128, 256, 512):
            for scale in (1, 2):
                target = iconset / (f'icon_{size}x{size}' + ('@2x' if scale == 2 else '') + '.png')
                subprocess.run(['sips', '-z', str(size * scale), str(size * scale),
                                str(root / 'assets/icons/installer.png'), '--out', str(target)],
                               check=True, stdout=subprocess.DEVNULL)
        icon = iconset.with_suffix('.icns')
        subprocess.run(['iconutil', '-c', 'icns', str(iconset), '-o', str(icon)], check=True)
        command += ['--osx-bundle-identifier', 'org.cleanyourtv.cytv', '--icon', str(icon)]
    elif sys.platform == 'win32':
        command += ['--icon', str(root / 'assets/icons/installer.ico')]
    command += [str(root / 'cytv/desktop_entry.py')]
    subprocess.run(command, cwd=root, env=environment, check=True)
    if sys.platform == 'darwin':
        bundle = output / 'cytv.app'
        info_path = bundle / 'Contents/Info.plist'
        with info_path.open('rb') as stream:
            info = plistlib.load(stream)
        info.update(CFBundleDisplayName='Clean Your TV', CFBundleShortVersionString=version,
                    CFBundleVersion=version, NSLocalNetworkUsageDescription='Find and connect to your LG webOS TV to install Clean Your TV.',
                    NSHighResolutionCapable=True, LSMinimumSystemVersion='13.0')
        with info_path.open('wb') as stream:
            plistlib.dump(info, stream)
        # Re-sign after updating Info.plist. Release signing/notarization can replace this ad-hoc signature.
        subprocess.run(['codesign', '--force', '--deep', '--sign', '-', str(bundle)], check=True)
        executable = bundle / 'Contents/MacOS/cytv'
        subprocess.run([str(executable), '--check-payload'], check=True)
        subprocess.run([str(executable), '--smoke-test'], env=dict(os.environ, QT_QPA_PLATFORM='offscreen'), check=True)
        archive = root / 'dist' / ('cytv-macos-' + ('arm64' if platform.machine() == 'arm64' else 'x64') + '.zip')
        subprocess.run(['ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', str(bundle), str(archive)], check=True)
    elif sys.platform == 'win32':
        frozen = output / name
        executable = frozen / (name + '.exe')
        subprocess.run([str(executable), '--check-payload'], check=True)
        subprocess.run([str(executable), '--smoke-test'], env=dict(os.environ, QT_QPA_PLATFORM='offscreen'), check=True)
        (frozen / 'version.json').write_text(json.dumps({
            'cytv': version, 'platform': 'windows-x64', 'entrypoint': 'cytv-desktop.exe'}), encoding='utf-8')
        archive = root / 'dist/cytv-windows-x64-desktop.zip'
        shutil.make_archive(str(archive.with_suffix('')), 'zip', root_dir=output, base_dir=name)
    else:
        if platform.machine() not in ('x86_64', 'AMD64'):
            raise RuntimeError('The desktop .deb currently targets x64 only.')
        frozen = output / name
        subprocess.run([str(frozen / name), '--check-payload'], check=True)
        subprocess.run([str(frozen / name), '--smoke-test'], env=dict(os.environ, QT_QPA_PLATFORM='offscreen'), check=True)
        tree = deb_tree(root, frozen, version, root / 'build/cytv/deb')
        archive = root / 'dist/cytv-linux-x64.deb'
        subprocess.run(['dpkg-deb', '--build', '--root-owner-group', str(tree), str(archive)], check=True)
    print('Desktop package:', archive)
