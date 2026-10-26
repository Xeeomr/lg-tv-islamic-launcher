"""Reconcile an interrupted removal using the driver already installed on the TV."""

SCRIPT = r'''
import json, os, sys
from pathlib import Path

READY = ('installed-recovery-only', 'uninstall-restored',
         'uninstall-rollback-complete', 'uninstall-refresh-complete')
FINISH = ('remove-submitting', 'remove-observed', 'uninstalled-state-retained')

def reconcile(driver, action, busy=False):
    if busy:
        return {'returnValue': False, 'reason': 'busy'}
    journal = json.loads(driver.checked_file(driver.STATE, 'deploy.json'))
    if journal.get('app') != driver.APP:
        return {'returnValue': False, 'reason': 'unknown'}
    stage = journal.get('stage')
    if stage in READY:
        if action == 'inspect':
            return {'returnValue': True, 'ready': True}
        return driver.uninstall()
    if stage not in FINISH:
        return {'returnValue': False, 'reason': 'unknown'}
    # An observed terminal can authorize cleanup of an empty package directory.
    # Without that evidence every package path must already be absent.
    evidence = journal.get('evidence', {}) if stage == 'remove-observed' else {}
    if action == 'inspect':
        paths = driver.installed_paths()
        if any(p.exists() or p.is_symlink() for p in paths):
            if stage != 'remove-observed':
                return {'returnValue': False, 'reason': 'unknown'}
        return {'returnValue': True, 'ready': True}
    driver.verify_removed(evidence)
    proof = {'provisioning_not_started': True} if journal.get('provisioning_not_started') is True else {}
    driver.write_stage('uninstalled-state-retained', **proof)
    return {'returnValue': True, 'removed': driver.APP, 'state_retained': str(driver.STATE)}

if __name__ == '__main__':
    import fcntl
    root = Path('/var/lib/clean-your-tv-root')
    sys.path.insert(0, str(root))
    import deploy
    # Serialize new recovery attempts and detect a still-running older driver.
    # Older releases do not participate in this lock.
    with (root/'uninstall-recovery.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps({'returnValue': False, 'reason': 'busy'}))
            sys.exit(0)
        active = {str(root/name).encode() for name in ('deploy.py', 'provision.py', 'runtime/cli.py')}
        busy = False
        for process in Path('/proc').iterdir():
            if not process.name.isdigit() or int(process.name) == os.getpid():
                continue
            try:
                args = (process/'cmdline').read_bytes().split(b'\0')
            except FileNotFoundError:
                continue
            if active.intersection(args):
                busy = True
        print(json.dumps(reconcile(deploy, sys.argv[1], busy)), flush=True)
'''
