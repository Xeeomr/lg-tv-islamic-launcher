"""Exercise the actual device script against private temporary files."""
import json
import os
from pathlib import Path
import tempfile
import unittest

from cytv.root_archive import SCRIPT
from cytv.state import private_write


@unittest.skipUnless(hasattr(os, 'O_NOFOLLOW') and hasattr(os, 'O_DIRECTORY'), 'Device-side script requires POSIX file flags')
class RootArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.root = self.base/'clean-your-tv-root'
        self.root.mkdir(mode=0o700)
        self.installed = self.base/'installed'
        self.override = self.base/'override.json'
        self.proc = self.base/'proc'
        self.proc.mkdir()
        self.destination = str(self.root)+'.archive-'+'a'*32
        self.save('deploy.json', {'stage':'uninstalled-state-retained','app':'com.cleanyourtv.root.preview'})
        self.save('ls2-provision-snapshot.json', {'phase':'rolled-back'})
        private_write(self.root/'evidence.bin', b'previous recovery evidence')
        namespace = {'__name__':'archive_test'}
        exec(compile(SCRIPT, '<device-archive>', 'exec'), namespace)
        self.operate = namespace['operate']

    def archive(self, root, installed, override):
        inspected = self.operate('inspect', root, installed, override, proc=self.proc)
        return self.operate('archive', root, installed, override, self.destination, inspected['identity'], proc=self.proc)

    def save(self, name, value):
        private_write(self.root/name, json.dumps(value).encode())

    def test_completed_removal_is_archived_without_deleting_evidence(self):
        result = self.archive(self.root, self.installed, self.override)
        destination = Path(result['archived'])
        self.assertFalse(self.root.exists())
        self.assertEqual(destination.parent, self.base)
        self.assertEqual((destination/'evidence.bin').read_bytes(), b'previous recovery evidence')
        self.assertEqual(json.loads((destination/'deploy.json').read_text())['stage'], 'uninstalled-state-retained')

    def test_never_provisioned_removal_can_archive_only_with_explicit_proof(self):
        (self.root/'ls2-provision-snapshot.json').unlink()
        for value in (None, False, 'true'):
            self.save('deploy.json', {'stage':'uninstalled-state-retained','app':'com.cleanyourtv.root.preview','provisioning_not_started':value})
            with self.assertRaises((ValueError,OSError)):self.archive(self.root,self.installed,self.override)
        self.save('deploy.json', {'stage':'uninstalled-state-retained','app':'com.cleanyourtv.root.preview','provisioning_not_started':True})
        self.archive(self.root,self.installed,self.override)
        self.assertEqual((Path(self.destination)/'evidence.bin').read_bytes(),b'previous recovery evidence')

    def test_never_provisioned_proof_cannot_override_an_incomplete_snapshot(self):
        self.save('deploy.json', {'stage':'uninstalled-state-retained','app':'com.cleanyourtv.root.preview','provisioning_not_started':True})
        self.save('ls2-provision-snapshot.json', {'phase':'restoring'})
        with self.assertRaises(ValueError):self.archive(self.root,self.installed,self.override)

    def test_completed_rollback_can_archive_a_leftover_pending_manifest(self):
        self.save('recovery-provision.pending.json', {'version':1})
        self.archive(self.root,self.installed,self.override)

    def test_never_provisioned_proof_refuses_a_pending_manifest(self):
        (self.root/'ls2-provision-snapshot.json').unlink()
        self.save('deploy.json', {'stage':'uninstalled-state-retained','app':'com.cleanyourtv.root.preview','provisioning_not_started':True})
        self.save('recovery-provision.pending.json', {'version':1})
        with self.assertRaises(ValueError):self.archive(self.root,self.installed,self.override)

    def test_incomplete_or_active_state_never_moves_recovery(self):
        for name, value in [
            ('deploy.json', {'stage':'installed-recovery-only','app':'com.cleanyourtv.root.preview'}),
            ('ls2-provision-snapshot.json', {'phase':'restoring'}),
            ('persistent-intent.json', {'phase':'active'}),
            ('profile-trial.json', {'state':'recovering'}),
        ]:
            with self.subTest(name=name):
                previous = (self.root/name).read_bytes() if (self.root/name).exists() else None
                self.save(name, value)
                with self.assertRaises((ValueError, OSError)):
                    self.archive(self.root, self.installed, self.override)
                self.assertTrue((self.root/'evidence.bin').exists())
                self.assertFalse(list(self.base.glob('clean-your-tv-root.archive-*')))
                if previous is None: (self.root/name).unlink()
                else: private_write(self.root/name, previous)

    def test_package_or_routing_remainder_blocks_archival_including_broken_symlinks(self):
        remainder = self.installed/'services/com.cleanyourtv.root.preview.service'
        remainder.parent.mkdir(parents=True)
        for path in (remainder, self.override):
            with self.subTest(path=path):
                path.symlink_to(self.base/'missing-target')
                with self.assertRaises(ValueError):
                    self.archive(self.root, self.installed, self.override)
                self.assertTrue(self.root.exists())
                path.unlink()

    def test_indirect_or_writable_removal_journal_is_rejected(self):
        original = (self.root/'deploy.json').read_bytes()
        for indirect in (False, True):
            with self.subTest(indirect=indirect):
                if indirect:
                    (self.root/'deploy.json').unlink()
                    private_write(self.base/'external.json', original)
                    (self.root/'deploy.json').symlink_to(self.base/'external.json')
                else:
                    (self.root/'deploy.json').chmod(0o666)
                with self.assertRaises((ValueError, OSError)):
                    self.archive(self.root, self.installed, self.override)
                (self.root/'deploy.json').unlink()
                private_write(self.root/'deploy.json', original)

    def test_old_provider_or_guardian_blocks_archive_until_it_exits(self):
        process = self.proc/'123'
        process.mkdir()
        for executable in ('service', 'runtime/guardian_device.py'):
            with self.subTest(executable=executable):
                (process/'cmdline').write_bytes(b'/usr/bin/node\0'+str(self.root/executable).encode()+b'\0')
                self.assertTrue(self.operate('inspect', self.root, self.installed, self.override, proc=self.proc)['busy'])
                with self.assertRaisesRegex(ValueError, 'still running'):
                    self.archive(self.root, self.installed, self.override)
                self.assertTrue(self.root.exists())
        (process/'cmdline').write_bytes(b'/usr/bin/other\0')
        self.archive(self.root, self.installed, self.override)
        self.assertFalse(self.root.exists())

    def test_lost_archive_reply_reconciles_both_unsubmitted_and_completed_rename(self):
        identity = self.operate('inspect', self.root, self.installed, self.override, proc=self.proc)['identity']
        args = (self.root, self.installed, self.override, self.destination, identity)
        self.assertEqual(self.operate('reconcile', *args, proc=self.proc)['state'], 'not-archived')
        self.operate('archive', *args, proc=self.proc)
        self.assertEqual(self.operate('reconcile', *args, proc=self.proc)['state'], 'archived')
        private_write(Path(self.destination)/'deploy.json', b'{"app":"other","stage":"uninstalled-state-retained"}')
        with self.assertRaises(ValueError):
            self.operate('reconcile', *args, proc=self.proc)

    def test_remaining_owned_registration_blocks_archive(self):
        artifact = self.base/'old-recovery-registration'
        artifact.write_bytes(b'remaining registration')
        with self.assertRaisesRegex(ValueError, 'artifacts remain'):
            self.operate('inspect', self.root, self.installed, self.override, proc=self.proc, artifacts=(artifact,))
        self.assertTrue(self.root.exists())
