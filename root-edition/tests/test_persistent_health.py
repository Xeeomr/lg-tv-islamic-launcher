import json,os,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
import device_adapter as d
import persistent_health as h
from test_persistent_recovery import IntegrationTests

class HealthTests(IntegrationTests):
 def setUp(self):
  super().setUp()
  self.health=self.root/'volatile';self.health.mkdir(mode=0o700)
  self.hp=patch.object(h,'ROOT',self.health);self.hp.start()
  self.bp=patch('intent_runtime.boot_identity',return_value='boot-a');self.bp.start()
 def tearDown(self):
  self.bp.stop();self.hp.stop();super().tearDown()
 def test_only_current_binding_can_publish(self):
  h.publish('route-a',1)
  with self.assertRaises(ValueError):h.publish('old',2)
  self.assertEqual(h.load('route-a')['sequence'],1)
 def test_expired_heartbeat_is_not_health(self):
  with patch.object(h.time,'monotonic',return_value=10):h.publish('route-a',1)
  with patch.object(h.time,'monotonic',return_value=13):
   with self.assertRaises(ValueError):h.require_fresh('route-a')
 def test_exit_revokes_persistent_authority(self):
  h.publish('route-a',1);self.assertTrue(h.authorized('route-a'))
  self.c.exit(self.intent)
  self.assertFalse(h.authorized('route-a'))
 def test_previous_boot_lease_cannot_be_used(self):
  h.publish('route-a',1)
  with patch('intent_runtime.boot_identity',return_value='boot-b'):
   with self.assertRaises(ValueError):h.require_fresh('route-a')
 def test_lease_is_private_and_volatile(self):
  h.publish('route-a',1)
  self.assertEqual(h.path('route-a').stat().st_mode & 0o777,0o600)
  self.assertFalse((self.root/'lease.json').exists())

 # Exercise the actual publisher/reader contract at a binary exponent boundary.
 def test_publisher_two_seconds_are_valid_at_float_boundaries(self):
  for seq,issued in enumerate((62.4,126.4,254.4,510.4,1022.4),1):
   with patch.object(h.time,'monotonic',return_value=issued):
    h.publish('route-a',seq)
    self.assertEqual(h.require_fresh('route-a')['sequence'],seq)
   with patch.object(h.time,'monotonic',return_value=issued+2):
    with self.assertRaises(ValueError):h.require_fresh('route-a')

if __name__=='__main__':unittest.main()

class GuardianPulseTests(unittest.TestCase):
 def test_missing_or_stalled_guardian_pulse_is_not_healthy(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(h,'ROOT',Path(tmp)),patch.object(d,'EXPECTED_UID',os.getuid()):
   with self.assertRaises(OSError):h.require_guardian('tx')
   with patch.object(h.time,'monotonic',return_value=10):h.guardian_ping('tx')
   with patch.object(h.time,'monotonic',return_value=11):h.require_guardian('tx')
   with patch.object(h.time,'monotonic',return_value=13):
    with self.assertRaises(ValueError):h.require_guardian('tx')

class IndependentDeviceGuardTests(unittest.TestCase):
 def test_real_health_adapter_recovers_when_publisher_is_stopped(self):
  import subprocess,signal,select
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);volatile=root/'health';volatile.mkdir(mode=0o700)
   state=dict(version=1,generation=1,phase='active',enabled=True,boot='boot-a',token='attempt-a')
   (root/'persistent-intent.json').write_text(json.dumps(state))
   (root/'persistent-binding.json').write_text(json.dumps(dict(version=1,generation=1,token='attempt-a',transaction='tx',restored=False)))
   (root/'profile-trial.json').write_text(json.dumps(dict(transaction='tx',state='pending')))
   setup="""
import os,sys,time
from pathlib import Path
import persistent_health as h, intent_runtime, device_adapter as d
d.STATE=Path(sys.argv[1]);d.EXPECTED_UID=os.getuid();h.ROOT=d.STATE/'health'
intent_runtime.boot_identity=lambda:'boot-a'
"""
   pub=setup+"\nseq=0\nwhile True:\n seq+=1;h.publish('tx',seq)\n if seq==1:print('READY',flush=True)\n time.sleep(.1)\n"
   guard=setup+"\nprint('READY',flush=True)\nh.run('tx',lambda tx:(d.STATE/'recovered').write_text(tx))\n"
   cwd=Path(__file__).resolve().parents[1]/'runtime'
   p=subprocess.Popen([sys.executable,'-c',pub,tmp],cwd=cwd,stdout=subprocess.PIPE,text=True);g=None
   try:
    self.assertTrue(select.select([p.stdout],[],[],3)[0]);self.assertEqual(p.stdout.readline().strip(),'READY')
    g=subprocess.Popen([sys.executable,'-c',guard,tmp],cwd=cwd,stdout=subprocess.PIPE,text=True)
    self.assertTrue(select.select([g.stdout],[],[],3)[0]);self.assertEqual(g.stdout.readline().strip(),'READY')
    os.kill(p.pid,signal.SIGSTOP)
    self.assertEqual(g.wait(timeout=5),0);self.assertIsNone(p.poll())
    self.assertEqual((root/'recovered').read_text(),'tx')
   finally:
    p.kill();p.wait();p.stdout.close()
    if g is not None:
     if g.poll() is None:g.kill();g.wait()
     g.stdout.close()
