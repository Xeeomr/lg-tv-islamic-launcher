"""Intent-bound trial, explicit promotion and guarded boot recovery."""
import os
import fcntl
import stat
from pathlib import Path
import uuid
import device_adapter as d
from persistent_store import Store
from persistent_recovery import Coordinator
from persistent_lifecycle import identifier


def boot_identity(proc=None):
    proc = d.PROC if proc is None else Path(proc)
    boot = (proc/'sys/kernel/random/boot_id').read_text().strip()
    starts = [line.split()[1:] for line in (proc/'stat').read_text().splitlines()
              if line.startswith('btime ')]
    if len(starts) != 1 or len(starts[0]) != 1 or not starts[0][0].isdigit():
        raise ValueError('Invalid kernel boot time')
    result = boot+':'+starts[0][0]
    if not identifier(result): raise ValueError('Invalid kernel boot identity')
    return result


def coordinator():
    if not os.path.lexists(d.STATE/'persistent-intent.json'): return None
    return Coordinator(Store(d.STATE))


def start():
    from provision import verify
    from helper_bridge import require_idle
    verify(); require_idle()
    c = Coordinator(Store(d.STATE)); intent = c.store.read()
    if intent['phase'] != 'disabled':
        raise ValueError('Restore previous intent before starting another trial')
    return c.start_trial(intent, boot_identity(), str(uuid.uuid4()))


def enable():
    from provision import verify
    from helper_bridge import require_idle
    verify(); require_idle()
    c = Coordinator(Store(d.STATE))
    return c.enable(c.store.read(), boot_identity(), str(uuid.uuid4()))


def later_legacy_trial(c):
    if not os.path.lexists(c.binding) or not os.path.lexists(d.STATE/'profile-trial.json'):
        return False
    from profile_recovery import validate
    binding = c.read_binding()
    journal = d.safe_json(d.STATE/'profile-trial.json'); validate(journal)
    return binding['restored'] and journal.get('transaction') != binding['transaction']


def restore():
    c = coordinator()
    if c is None or later_legacy_trial(c): return None
    intent = c.store.read()
    if intent['phase'] == 'disabled': return None
    result = c.exit(intent)
    return 'restored' if result.get('restored_transaction') else None


def boot():
    if not os.path.lexists(d.STATE/'persistent-intent.json'): return None
    d.trusted_dir(d.STATE)
    fd=os.open(d.STATE/'boot-dispatch.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        info=os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != d.EXPECTED_UID
                or info.st_nlink != 1 or info.st_mode & 0o022):
            raise ValueError('Unsafe boot dispatch lock')
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return 'boot-in-progress'
        try:return _boot()
        except Exception as exc:
            from boot_gate import audit
            audit('boot-error',error=type(exc).__name__+': '+str(exc))
            raise
    finally:os.close(fd)


def _boot():
    c = coordinator()
    if c is None or later_legacy_trial(c): return None
    intent = c.store.read(); identity = boot_identity(); failsafe = d.FAILSAFE.exists()
    if not failsafe and identity == intent['boot']:
        if intent['phase'] == 'stopping':
            c.shutdown(intent)
            return 'shutdown-pending'
        try: journal = d.safe_json(d.STATE/'profile-trial.json')
        except FileNotFoundError: journal = None
        if journal is not None and d.active_guardian(journal): return 'guarded-intent-trial'
        if intent['phase'] == 'disabled': return 'restored'
        # Expired trial or interrupted startup in this same boot: disable intent,
        # never infer health from an application merely existing in /proc.
        c.exit(intent, reason='fault')
        return 'restored'
    # Restore first. Normal startup also sets FAILSAFE temporarily; only the
    # current-boot init.d marker plus a cleared flag permits reactivation.
    from boot_gate import audit, observation
    audit('recover-before-gate',prior=intent,boot=identity,observation=observation())
    result = c.boot(intent, identity, str(uuid.uuid4()), False if identity != intent['boot'] else failsafe)
    if result['effect'] == 'start_guarded':
        from boot_gate import wait
        ready = wait()
        audit('gate-complete',prior=intent,boot=identity,ready=ready,observation=observation())
        if not ready:
            c.exit(result['intent'], reason='fault')
            return 'restored'
        return c.restart(result['intent'])
    return 'restored'


def confirm(transaction=None):
    c = coordinator()
    if c is None: raise ValueError('No intent-bound trial to confirm')
    if transaction != c.read_binding()['transaction']: raise ValueError('Stale confirmation transaction')
    return c.confirm(c.store.read())
