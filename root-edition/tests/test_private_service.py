import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('private_provision',Path(__file__).parents[1]/'provision.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class PrivateServiceTests(unittest.TestCase):
 def test_exec_uses_private_bootstrap_not_homebrew(self):
  original={'service':'Exec=/usr/bin/run-js-service -n '+str(p.SERVICE),'role':json.dumps({'appId':p.NAME}),'client':'{}','api':'{}'}
  result=p.plan(original)['service'].decode()
  self.assertNotIn('org.webosbrew',result)
  self.assertIn('/var/lib/clean-your-tv-root/',result)
  self.assertNotIn(' -n '+str(p.SERVICE),result)
 def test_private_copy_checks_hashes_and_is_idempotent(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp).resolve();src=root/'installed';src.mkdir();state=root/'state';state.mkdir()
   files={}
   for name in (*p.PRIVATE_FILES, 'app-inventory.js'):
    data=(name+' fixture').encode();(src/name).write_bytes(data)
    files['usr/palm/services/'+p.NAME+'/'+name]=p.sha(data)
   (state/'release.json').write_text(json.dumps({'files':files}))
   with patch.object(p,'STATE',state),patch.object(p,'SERVICE',src),patch.object(p,'PRIVATE_SERVICE',state/'service'),patch.object(p,'RUNNER',state/'run-service'),patch.object(p,'SYSTEM_FILES',()),patch.object(p,'secure',side_effect=lambda path:path.read_bytes()):
    p.prepare_private_service();p.prepare_private_service()
    self.assertEqual((state/'service/service.js').read_bytes(),(src/'service.js').read_bytes())
    inventory=state/'service/app-inventory.js'
    self.assertTrue(inventory.is_file(), 'Privileged service inventory dependency must be copied')
    self.assertEqual(inventory.read_bytes(),(src/'app-inventory.js').read_bytes())
    self.assertEqual((state/'run-service').stat().st_mode & 0o777,0o700)
    inventory.write_text('changed')
    with self.assertRaises(ValueError):p.prepare_private_service()
 def test_hash_mismatch_creates_no_runner(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp).resolve();src=root/'installed';src.mkdir();state=root/'state';state.mkdir()
   (state/'release.json').write_text(json.dumps({'files':{}}))
   with patch.object(p,'STATE',state),patch.object(p,'SERVICE',src),patch.object(p,'PRIVATE_SERVICE',state/'service'),patch.object(p,'RUNNER',state/'run-service'),patch.object(p,'SYSTEM_FILES',()):
    with self.assertRaises((ValueError,FileNotFoundError)):p.prepare_private_service()
    self.assertFalse((state/'run-service').exists())
