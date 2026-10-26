"""Profile recovery policy with injected I/O. No deployment or TV activation.

Caller must hold one transaction lock and durably save the journal. remove_owned
must verify the fixed file's ownership/type/digest and preserve conflicts. All
service operations must have bounded deadlines. These are adapter obligations,
not guarantees supplied by this pure policy module.
"""
import hashlib
import json
from profile_plan import plan, STOCK, CANDIDATE

REAL_HOME = CANDIDATE
def payload_for(candidate):
    if candidate != CANDIDATE: raise ValueError('Unsupported candidate')
    return (json.dumps({'defaultApps': {'categories': {'home': candidate}},
                       'idleApp': {'appId': candidate}}, sort_keys=True) + '\n').encode()

PAYLOAD = payload_for(CANDIDATE)
DIGEST = hashlib.sha256(PAYLOAD).hexdigest()
STATES = ('pending', 'recovering', 'restored', 'conflict')


def prepare(reply, sam_home, candidate=CANDIDATE):
    return {'version': 1, 'armed': True, 'state': 'pending',
            'candidate':candidate, 'payload_sha256': hashlib.sha256(payload_for(candidate)).hexdigest(), 'baseline': plan(reply, sam_home)['baseline']}


def validate(journal):
    if (journal.get('version') != 1 or journal.get('armed') is not True
            or journal.get('payload_sha256') != hashlib.sha256(payload_for(journal.get('candidate', CANDIDATE))).hexdigest() or journal.get('state') not in STATES):
        raise ValueError('Invalid profile recovery journal')
    try:
        b = journal['baseline']
        plan({'returnValue': True, 'profiles': b['profiles']}, b['sam_home'])
    except (KeyError, TypeError) as exc:
        raise ValueError('Invalid baseline') from exc


def recover(journal, remove_owned, refresh, read, write_sam, save):
    validate(journal)
    if journal['state'] in ('restored', 'conflict'):
        return journal['state']

    def record(state):
        updated = dict(journal, state=state)
        save(updated)
        journal.update(updated)
        return state

    record('recovering')  # Durable before deletion, even if previous apply crashed.
    try:
        removal = remove_owned()
    except OSError:
        return 'recovering'
    if removal == 'conflict':
        return record('conflict')
    if removal not in ('removed', 'absent'):
        raise ValueError('Invalid owned-file removal result')
    # Missing candidate is not proof the generated profile or consumer cache reset.
    try:
        refresh()
    except Exception:
        pass  # The response can be lost after a successful refresh. Read back.
    try:
        current = read()
    except Exception:
        return 'recovering'
    sam = current.get('sam_home')
    if sam not in (STOCK, journal.get('candidate', CANDIDATE)):
        return record('conflict')
    if sam == journal.get('candidate', CANDIDATE):
        try:
            write_sam(STOCK)
        except Exception:
            pass
        try:
            current = read()
        except Exception:
            return 'recovering'
    if current == journal['baseline']:
        return record('restored')
    return 'recovering'
