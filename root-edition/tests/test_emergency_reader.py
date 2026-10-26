import os,select,struct,subprocess,sys,unittest
from pathlib import Path
RUNTIME=Path(__file__).resolve().parents[1]/'runtime'
sys.path.insert(0,str(RUNTIME))
from emergency_watchdog import watch
class ReaderTests(unittest.TestCase):
 def run_input(self,events):
  ir,iw=os.pipe();hr,hw=os.pipe();env=os.environ.copy();env['PYTHONPATH']=str(RUNTIME)
  code='import sys;from emergency_reader import observe;observe(int(sys.argv[1]),int(sys.argv[2]),lambda:True)'
  p=subprocess.Popen([sys.executable,'-c',code,str(ir),str(hw)],pass_fds=(ir,hw),env=env,stderr=subprocess.PIPE)
  os.close(ir);os.close(hw)
  try:
   self.assertTrue(select.select([hr],[],[],2)[0]);os.write(iw,events)
   return watch(hr,lambda reason:True,timeout=.5)
  finally:
   if p.poll() is None:p.kill()
   p.communicate();os.close(iw);os.close(hr)
 def test_three_taps_pass_through_reader_to_watchdog(self):
  data=b''.join(struct.pack('<IIHHi',1,t*1000,1,773,v) for t,v in [(0,1),(100,0),(300,1),(400,0),(600,1),(700,0)])
  self.assertEqual(self.run_input(data),'escape')
 def test_input_loss_recovers(self):
  self.assertEqual(self.run_input(struct.pack('<IIHHi',1,0,0,3,0)),'input_lost')
 def test_partial_event_recovers(self):
  self.assertEqual(self.run_input(b'bad'),'input_lost')

class DiscoveryTests(unittest.TestCase):
 def test_disconnected_unrelated_node_is_skipped(self):
  import emergency_reader as r,errno
  from unittest.mock import patch,Mock
  paths=[Path('/dev/input/event11'),Path('/dev/input/event3')]
  def opened(path,flags):
   self.assertEqual(flags & os.O_ACCMODE,os.O_RDONLY)
   if path==paths[0]:raise OSError(errno.ENXIO,'inactive')
   return 42
  with patch.object(r.struct,'calcsize',side_effect=lambda fmt:16 if fmt=='@llHHi' else 4),patch.object(r.Path,'glob',return_value=paths),patch.object(r.os,'open',side_effect=opened),patch.object(r.os,'fstat',return_value=Mock(st_mode=0o020600)),patch.object(r,'query',return_value=r.NAME+b'\0'),patch.object(r.os,'close'):
   self.assertEqual(r.open_remote(),42)
