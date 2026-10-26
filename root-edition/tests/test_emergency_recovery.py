import sys,unittest
from pathlib import Path
from unittest.mock import patch,Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
import emergency_trial as e
class RecoveryTests(unittest.TestCase):
 def test_superseded_never_launches_or_reads_new_state(self):
  with patch.object(e.d,'restore_once',return_value='superseded') as restore,patch.object(e.d,'read') as read,patch.object(e.d,'sam_transport') as bus:
   self.assertTrue(e.recover('old','escape'));restore.assert_called_once_with(expected_transaction='old');read.assert_not_called();bus.assert_not_called()
 def test_conflict_does_not_launch(self):
  with patch.object(e.d,'restore_once',return_value='conflict'),patch.object(e.d,'sam_transport') as bus:
   self.assertFalse(e.recover('tx','escape'));bus.assert_not_called()
 def test_mismatched_readback_never_launches(self):
  with patch.object(e.d,'restore_once',return_value='restored'),patch.object(e.d,'safe_json',return_value={'transaction':'tx','baseline':{'home':'stock'}}),patch.object(e.d,'read',return_value={'home':'other'}),patch.object(e.d,'sam_transport') as bus:
   self.assertFalse(e.recover('tx','escape'));bus.assert_not_called()
 def test_verified_restore_launches_only_lg_home(self):
  bus=Mock()
  with patch.object(e.d,'restore_once',return_value='restored'),patch.object(e.d,'safe_json',return_value={'transaction':'tx','baseline':{'home':'stock'}}),patch.object(e.d,'read',return_value={'home':'stock'}),patch.object(e.d,'sam_transport',return_value=bus):
   self.assertTrue(e.recover('tx','escape'));bus.call.assert_called_once_with('luna://com.webos.applicationManager/launch',{'id':'com.webos.app.home'})
 def test_no_ready_prevents_returning_guardian_for_publication(self):
  supervisor=Mock(pid=123);supervisor.poll.return_value=1
  guardian=Mock(pid=456)
  with patch.object(e.bounded,'spawn',return_value=guardian),patch.object(e.subprocess,'Popen',return_value=supervisor),patch.object(e.os,'open',return_value=9),patch.object(e.os,'close'),patch.object(e.d,'safe_json',return_value={}),patch.object(e.bounded,'begin',side_effect=lambda spawn:spawn('tx')):
   with self.assertRaisesRegex(RuntimeError,'before activation'):e.start()
