"""Private interpreter binding, immutable evidence, and legacy recovery."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

class BindingTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('binding_test', ROOT/'python_binding.py')
        self.b = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.b)
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.state = self.root/'state'; self.state.mkdir(mode=0o700)

    def write(self, path, raw, mode=0o600):
        path.write_bytes(raw); path.chmod(mode)

    def managed(self):
        slot = self.root/'python'/self.b.ARCHIVE_SHA256
        executable = slot/'bin/python3.13'; executable.parent.mkdir(parents=True)
        executable.write_bytes(b'python binary'); executable.chmod(0o755)
        library = slot/'lib/stdlib.py'; library.parent.mkdir(); library.write_bytes(b'stdlib')
        files = {'bin/python3.13': hashlib.sha256(b'python binary').hexdigest(), 'lib/stdlib.py': hashlib.sha256(b'stdlib').hexdigest()}
        (slot/'.cytv-runtime.json').write_text(json.dumps({'schema':1, 'archive_sha256': self.b.ARCHIVE_SHA256, 'files': files}))
        self.addCleanup(patch.stopall)
        patch.object(self.b, 'MANAGED_ROOT', self.root/'python').start()
        original = self.b._directory
        patch.object(self.b, '_directory', side_effect=lambda path: original(path) if path.is_relative_to(self.root) else None).start()
        patch.object(self.b, 'EXPECTED_UID', os.getuid()).start()
        patch.object(self.b.sys, 'executable', str(executable)).start()
        return executable

    def test_host_and_environment_cannot_select_arbitrary_python(self):
        with patch.dict(os.environ, {'CYTV_PYTHON':'/tmp/evil'}), patch.object(self.b.sys, 'executable','/tmp/python3'):
            self.assertEqual(self.b.current_executable(), '/usr/bin/python3')
        with self.assertRaises(ValueError): self.b.launcher_bytes('/tmp/evil')

    def test_legacy_state_remains_system_python_without_writes(self):
        self.assertEqual(self.b.verify_binding(self.state), '/usr/bin/python3')
        self.assertEqual(self.b.install_launcher(self.state, self.write), '/usr/bin/python3')
        self.assertEqual(list(self.state.iterdir()), [])

    def test_managed_binding_persists_literal_exec_and_rechecks_full_runtime(self):
        executable = self.managed()
        self.assertEqual(self.b.install_launcher(self.state, self.write), str(executable))
        launcher = self.state/'python-launcher'
        self.assertEqual(launcher.read_bytes(), ('#!/bin/sh\nunset PYTHONHOME PYTHONPATH\nexport PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1\nexec '+str(executable)+' "$@"\n').encode())
        self.assertEqual(launcher.stat().st_mode & 0o777, 0o700)
        self.assertEqual(self.b.verify_binding(self.state), str(executable))
        self.assertEqual(self.b.command(self.state), str(launcher))
        (executable.parents[1]/'lib/stdlib.py').write_bytes(b'corrupt')
        with self.assertRaises(ValueError): self.b.verify_binding(self.state)

    def test_foreign_launcher_is_never_adopted(self):
        self.managed(); (self.state/'python-launcher').write_bytes(b'foreign')
        with self.assertRaises(ValueError): self.b.install_launcher(self.state,self.write)
        self.assertEqual((self.state/'python-launcher').read_bytes(), b'foreign')

    def test_binding_rejects_symlink_and_writable_runtime(self):
        executable = self.managed(); executable.chmod(0o777)
        with self.assertRaises(ValueError): self.b.install_launcher(self.state,self.write)
        executable.chmod(0o755); executable.unlink(); executable.symlink_to('/usr/bin/python3')
        with self.assertRaises(ValueError): self.b.install_launcher(self.state,self.write)

    def test_recovery_proof_requires_persisted_binding_evidence(self):
        self.managed(); self.b.install_launcher(self.state,self.write)
        sys.path.insert(0,str(ROOT/'runtime'))
        import device_adapter as d
        spec=importlib.util.spec_from_file_location('binding_recovery',ROOT/'runtime/provision.py')
        recovery=importlib.util.module_from_spec(spec);spec.loader.exec_module(recovery)
        runtime=self.state/'runtime';runtime.mkdir()
        module=runtime/'provision.py';module.write_bytes(b'fixture')
        callback=self.state/'boot.sh';callback.write_text(str(runtime/'cli.py')+' boot')
        helper=self.state/'python_binding.py';helper.write_bytes(b'fixture helper')
        paths=(module,callback,helper,self.state/'python-launcher',self.state/'python-runtime.json')
        proof={'version':1,'mode':'recovery-only','boot_callback':str(callback),
               'files':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
        self.write(self.state/'recovery-provision.json',json.dumps(proof).encode())
        with patch.object(d,'STATE',self.state),patch.object(d,'EXPECTED_UID',os.getuid()),patch.object(d,'trusted_dir'),patch.object(d,'python_binding',self.b),patch.object(recovery,'__file__',str(module)):
            self.assertTrue(recovery.verify()['integrity_verified'])
            proof['files'].pop(str(self.state/'python-runtime.json'))
            self.write(self.state/'recovery-provision.json',json.dumps(proof).encode())
            with self.assertRaisesRegex(ValueError,'Incomplete'):recovery.verify()

    def test_existing_binding_is_retained_when_new_process_uses_system_python(self):
        executable = self.managed(); self.b.install_launcher(self.state,self.write)
        with patch.object(self.b.sys, 'executable', '/usr/bin/python3'):
            self.assertEqual(self.b.install_launcher(self.state,self.write), str(executable))
        (self.state/'python-launcher').write_bytes(b'changed')
        with self.assertRaises(ValueError): self.b.install_launcher(self.state,self.write)


class RuntimeBindingTests(unittest.TestCase):
    def test_guardian_identity_uses_selected_interpreter(self):
        import sys
        sys.path.insert(0, str(ROOT/'runtime'))
        import device_adapter as d
        with tempfile.TemporaryDirectory() as tmp:
            proc = Path(tmp)/'123'; proc.mkdir()
            guardian = str(ROOT/'runtime/guardian_device.py')
            selected = '/var/lib/clean-your-tv-python/4a71641c8d5536175e404a961624e8656eba30e97b5026f6bd7dc31e4bbeaaea/bin/python3.13'
            (proc/'cmdline').write_bytes((selected+'\0'+guardian+'\0test\0').encode())
            (proc/'stat').write_text('123 (python3) S '+'0 '*18+'42 0')
            journal={'transaction':'test','state':'pending','deadline':101}
            ready={'transaction':'test','pid':123,'deadline':101,'start_ticks':'42'}
            with patch.object(d,'PROC',Path(tmp)), patch.object(d,'EXPECTED_UID',os.getuid()), patch.object(d,'safe_json',return_value=ready), patch.object(d.time,'monotonic',return_value=100), patch.object(d,'current_executable',return_value=selected):
                self.assertTrue(d.active_guardian(journal))
                (proc/'cmdline').write_bytes(('/usr/bin/python3\0'+guardian+'\0test\0').encode())
                self.assertFalse(d.active_guardian(journal))

    def test_managed_startup_receipt_survives_legacy_remove(self):
        spec=importlib.util.spec_from_file_location('binding_hook',ROOT/'startup_hook.py')
        hook=importlib.util.module_from_spec(spec);spec.loader.exec_module(hook)
        with tempfile.TemporaryDirectory() as tmp:
            state=Path(tmp); target=state/'boot-hook'
            def write(path,raw,mode=0o600):
                path.write_bytes(raw.encode() if isinstance(raw,str) else raw);path.chmod(mode)
            with patch.object(hook,'STATE',state),patch.object(hook,'HOOK',target),patch.object(hook,'python_command',return_value=str(state/'python-launcher')):
                # Ownership checks on host ancestors are already tested by binding tests.
                with patch.object(hook,'trusted_hook_directory'):
                    hook.install(Path.read_bytes,write)
                self.assertIn((str(state/'service/boot-recover.sh')+' mark').encode(),target.read_bytes())
                hook.remove(Path.read_bytes)
                self.assertFalse(target.exists())
                self.assertTrue((state/'startup-hook.json').exists())

class BootBindingTests(unittest.TestCase):
    def test_node_service_validates_launcher_receipt_and_pinned_executable(self):
        import subprocess
        result=subprocess.run(['node',str(ROOT/'service/test-python-binding.js')],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_boot_and_marker_reject_launcher_before_touch_marker(self):
        import shutil
        import subprocess
        for entrypoint in ('boot','mark'):
            for fault in ('altered','missing-receipt','mismatched-receipt','symlink','writable'):
                with self.subTest(entrypoint=entrypoint,fault=fault),tempfile.TemporaryDirectory() as tmp:
                    state=Path(tmp).resolve(); marker=state/'executed'
                    script=(ROOT/'service/boot-recover.sh').read_text().replace('/var/lib/clean-your-tv-root',str(state)).replace('/usr/bin/node',shutil.which('node'))
                    boot=state/'boot';boot.write_text(script)
                    helper=ROOT/'python_boot.js'
                    if helper.exists(): (state/'python_boot.js').write_bytes(helper.read_bytes())
                    launcher=state/'python-launcher'
                    launcher.write_text('#!/bin/sh\ntouch '+str(marker)+'\n');launcher.chmod(0o700)
                    receipt=state/'python-runtime.json';receipt.write_text('{}')
                    if fault=='missing-receipt':receipt.unlink()
                    if fault=='symlink':
                        actual=state/'foreign';launcher.rename(actual);launcher.symlink_to(actual)
                    if fault=='writable':launcher.chmod(0o777)
                    result=subprocess.run(['/bin/sh',str(boot),entrypoint],capture_output=True,text=True)
                    self.assertNotEqual(result.returncode,0,result.stderr)
                    self.assertFalse(marker.exists(),'launcher ran before binding verification')
                    self.assertIn('python-binding',result.stderr)


class HostSelectionTests(unittest.TestCase):
    def test_manual_controller_only_accepts_pinned_interpreters(self):
        spec=importlib.util.spec_from_file_location('binding_setup',ROOT/'setup.py')
        setup=importlib.util.module_from_spec(spec);spec.loader.exec_module(setup)
        calls=[]
        def run(argv,**kwargs): calls.append(argv)
        selected='/var/lib/clean-your-tv-python/4a71641c8d5536175e404a961624e8656eba30e97b5026f6bd7dc31e4bbeaaea/bin/python3.13'
        setup.execute('status','living-room',run=run,python=selected)
        self.assertEqual(calls[-1][-1],'unset PYTHONHOME PYTHONPATH; export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1; exec '+selected+' /var/lib/clean-your-tv-root/deploy.py status')
        with self.assertRaises(ValueError): setup.execute('status','living-room',run=run,python='/tmp/evil')
        self.assertEqual(len(calls),1)


if __name__ == '__main__': unittest.main()
