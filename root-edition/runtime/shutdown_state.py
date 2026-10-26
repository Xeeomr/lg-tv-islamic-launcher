"""Observe PID 1 independently, before shutdown makes synchronous queries stall."""
import json
import os
import stat
from pathlib import Path
import subprocess
import tempfile
import threading
import time
import device_adapter as d
import persistent_health as health


def query():
    try:
        result = subprocess.run(['/usr/bin/systemctl','is-system-running'],
            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
            timeout=.5,universal_newlines=True)
        return result.stdout.strip() == 'stopping'
    except (OSError,subprocess.TimeoutExpired): return False


def record(transaction, source="systemd"):
    from intent_runtime import boot_identity
    try:health.ROOT.mkdir(mode=0o700)
    except FileExistsError:pass
    d.trusted_dir(health.ROOT)
    fd,name=tempfile.mkstemp(dir=health.ROOT,prefix='.shutdown-')
    try:
        with os.fdopen(fd,'w') as out:
            json.dump(dict(transaction=transaction,boot=boot_identity(),issued=time.monotonic(),source=source),out)
        os.replace(name,health.path(transaction).with_suffix('.shutdown'))
    finally:
        if os.path.exists(name):os.unlink(name)


def stopping(transaction=None):
    if transaction is not None:
        try:
            from intent_runtime import boot_identity
            d.trusted_dir(health.ROOT)
            v=d.safe_json(health.path(transaction).with_suffix('.shutdown'))
            from persistent_lease import finite
            if (v.get('transaction') == transaction and v.get('boot') == boot_identity()
                    and finite(v.get('issued')) and 0 <= time.monotonic()-v['issued'] < 5):
                return True
        except (OSError,ValueError):pass
    return query()


class PowerReason:
    """Accept a newly appearing root-owned firmware request, never a stale file."""
    def __init__(self, path=Path('/tmp/poweroff_reason')):
        self.path = path
        self.saw_absent = False
        self.consumed = False

    def poll(self):
        if self.consumed: return False
        try:
            fd = os.open(self.path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
            with os.fdopen(fd,'rb') as stream:
                info=os.fstat(stream.fileno())
                if (not self.saw_absent or not stat.S_ISREG(info.st_mode)
                        or info.st_uid != d.EXPECTED_UID or info.st_mode & 0o022
                        or info.st_nlink != 1 or info.st_size > 256):
                    self.consumed=True;return False
                value=stream.read(257).strip()
                # The firmware may have created the inode before writing bytes.
                if not value:return False
                self.consumed=True
                return value == b'poweroff_reason=remoteKey'
        except FileNotFoundError:
            self.saw_absent=True;return False
        except OSError:
            self.consumed=True;return False


def monitor(transaction):
    stop=threading.Event()
    reason=PowerReason()
    reason.poll()  # Establish absence before announcing guardian readiness.
    def power_request():
        pending_until = 0
        while not stop.is_set():
            try:
                if reason.poll(): pending_until=time.monotonic()+1
                if time.monotonic() < pending_until:
                    record(transaction,source='firmware-remoteKey')
                    pending_until=0
                    print(json.dumps(dict(event='shutdown-request-observed',transaction=transaction,uptime=time.monotonic())),flush=True)
            except (OSError,ValueError):pass
            stop.wait(.05)
    def manager():
        while not stop.is_set():
            try:
                if query():record(transaction)
            except (OSError,ValueError):pass
            stop.wait(.25)
    # A stalled systemctl call must not delay the firmware request observer.
    for observe in (power_request,manager):
        threading.Thread(target=observe,daemon=True).start()
    return stop
