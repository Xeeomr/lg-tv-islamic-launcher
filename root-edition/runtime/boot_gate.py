"""Normal Homebrew startup evidence, independent of its transient failsafe flag.

The init.d hook only writes a current-boot marker and returns. Waiting inside
that hook would deadlock: Homebrew clears its flag after run-parts returns.
"""
import json
import os
from pathlib import Path
import tempfile
import time
import device_adapter as d

ROOT = Path('/tmp/clean-your-tv-root-boot')


def mark():
    from intent_runtime import boot_identity
    if os.geteuid() != d.EXPECTED_UID: raise PermissionError('Root required')
    try: ROOT.mkdir(mode=0o700)
    except FileExistsError: pass
    d.trusted_dir(ROOT)
    fd, name = tempfile.mkstemp(dir=ROOT, prefix='.normal-')
    try:
        with os.fdopen(fd,'w') as out:
            json.dump({'version':1,'boot':boot_identity()},out)
        os.replace(name,ROOT/'normal.json')
    finally:
        if os.path.lexists(name): os.unlink(name)


def observation():
    from intent_runtime import boot_identity
    normal = False
    try:
        d.trusted_dir(ROOT)
        value = d.safe_json(ROOT/'normal.json')
        normal = value == {'version':1,'boot':boot_identity()}
    except (OSError,ValueError): pass
    # lexists also fails closed on an unexpected symlink.
    return normal, os.path.lexists(d.FAILSAFE)


def audit(event, **details):
    d.trusted_dir(d.STATE)
    fd, name = tempfile.mkstemp(dir=d.STATE, prefix='.boot-decision-')
    try:
        with os.fdopen(fd,'w') as out:
            json.dump(dict(event=event,uptime=time.monotonic(),**details),out)
            out.flush(); os.fsync(out.fileno())
        os.replace(name,d.STATE/'boot-decision.json')
    finally:
        if os.path.lexists(name):os.unlink(name)


def wait(observe=observation, timeout=35, clock=time.monotonic, sleep=time.sleep):
    deadline = clock()+timeout
    while True:
        normal, flag = observe()
        if normal and not flag: return True
        remaining = deadline-clock()
        if remaining <= 0: return False
        sleep(min(.25, remaining))


if __name__ == '__main__':
    import sys
    if sys.argv[1:] != ['mark']: raise ValueError('Expected mark')
    mark()
