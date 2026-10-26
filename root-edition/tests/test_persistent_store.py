import json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
import device_adapter as d
from persistent_lifecycle import initial
from persistent_store import Store

class StoreTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.root.chmod(0o700)
  self.uid=patch.object(d,'EXPECTED_UID',os.getuid());self.uid.start();self.store=Store(self.root)
 def tearDown(self):self.uid.stop();self.tmp.cleanup()
 def event(self,s,kind,**kw):return dict(kind=kind,generation=s['generation'],**kw)
 def enable(self):
  s=self.store.read()
  return self.store.apply(s,self.event(s,'enable',boot='a',token='t'))[0]
 def test_reload_unconfirmed_trial_never_enables(self):
  s=self.enable();again=Store(self.root);self.assertEqual(again.read(),s)
  n,e=again.apply(s,self.event(s,'boot',boot='b',token='b',failsafe=False))
  self.assertFalse(n['enabled']);self.assertEqual(e,'recover')
 def test_exit_remains_disabled_after_disk_reload(self):
  s=self.enable();s,_=self.store.apply(s,self.event(s,'confirmed',token='t'))
  s,e=self.store.apply(s,self.event(s,'exit',token='t'))
  self.assertEqual(e,'recover');self.assertFalse(Store(self.root).read()['enabled'])
 def test_stale_snapshot_cannot_commit_after_exit(self):
  s=self.enable();n,_=self.store.apply(s,self.event(s,'fault',token='t'))
  with self.assertRaises(ValueError):self.store.apply(s,self.event(s,'confirmed',token='t'))
  self.assertEqual(self.store.read(),n)
 def test_replace_failure_preserves_previous_and_no_effect_returned(self):
  s=self.enable()
  with patch('persistent_store.os.replace',side_effect=OSError('disk failure')):
   with self.assertRaises(OSError):self.store.apply(s,self.event(s,'confirmed',token='t'))
  self.assertEqual(Store(self.root).read(),s)
  self.assertEqual(list(self.root.glob('.intent-*')),[])
 def test_fsync_failure_does_not_return_activation_effect(self):
  s=initial()
  with patch('persistent_store.os.fsync',side_effect=OSError('full disk')):
   with self.assertRaises(OSError):self.store.apply(s,self.event(s,'enable',boot='a',token='t'))
  self.assertEqual(self.store.read(),s)
 def test_symlink_journal_and_lock_rejected(self):
  outside=self.root/'outside';outside.write_text(json.dumps(initial()))
  for name in ('persistent-intent.json','persistent-intent.lock'):
   target=self.root/name;target.symlink_to(outside)
   with self.assertRaises((ValueError,OSError)):self.enable()
   target.unlink()
 def test_unsafe_permissions_and_corrupt_journal_rejected(self):
  self.enable();p=self.root/'persistent-intent.json';p.chmod(0o666)
  with self.assertRaises(ValueError):self.store.read()
  p.chmod(0o600);p.write_text('{}')
  with self.assertRaises(ValueError):self.store.read()
 def test_reload_interrupted_recovery_disables_restart(self):
  s=self.enable();s,_=self.store.apply(s,self.event(s,'confirmed',token='t'))
  s,_=self.store.apply(s,self.event(s,'boot',boot='b',token='b',failsafe=False))
  again=Store(self.root);s=again.read()
  s,e=again.apply(s,self.event(s,'boot',boot='c',token='c',failsafe=False))
  self.assertEqual(e,'recover');self.assertFalse(s['enabled'])
 def test_read_does_not_create_state(self):
  self.assertEqual(self.store.read(),initial());self.assertEqual(list(self.root.iterdir()),[])
