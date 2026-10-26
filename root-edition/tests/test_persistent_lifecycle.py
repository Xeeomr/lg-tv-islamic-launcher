import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'runtime'))
from persistent_lifecycle import initial, transition

class LifecycleTests(unittest.TestCase):
 def apply(self, state, kind, **kw):
  return transition(state, dict(kind=kind, generation=state['generation'], **kw))
 def enabled(self):
  s,_=self.apply(initial(),'enable',boot='boot-a',token='trial-a')
  return self.apply(s,'confirmed',token='trial-a')[0]
 def test_requires_explicit_confirmation(self):
  s,e=self.apply(initial(),'enable',boot='boot-a',token='trial-a')
  self.assertEqual((s['phase'],s['enabled'],e),('trial',False,'start_guarded'))
  s,e=self.apply(s,'confirmed',token='trial-a')
  self.assertEqual((s['phase'],s['enabled'],e),('active',True,'none'))
 def test_expired_trial_never_persists(self):
  s,_=self.apply(initial(),'enable',boot='a',token='t')
  s,e=self.apply(s,'fault',token='t')
  self.assertFalse(s['enabled']);self.assertEqual(e,'recover')
 def test_normal_boot_restores_before_start(self):
  s,e=self.apply(self.enabled(),'boot',boot='boot-b',token='start-b',failsafe=False)
  self.assertEqual((s['phase'],e),('recovering','recover'))
  s,e=self.apply(s,'restored',token='start-b')
  self.assertEqual((s['phase'],e),('starting','start_guarded'))
  s,e=self.apply(s,'ready',token='start-b')
  self.assertEqual((s['phase'],s['enabled'],e),('active',True,'none'))
 def test_duplicate_boot_does_not_cancel_live_mode(self):
  s=self.enabled();n,e=self.apply(s,'boot',boot='boot-a',token='ignored',failsafe=False)
  self.assertEqual((n,e),(s,'none'))
 def test_duplicate_callback_during_start_does_not_restart(self):
  s,_=self.apply(self.enabled(),'boot',boot='b',token='b',failsafe=False)
  s,_=self.apply(s,'restored',token='b')
  n,e=self.apply(s,'boot',boot='b',token='different',failsafe=False)
  self.assertEqual((n,e),(s,'none'))
 def test_interrupted_start_on_next_boot_disables(self):
  s,_=self.apply(self.enabled(),'boot',boot='b',token='b',failsafe=False)
  s,_=self.apply(s,'restored',token='b')
  s,e=self.apply(s,'boot',boot='c',token='c',failsafe=False)
  self.assertEqual((s['enabled'],s['phase'],e),(False,'recovering','recover'))
  s,e=self.apply(s,'restored',token='c')
  self.assertEqual((s['phase'],e),('disabled','none'))
 def test_exit_is_durable_before_restore(self):
  s,e=self.apply(self.enabled(),'exit',token='trial-a')
  self.assertEqual((s['enabled'],s['phase'],e),(False,'recovering','recover'))
  s,e=self.apply(s,'boot',boot='b',token='b',failsafe=False)
  s,e=self.apply(s,'restored',token='b')
  self.assertEqual((s['enabled'],s['phase'],e),(False,'disabled','none'))
 def test_failsafe_overrides_same_boot(self):
  s,e=self.apply(self.enabled(),'boot',boot='boot-a',token='fs',failsafe=True)
  self.assertEqual((s['enabled'],e),(False,'recover'))
 def test_stale_confirmation_and_stale_fault_noop(self):
  s=self.enabled()
  for kind in ('confirmed','fault','exit','restored','ready'):
   n,e=transition(s,dict(kind=kind,generation=s['generation']-1,token=s['token']))
   self.assertEqual((n,e),(s,'none'))
   n,e=self.apply(s,kind,token='old-token')
   self.assertEqual((n,e),(s,'none'))
 def test_failed_restore_requires_explicit_enable_after_recovery(self):
  s,_=self.apply(self.enabled(),'boot',boot='b',token='b',failsafe=False)
  s,e=self.apply(s,'fault',token='b')
  self.assertFalse(s['enabled']);self.assertEqual(e,'recover')
  s,e=self.apply(s,'restored',token='b')
  self.assertEqual((s['phase'],e),('disabled','none'))
 def test_cannot_enable_during_recovery(self):
  s,_=self.apply(self.enabled(),'exit',token='trial-a')
  with self.assertRaises(ValueError):self.apply(s,'enable',boot='a',token='new')
 def test_invalid_state_and_events_rejected(self):
  for state in ({},dict(initial(),enabled='yes'),dict(initial(),generation=True)):
   with self.assertRaises(ValueError):transition(state,dict(kind='boot',generation=0,boot='a',token='x',failsafe=False))
  for kw in ({'kind':'invalid'}, {'kind':'boot','boot':'','token':'x','failsafe':False}):
   with self.assertRaises(ValueError):transition(initial(),dict(generation=0,**kw))
