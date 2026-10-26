#!/usr/bin/python3
"""Root activation, status, restore, boot recovery and diagnostic trials."""
import json
import os
import sys
import device_adapter as d


def main(mode, transaction=None):
    if os.geteuid() != 0:
        raise PermissionError('Root required')
    if mode in ('enable','intent-trial','confirm','trial','emergency-trial','boot'):
        from update_guard import control
        # Boot during an update must restore, never reactivate a prior intent.
        if mode == 'boot' and os.path.lexists(d.STATE/'update-block.json'):
            return main('restore')
        with control(d.STATE,d.EXPECTED_UID):
            return execute(mode,transaction)
    return execute(mode,transaction)


def execute(mode, transaction=None):
    if mode in ('suspend-update','finish-update','abort-update'):
        from update_guard import suspend, finish, abort
        operation = {'suspend-update':suspend,'finish-update':finish,'abort-update':abort}[mode]
        return operation(transaction,d.STATE,d.EXPECTED_UID)
    if mode == 'confirm':
        from intent_runtime import confirm
        return confirm(transaction)
    if mode == 'enable':
        from intent_runtime import enable
        return enable()
    if mode == 'intent-trial':
        from intent_runtime import start
        return start()
    if mode == 'emergency-trial':
        from emergency_trial import start
        return start()
    if mode == 'trial':
        from bounded_profile_trial import begin, spawn
        return begin(spawn)
    if mode == 'restore':
        from update_guard import cancel
        from intent_runtime import restore
        try:
            cancel(d.STATE,d.EXPECTED_UID)
        finally:
            # Damaged updater evidence must never prevent explicit Home recovery.
            result = restore()
            result = d.main('recover') if result is None else result
        return result
    if mode == 'boot':
        from intent_runtime import boot
        result = boot()
        return d.main('boot') if result is None else result
    if mode == 'status':
        from provision import verify
        result = d.main('status')
        try:
            result['recovery'] = verify()
        except (OSError, ValueError, TypeError) as exc:
            result['recovery'] = {'integrity_verified':False,'error':str(exc)}
        result['update_home_resume_available'] = True
        result['candidate'] = d.CANDIDATE
        result['persistent_enable_available'] = result['recovery'].get('integrity_verified',False)
        from intent_runtime import coordinator
        c = coordinator()
        result['intent'] = c.store.read() if c is not None else None
        return result
    raise ValueError('Expected status, trial, emergency-trial, restore, boot, enable, confirm, suspend-update, finish-update or abort-update')


if __name__ == '__main__':
    try:
        result = main(sys.argv[1] if len(sys.argv) in (2,3) else '', sys.argv[2] if len(sys.argv) == 3 else None)
        print(json.dumps({'returnValue':True,'result':result}), flush=True)
        if isinstance(result, str) and result in ('recovering', 'conflict'):
            sys.exit(2)
    except Exception as exc:
        print(json.dumps({'returnValue':False,'error':str(exc)}), flush=True)
        sys.exit(1)
