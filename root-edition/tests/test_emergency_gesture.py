import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
from emergency_gesture import TripleHome
class GestureTests(unittest.TestCase):
 def tap(self,g,t,d=100):
  g.event(1,773,1,t);return g.event(1,773,0,t+d)
 def test_three_completed_short_presses(self):
  g=TripleHome();self.assertFalse(self.tap(g,0));self.assertFalse(self.tap(g,300));self.assertTrue(self.tap(g,600));self.assertFalse(self.tap(g,900))
 def test_long_hold_and_repeat_do_not_count(self):
  g=TripleHome();self.tap(g,0);g.event(1,773,1,300);g.event(1,773,2,400);self.assertFalse(g.event(1,773,0,450));self.assertFalse(self.tap(g,600));self.assertFalse(self.tap(g,900))
 def test_timeout_other_button_and_orphan_release(self):
  g=TripleHome();self.assertFalse(g.event(1,773,0,0));self.tap(g,100);self.tap(g,500);self.assertFalse(self.tap(g,2200));g.event(1,103,1,2400);self.assertFalse(self.tap(g,2600))
 def test_bounce_long_press_clock_reversal(self):
  g=TripleHome();self.assertFalse(self.tap(g,0,5));self.assertFalse(self.tap(g,200,600));self.tap(g,1000);self.tap(g,1300);self.assertFalse(self.tap(g,500))
 def test_dropped_events_fail_closed(self):
  with self.assertRaises(ValueError):TripleHome().event(0,3,0,0)

 def test_cursor_show_does_not_discard_first_home(self):
  # Recorded Magic Remote sequence: cursor-show follows first Home release.
  g=TripleHome()
  events=[(773,1,0),(773,0,159.634),(1198,1,159.945),(1198,0,159.945),
          (773,1,360.822),(773,0,532.053),(773,1,777.511),(773,0,879.616)]
  results=[g.event(1,c,v,t) for c,v,t in events]
  self.assertEqual(results,[False]*7+[True])
