import copy
from pathlib import Path
import sys
import unittest
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from updater.device import Device
from updater.store import Store
import os
from types import SimpleNamespace


class DeviceTests(unittest.TestCase):
    def test_route_suspension_uses_transaction_bound_runtime_operation(self):
        tx = {'id':'a'*32, 'phase':'restoring-route'}
        calls=[]
        device=Device(SimpleNamespace(root='/tmp',read=lambda name:tx))
        device.reserve_route=lambda:calls.append(('reserve',None))
        def runtime(mode,transaction=None):
            calls.append((mode,transaction))
            return self.status() if mode=='status' else 'restored'
        device.runtime=runtime
        device.restore_route()
        self.assertEqual([('reserve',None),('suspend-update','a'*32),('status',None)],calls)

    def test_legacy_runtime_is_rejected_before_update_suspension(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'runtime').mkdir()
            code=root/'runtime/update_guard.py'
            code.write_text('HOME_RESUME_PROTOCOL = 0\n')
            with self.assertRaisesRegex(ValueError,'migrate from computer'):
                Device.require_home_resume_runtime(root)
            code.write_text('HOME_RESUME_PROTOCOL = 1\n')
            Device.require_home_resume_runtime(root)

    def test_finish_resumes_only_verified_terminal_outcomes_and_persists_result(self):
        for phase,command in [('complete','finish-update'),('rolled-back','finish-update'),('aborted','abort-update')]:
            with self.subTest(phase=phase),tempfile.TemporaryDirectory() as temp:
                store=Store(os.path.realpath(temp),uid=os.getuid())
                tx={'id':'a'*32,'phase':phase};store.write('transaction',tx)
                device=Device(store);calls=[]
                device.runtime=lambda mode,transaction=None:calls.append((mode,transaction)) or {'status':'restored'}
                device.finish(tx);device.finish(tx)
                self.assertEqual([(command,'a'*32)],calls)
                self.assertEqual({'status':'restored'},store.read('transaction')['homeResume'])
                self.assertEqual(phase,store.read('transaction')['homeResumePhase'])

    def test_finish_cannot_resume_a_superseded_or_unhealthy_transaction(self):
        with tempfile.TemporaryDirectory() as temp:
            store=Store(os.path.realpath(temp),uid=os.getuid())
            device=Device(store);calls=[]
            device.runtime=lambda *args:calls.append(args)
            for phase in ('rolling-back','recovery-required'):
                tx={'id':'a'*32,'phase':phase};store.write('transaction',tx)
                device.finish({'id':'a'*32,'phase':'complete'})
                device.finish(tx)
            store.write('transaction',{'id':'b'*32,'phase':'preparing'})
            device.finish({'id':'a'*32,'phase':'complete'})
            self.assertEqual([],calls)

    def test_home_resume_failure_is_separate_from_successful_package_installation(self):
        with tempfile.TemporaryDirectory() as temp:
            store=Store(os.path.realpath(temp),uid=os.getuid())
            tx={'id':'a'*32,'phase':'complete'};store.write('transaction',tx)
            device=Device(store)
            def fail(*args):raise RuntimeError('guardian did not become ready')
            device.runtime=fail
            device.finish(tx)
            current=store.read('transaction')
            self.assertEqual('complete',current['phase'])
            self.assertEqual('failed',current['homeResume']['status'])
            self.assertIn('guardian',current['homeResume']['error'])

    def test_unresolved_runtime_cleanup_can_be_reconciled_without_reinstalling(self):
        with tempfile.TemporaryDirectory() as temp:
            store=Store(os.path.realpath(temp),uid=os.getuid())
            tx={'id':'a'*32,'phase':'complete'};store.write('transaction',tx)
            device=Device(store);calls=[]
            def finish(mode,transaction):
                calls.append((mode,transaction))
                if len(calls)==1:raise RuntimeError('route recovery incomplete')
                return {'status':'skipped'}
            device.runtime=finish
            device.finish(tx);device.finish(tx)
            self.assertEqual(2,len(calls))
            self.assertEqual({'status':'skipped'},store.read('transaction')['homeResume'])

    def status(self):
        return {'intent':{'phase':'disabled'},'effective':{'sam_home':'com.webos.app.home','profiles':{'defaultApps':{'categories':{'home':'com.webos.app.home'}},'idleApp':{'appId':'com.webos.app.home','support':True}}}}

    def test_route_readback_cannot_be_inferred_from_disabled_intent(self):
        status=self.status()
        self.assertEqual({'active':False,'safe':True,'intent':{'phase':'disabled'}},Device.route_state(status))
        status['effective']['sam_home']='com.cleanyourtv.root.preview'
        self.assertTrue(Device.route_state(status)['active']);self.assertFalse(Device.route_state(status)['safe'])
        status=self.status();status['effective']['profiles']['idleApp']['appId']='other'
        self.assertFalse(Device.route_state(status)['safe'])
        self.assertFalse(Device.route_state({'intent':{'phase':'disabled'}})['safe'])

    def test_active_and_legacy_trial_routing_is_recorded_for_post_update_choice(self):
        status=self.status();status['intent']={'phase':'active'}
        self.assertTrue(Device.route_state(status)['active'])
        status=self.status();status['intent']=None
        status['effective']['profiles']['defaultApps']['categories']['home']='com.cleanyourtv.root.preview'
        self.assertTrue(Device.route_state(status)['active'])


if __name__=='__main__':unittest.main()
