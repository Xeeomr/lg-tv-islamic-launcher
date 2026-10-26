import io
import json
import os
import shutil
import sys
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]

class PackageTests(unittest.TestCase):
    def test_source_build_reuses_published_helper_without_compiling_it(self):
        with tempfile.TemporaryDirectory(prefix='pinned helper ') as tmp:
            root = Path(tmp)
            for directory in ('scripts', 'native/app', 'native/published', 'launcher'):
                (root/directory).mkdir(parents=True)
            for name in ('build.sh', 'build-cytv.py', 'tv_web_build.py', 'compile-tv-web.cjs', 'helper_build.py', 'compile-helper.cjs'):
                shutil.copy(ROOT/'scripts'/name, root/'scripts'/name)
            shutil.copy(ROOT/'package.json', root/'package.json')
            helper = 'com.local.nativehome_0.6.17_arm.ipk'
            shutil.copy(ROOT/'native/published'/helper, root/'native/published'/helper)
            (root/'native/app/appinfo.json').write_text(json.dumps({'id':'com.local.nativehome','version':'0.6.17'}))
            (root/'launcher/index.html').write_text('<html><head></head><body></body></html>')
            zig = root/'zig'
            zig.write_text('#!/bin/sh\nexit 99\n')
            zig.chmod(0o755)
            packager = root/'packager'
            packager.write_text('#!/bin/sh\ntest "$1" = build/home-app\n')
            packager.chmod(0o755)
            env = dict(os.environ, ZIG=str(zig), ARES_PACKAGE=str(packager),
                       PYTHONPATH=str(ROOT), NODE_PATH=str(ROOT/'node_modules'))
            result = subprocess.run(['bash', 'scripts/build.sh'], cwd=root, env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertEqual((root/'dist'/helper).read_bytes(), (ROOT/'native/published'/helper).read_bytes())

    def test_build_repairs_current_metadata_package_and_preserves_stale_package(self):
        with tempfile.TemporaryDirectory(prefix='helper build ') as tmp:
            root = Path(tmp)
            (root/'scripts').mkdir()
            for name in ('build.sh', 'build-cytv.py', 'fix-package-data.py', 'tv_web_build.py', 'compile-tv-web.cjs', 'helper_build.py', 'compile-helper.cjs'):
                shutil.copy(ROOT/'scripts'/name, root/'scripts'/name)
            shutil.copy(ROOT/'package.json', root/'package.json')
            for directory in ('native/app', 'native/service', 'launcher'):
                path = root/directory
                path.mkdir(parents=True)
                (path/'example.js').write_text('// fixture')
                (path/'icon.png').write_bytes(b'fixture')
                (path/'appinfo.json').write_text(json.dumps({
                    'id': 'com.local.nativehome' if directory == 'native/app' else 'com.gathin.tvhome',
                    'version': '9.8.7'}))
            shutil.copy(ROOT/'native/app/state-permissions.js', root/'native/app/state-permissions.js')
            (root/'native/app/vendor').mkdir()
            (root/'bin').mkdir()
            zig = root/'bin/zig'
            zig.write_text('#!/bin/sh\nfor arg do target="$arg"; done\n: > "$target"\n')
            zig.chmod(0o755)
            packager = root/'bin/ares-package'
            packager.write_text('#!' + sys.executable + "\n" + '''
import json, sys
from pathlib import Path
from cytv.package import ipk
app = json.loads((Path(sys.argv[1])/'appinfo.json').read_text())
helper = app['id'] == 'com.local.nativehome'
files = {'usr/palm/applications/'+app['id']+'/state/.keep': b''}
if helper:
    assert (Path(sys.argv[2])/'state-permissions.js').read_bytes() == (Path(sys.argv[1])/'state-permissions.js').read_bytes()
    files['usr/palm/services/com.local.nativehome.service/state/.keep'] = b''
arch = 'arm' if helper else 'all'
(Path('dist')/(app['id']+'_'+app['version']+'_'+arch+'.ipk')).write_bytes(
    ipk(app['id'], app['version'], files, architecture=arch))
''')
            packager.chmod(0o755)
            (root/'dist').mkdir()
            stale = root/'dist/com.local.nativehome_0.6.14_arm.ipk'
            stale.write_bytes(b'old package must stay untouched')
            env = dict(os.environ, NODE_PATH=str(ROOT/'node_modules'), PATH=str(root/'bin')+os.pathsep+os.environ['PATH'],
                       ZIG=str(zig), ARES_PACKAGE=str(packager), PYTHONPATH=str(ROOT))
            result = subprocess.run(['bash', 'scripts/build.sh'], cwd=root, env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertEqual(stale.read_bytes(), b'old package must stay untouched')
            sys.path.insert(0, str(ROOT))
            from cytv.package import read_ar
            data = read_ar((root/'dist/com.local.nativehome_9.8.7_arm.ipk').read_bytes())['data.tar.gz']
            with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
                for name in ('usr/palm/applications/com.local.nativehome/state',
                             'usr/palm/services/com.local.nativehome.service/state'):
                    entry = archive.getmember(name)
                    self.assertEqual((entry.uid, entry.gid, entry.mode), (5999, 5000, 0o770))

    def test_archive_members_and_state_permissions(self):
        payload = io.BytesIO()
        names = ['usr/palm/applications/com.local.nativehome/state',
                 'usr/palm/services/com.local.nativehome.service/state']
        with tarfile.open(fileobj=payload, mode='w:gz') as archive:
            for name in names:
                entry = tarfile.TarInfo(name); entry.type = tarfile.DIRTYPE
                entry.mode = 0o775; archive.addfile(entry)
            entry = tarfile.TarInfo('usr/palm/example.txt'); entry.size = 5
            archive.addfile(entry, io.BytesIO(b'hello'))
        members = [('debian-binary', b'2.0\n'), ('control.tar.gz', b'odd'), ('data.tar.gz', payload.getvalue())]
        raw = bytearray(b'!<arch>\n')
        for name, data in members:
            header = f'{name+"/":<16}{0:<12}{0:<6}{0:<6}{"100644":<8}{len(data):<10}`\n'.encode()
            raw += header + data + (b'\n' if len(data)%2 else b'')
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp)/'test.ipk'; package.write_bytes(raw)
            subprocess.run(['python3', str(ROOT/'scripts/fix-package-data.py'), str(package)], check=True, capture_output=True)
            data = package.read_bytes(); self.assertEqual(data[:8], b'!<arch>\n')
            offset=8; found={}
            while offset < len(data):
                header=data[offset:offset+60]; self.assertEqual(header[58:], b'`\n')
                size=int(header[48:58]); name=header[:16].decode().strip().rstrip('/')
                found[name]=data[offset+60:offset+60+size]
                self.assertEqual(len(found[name]), size)
                offset += 60+size+(size%2)
            self.assertEqual(offset, len(data))
            self.assertEqual(list(found), [name for name,_ in members])
            self.assertEqual(found['debian-binary'], b'2.0\n')
            self.assertEqual(found['control.tar.gz'], b'odd')
            with tarfile.open(fileobj=io.BytesIO(found['data.tar.gz']), mode='r:gz') as archive:
                for name in names:
                    entry=archive.getmember(name)
                    self.assertEqual((entry.uid,entry.gid,entry.mode), (5999,5000,0o770))
                    self.assertEqual((entry.uname,entry.gname), ('prisoner','jailer'))
                self.assertEqual(archive.extractfile('usr/palm/example.txt').read(), b'hello')

if __name__ == '__main__': unittest.main()
