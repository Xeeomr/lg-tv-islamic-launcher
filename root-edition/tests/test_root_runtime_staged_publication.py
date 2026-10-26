import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"runtime"))
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import staged_publication as p
from profile_recovery import PAYLOAD


class PublicationTests(unittest.TestCase):
    def test_process_death_at_every_publication_boundary(self):
        for boundary in ('journal', 'linked', 'published'):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                script = '''
import json, os, sys
from pathlib import Path
import staged_publication as p
r=Path(sys.argv[1])
def save(identity):
    with (r/'journal').open('w') as f:
        json.dump(identity,f); f.flush(); os.fsync(f.fileno())
def checkpoint(name):
    if name==sys.argv[2]: os._exit(73)
p.publish(r/'stage',r/'target',save,checkpoint,os.geteuid())
'''
                child = subprocess.run([sys.executable, '-c', script, tmp, boundary],
                                       cwd=Path(__file__).resolve().parents[1]/"runtime")
                self.assertEqual(child.returncode, 73)
                identity = json.loads((root/'journal').read_text())
                self.assertEqual(p.remove(root/'stage', root/'target', identity, os.geteuid()), 'removed')
                self.assertFalse((root/'stage').exists())
                self.assertFalse((root/'target').exists())
                self.assertEqual(p.remove(root/'stage', root/'target', identity, os.geteuid()), 'absent')

    def test_existing_target_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp); (r/'target').write_bytes(b'foreign')
            with self.assertRaises(FileExistsError):
                p.publish(r/'stage', r/'target', lambda _: None, uid=os.geteuid())
            self.assertEqual((r/'target').read_bytes(), b'foreign')

    def test_foreign_same_content_inode_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp); saved=[]
            p.publish(r/'stage', r/'target', saved.append, uid=os.geteuid())
            (r/'other').write_bytes(PAYLOAD); (r/'other').chmod(0o600)
            os.replace(r/'other',r/'target')
            self.assertEqual(p.remove(r/'stage',r/'target',saved[0],os.geteuid()), 'conflict')
            self.assertTrue((r/'target').exists())

    def test_failed_journal_write_never_publishes(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp)
            def fail(_): raise OSError('disk full')
            with self.assertRaises(OSError):
                p.publish(r/'stage',r/'target',fail,uid=os.geteuid())
            self.assertFalse((r/'target').exists())

    def test_unexpected_third_link_blocks_removal(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp); saved=[]
            p.publish(r/'stage',r/'target',saved.append,uid=os.geteuid())
            os.link(r/'target',r/'foreign-link')
            self.assertEqual(p.remove(r/'stage',r/'target',saved[0],os.geteuid()), 'conflict')

    def test_symlink_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp); (r/'target').symlink_to(r/'missing')
            self.assertEqual(p.remove(r/'stage',r/'target',{'device':0,'inode':0},os.geteuid()), 'conflict')


if __name__ == '__main__': unittest.main()
