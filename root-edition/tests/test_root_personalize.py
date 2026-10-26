import importlib.util,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import personalize

class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.source=Path(self.t.name).resolve()/'source';self.source.mkdir()
  (self.source/'apps.js').write_bytes(b'window.TV_APPS={apps:[{icon:"icons/a.png"}],inputs:[]};')
  (self.source/'config.js').write_bytes(b'window.CONFIG={columns:5};')
  (self.source/'icons').mkdir();(self.source/'icons/a.png').write_bytes(b'image')
 def test_copies_packaged_preferences_and_icons(self):
  result=personalize.prepare(self.source)
  self.assertEqual(result['apps.js'],(self.source/'apps.js').read_bytes())
  self.assertEqual(result['icons/a.png'],b'image')
  self.assertIn(b'com.cleanyourtv.root.preview',result['config.js'])
 def test_symlink_icon_refused(self):
  (self.source/'icons/a.png').unlink();(self.source/'icons/a.png').symlink_to(self.source/'config.js')
  with self.assertRaises(ValueError):personalize.prepare(self.source)
 def test_traversal_reference_refused(self):
  (self.source/'apps.js').write_text('window.TV_APPS={icon:"icons/../config.js"};')
  with self.assertRaises(ValueError):personalize.prepare(self.source)
 def test_source_never_written(self):
  before=(self.source/'config.js').read_bytes();personalize.prepare(self.source)
  self.assertEqual((self.source/'config.js').read_bytes(),before)
 def test_missing_source_fails_not_empty_success(self):
  (self.source/'apps.js').unlink()
  with self.assertRaises((OSError,ValueError)):personalize.prepare(self.source)

 def test_developer_packaged_data_is_not_executed_as_root(self):
  (self.source/'apps.js').chmod(0o777)
  result=personalize.prepare(self.source)
  self.assertEqual(result['apps.js'],(self.source/'apps.js').read_bytes())

 def test_saved_profile_migrates_inventory_without_source_writes(self):
  import json
  profile=self.source/'profile.json'
  data={'schema':1,'inventory':{'apps':[{'id':'test.app','title':'Example','icon':'data:image/png;base64,YQ=='}],'inputs':[]},'config':{'columns':5,'dockApps':['test.app'],'hiddenApps':[]},'settings':{}}
  profile.write_text(json.dumps(data));before=profile.read_bytes()
  result=personalize.from_profile(profile)
  self.assertIn(b'test.app',result['apps.js']);self.assertIn(b'com.cleanyourtv.root.preview',result['config.js'])
  self.assertEqual(profile.read_bytes(),before)
 def test_saved_profile_rejects_remote_icon(self):
  import json
  profile=self.source/'profile.json'
  data={'schema':1,'inventory':{'apps':[{'id':'a','title':'A','icon':'https://example.com/a.png'}],'inputs':[]},'config':{'columns':5,'dockApps':[],'hiddenApps':[]},'settings':{}}
  profile.write_text(json.dumps(data))
  with self.assertRaises(ValueError):personalize.from_profile(profile)
