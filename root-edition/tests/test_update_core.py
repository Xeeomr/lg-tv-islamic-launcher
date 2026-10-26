"""Disk-backed update/recovery contract; only the TV side effects are simulated."""
import copy
import json
import multiprocessing
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from updater.core import Manager
from updater.store import Store
from updater.profile import validate


def profile():
    return {'schema': 1, 'inventory': {'apps': [
        {'id': 'org.test.app', 'title': 'Телевизор',
         'icon': 'data:image/png;base64,aWNvbg==', 'iconColor': '#123456'}],
        'inputs': [{'appId': 'com.webos.app.hdmi1', 'label': 'Консоль'}]},
        'config': {'columns': 5, 'dockApps': ['org.test.app'], 'hiddenApps': [],
                   'liveTvApp': 'com.webos.app.livetv'},
        'settings': {'tvhome.order': '{"ids":["org.test.app"],"dock":"org.test.app"}'}}


class Device:
    def __init__(self):
        self.time = 1000
        self.version = '1.0.0'
        self.prior = {'version': '1.0.0', 'sha256': 'a' * 64}
        self.candidate = {'version': '1.1.0', 'sha256': 'b' * 64}
        self.calls = []
        self.active = True
        self.route_ok = True
        self.outcomes = [True, True]
        self.verify_ok = True
        self.prepare_error = False
    def offer(self):
        return {'installed': self.version, 'prior': self.prior,
                'candidate': self.candidate, 'canInstall': True, 'reason': ''}
    def installed(self): return {'version': self.version}
    def now(self): return self.time
    def prepare(self, candidate, prior):
        self.calls.append('prepare')
        if self.prepare_error: raise ValueError('missing rollback package')
        return {'candidate': candidate, 'prior': prior}
    def routing_status(self): return {'active': self.active, 'safe': not self.active}
    def restore_route(self):
        self.calls.append('restore')
        if self.route_ok: self.active = False
        return self.route_ok
    def install(self, manifest, on_submit, on_terminal):
        self.calls.append('install:' + manifest['version'])
        on_submit({'job': len(self.calls)})
        outcome = self.outcomes.pop(0)
        if outcome == 'crash': raise KeyboardInterrupt('worker died')
        if outcome is None: return
        if outcome: self.version = manifest['version']
        on_terminal({'success': outcome, 'job': len(self.calls)})
    def verify_installed(self, manifest):
        self.calls.append('verify:' + manifest['version'])
        return self.verify_ok and self.version == manifest['version']
    def launch(self): self.calls.append('launch')
    def finish(self, tx):
        self.calls.append('finish:'+tx['phase'])
        tx['homeResume']={'status':'unchanged'};tx['homeResumePhase']=tx['phase']
        self.store.write('transaction',tx)


