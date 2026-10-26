import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
import helper_bridge as h
import bounded_profile_trial as trial
import device_adapter as d


class HelperIsolationTests(unittest.TestCase):
    def test_active_or_stale_controller_rejected_and_latch_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            state=Path(tmp);proc=state/'proc';proc.mkdir()
            (state/'controller.pid').write_text('123')
            (state/'blocked').write_text('user disabled')
            with patch.object(h,'STATE',state),patch.object(h,'PROC',proc):
                with self.assertRaisesRegex(ValueError,'no-root-helper-active'):h.require_idle()
                self.assertEqual((state/'blocked').read_text(),'user disabled')
                self.assertEqual((state/'controller.pid').read_text(),'123')

    def test_orphan_relay_blocks_trial_even_without_controller(self):
        with tempfile.TemporaryDirectory() as tmp:
            state=Path(tmp);proc=state/'proc';process=proc/'123';process.mkdir(parents=True)
            (process/'cmdline').write_bytes(str(h.APP/'relay').encode()+b'\0')
            with patch.object(h,'STATE',state),patch.object(h,'PROC',proc):
                with self.assertRaisesRegex(ValueError,'no-root-helper-active'):h.require_idle()

    def test_idle_helper_remains_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            state=Path(tmp);proc=state/'proc';proc.mkdir()
            (state/'blocked').write_text('disabled')
            with patch.object(h,'STATE',state),patch.object(h,'PROC',proc):
                self.assertTrue(h.require_idle()['blocked'])
                self.assertEqual((state/'blocked').read_text(),'disabled')

    def test_active_helper_rejection_precedes_routing_and_guardian(self):
        with patch('provision.verify'),patch.object(h,'require_idle',side_effect=ValueError('no-root-helper-active')),patch.object(d,'read') as read:
            with self.assertRaisesRegex(ValueError,'no-root-helper-active'):
                trial.begin(lambda _:self.fail('must not spawn'))
            read.assert_not_called()


if __name__=='__main__':unittest.main()
