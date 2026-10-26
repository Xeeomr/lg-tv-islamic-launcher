import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
from installer_status import Completion
class Tests(unittest.TestCase):
 def event(self,**extra):
  r={'id':'test.app','statusValue':30,'details':{'packageId':'test.app','ipkFile':'/private/test.ipk','client':'com.webos.lunasend-42'}};r.update(extra);return r
 def test_timeout_idle_or_disconnect_is_not_completion(self):
  c=Completion('test.app','/private/test.ipk','com.webos.lunasend-42')
  for r in ({'returnValue':True,'status':{'apps':[]}}, {'returnValue':False}, {'subscribed':True},self.event(statusValue=17)):
   self.assertFalse(c.feed(r))
 def test_only_matching_final_success_authorizes_next_install(self):
  for field,value in [('packageId','other'),('ipkFile','/other'),('client','com.webos.lunasend-43')]:
   c=Completion('test.app','/private/test.ipk','com.webos.lunasend-42');r=self.event();r['details'][field]=value;self.assertFalse(c.feed(r))
  c=Completion('test.app','/private/test.ipk','com.webos.lunasend-42');self.assertFalse(c.feed(self.event(id='other')));self.assertTrue(c.feed(self.event()))
 def test_error_payload_cannot_look_like_success(self):
  c=Completion('test.app','/private/test.ipk','com.webos.lunasend-42');r=self.event();r['details']['errorCode']=1;self.assertFalse(c.feed(r))
 def test_top_level_error_cannot_complete(self):
  c=Completion('test.app','/private/test.ipk','com.webos.lunasend-42');self.assertFalse(c.feed(self.event(errorCode=1)))
 def test_malformed_payload_fails_closed(self):
  c=Completion('test.app','/private/test.ipk','com.webos.lunasend-42')
  for r in (None,[],{},self.event(details=None),self.event(statusValue='30')):self.assertFalse(c.feed(r))
if __name__=='__main__':unittest.main()
