"""Exercise reconciliation against the real retained Root driver on local files."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from cytv.root_remove_recovery import SCRIPT

ROOT = Path(__file__).resolve().parents[2] / 'root-edition'


@unittest.skipIf(os.name == 'nt', 'TV-side driver requires POSIX directory fsync')
class RootRemovalRecoveryTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('recovery_deploy', ROOT / 'deploy.py')
        self.driver = importlib.util.module_from_spec(spec)
        with patch.object(sys, 'path', [str(ROOT), *sys.path]):
            spec.loader.exec_module(self.driver)
        namespace = {'__name__': 'test_recovery'}
        exec(SCRIPT, namespace)
        self.reconcile = namespace['reconcile']
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.driver.STATE = Path(self.tmp.name).resolve() / 'state'
        self.driver.STATE.mkdir()
        self.driver.INSTALLED = Path(self.tmp.name).resolve() / 'installed'

    def journal(self, stage, **extra):
        self.driver.write_stage(stage, **extra)

    def test_pre_submission_failure_can_resume_and_survives_another_failure(self):
        for stage in ('installed-recovery-only', 'uninstall-restored',
                      'uninstall-rollback-complete', 'uninstall-refresh-complete'):
            with self.subTest(stage=stage):
                self.journal(stage)
                with patch.object(self.driver, 'uninstall', side_effect=RuntimeError('lost connection')) as remove:
                    self.assertTrue(self.reconcile(self.driver, 'inspect')['ready'])
                    remove.assert_not_called()
                    with self.assertRaisesRegex(RuntimeError, 'lost connection'):
                        self.reconcile(self.driver, 'resume')
                    self.assertEqual(json.loads((self.driver.STATE/'deploy.json').read_text())['stage'], stage)
                with patch.object(self.driver, 'uninstall', return_value={'returnValue': True}) as remove:
                    self.assertTrue(self.reconcile(self.driver, 'resume')['returnValue'])
                    remove.assert_called_once_with()

    def test_completed_or_lost_terminal_is_reconciled_from_absence_without_resubmission(self):
        for stage in ('remove-submitting', 'remove-observed', 'uninstalled-state-retained'):
            with self.subTest(stage=stage):
                self.journal(stage)
                with patch.object(self.driver, 'uninstall') as remove:
                    self.assertTrue(self.reconcile(self.driver, 'inspect')['ready'])
                    reply = self.reconcile(self.driver, 'resume')
                    self.assertEqual(reply['removed'], self.driver.APP)
                    remove.assert_not_called()
                self.assertEqual(json.loads((self.driver.STATE/'deploy.json').read_text())['stage'], 'uninstalled-state-retained')

    def test_submitted_but_present_or_symlink_is_never_removed_again(self):
        for path in self.driver.installed_paths():
            with self.subTest(path=path):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(path.parent/'missing')
                self.journal('remove-submitting')
                with patch.object(self.driver, 'uninstall') as remove:
                    self.assertEqual(self.reconcile(self.driver, 'inspect')['reason'], 'unknown')
                    with self.assertRaises(self.driver.OutcomeUnknown):
                        self.reconcile(self.driver, 'resume')
                    remove.assert_not_called()
                self.assertTrue(path.is_symlink())
                path.unlink()

    def test_lost_terminal_keeps_never_provisioned_proof_for_archive(self):
        self.journal('remove-submitting', provisioning_not_started=True)
        self.reconcile(self.driver,'resume')
        self.assertIs(json.loads((self.driver.STATE/'deploy.json').read_text())['provisioning_not_started'],True)

    def test_observed_terminal_finishes_empty_metadata_cleanup_only_with_matching_evidence(self):
        package = self.driver.installed_paths()[1]
        package.mkdir(parents=True)
        self.journal('remove-observed', evidence={'completed': True})
        with self.assertRaises(self.driver.OutcomeUnknown):
            self.reconcile(self.driver, 'resume')
        self.assertTrue(package.exists())
        evidence = {'completed': True, 'event': {'id': self.driver.APP, 'statusValue': 31,
                    'details': {'packageId': self.driver.APP, 'state': 'removed'}}}
        self.journal('remove-observed', evidence=evidence)
        self.assertEqual(self.reconcile(self.driver, 'resume')['removed'], self.driver.APP)
        self.assertFalse(package.exists())

    def test_unknown_journal_or_running_driver_keeps_evidence(self):
        for stage, busy in (('install-submitting', False), ('installed-recovery-only', True)):
            self.journal(stage)
            before = (self.driver.STATE/'deploy.json').read_bytes()
            with patch.object(self.driver, 'uninstall') as remove:
                self.assertFalse(self.reconcile(self.driver, 'inspect', busy)['returnValue'])
                self.assertFalse(self.reconcile(self.driver, 'resume', busy)['returnValue'])
                remove.assert_not_called()
            self.assertEqual((self.driver.STATE/'deploy.json').read_bytes(), before)
