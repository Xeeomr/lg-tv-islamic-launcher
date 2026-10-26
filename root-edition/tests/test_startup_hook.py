import importlib.util, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('hook_under_test',Path(__file__).parents[1]/'startup_hook.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)

class HookTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        self.a=patch.object(h,'STATE',self.root);self.b=patch.object(h,'HOOK',self.root/'hook')
        self.a.start();self.b.start()
    def tearDown(self):
        self.a.stop();self.b.stop();self.tmp.cleanup()
    def test_collision_is_not_adopted_or_removed(self):
        h.HOOK.write_bytes(h.CONTENT)
        with self.assertRaises(ValueError):h.install(Path.read_bytes,lambda *a:None)
        h.remove(Path.read_bytes);self.assertTrue(h.HOOK.exists())
    def test_owned_drift_is_not_removed(self):
        import json
        (h.STATE/'startup-hook.json').write_text(json.dumps({'version':1,'path':str(h.HOOK),'content':h.CONTENT.decode()}))
        h.HOOK.write_bytes(b'other')
        with self.assertRaises(ValueError):h.remove(Path.read_bytes)
        self.assertEqual(h.HOOK.read_bytes(),b'other')
    def test_owned_remove_is_idempotent(self):
        import json
        (h.STATE/'startup-hook.json').write_text(json.dumps({'version':1,'path':str(h.HOOK),'content':h.CONTENT.decode()}))
        h.HOOK.write_bytes(h.CONTENT)
        h.remove(Path.read_bytes);h.remove(Path.read_bytes)
        self.assertFalse(h.HOOK.exists());self.assertTrue((h.STATE/'startup-hook.json').exists())
