import sys,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
import shutdown_state as s
class Tests(unittest.TestCase):
 def test_only_manager_stopping_is_accepted(self):
  for state in ('stopping\n','running\n','degraded\n','offline\n','unknown\n',''):
   with patch.object(s.subprocess,'run',return_value=subprocess.CompletedProcess([],1,stdout=state,stderr='')):
    self.assertEqual(s.stopping(),state=='stopping\n')
 def test_unavailable_manager_is_not_shutdown_permission(self):
  with patch.object(s.subprocess,'run',side_effect=OSError()):self.assertFalse(s.stopping())

class CachedTests(unittest.TestCase):
 def test_recent_confirmed_shutdown_survives_query_timeout_but_expires(self):
  import tempfile,os
  import persistent_health as h,device_adapter as d
  with tempfile.TemporaryDirectory() as tmp,patch.object(h,'ROOT',Path(tmp)),patch.object(d,'EXPECTED_UID',os.getuid()),patch('intent_runtime.boot_identity',return_value='boot-a'):
   with patch.object(s.time,'monotonic',return_value=10):s.record('tx')
   with patch.object(s.time,'monotonic',return_value=11),patch.object(s.subprocess,'run',side_effect=subprocess.TimeoutExpired('systemctl',.5)):
    self.assertTrue(s.stopping('tx'));self.assertFalse(s.stopping('other'))
   with patch.object(s.time,'monotonic',return_value=16),patch.object(s.subprocess,'run',side_effect=OSError()):
    self.assertFalse(s.stopping('tx'))
 def test_cached_shutdown_from_previous_boot_is_rejected(self):
  import tempfile,os
  import persistent_health as h,device_adapter as d
  with tempfile.TemporaryDirectory() as tmp,patch.object(h,'ROOT',Path(tmp)),patch.object(d,'EXPECTED_UID',os.getuid()):
   with patch('intent_runtime.boot_identity',return_value='old'):s.record('tx')
   with patch('intent_runtime.boot_identity',return_value='new'),patch.object(s.subprocess,'run',side_effect=OSError()):self.assertFalse(s.stopping('tx'))