def competing_lock(root, queue):
    queue.put('waiting')
    with Store(root, uid=os.getuid()).lock():
        queue.put('acquired')


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.tmp.name)
        self.store = Store(self.root, uid=os.getuid())
        self.io = Device()
        self.io.store = self.store
        self.m = Manager(self.store, self.io)
    def tearDown(self): self.tmp.cleanup()
    def advance(self, phase, limit=20):
        for _ in range(limit):
            state = self.m.run()
            if phase == 'rolled-back' and state['phase'] == 'verifying-rollback':
                self.assertIn('launch',self.io.calls)
                self.m.ready(state['id'],state['prior']['version'])
            if state['phase'] == phase: return state
        self.fail('did not reach ' + phase + ': ' + repr(state))
    def start(self): return self.m.install('1.1.0', profile())
    def receipt(self, tx):
        self.m.ready(tx['id'], '1.1.0')
        self.m.confirm(tx['id'], '1.1.0')
    def installs(self): return [c for c in self.io.calls if c.startswith('install:')]

    def test_install_only_enqueues_and_preserves_exact_immutable_snapshot(self):
        original = profile()
        tx = self.m.install('1.1.0', original)
        self.assertEqual('preparing', tx['phase'])
        self.assertEqual([], self.io.calls)
        original['inventory']['apps'].clear()
        self.assertEqual(profile(), self.m.restore_profile()['profile'])
        self.assertEqual(tx['id'], self.start()['id'])
        self.assertEqual(profile(), self.store.read(tx['profile']))
        with self.assertRaises(ValueError): self.store.write(tx['profile'], original)

    def test_success_requires_ready_and_explicit_confirm_and_leaves_lg_route(self):
        tx = self.start()
        self.advance('verifying')
        self.assertLess(self.io.calls.index('restore'), self.io.calls.index('install:1.1.0'))
        self.assertEqual('verifying', self.m.run()['phase'])
        self.m.ready(tx['id'], '1.1.0')
        self.assertEqual('verifying', self.m.run()['phase'])
        self.m.confirm(tx['id'], '1.1.0')
        self.advance('complete')
        self.assertFalse(self.io.active)
        self.assertEqual('1.1.0', self.store.read('current')['version'])
        self.assertEqual(profile(), self.m.restore_profile()['profile'])
        self.assertEqual(['install:1.1.0'], self.installs())

    def test_timely_confirmation_survives_late_poll_and_worker_restart(self):
        tx=self.start();self.advance('verifying')
        self.io.time+=119.9;self.receipt(tx)
        self.io.time+=3;self.m=Manager(Store(self.root,uid=os.getuid()),self.io)
        self.assertEqual('complete',self.m.run()['phase'])

    def test_confirmed_update_can_roll_back_days_later_after_restart(self):
        tx = self.start()
        self.advance('verifying'); self.receipt(tx); self.advance('complete')
        self.io.time += 30 * 86400
        self.io.active = True
        self.m = Manager(Store(self.root, uid=os.getuid()), self.io)
        self.assertEqual('rolling-back', self.m.rollback()['phase'])
        self.advance('verifying-rollback')
        self.assertFalse(self.io.active)
        self.assertEqual(profile(), self.m.restore_profile()['profile'])
        self.assertEqual('verifying-rollback', self.m.run()['phase'])
        self.m.ready(tx['id'], '1.0.0')
        self.assertEqual('rolled-back', self.m.run()['phase'])
        self.assertEqual('1.0.0', self.store.read('current')['version'])
        for _ in range(3): self.m.rollback(); self.m.run()
        self.assertEqual(['install:1.1.0', 'install:1.0.0'], self.installs())

    def test_confirmed_update_rollback_does_not_replace_an_unrelated_version(self):
        tx = self.start()
        self.advance('verifying'); self.receipt(tx); self.advance('complete')
        self.io.version = '2.0.0'
        with self.assertRaisesRegex(ValueError, 'installed version changed'):
            self.m.rollback()
        self.assertEqual('complete', self.m.status()['phase'])
        self.assertEqual(['install:1.1.0'], self.installs())

    def test_next_update_replaces_confirmed_rollback_target_and_snapshot(self):
        tx = self.start()
        self.advance('verifying'); self.receipt(tx); self.advance('complete')
        self.io.prior = self.io.candidate
        self.io.candidate = {'version': '1.2.0', 'sha256': 'c' * 64}
        self.io.outcomes = [True, True]
        snapshot = profile(); snapshot['config']['columns'] = 6
        tx = self.m.install('1.2.0', snapshot)
        self.assertIn('finish:complete',self.io.calls)
        self.advance('verifying')
        self.m.ready(tx['id'], '1.2.0'); self.m.confirm(tx['id'], '1.2.0')
        self.advance('complete')
        self.assertEqual('rolling-back', self.m.rollback()['phase'])
        self.advance('verifying-rollback')
        self.assertEqual(snapshot, self.m.restore_profile()['profile'])
        self.m.ready(tx['id'], '1.1.0')
        self.assertEqual('rolled-back', self.m.run()['phase'])
        self.assertEqual(['install:1.1.0', 'install:1.2.0', 'install:1.1.0'], self.installs())

    def test_next_update_cannot_replace_transaction_with_unresolved_home_cleanup(self):
        tx=self.start();self.advance('verifying');self.receipt(tx);self.advance('complete')
        self.io.prior=self.io.candidate
        self.io.candidate={'version':'1.2.0','sha256':'c'*64}
        self.io.finish=lambda previous:None
        with self.assertRaisesRegex(ValueError,'Home recovery pending'):
            self.m.install('1.2.0',profile())
        self.assertEqual(tx['id'],self.m.status()['id'])
        self.assertEqual(['install:1.1.0'],self.installs())

    def test_crash_at_durable_launch_boundary_reopens_without_reinstall(self):
        self.start();self.advance('awaiting-launch')
        write=self.store.write
        def crash(name,value):
            result=write(name,value)
            if name=='transaction' and value.get('phase')=='verifying':raise KeyboardInterrupt()
            return result
        self.store.write=crash
        with self.assertRaises(KeyboardInterrupt):self.m.run()
        self.assertNotIn('launch',self.io.calls)
        self.m=Manager(Store(self.root,uid=os.getuid()),self.io)
        self.m.run()
        self.assertEqual(1,self.io.calls.count('launch'))
        self.assertEqual(['install:1.1.0'],self.installs())

    def test_rollback_waits_for_actual_profile_readiness_and_never_retries(self):
        self.io.outcomes=[False,True];self.start();state=self.advance('verifying-rollback')
        self.assertEqual('1.0.0',self.m.restore_profile()['version'])
        self.assertEqual('verifying-rollback',self.m.run()['phase'])
        with self.assertRaises(ValueError):self.m.confirm(state['id'],'1.0.0')
        self.io.time+=121
        self.assertEqual('recovery-required',self.m.run()['phase'])
        self.assertEqual(['install:1.1.0','install:1.0.0'],self.installs())

    def test_candidate_readiness_does_not_confirm_or_break_rollback_readiness(self):
        tx=self.start();self.advance('verifying');self.m.ready(tx['id'],'1.1.0')
        self.io.time+=121;self.advance('verifying-rollback')
        self.assertEqual('verifying-rollback',self.m.run()['phase'])
        self.m.ready(tx['id'],'1.0.0')
        self.assertEqual('rolled-back',self.m.run()['phase'])

    def test_timeout_rolls_back_exactly_once_and_restores_same_profile(self):
        self.start()
        self.advance('verifying')
        self.io.time += 121
        state = self.advance('rolled-back')
        self.assertTrue(state['rollbackAttempted'])
        for _ in range(3): self.m.run(); self.m.rollback()
        self.assertEqual(['install:1.1.0', 'install:1.0.0'], self.installs())
        self.assertEqual('1.0.0', self.m.restore_profile()['version'])
        self.assertEqual(profile(), self.m.restore_profile()['profile'])
        self.assertFalse(self.io.active)

    def test_definite_failure_is_eligible_for_one_rollback(self):
        self.io.outcomes = [False, True]
        self.start()
        self.advance('rolled-back')
        self.assertEqual(['install:1.1.0', 'install:1.0.0'], self.installs())

    def test_unknown_outcome_never_submits_rollback_or_another_update(self):
        self.io.outcomes = [None]
        self.start()
        self.advance('recovery-required')
        self.m = Manager(Store(self.root, uid=os.getuid()), self.io)
        self.m.reconcile(); self.m.rollback(); self.m.run()
        self.assertEqual(['install:1.1.0'], self.installs())
        with self.assertRaises(ValueError): self.start()

    def test_process_death_after_submission_is_not_replayed(self):
        self.io.outcomes = ['crash']
        self.start()
        with self.assertRaises(KeyboardInterrupt):
            for _ in range(10): self.m.run()
        self.m = Manager(Store(self.root, uid=os.getuid()), self.io)
        self.assertEqual('recovery-required', self.m.reconcile()['phase'])
        self.assertEqual(['install:1.1.0'], self.installs())

    def test_restart_after_terminal_receipt_continues_without_duplicate(self):
        self.start()
        self.advance('awaiting-launch')
        self.m = Manager(Store(self.root, uid=os.getuid()), self.io)
        state = self.advance('verifying')
        self.receipt(state)
        self.advance('complete')
        self.assertEqual(['install:1.1.0'], self.installs())

    def test_rollback_failure_keeps_evidence_and_never_retries(self):
        self.io.outcomes = [False, False]
        tx = self.start()
        state = self.advance('recovery-required')
        self.assertTrue(state['rollbackAttempted'])
        self.m.rollback(); self.m.reconcile(); self.m.run()
        self.assertEqual(['install:1.1.0', 'install:1.0.0'], self.installs())
        self.assertEqual(profile(), self.store.read(tx['profile']))

    def test_stale_receipts_and_confirm_before_ready_are_rejected(self):
        tx = self.start()
        with self.assertRaises(ValueError): self.m.ready('0' * 32, '1.1.0')
        with self.assertRaises(ValueError): self.m.ready(tx['id'], '1.0.0')
        with self.assertRaises(ValueError): self.m.confirm(tx['id'], '1.1.0')
        self.advance('verifying')
        with self.assertRaises(ValueError): self.m.confirm(tx['id'], '1.1.0')
        self.io.time += 121
        with self.assertRaises(ValueError): self.m.ready(tx['id'], '1.1.0')

    def test_receipts_and_profile_read_do_not_wait_for_worker_flock(self):
        tx = self.start()
        self.advance('verifying')
        with self.store.lock():
            other = Manager(Store(self.root, uid=os.getuid()), self.io)
            self.assertEqual(profile(), other.restore_profile()['profile'])
            other.ready(tx['id'], '1.1.0')
            other.confirm(tx['id'], '1.1.0')
        self.advance('complete')

    def test_corrupt_profile_fails_closed_before_install(self):
        tx = self.start()
        (Path(self.tmp.name) / (tx['profile'] + '.json')).write_text('{broken')
        self.assertEqual('recovery-required', self.m.run()['phase'])
        self.assertEqual([], self.installs())
        with self.assertRaises(ValueError): self.m.restore_profile()

    def test_corrupt_journal_never_starts_second_transaction(self):
        self.start()
        (Path(self.tmp.name) / 'transaction.json').write_text('{broken')
        with self.assertRaises(ValueError): self.start()
        with self.assertRaises(ValueError): self.m.run()
        self.assertEqual([], self.installs())

    def test_missing_rollback_and_unconfirmed_route_abort_before_replacement(self):
        self.io.prepare_error = True
        self.start()
        self.advance('aborted')
        self.assertEqual([], self.installs())
        self.io.prepare_error = False
        self.start()
        self.advance('verifying')

    def test_route_must_be_observably_safe_before_installer(self):
        self.io.route_ok = False
        self.start()
        self.advance('aborted')
        self.assertEqual([], self.installs())

    def test_prior_mismatch_downgrade_and_changed_offer_block(self):
        self.io.prior['version'] = '0.9.0'
        with self.assertRaises(ValueError): self.start()
        self.io.prior['version'] = '1.0.0'
        self.io.candidate['version'] = '0.9.0'
        with self.assertRaises(ValueError): self.m.install('0.9.0', profile())
        self.io.candidate['version'] = '1.2.0'
        with self.assertRaises(ValueError): self.start()

    def test_installed_version_change_before_submission_blocks(self):
        self.start()
        self.io.version = '2.0.0'
        self.advance('aborted')
        self.assertEqual([], self.installs())

    def test_store_rejects_symlinks_unsafe_names_and_nonprivate_paths(self):
        with self.assertRaises(ValueError): self.store.write('../escape', {})
        outside = Path(self.tmp.name) / 'outside'
        outside.write_text('{}')
        (Path(self.tmp.name) / 'link.json').symlink_to(outside)
        with self.assertRaises(ValueError): self.store.read('link')
        with self.assertRaises(ValueError): self.store.write('link', {})
        rootlink = Path(self.tmp.name) / 'rootlink'
        rootlink.symlink_to(self.tmp.name, target_is_directory=True)
        with self.assertRaises(ValueError): Store(str(rootlink), uid=os.getuid())
        os.chmod(self.tmp.name, 0o777)
        with self.assertRaises(ValueError): Store(self.root, uid=os.getuid())

    def test_flock_is_process_independent(self):
        context = multiprocessing.get_context('fork')
        queue = context.Queue()
        with self.store.lock():
            process = context.Process(target=competing_lock, args=(self.root, queue))
            process.start()
            self.assertEqual('waiting', queue.get(timeout=3))
            with self.assertRaises(__import__('queue').Empty): queue.get(timeout=0.1)
        self.assertEqual('acquired', queue.get(timeout=3))
        process.join(3)
        self.assertEqual(0, process.exitcode)

    def test_symlink_ancestor_is_rejected_even_when_leaf_is_private(self):
        real = Path(self.root) / 'real'
        real.mkdir(mode=0o700)
        (real / 'state').mkdir(mode=0o700)
        link = Path(self.root) / 'alias'
        link.symlink_to(real, target_is_directory=True)
        with self.assertRaises(ValueError): Store(str(link / 'state'), uid=os.getuid())

    def test_verified_terminal_success_with_identity_error_rolls_back(self):
        self.start()
        self.advance('awaiting-launch')
        original = self.io.verify_installed
        def verify(manifest):
            if manifest['version'] == '1.1.0': raise ValueError('installed payload hash mismatch')
            return original(manifest)
        self.io.verify_installed = verify
        self.advance('rolled-back')
        self.assertEqual(['install:1.1.0', 'install:1.0.0'], self.installs())

    def test_confirmed_identity_error_rolls_back(self):
        tx = self.start()
        self.advance('verifying')
        self.receipt(tx)
        original = self.io.verify_installed
        def verify(manifest):
            if manifest['version'] == '1.1.0': raise ValueError('installed payload changed')
            return original(manifest)
        self.io.verify_installed = verify
        self.advance('rolled-back')

    def test_rollback_flag_cannot_disagree_with_durable_evidence(self):
        self.io.outcomes = [False, None]
        self.start()
        tx = self.advance('recovery-required')
        tx['rollbackAttempted'] = False
        self.store.write('transaction', tx)
        with self.assertRaises(ValueError): self.m.rollback()
        self.assertEqual(['install:1.1.0', 'install:1.0.0'], self.installs())

    def test_null_journal_is_corruption_not_absence(self):
        self.start()
        (Path(self.root) / 'transaction.json').write_text('null')
        with self.assertRaises(ValueError): self.start()

    def test_installer_evidence_cannot_be_reset_by_earlier_phase(self):
        self.io.outcomes = [None]
        self.start()
        tx = self.advance('recovery-required')
        tx['phase'] = 'backed-up'
        self.store.write('transaction', tx)
        with self.assertRaises(ValueError): self.m.run()
        self.assertEqual(['install:1.1.0'], self.installs())

    def test_restart_at_every_durable_phase_never_repeats_an_install(self):
        # Crash immediately after actual fsynced writes, not at a fake journal.
        class Crash(Store):
            def write(inner, name, value):
                result = super().write(name, value)
                if name == 'transaction' and predicate(value):
                    raise KeyboardInterrupt('power lost after fsync')
                return result
        cases = [
            ('preparing', False, None, 'complete', 1),
            ('downloading', False, None, 'complete', 1),
            ('backed-up', False, None, 'complete', 1),
            ('restoring-route', False, None, 'complete', 1),
            ('installing', False, 'before', 'recovery-required', 0),
            ('installing', False, 'submitted', 'recovery-required', 1),
            ('installing', False, 'terminal', 'complete', 1),
            ('awaiting-launch', False, None, 'complete', 1),
            ('verifying', False, None, 'complete', 1),
            ('complete', False, None, 'complete', 1),
            ('rolling-back', True, 'before', 'rolled-back', 2),
            ('rolling-back', True, 'attempted', 'recovery-required', 1),
            ('rolling-back', True, 'submitted', 'recovery-required', 2),
            ('rolling-back', True, 'terminal', 'rolled-back', 2),
            ('verifying-rollback', True, None, 'rolled-back', 2),
            ('rolled-back', True, None, 'rolled-back', 2),
        ]
        for phase, rollback, boundary, expected, count in cases:
            with self.subTest(phase=phase, boundary=boundary), tempfile.TemporaryDirectory() as directory:
                root = os.path.realpath(directory)
                io = Device()
                if rollback: io.outcomes = [False, True]
                def predicate(tx):
                    if tx['phase'] != phase: return False
                    evidence = tx['rollbackEvidence' if rollback else 'installEvidence']
                    if boundary == 'before': return not tx['rollbackAttempted'] if rollback else evidence['submitted'] is None
                    if boundary == 'attempted': return tx['rollbackAttempted'] and evidence['submitted'] is None
                    if boundary == 'submitted': return evidence['submitted'] is not None and evidence['terminal'] is None
                    if boundary == 'terminal': return evidence['terminal'] is not None
                    return True
                manager = Manager(Crash(root, uid=os.getuid()), io)
                with self.assertRaises(KeyboardInterrupt):
                    manager.install('1.1.0', profile())
                    for _ in range(20):
                        state = manager.run()
                        if state['phase'] == 'verifying':
                            self.assertIn('launch',io.calls)
                            manager.ready(state['id'], '1.1.0')
                            manager.confirm(state['id'], '1.1.0')
                        elif state['phase']=='verifying-rollback':
                            self.assertIn('launch',io.calls)
                            manager.ready(state['id'],'1.0.0')
                manager = Manager(Store(root, uid=os.getuid()), io)
                for _ in range(20):
                    state = manager.run()
                    if state['phase'] == 'verifying':
                        self.assertIn('launch',io.calls)
                        manager.ready(state['id'], '1.1.0')
                        manager.confirm(state['id'], '1.1.0')
                    elif state['phase']=='verifying-rollback':
                        self.assertIn('launch',io.calls)
                        manager.ready(state['id'],'1.0.0')
                    if state['phase'] in {'complete', 'rolled-back', 'recovery-required'}: break
                self.assertEqual(expected, state['phase'])
                self.assertEqual(count, len([c for c in io.calls if c.startswith('install:')]))

    def test_profile_boundaries_use_utf8_bytes_and_reject_executable_fields(self):
        value = profile()
        value['renewal'] = {'enabled': False}
        with self.assertRaises(ValueError): validate(value)
        value = profile(); value['config']['command'] = 'anything'
        with self.assertRaises(ValueError): validate(value)
        value = profile(); value['settings']['tvhome.order'] = 'Ж' * (2 * 1024 * 1024)
        with self.assertRaises(ValueError): validate(value)
        value = profile(); value['inventory']['apps'][0]['icon'] = 'file:///tmp/icon'
        with self.assertRaises(ValueError): validate(value)
        value = profile(); value['inventory']['apps'][0]['icon'] = 'data:image/png;base64,' + 'YQ==' * 90000
        with self.assertRaises(ValueError): validate(value)
        self.assertEqual(profile(), validate(profile()))

    def test_unreadable_order_or_contradictory_journal_cannot_be_replaced(self):
        for order in ('{broken','{"dock":"app","ids":"wrong"}','{"dock":"app","ids":["app","app"]}'):
            value=profile();value['settings']['tvhome.order']=order
            with self.assertRaises(ValueError):validate(value)
        self.start();tx=self.advance('verifying');self.receipt(tx);self.advance('complete')
        tx=self.m.status();tx['rollbackAttempted']=True
        tx['rollbackEvidence']['submitted']={'job':3}
        self.store.write('transaction',tx)
        with self.assertRaises(ValueError):self.start()


if __name__ == '__main__': unittest.main()
