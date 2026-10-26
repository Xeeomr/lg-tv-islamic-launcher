import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
from emergency_gesture import LongBack
class Tests(unittest.TestCase):
 def test_hold_fires_once_without_repeats(self):
  p=LongBack();p.event(1,412,1,100)
  self.assertFalse(p.tick(1299));self.assertTrue(p.tick(1300));self.assertFalse(p.tick(1500))
  p.event(1,412,0,1600);p.event(1,412,1,2000);self.assertTrue(p.tick(3200))
 def test_short_press_and_orphan_repeat_do_not_exit(self):
  p=LongBack();p.event(1,412,1,100);p.event(1,412,0,200);self.assertFalse(p.tick(2000))
  p.event(1,412,2,3000);self.assertFalse(p.tick(5000))
