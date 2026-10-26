"""Root-private atomic intent journal. No Home, helper or service operations.

An effect is returned only after the state and directory entry have been synced.
The caller must reconcile an uncertain write by reading, never blindly replay an
effect. expected is a complete snapshot, so a concurrent exit wins over an old
confirmation even within the same generation.
"""
import fcntl
import json
import os
from pathlib import Path
import stat
import tempfile
import device_adapter as d
from persistent_lifecycle import initial, transition, validate


class Store:
    def __init__(self, root):
        self.root = Path(root)
        self.path = self.root/'persistent-intent.json'

    def read(self):
        d.trusted_dir(self.root)
        try: value = d.safe_json(self.path)
        except FileNotFoundError: return initial()
        return validate(value)

    def apply(self, expected, event):
        d.trusted_dir(self.root)
        fd = os.open(self.root/'persistent-intent.lock',
                     os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        try:
            info = os.fstat(fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != d.EXPECTED_UID
                    or info.st_nlink != 1 or info.st_mode & 0o022):
                raise ValueError('Unsafe lifecycle lock')
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            current = self.read()
            if current != expected: raise ValueError('Stale lifecycle snapshot')
            updated, effect = transition(current, event)
            if updated != current: self._save(updated)
            return updated, effect
        finally:
            os.close(fd)

    def _save(self, value):
        fd, name = tempfile.mkstemp(dir=self.root, prefix='.intent-')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(value, f, sort_keys=True)
                f.flush(); os.fsync(f.fileno())
            os.replace(name, self.path)
            d.sync(self.root)
        finally:
            if os.path.exists(name): os.unlink(name)
