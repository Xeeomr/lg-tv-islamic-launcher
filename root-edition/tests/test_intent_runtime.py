import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch,Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
import intent_runtime as r

class RuntimeTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  self.state=patch.object(r.d,'STATE',self.root);self.state.start();self.addCleanup(self.state.stop)
  self.uid=patch.object(r.d,'EXPECTED_UID',__import__('os').getuid());self.uid.start();self.addCleanup(self.uid.stop)
  (self.root/'persistent-intent.json').write_text('{}')
  self.audit=patch('boot_gate.audit');self.audit.start();self.addCleanup(self.audit.stop)
  self.observation=patch('boot_gate.observation',return_value=(False,False));self.observation.start();self.addCleanup(self.observation.stop)
 def tearDown(self):self.tmp.cleanup()
 def test_snapshot_boot_identity_includes_kernel_start_time(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'sys/kernel/random').mkdir(parents=True)
   (p/'sys/kernel/random/boot_id').write_text('abc-boot\n');(p/'stat').write_text('cpu 1\nbtime 100\n')
   a=r.boot_identity(p);(p/'stat').write_text('cpu 1\nbtime 200\n')
   self.assertNotEqual(a,r.boot_identity(p))
 def test_missing_identity_is_not_inferred_from_wall_clock(self):
  with tempfile.TemporaryDirectory() as tmp:
   with self.assertRaises(OSError):r.boot_identity(Path(tmp))
 def test_legacy_install_has_no_intent_side_effects(self):
  with patch.object(r.os.path,'lexists',return_value=False),patch.object(r,'Coordinator') as c:
   self.assertIsNone(r.restore());self.assertIsNone(r.boot());c.assert_not_called()
 def test_bound_restore_uses_intent_coordinator(self):
  c=Mock(binding=self.root/'missing-binding');c.store.read.return_value={'phase':'active'};c.exit.return_value={'restored_transaction':'tx'}
  with patch.object(r,'coordinator',return_value=c):self.assertEqual(r.restore(),'restored')
  c.exit.assert_called_once_with({'phase':'active'})
 def test_live_bounded_guard_is_preserved_on_duplicate_boot(self):
  c=Mock(binding=self.root/'missing-binding');s={'boot':'same','phase':'trial'};c.store.read.return_value=s
  with patch.object(r,'coordinator',return_value=c),patch.object(r,'boot_identity',return_value='same'),patch.object(r.d.FAILSAFE.__class__,'exists',return_value=False),patch.object(r.d,'safe_json',return_value={}),patch.object(r.d,'active_guardian',return_value=True):
   self.assertEqual(r.boot(),'guarded-intent-trial')
  c.boot.assert_not_called()
 def test_failsafe_never_preserves_guarded_route(self):
  c=Mock(binding=self.root/'missing-binding');c.store.read.return_value={'boot':'same','phase':'trial'}
  c.boot.return_value={'effect':'none','intent':{'phase':'disabled'}}
  with patch.object(r,'coordinator',return_value=c),patch.object(r,'boot_identity',return_value='same'),patch.object(r.d.FAILSAFE.__class__,'exists',return_value=True),patch.object(r.d,'active_guardian',return_value=True):r.boot()
  self.assertTrue(c.boot.call_args.args[-1])
 def test_boot_restarts_only_after_coordinator_verified_recovery(self):
  c=Mock(binding=self.root/'missing-binding');c.store.read.return_value={'boot':'old','phase':'active'}
  new={'phase':'starting'};c.boot.return_value={'effect':'start_guarded','intent':new}
  with patch.object(r,'coordinator',return_value=c),patch.object(r,'boot_identity',return_value='new'),patch('boot_gate.wait',return_value=True),patch.object(r.d.FAILSAFE.__class__,'exists',return_value=False):r.boot()
  c.restart.assert_called_once_with(new)
  c.exit.assert_not_called()

 def test_true_failsafe_restores_before_refusing_restart(self):
  c=Mock(binding=self.root/'missing-binding');c.store.read.return_value={'boot':'old','phase':'active'}
  new={'phase':'starting'};c.boot.return_value={'effect':'start_guarded','intent':new}
  def refused():
   c.boot.assert_called_once();c.restart.assert_not_called();return False
  with patch.object(r,'coordinator',return_value=c),patch.object(r,'boot_identity',return_value='new'),patch.object(r.d.FAILSAFE.__class__,'exists',return_value=True),patch('boot_gate.wait',side_effect=refused):
   self.assertEqual(r.boot(),'restored')
  c.exit.assert_called_once_with(new,reason='fault');c.restart.assert_not_called()

 def test_duplicate_callback_during_shutdown_does_not_revoke_or_restart(self):
  c=Mock(binding=self.root/'missing-binding');intent={'boot':'same','phase':'stopping'};c.store.read.return_value=intent
  with patch.object(r,'coordinator',return_value=c),patch.object(r,'boot_identity',return_value='same'),patch.object(r.d.FAILSAFE.__class__,'exists',return_value=False):
   self.assertEqual(r.boot(),'shutdown-pending')
  c.shutdown.assert_called_once_with(intent);c.exit.assert_not_called();c.restart.assert_not_called()

 def test_duplicate_boot_during_gate_wait_cannot_disable_starting_intent(self):
  current=[{'boot':'old','phase':'active'}]
  new={'boot':'new','phase':'starting'}
  c=Mock(binding=self.root/'missing-binding');c.store.read.side_effect=lambda:current[0]
  def recover(*args):
   current[0]=new;return {'effect':'start_guarded','intent':new}
  c.boot.side_effect=recover
  def gate():
   self.assertEqual(r.boot(),'boot-in-progress')
   c.exit.assert_not_called()
   return True
  with patch.object(r,'coordinator',return_value=c),patch.object(r,'boot_identity',return_value='new'),patch.object(r.d.FAILSAFE.__class__,'exists',return_value=False),patch('boot_gate.wait',side_effect=gate),patch.object(r.d,'safe_json',return_value={}),patch.object(r.d,'active_guardian',return_value=False):
   r.boot()
  c.restart.assert_called_once_with(new);c.exit.assert_not_called()
