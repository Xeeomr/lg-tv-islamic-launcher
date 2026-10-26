import os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
import shutdown_state as s

class ReasonTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.path=self.root/'reason'
  self.addCleanup(self.tmp.cleanup)
 def test_new_trusted_remote_request_is_observed_once(self):
  with patch.object(s.d,'EXPECTED_UID',os.getuid()):
   observer=s.PowerReason(self.path)
   self.assertFalse(observer.poll())
   self.path.write_text('poweroff_reason=remoteKey\n')
   self.assertTrue(observer.poll());self.assertFalse(observer.poll())
 def test_preexisting_request_never_authorizes(self):
  self.path.write_text('poweroff_reason=remoteKey\n')
  with patch.object(s.d,'EXPECTED_UID',os.getuid()):
   observer=s.PowerReason(self.path)
   self.assertFalse(observer.poll());self.assertFalse(observer.poll())
 def test_crash_unknown_malformed_and_writable_requests_fail_closed(self):
  for value in ('poweroff_reason=watchdog','poweroff_reason=unknown','remoteKey','poweroff_reason=remoteKey\nextra'):
   self.path.unlink(missing_ok=True)
   with patch.object(s.d,'EXPECTED_UID',os.getuid()):
    observer=s.PowerReason(self.path);observer.poll();self.path.write_text(value)
    self.assertFalse(observer.poll())
  self.path.unlink()
  with patch.object(s.d,'EXPECTED_UID',os.getuid()):
   observer=s.PowerReason(self.path);observer.poll();self.path.write_text('poweroff_reason=remoteKey');self.path.chmod(0o666)
   self.assertFalse(observer.poll())
 def test_symlink_and_foreign_owner_are_rejected(self):
  target=self.root/'other';target.write_text('poweroff_reason=remoteKey')
  with patch.object(s.d,'EXPECTED_UID',os.getuid()):
   observer=s.PowerReason(self.path);observer.poll();self.path.symlink_to(target)
   self.assertFalse(observer.poll())
  self.path.unlink()
  with patch.object(s.d,'EXPECTED_UID',os.getuid()+1):
   observer=s.PowerReason(self.path);observer.poll();self.path.write_text('poweroff_reason=remoteKey')
   self.assertFalse(observer.poll())

class MonitorTests(unittest.TestCase):
 def test_blocked_manager_does_not_block_request_and_record_retry(self):
  import threading,time
  observer=unittest.mock.Mock()
  observer.poll.side_effect=[False,True]+[False]*100
  recorded=threading.Event();release=threading.Event();attempts=[]
  def record(*args,**kwargs):
   attempts.append(1)
   if len(attempts)==1:raise OSError('transient write failure')
   recorded.set()
  with patch.object(s,'PowerReason',return_value=observer),patch.object(s,'query',side_effect=lambda: release.wait(2) and False),patch.object(s,'record',side_effect=record):
   stop=s.monitor('tx')
   try:self.assertTrue(recorded.wait(1));self.assertEqual(len(attempts),2)
   finally:stop.set();release.set();time.sleep(.1)
