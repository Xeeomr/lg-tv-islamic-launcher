import os, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
import boot_gate as g

class StorageTests(unittest.TestCase):
    def test_marker_is_private_and_bound_to_kernel_boot(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(g,'ROOT',Path(tmp)/'marker'),patch.object(g.d,'EXPECTED_UID',os.getuid()),patch.object(g.d,'FAILSAFE',Path(tmp)/'failsafe'):
            with patch('intent_runtime.boot_identity',return_value='boot-a'):
                g.mark(); self.assertEqual(g.observation(),(True,False))
                self.assertEqual((g.ROOT/'normal.json').stat().st_mode & 0o777,0o600)
            with patch('intent_runtime.boot_identity',return_value='boot-b'):
                self.assertEqual(g.observation(),(False,False))
    def test_symlink_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(g,'ROOT',Path(tmp)/'link'),patch.object(g.d,'EXPECTED_UID',os.getuid()):
            g.ROOT.symlink_to(Path(tmp),target_is_directory=True)
            with self.assertRaises(ValueError):g.mark()
