import sys,tempfile,json,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]))
import activity as a
class Tests(unittest.TestCase):
 def test_registration_repeat_and_owned_removal(self):
  spec=json.loads((Path(__file__).parents[1]/'service/activity.json').read_text());items=[]
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'service').mkdir();(root/'service/activity.json').write_text(json.dumps(spec))
   def call(method,payload):
    if method=='list':
     self.assertEqual(payload,dict(details=True,subscribers=True,current=False,internal=False));return {'activities':list(items)}
    if method=='create':items.append(dict(spec,creator={'serviceId':a.SENDER},activityId=12))
    if method=='cancel':items.clear()
    return {'returnValue':True}
   with patch.object(a,'STATE',root),patch.object(a.os,'geteuid',return_value=0),patch.object(a,'call',side_effect=call):
    for _ in range(2):self.assertTrue(a.manage('register',Path.read_bytes,lambda p,b:p.write_bytes(b))['registered'])
    self.assertEqual(len(items),1)
    items[0]['creator']={'serviceId':'foreign'}
    with self.assertRaises(ValueError):a.manage('unregister',Path.read_bytes,lambda p,b:p.write_bytes(b))
    self.assertEqual(len(items),1)
    items[0]['creator']={'serviceId':a.SENDER}
    self.assertFalse(a.manage('unregister',Path.read_bytes,lambda p,b:p.write_bytes(b))['registered'])
