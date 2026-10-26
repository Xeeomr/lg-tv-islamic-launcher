import base64
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
STATE = '/media/developer/apps/usr/palm/applications/com.local.nativehome/state'

class TransferTests(unittest.TestCase):
    def run_setup(self, fault='', eim='success'):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            shutil.copytree(ROOT / 'scripts', p / 'scripts')
            (p / 'launcher').mkdir()
            (p / 'launcher/apps.js').write_text('var apps = {"apps": [{"id":"example.app"}]};')
            (p / '.lgtv-key.json').write_text('{"test-tv":"SECRET-TEST-KEY"}')
            state = p / 'state'; state.mkdir()
            key = state / 'ssap-key.json'; key.write_text('previous key'); key.chmod(0o640)
            bindir = p / 'bin'; bindir.mkdir()
            cli = bindir / 'ares-novacom'
            cli.write_text('''#!/usr/bin/env python3
import os, subprocess, sys
command = sys.argv[sys.argv.index('--run') + 1]
if os.environ['FAULT'] == 'transport':
    print(command, file=sys.stderr)
    sys.exit(1)
if 'luna-send-pub' in command:
    mode=os.environ['EIM_TEST']
    if mode=='success': print('{"returnValue":true}')
    elif mode=='denied': print('{"returnValue":false,"errorText":"denied"}')
    elif mode=='nested': print('{"result":{"returnValue":true}}')
    sys.exit(1 if mode=='command-error' else 0)
command = command.replace(os.environ['REMOTE_STATE'], os.environ['TEST_STATE'])
print('[Info] test connection', flush=True)
sys.exit(subprocess.call(['sh', '-c', command]))
'''); cli.chmod(0o755)
            stat = bindir / 'stat'
            stat.write_text("#!/usr/bin/env python3\nimport os,sys\nprint(oct(os.stat(sys.argv[-1]).st_mode & 0o7777)[2:])\n"); stat.chmod(0o755)
            digest = bindir / 'sha256sum'
            digest.write_text("#!/usr/bin/env python3\nimport hashlib,sys\np=sys.argv[-1]\nprint(hashlib.sha256(open(p,'rb').read()).hexdigest()+'  '+p)\n"); digest.chmod(0o755)
            chmod = bindir / 'chmod'
            chmod.write_text('''#!/bin/sh
case "$FAULT" in
 chmod) exit 1;;
 mode) exit 0;;
esac
exec /bin/chmod "$@"
'''); chmod.chmod(0o755)
            decoder = bindir / 'base64'
            decoder.write_text('''#!/usr/bin/env python3
import base64, os, sys
raw=sys.stdin.buffer.read()
if '-d' in sys.argv:
    if os.environ['FAULT']=='decode': sys.exit(1)
    raw=base64.b64decode(raw)
    if os.environ['FAULT']=='corrupt': raw=b'x'*len(raw)
    sys.stdout.buffer.write(raw)
else: sys.stdout.buffer.write(base64.b64encode(raw)+b'\\n')
'''); decoder.chmod(0o755)
            env = dict(os.environ, PATH=str(bindir)+':'+os.environ['PATH'], TV_HOST='test-tv',
                       FAULT=fault, EIM_TEST=eim, REMOTE_STATE=STATE, TEST_STATE=str(state))
            result = subprocess.run(['bash', 'scripts/configure-tv.sh'], cwd=p, env=env, capture_output=True, text=True)
            output=result.stdout+result.stderr
            self.assertNotIn('SECRET-TEST-KEY', output)
            self.assertNotIn(base64.b64encode(b'{"key": "SECRET-TEST-KEY"}').decode(), output)
            if fault:
                self.assertNotEqual(result.returncode, 0, output)
                self.assertEqual(key.read_text(), 'previous key')
            else:
                self.assertEqual(result.returncode, 0, output)
                self.assertEqual(key.read_text(), '{"key": "SECRET-TEST-KEY"}')
                self.assertEqual(key.stat().st_mode & 0o777, 0o640)
                self.assertEqual((state/'apps.json').stat().st_mode & 0o777, 0o644)
            self.assertEqual(sorted(x.name for x in state.iterdir()), ['ssap-key.json'] if fault else ['apps.json','ssap-key.json'])

            return output

    def test_eim_empty_is_unknown(self):
        output=self.run_setup(eim='empty')
        self.assertIn('no reply from the dev shell',output)
        self.assertNotIn('Startup will rely',output)

    def test_eim_explicit_denial(self):
        self.assertIn('EIM registration rejected',self.run_setup(eim='denied'))

    def test_eim_command_failure(self):
        self.assertIn('EIM command failed',self.run_setup(eim='command-error'))

    def test_eim_nested_success_is_not_confirmation(self):
        output=self.run_setup(eim='nested')
        self.assertNotIn('Early input restoration registered',output)
        self.assertIn('unrecognized reply',output)

    def test_success(self): self.run_setup()
    def test_chmod_failure(self): self.run_setup('chmod')
    def test_wrong_mode(self): self.run_setup('mode')
    def test_same_length_corruption(self): self.run_setup('corrupt')
    def test_decoder_failure(self): self.run_setup('decode')
    def test_transport_error_does_not_print_key(self): self.run_setup('transport')

if __name__ == '__main__': unittest.main()
