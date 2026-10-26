"""Serialize activation with updater reservation; explicit recovery stays available."""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import uuid

STATE = Path('/var/lib/clean-your-tv-root')
HOME_RESUME_PROTOCOL = 1


@contextmanager
def locked(root,uid):
    for p in (root,*root.parents):
        st=p.lstat()
        # Ancestors such as /tmp may be sticky. The private state itself may not.
        if not stat.S_ISDIR(st.st_mode) or (p==root and (st.st_uid!=uid or st.st_mode & 0o022)):
            raise ValueError('Unsafe routing lock directory')
    fd=os.open(root/'software-update.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW|os.O_NONBLOCK,0o600)
    try:
        st=os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid!=uid or st.st_nlink!=1 or st.st_mode & 0o022:raise ValueError('Unsafe routing lock')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield
    finally:os.close(fd)


@contextmanager
def control(root=STATE,uid=0):
    root=Path(root)
    with locked(root,uid):
        if os.path.lexists(root/'update-block.json'):raise RuntimeError('Software update pending; use Root Updater Recovery before enabling Root')
        yield


def read(path,uid,limit=1024):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd) as f:
        st=os.fstat(f.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_uid!=uid or st.st_nlink!=1 or st.st_size>limit or st.st_mode & 0o022:raise ValueError('Unsafe reservation')
        return json.load(f)


def sync(root):
    fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)


def reserve(transaction,root=STATE,uid=0):
    if not isinstance(transaction,str) or not re.fullmatch('[a-f0-9]{32}',transaction):raise ValueError('Invalid update identity')
    root=Path(root)
    with locked(root,uid):
        p=root/'update-block.json';value={'transaction':transaction}
        if os.path.lexists(p):
            if read(p,uid)!=value:raise ValueError('Another update owns routing')
            return
        # A fresh reservation starts a new cycle, including rollback of the same update.
        # Remove the old receipt before publishing the reservation, never on retry.
        for name in ('update-home-resume.json','update-home-cancel.json'):
            old=root/name
            if os.path.lexists(old):old.unlink()
        sync(root)
        fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'w') as f:json.dump(value,f);f.flush();os.fsync(f.fileno())
        sync(root)


def release(transaction,root=STATE,uid=0):
    root=Path(root)
    with locked(root,uid):
        p=root/'update-block.json'
        if not os.path.lexists(p):return
        if read(p,uid)!={'transaction':transaction}:raise ValueError('Reservation owner mismatch')
        p.unlink();sync(root)


def identity(transaction):
    if not isinstance(transaction,str) or not re.fullmatch('[a-f0-9]{32}',transaction):
        raise ValueError('Invalid update identity')


def atomic(path,value):
    fd,temp=tempfile.mkstemp(dir=path.parent,prefix='.update-home-')
    try:
        with os.fdopen(fd,'w') as out:
            json.dump(value,out,sort_keys=True);out.flush();os.fsync(out.fileno())
        os.replace(temp,path);sync(path.parent)
    finally:
        if os.path.exists(temp):os.unlink(temp)


def reservation(transaction,root,uid,required=True):
    identity(transaction)
    try:value=read(root/'update-block.json',uid)
    except FileNotFoundError:
        if required:raise ValueError('No update reservation')
        return False
    if value!={'transaction':transaction}:raise ValueError('Reservation owner mismatch')
    return True


def ticket(root,uid):
    from persistent_lifecycle import identifier, validate
    try:t=read(root/'update-home-resume.json',uid,16384)
    except FileNotFoundError:return None
    if not isinstance(t,dict) or not {'transaction','ticket'} <= set(t):
        raise ValueError('Invalid update Home ticket')
    identity(t['transaction']);identity(t['ticket'])
    receipt={'transaction','ticket','outcome'}
    fields={'transaction','ticket','boot','before','desired','suspended','attempted'}
    if set(t)!=receipt:
        if not fields <= set(t) or set(t)-fields-{'suspend_result','outcome'}:
            raise ValueError('Invalid update Home ticket fields')
        if not identifier(t['boot']) or type(t['desired']) is not bool or type(t['attempted']) is not bool:
            raise ValueError('Invalid update Home ticket state')
        for key in ('before','suspended'):
            if t[key] is not None:validate(t[key])
        if not disabled(t['suspended']) or (t['desired'] and (t['before'] is None or t['before']['phase']!='active' or not t['before']['enabled'])):
            raise ValueError('Invalid update Home intent snapshots')
        if t['attempted'] and t['suspended'] is None:
            raise ValueError('Unverified update Home activation')
        if 'suspend_result' in t and t['suspend_result'] not in ('restored','absent'):
            raise ValueError('Invalid update Home suspension result')
    if 'outcome' in t:
        outcome=t['outcome']
        if (not isinstance(outcome,dict) or not {'status'} <= set(outcome) or set(outcome)-{'status','error'}
                or outcome['status'] not in ('restored','skipped','cancelled','failed','unchanged')
                or ('error' in outcome and not isinstance(outcome['error'],str))):
            raise ValueError('Invalid update Home outcome')
    return t


def _intent():
    from intent_runtime import coordinator
    c=coordinator()
    return c.store.read() if c is not None else None


def _boot():
    from intent_runtime import boot_identity
    return boot_identity()


def _failsafe():
    import device_adapter as d
    return os.path.lexists(d.FAILSAFE)


