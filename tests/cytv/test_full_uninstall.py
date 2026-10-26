from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from cytv.operations import Installer, UPDATER_APP
from cytv import state, package

class FullUninstallTests(unittest.TestCase):
    def test_full_removal_disables_and_archives_independent_supervisor(self):
        app='com.cleanyourtv.system.updater'
        with tempfile.TemporaryDirectory() as tmp:
            store=state.Store(tmp);profile=state.target('tv.local','root');remote=MagicMock()
            remote.luna.return_value={'returnValue':True,'status':{'apps':[]}}
            remote.run.return_value=''
            inst=Installer(remote,store,profile,Path(tmp),{},lambda *_:None)
            inst._selected_python='/usr/bin/python3'
            inst.installed_apps=MagicMock(side_effect=[[{'id':app}],[]])
            inst.root_updater_cleanup=MagicMock(side_effect=[{'disabled':True},{'removed':True,'archive':'saved'}])
            inst.system_updater_cleanup=MagicMock(side_effect=[{'present':True,'bootstrap_complete':True}, {'disabled':True}, {'removed':True,'archive':'system-saved'}])
            inst.cleanup_updater_app_permissions=MagicMock();inst.verify_project_removed=MagicMock();inst.verify_absent=MagicMock();inst.cleanup_legacy_permissions=MagicMock()
            result=inst.uninstall(full_project=True)
            self.assertTrue(result['removed'])
            self.assertEqual(result['system_updater_archive'],'system-saved')
            removes=[c for c in remote.luna.call_args_list if c.args[0].endswith('/remove')]
            self.assertEqual([c.args[1]['id'] for c in removes],[app])
            self.assertEqual([c.args[0] for c in inst.system_updater_cleanup.call_args_list],['status','disable','archive'])
            self.assertIsNone(store.pending(profile))

    def test_removes_leftover_updater_without_resubmitting_root_removal(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=state.Store(tmp);profile=state.target('tv.local','root');remote=MagicMock()
            remote.luna.return_value={'returnValue':True,'status':{'apps':[]}}
            remote.run.return_value=''
            inst=Installer(remote,store,profile,Path(tmp),{},lambda *_:None)
            inst._selected_python='/usr/bin/python3'
            inst.installed_apps=MagicMock(side_effect=[[{'id':UPDATER_APP}],[]])
            inst.root_updater_cleanup=MagicMock(side_effect=[{'disabled':True},{'removed':True,'archive':'saved'}])
            inst.cleanup_updater_app_permissions=MagicMock();inst.verify_project_removed=MagicMock();inst.verify_absent=MagicMock();inst.root_action=MagicMock();inst.cleanup_legacy_permissions=MagicMock()
            result=inst.uninstall(full_project=True)
            self.assertTrue(result['removed'])
            inst.root_action.assert_not_called()
            self.assertEqual([c.args[0] for c in inst.root_updater_cleanup.call_args_list],['disable','finalize'])
            removes=[c for c in remote.luna.call_args_list if c.args[0].endswith('/remove')]
            self.assertEqual([c.args[1]['id'] for c in removes],[UPDATER_APP])
            self.assertIsNone(store.pending(profile))

    def test_resume_after_updater_state_archived_cleans_permissions_without_remove(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=state.Store(tmp);profile=state.target('tv.local','root');remote=MagicMock()
            remote.luna.return_value={'returnValue':True,'status':{'apps':[]}}
            remote.run.return_value=''
            inst=Installer(remote,store,profile,Path(tmp),{},lambda *_:None)
            inst._selected_python='/usr/bin/python3'
            inst.installed_apps=MagicMock(return_value=[])
            inst.root_updater_cleanup=MagicMock(return_value={'disabled':True,'removed':True,'archive':'saved'})
            inst.cleanup_updater_app_permissions=MagicMock();inst.verify_project_removed=MagicMock()
            inst.verify_absent=MagicMock();inst.cleanup_legacy_permissions=MagicMock()
            store.begin(profile,'uninstall',full_project=True,removals={UPDATER_APP:'done'},updater_archive='/var/lib/clean-your-tv-root-updater.archive-'+'a'*32)
            self.assertTrue(inst.uninstall(full_project=True)['removed'])
            inst.cleanup_updater_app_permissions.assert_called_once()
            self.assertFalse(any(c.args[0].endswith('/remove') for c in remote.luna.call_args_list))
            self.assertIsNone(store.pending(profile))

    def test_uncertain_updater_remove_is_not_submitted_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=state.Store(tmp);profile=state.target('tv.local','root');remote=MagicMock()
            remote.luna.return_value={'returnValue':True,'status':{'apps':[]}}
            remote.run.return_value=''
            inst=Installer(remote,store,profile,Path(tmp),{},lambda *_:None)
            inst._selected_python='/usr/bin/python3'
            inst.verify_absent=MagicMock();inst.cleanup_legacy_permissions=MagicMock()
            inst.installed_apps=MagicMock(return_value=[{'id':UPDATER_APP}]);inst.root_updater_cleanup=MagicMock(return_value={'disabled':True})
            store.begin(profile,'uninstall',full_project=True,removals={UPDATER_APP:'submitted'},updater_archive='/var/lib/clean-your-tv-root-updater.archive-'+'a'*32)
            with self.assertRaisesRegex(RuntimeError,'unknown'):inst.uninstall(full_project=True)
            self.assertFalse(any(c.args[0].endswith('/remove') for c in remote.luna.call_args_list))
            self.assertIsNotNone(store.pending(profile))

    def test_final_verification_checks_registrations_even_without_root_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            remote=MagicMock();remote.run.return_value=''
            inst=Installer(remote,state.Store(tmp),state.target('tv.local','root'),Path(tmp),{},lambda *_:None)
            with self.assertRaisesRegex(RuntimeError,'registrations remain'):inst.verify_project_removed()
            remote.luna.assert_not_called()
            command=remote.run.call_args.args[0]
            self.assertIn('50-clean-your-tv-root',command)
            self.assertIn('clean-your-tv-root.json',command)

    def test_status_never_finishes_partial_full_uninstall(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=state.Store(tmp);profile=state.target('tv.local','root');remote=MagicMock()
            remote.run.return_value='{"stage":"uninstalled-state-retained"}'
            inst=Installer(remote,store,profile,Path(tmp),{},lambda *_:None)
            inst._selected_python='/usr/bin/python3';inst.verify_absent=MagicMock()
            store.begin(profile,'uninstall',full_project=True)
            self.assertIsNotNone(inst.status()['pending'])
            self.assertIsNotNone(store.pending(profile))

    def test_final_verification_waits_for_root_exit_before_finishing(self):
        scenarios = (
            ('already stopped', [{'busy': False}], False),
            ('exits after polling', [{'busy': True}, {'busy': True}, {'busy': False}], False),
            ('still running at deadline', [{'busy': True}], True),
            ('inspection fails', [RuntimeError('connection lost')], True),
        )
        for name, replies, fails in scenarios:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                store = state.Store(tmp)
                profile = state.target('tv.local', 'root')
                remote = MagicMock()
                remote.luna.return_value = {'returnValue': True, 'status': {'apps': []}}
                remote.run.return_value = 'CYTV_ROOT_RETAINED'
                inst = Installer(remote, store, profile, Path(tmp), {}, lambda *_: None)
                inst._selected_python='/usr/bin/python3'
                inst.installed_apps = MagicMock(return_value=[])
                inst.root_updater_cleanup = MagicMock(return_value={'disabled': True, 'removed': True})
                inst.cleanup_legacy_permissions = MagicMock()
                inst.cleanup_updater_app_permissions = MagicMock()
                inst.verify_project_removed = MagicMock()
                inst.verify_absent = MagicMock()
                elapsed = [0]
                def sleep(seconds):
                    self.assertIsNotNone(store.pending(profile))
                    elapsed[0] += seconds
                def inspect(action):
                    self.assertEqual(action, 'inspect')
                    reply = replies.pop(0) if len(replies) > 1 else replies[0]
                    if isinstance(reply, Exception):
                        raise reply
                    return reply
                inst.root_archive = inspect
                with patch('cytv.operations.time', create=True) as clock:
                    clock.monotonic.side_effect = lambda: elapsed[0]
                    clock.sleep.side_effect = sleep
                    if fails:
                        with self.assertRaises(RuntimeError):
                            inst.uninstall(full_project=True)
                        self.assertIsNotNone(store.pending(profile))
                        if name == 'still running at deadline':
                            self.assertGreater(elapsed[0], 0)
                            self.assertLessEqual(elapsed[0], 60)
                    else:
                        self.assertTrue(inst.uninstall(full_project=True)['removed'])
                        self.assertIsNone(store.pending(profile))
                        if name == 'exits after polling':
                            self.assertGreater(elapsed[0], 0)
                self.assertFalse(any(c.args[0].endswith('/remove') for c in remote.luna.call_args_list))

    def test_interrupted_root_removal_checks_device_before_continuing(self):
        for outcome in ('completed', 'ready', 'unknown', 'busy', 'retry-fails'):
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory() as tmp:
                store = state.Store(tmp)
                profile = state.target('tv.local', 'root')
                remote = MagicMock()
                remote.luna.return_value = {'returnValue': True, 'status': {'apps': []}}
                remote.run.return_value = ''
                inst = Installer(remote, store, profile, Path(tmp), {}, lambda *_: None)
                inst._selected_python='/usr/bin/python3'
                inst.installed_apps = MagicMock(side_effect=[[{'id': package.ROOT_APP}], []])
                inst.root_updater_cleanup = MagicMock(return_value={'disabled': True, 'removed': True})
                inst.cleanup_legacy_permissions = MagicMock()
                inst.cleanup_updater_app_permissions = MagicMock()
                inst.verify_project_removed = MagicMock()
                inst.verify_absent = MagicMock()
                inst.root_action = MagicMock()
                # Simulate the structured answer of the installed recovery driver.
                import json
                reply = {'returnValue': True, 'removed': package.ROOT_APP,
                         'state_retained': '/var/lib/clean-your-tv-root'}
                if outcome in ('unknown', 'busy'):
                    reply = {'returnValue': False, 'reason': outcome}
                remote.run.side_effect = [json.dumps({'returnValue': True, 'ready': True}) if outcome in ('completed', 'ready') else json.dumps(reply), json.dumps(reply), '']
                if outcome == 'retry-fails':
                    remote.run.side_effect = [json.dumps({'returnValue': True, 'ready': True}), RuntimeError('connection lost')]
                store.begin(profile, 'uninstall', full_project=True, root_submitted=True,
                            removals={}, updater_archive='/var/lib/clean-your-tv-root-updater.archive-'+'a'*32)
                if outcome in ('completed', 'ready'):
                    self.assertTrue(inst.uninstall(full_project=True)['removed'])
                    self.assertIsNone(store.pending(profile))
                else:
                    with self.assertRaises(RuntimeError):
                        inst.uninstall(full_project=True)
                    self.assertTrue(store.pending(profile)['root_submitted'])
                    if outcome == 'retry-fails':
                        self.assertEqual([c.args[0] for c in inst.root_updater_cleanup.call_args_list], ['disable'])
                    else:
                        inst.root_updater_cleanup.assert_not_called()
                inst.root_action.assert_not_called()
                self.assertTrue(remote.run.called)
