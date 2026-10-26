import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]))
import system_permissions as p
class Tests(unittest.TestCase):
 def test_scoped_registration_and_conflict_aware_removal(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);state=root/'state';state.mkdir();manifest=root/'manifest.json'
   def write(path,data):path.write_bytes(data)
   with patch.object(p,'STATE',state),patch.object(p,'MANIFEST',manifest):
    p.apply(Path.read_bytes,write);p.apply(Path.read_bytes,write)
    self.assertEqual(len(p.contents()),3)
    self.assertNotIn('systemProfile',manifest.read_text())
    client=state/'permissions/client.json';old=client.read_bytes();client.write_text('foreign')
    with self.assertRaises(ValueError):p.remove(Path.read_bytes)
    self.assertTrue(manifest.exists())
    client.write_bytes(old);p.remove(Path.read_bytes);p.remove(Path.read_bytes)
    self.assertFalse(manifest.exists())
 def test_unknown_manifest_never_overwritten(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);manifest=root/'manifest';manifest.write_text('foreign')
   with patch.object(p,'STATE',root),patch.object(p,'MANIFEST',manifest):
    with self.assertRaises(ValueError):p.apply(Path.read_bytes,lambda path,data:path.write_bytes(data))
    self.assertEqual(manifest.read_text(),'foreign')