def _restore():
    from intent_runtime import restore
    import device_adapter as d
    result=restore()
    result=d.main('recover') if result is None else result
    if result not in ('restored','absent'):raise ValueError('Home restoration incomplete: '+str(result))
    return result


def _enable():
    from intent_runtime import enable
    return enable()


def disabled(intent):
    return intent is None or (intent['phase']=='disabled' and intent['enabled'] is False)


def cancel(root=STATE,uid=0,expected=None):
    """Explicit off wins without waiting for the activation/update lock.

    Emergency observers pass their current bound intent, so old observers cannot
    cancel a different update or a newer lifecycle attempt.
    """
    root=Path(root);t=ticket(root,uid)
    if t is None:
        if expected is not None:return
        try:block=read(root/'update-block.json',uid)
        except FileNotFoundError:return
        if not isinstance(block,dict) or set(block)!={'transaction'}:raise ValueError('Invalid update reservation')
        identity(block['transaction'])
        # Explicit off in the reserve/suspend gap applies to this fresh cycle.
        atomic(root/'update-home-cancel.json',dict(transaction=block['transaction'],ticket=None))
        return
    if 'outcome' in t:return
    if not reservation(t['transaction'],root,uid,required=False):return
    if expected is not None:
        before=t['before'];suspended=t.get('suspended')
        same=before is not None and (expected['generation'],expected['token'])==(before['generation'],before['token'])
        activating=(t.get('attempted') and suspended is not None
                    and expected['generation']==suspended['generation']+1 and expected['boot']==t['boot'])
        if not (same or activating):return
    atomic(root/'update-home-cancel.json',dict(transaction=t['transaction'],ticket=t['ticket']))


def cancelled(t,root,uid):
    try:value=read(root/'update-home-cancel.json',uid)
    except FileNotFoundError:return False
    if not isinstance(value,dict) or set(value)!={'transaction','ticket'}:raise ValueError('Invalid update Home cancellation')
    identity(value['transaction'])
    if value['ticket'] is not None:identity(value['ticket'])
    return value['transaction']==t['transaction'] and value['ticket'] in (None,t['ticket'])


def suspend(transaction,root=STATE,uid=0):
    root=Path(root)
    with locked(root,uid):
        reservation(transaction,root,uid)
        path=root/'update-home-resume.json';t=ticket(root,uid)
        if t is not None and t['transaction']!=transaction:raise ValueError('Resume ticket owner mismatch')
        if t is None:
            before=_intent()
            t=dict(transaction=transaction,ticket=uuid.uuid4().hex,boot=_boot(),before=before,
                   desired=before is not None and before['phase']=='active' and before['enabled'] is True,
                   suspended=None,attempted=False)
            atomic(path,t)
            fresh=True
        else:
            if 'outcome' in t:raise ValueError('Update Home suspension already finished')
            fresh=False
        result=_restore();after=_intent()
        if not disabled(after):raise ValueError('Persistent intent was not disabled')
        # An interrupted suspension has no verified post-restore snapshot. Retrying
        # can recover stock Home but must not infer permission to enable again.
        if t['suspended'] is None:
            t.update(suspended=after,desired=t['desired'] and fresh,suspend_result=result)
            atomic(path,t)
        return result


def finish(transaction,root=STATE,uid=0,resume=True):
    root=Path(root)
    with locked(root,uid):
        owned=reservation(transaction,root,uid,required=False)
        path=root/'update-home-resume.json';t=ticket(root,uid)
        if not owned and (t is None or t['transaction']!=transaction):return dict(status='unchanged')
        if t is not None and t['transaction']!=transaction:raise ValueError('Resume ticket owner mismatch')
        if t is not None and 'outcome' in t:
            if owned:(root/'update-block.json').unlink();sync(root)
            return t['outcome']
        if not owned:raise ValueError('No update reservation')
        outcome=dict(status='unchanged')
        if t is not None:
            outcome=dict(status='skipped')
            if cancelled(t,root,uid):outcome=dict(status='cancelled')
            elif resume and t['desired'] and not t['attempted'] and t.get('suspended') is not None and _boot()==t['boot'] and not _failsafe() and _intent()==t['suspended']:
                # Persist BEFORE activation. An uncertain attempt is recovered off,
                # never replayed, even when the updater process is restarted.
                t['attempted']=True;atomic(path,t)
                try:
                    if cancelled(t,root,uid):outcome=dict(status='cancelled')
                    else:
                        result=_enable();current=_intent()
                        if not isinstance(result,dict) or result.get('intent')!=current or current['phase']!='active' or current['enabled'] is not True:
                            raise ValueError('Persistent Home activation not confirmed')
                        outcome=dict(status='restored')
                except Exception as exc:outcome=dict(status='failed',error=str(exc))
                if cancelled(t,root,uid):outcome=dict(status='cancelled')
            if outcome['status']!='restored' and (t['attempted'] or not disabled(_intent())):
                _restore()
                if not disabled(_intent()):raise ValueError('Persistent intent was not disabled')
            # A cancellation arriving after enable must also win before release.
            if cancelled(t,root,uid) and outcome['status']=='restored':
                _restore()
                if not disabled(_intent()):raise ValueError('Persistent intent was not disabled')
                outcome=dict(status='cancelled')
            t['outcome']=outcome;atomic(path,t)
        else:
            atomic(path,dict(transaction=transaction,ticket=uuid.uuid4().hex,outcome=outcome))
        (root/'update-block.json').unlink();sync(root)
        return outcome


def abort(transaction,root=STATE,uid=0):
    return finish(transaction,root,uid,resume=False)
