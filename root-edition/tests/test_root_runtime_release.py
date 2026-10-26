"""Release boundaries: provisioning, isolated app identity, CLI failure signals."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'runtime'))
import bounded_profile_trial as trial
import cli
import device_adapter as d
import provision
from profile_plan import CANDIDATE


class ReleaseTests(unittest.TestCase):
    def test_release_candidate_is_isolated(self):
        self.assertEqual(CANDIDATE, 'com.cleanyourtv.root.preview')
        self.assertEqual(str(d.STATE), '/var/lib/clean-your-tv-root')
        self.assertEqual(str(d.TARGET), '/var/webos-profile/override/clean-your-tv-root.json')

    def test_provision_failure_precedes_any_routing_read_or_guardian(self):
        with patch('provision.verify', side_effect=ValueError('unprovisioned')), patch.object(d,'read') as read:
            with self.assertRaisesRegex(ValueError, 'unprovisioned'):
                trial.begin(lambda _: self.fail('guardian must not launch'))
            read.assert_not_called()

    def test_provision_is_rechecked_under_lock_before_any_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(d, 'STATE', root), patch.object(d, 'EXPECTED_UID', os.geteuid()), patch('provision.verify', side_effect=[{}, ValueError('revoked')]) as verify, patch('helper_bridge.require_idle'), patch.object(d, 'read') as read:
                with self.assertRaisesRegex(ValueError, 'revoked'):
                    trial.begin(lambda _: self.fail('must not spawn'))
                self.assertEqual(verify.call_count, 2)
                read.assert_not_called()
                self.assertFalse((root/'profile-trial.json').exists())

    def test_recovery_retry_diagnostics_do_not_corrupt_json_stdout(self):
        import contextlib
        import io
        output, errors = io.StringIO(), io.StringIO()
        with patch.object(d, 'trusted_dir'), patch.object(d, 'restore_once', side_effect=[OSError('temporary'), 'restored']), patch.object(d.time, 'sleep'), contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            self.assertEqual(d.main('recover'), 'restored')
        self.assertEqual(output.getvalue(), '')
        self.assertIn('temporary', errors.getvalue())

    def test_enable_dispatches_persistent_activation_and_confirm_requires_existing_intent(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(d,'STATE',Path(tmp).resolve()),patch.object(d,'EXPECTED_UID',os.getuid()):
            with patch.object(cli.os,'geteuid',return_value=0), patch('intent_runtime.enable',return_value={'persistent':True}) as start:
                self.assertTrue(cli.main('enable')['persistent'])
                start.assert_called_once_with()
            with patch.object(cli.os,'geteuid',return_value=0), patch('intent_runtime.coordinator',return_value=None):
                with self.assertRaisesRegex(ValueError,'No intent'): cli.main('confirm')

    def test_restore_works_without_provision_manifest(self):
        with patch.object(cli.os,'geteuid',return_value=0), patch.object(d,'main', return_value='restored') as adapter, patch('provision.verify',side_effect=ValueError('missing')):
            self.assertEqual(cli.main('restore'),'restored')
            adapter.assert_called_once_with('recover')

    def test_nonroot_rejected_before_dispatch(self):
        with patch.object(cli.os,'geteuid',return_value=123), patch.object(d,'main') as adapter:
            with self.assertRaises(PermissionError): cli.main('restore')
            adapter.assert_not_called()

    def test_manifest_requires_all_files_and_matching_digests(self):
        with tempfile.TemporaryDirectory() as tmp:
            state=Path(tmp).resolve(); runtime=state/'runtime'; runtime.mkdir()
            module=runtime/'provision.py'; module.write_text('# fixture')
            entry=runtime/'cli.py'; entry.write_text('# fixture')
            callback=state/'boot-recover.sh'; callback.write_text('/usr/bin/python3 '+str(entry)+' boot\n')
            manifest={'version':1,'mode':'recovery-only','boot_callback':str(callback),
                      'files':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (module,entry,callback)}}
            def save():
                path=state/'recovery-provision.json';path.write_text(json.dumps(manifest));path.chmod(0o600)
            save()
            # Ancestor ownership belongs to the host; file integrity is exercised for real.
            with patch.object(d,'STATE',state), patch.object(d,'EXPECTED_UID',os.geteuid()), patch.object(d,'trusted_dir'), patch.object(provision,'__file__',str(module)):
                self.assertEqual(provision.verify()['hardware_validated'],False)
                callback.write_text('corrupt callback')
                with self.assertRaisesRegex(ValueError,'digest mismatch'): provision.verify()
                manifest['files'].pop(str(entry));save()
                with self.assertRaisesRegex(ValueError,'Incomplete'): provision.verify()


if __name__ == '__main__': unittest.main()
