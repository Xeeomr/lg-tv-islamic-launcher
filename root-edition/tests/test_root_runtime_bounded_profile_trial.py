import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"runtime"))
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import bounded_profile_trial as b
import device_adapter as d
from profile_plan import snapshot,STOCK,CANDIDATE
from test_root_runtime_profile_plan import response


class TrialTests(unittest.TestCase):
    def setUp(self):
        provision = patch("provision.verify", return_value={"integrity_verified":True})
        provision.start()
        self.addCleanup(provision.stop)
        helper = patch("helper_bridge.require_idle", return_value={})
        helper.start()
        self.addCleanup(helper.stop)

    def fixture(self, mode, candidate=CANDIDATE):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); target=root/'candidate'; sam=[STOCK]
            baseline=snapshot(response(),STOCK)
            def read():
                value=copy.deepcopy(baseline); value['sam_home']=sam[0]
                if target.exists():
                    value['profiles']['defaultApps']['categories']['home']=candidate
                    value['profiles']['idleApp']['appId']=candidate
                if mode=='readback' and target.exists(): value['profiles']['idleApp']['support']=False
                return value
            class Transport:
                def call(self,uri,payload):
                    if uri.endswith('/setDefaultApp'): sam[0]=payload['appId']
                    return {'appInfo':{'id':candidate,'type':'web','version':'1.1.0','appCategory':[] if mode=='no-category' else ['home']},'returnValue':True}
                def write(self,target): sam[0]=target
            class Child:
                pid=123
                def poll(self): return 1 if mode=='dead' else None
            def bind(tx):
                self.assertFalse(target.exists())
                self.assertEqual(sam[0],STOCK)
                self.assertEqual(d.safe_json(root/'profile-trial.json')['transaction'],tx)
                raise ValueError('binding persistence failed')
            def spawn(tx):
                j=d.safe_json(root/'profile-trial.json')
                (root/'profile-guardian-ready.json').write_text(json.dumps(
                    {'transaction':tx,'deadline':j['deadline'],'pid':123}))
                (root/'profile-guardian-ready.json').chmod(0o600)
                return Child()
            with patch.object(d,'STATE',root),patch.object(d,'TARGET',target), \
                    patch.object(d,'EXPECTED_UID',os.geteuid()),patch.object(d,'read',side_effect=read), \
                    patch.object(d,'sam_transport',return_value=Transport()),patch.object(b.time,'sleep'):
                if mode=='bind-failed':
                    with self.assertRaisesRegex(ValueError,'binding persistence failed'):
                        b.begin(lambda tx:self.fail('guardian should not start'), before_publish=bind)
                    self.assertFalse(target.exists());self.assertEqual(sam[0],STOCK)
                    self.assertEqual(d.safe_json(root/'profile-trial.json')['state'],'restored')
                    return
                if mode=='no-category':
                    with self.assertRaises(ValueError): b.begin(spawn,candidate=candidate)
                    self.assertFalse(target.exists())
                    self.assertFalse((root/'profile-trial.json').exists())
                    self.assertEqual(sam[0],STOCK)
                    return
                if mode=='ok':
                    result=b.begin(spawn,candidate=candidate); self.assertEqual(result['effective']['sam_home'],candidate)
                    self.assertTrue(target.exists())
                    self.assertEqual(d.restore_once(result['transaction']),'restored')
                else:
                    with self.assertRaises(RuntimeError): b.begin(spawn,candidate=candidate)
                self.assertFalse(target.exists())
                self.assertEqual(read(),baseline)
                self.assertEqual(d.safe_json(root/'profile-trial.json')['state'],'restored')

    def test_no_root_launcher_is_rejected(self):
        with self.assertRaises(ValueError): self.fixture('ok','com.gathin.tvhome')
    def test_unregistered_home_category_prevents_any_trial(self): self.fixture('no-category')

    def test_binding_is_durable_before_any_publication(self): self.fixture('bind-failed')

    def test_apply_and_full_recovery(self): self.fixture('ok')
    def test_dead_guardian_prevents_publication(self): self.fixture('dead')
    def test_readback_mismatch_triggers_immediate_recovery(self): self.fixture('readback')


if __name__=='__main__': unittest.main()
