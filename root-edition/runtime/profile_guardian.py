"""Transaction-bound timer policy. Recovery must recheck the ID under its lock."""
import math


def watch(transaction, load, ready, restore, clock, sleep, continuation=lambda:None):
    journal = load()
    if journal.get('transaction') != transaction: return 'superseded'
    if journal.get('state') in ('restored','conflict'): return journal['state']
    if journal.get('state') not in ('pending','recovering'): raise ValueError('Invalid state')
    deadline = journal.get('deadline')
    if (type(deadline) not in (int,float) or not math.isfinite(deadline)
            or deadline > clock()+90):
        raise ValueError('Invalid or excessive trial deadline')
    if deadline > clock(): ready(transaction,deadline)
    while clock() < deadline:
        ongoing = continuation()
        if ongoing is not None: return ongoing
        sleep(min(0.25,deadline-clock()))
        current = load()
        if current.get('transaction') != transaction: return 'superseded'
        if current.get('state') in ('restored','conflict'): return current['state']
        if current.get('deadline') != deadline: raise ValueError('Deadline changed')
    return restore(transaction)
