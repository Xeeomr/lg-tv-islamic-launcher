import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
import boot_gate as g

class GateTests(unittest.TestCase):
    def run_gate(self, observations):
        clock=[0.0]; values=iter(observations); last=[None]
        def observe():
            try:last[0]=next(values)
            except StopIteration:pass
            return last[0]
        def sleep(t):clock[0]+=t
        return g.wait(observe,timeout=3,clock=lambda:clock[0],sleep=sleep)
    def test_normal_start_waits_for_flag_clear(self):
        self.assertTrue(self.run_gate([(False,False),(False,True),(True,True),(True,False)]))
    def test_real_failsafe_flag_clear_does_not_authorize(self):
        self.assertFalse(self.run_gate([(False,True),(False,False)]))
    def test_never_started_homebrew_is_not_ready(self):
        self.assertFalse(self.run_gate([(False,False)]))
    def test_normal_hook_with_stuck_flag_still_refuses(self):
        self.assertFalse(self.run_gate([(True,True)]))
    def test_complete_normal_boot_is_ready(self):
        self.assertTrue(self.run_gate([(True,False)]))
