"""Crash-recoverable publication primitive; no service calls or activation CLI.

Caller supplies fixed paths in trusted directories, holds the transaction lock,
durably saves identity, and arms the independent recovery timer before publication.
Not a defense against a concurrent hostile root process.
"""
import os
import stat
from profile_recovery import PAYLOAD


def sync(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try: os.fsync(fd)
    finally: os.close(fd)


def trusted(path, uid):
    st = path.lstat()
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != uid or st.st_mode & 0o022:
        raise ValueError('Untrusted publication directory')
    return st


def publish(stage, target, save_identity, checkpoint=lambda _: None, uid=0, payload=PAYLOAD):
    if stage == target: raise ValueError('Distinct paths required')
    a, b = trusted(stage.parent, uid), trusted(target.parent, uid)
    if a.st_dev != b.st_dev: raise ValueError('Publication requires one filesystem')
    # Exclusive hard-link publication below also handles a target appearing later.
    try: target.lstat()
    except FileNotFoundError: pass
    else: raise FileExistsError(str(target))
    fd = os.open(stage, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(payload); f.flush(); os.fsync(f.fileno())
        st = os.fstat(f.fileno())
        identity = {'device': st.st_dev, 'inode': st.st_ino}
    sync(stage.parent)
    # A failed save leaves only staging data, never an active profile.
    save_identity(identity)
    checkpoint('journal')
    os.link(stage, target, follow_symlinks=False)
    sync(target.parent)
    checkpoint('linked')
    stage.unlink(); sync(stage.parent)
    checkpoint('published')
    return identity


def remove(stage, target, identity, uid=0, payload=PAYLOAD):
    if stage == target: raise ValueError('Distinct paths required')
    for directory in {stage.parent, target.parent}: trusted(directory, uid)
    if any(type(identity.get(k)) is not int or identity[k] < 0 for k in ('device','inode')):
        raise ValueError('Invalid identity')
    opened = []
    try:
        for path in (stage, target):
            try: fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            except FileNotFoundError: continue
            except OSError: return 'conflict'
            st = os.fstat(fd); opened.append((path, fd, st))
            if (not stat.S_ISREG(st.st_mode) or st.st_uid != uid or st.st_mode & 0o022
                    or st.st_size != len(payload)
                    or (st.st_dev,st.st_ino) != (identity['device'],identity['inode'])):
                return 'conflict'
            with os.fdopen(os.dup(fd), 'rb') as f:
                if f.read(len(payload)+1) != payload: return 'conflict'
        if not opened: return 'absent'
        if any(st.st_nlink != len(opened) for _, _, st in opened): return 'conflict'
        attrs = lambda s: (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
        for path, _, st in opened:
            if attrs(path.lstat()) != attrs(st): return 'conflict'
        # If killed after the first unlink, a retry sees one valid link and resumes.
        for path, _, _ in opened:
            path.unlink(); sync(path.parent)
        return 'removed'
    finally:
        for _, fd, _ in opened: os.close(fd)
