"""Fixed device-side script: preserve a completed removal before reinstalling."""

SCRIPT = r'''
import hashlib, json, os, re, stat, sys
from pathlib import Path

def operate(action, root, installed, override, destination=None, expected=None, proc='/proc', artifacts=()):
    root, installed, override = Path(root), Path(installed), Path(override)
    original = root
    if action not in ('inspect', 'archive', 'reconcile'): raise ValueError('Unsupported archive action')
    if action != 'inspect':
        if not isinstance(destination, str) or not re.fullmatch(re.escape(str(root))+r'\.archive-[0-9a-f]{32}', destination):
            raise ValueError('Invalid archive destination')
        destination = Path(destination)
        if action == 'reconcile' and not os.path.lexists(root): root = destination
    def directory(path):
        info = path.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o022:
            raise ValueError('Unsafe recovery directory')
    def record(name):
        fd = os.open(root/name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd) as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.geteuid()
                    or info.st_mode & 0o022 or info.st_size > 1048576):
                raise ValueError('Unsafe recovery record')
            value = json.load(stream)
            if not isinstance(value, dict): raise ValueError('Invalid recovery record')
            return value, hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
    directory(root.parent); directory(root)
    journal, digest = record('deploy.json')
    if (journal.get('stage') != 'uninstalled-state-retained'
            or journal.get('app') != 'com.cleanyourtv.root.preview'):
        raise ValueError('Removal has not been verified')
    app = 'com.cleanyourtv.root.preview'
    for kind, name in (('applications',app), ('services',app+'.service'), ('packages',app)):
        if os.path.lexists(installed/kind/name): raise ValueError('Root package files remain')
    if os.path.lexists(override): raise ValueError('Root Home routing remains')
    snapshot = root/'ls2-provision-snapshot.json'
    if os.path.lexists(snapshot):
        rolled_back = record('ls2-provision-snapshot.json')[0].get('phase') == 'rolled-back'
    else:
        rolled_back = journal.get('provisioning_not_started') is True
    if not rolled_back:
        raise ValueError('Recovery service rollback is incomplete')
    if os.path.lexists(root/'persistent-intent.json') and record('persistent-intent.json')[0].get('phase') != 'disabled':
        raise ValueError('Root control is still enabled')
    if os.path.lexists(root/'profile-trial.json') and record('profile-trial.json')[0].get('state') != 'restored':
        raise ValueError('Home recovery is incomplete')
    pending = () if os.path.lexists(snapshot) else (root/'recovery-provision.pending.json',)
    for path in (*artifacts, *pending, root/'permissions/client.json', root/'permissions/api.json', root/'recovery-provision.json'):
        if os.path.lexists(path): raise ValueError('Root registration artifacts remain')
    info = root.stat()
    identity = {'device':info.st_dev, 'inode':info.st_ino, 'journal':digest}
    busy = False
    prefix = str(original).encode()+b'/'
    for process in Path(proc).iterdir():
        if not process.name.isdigit(): continue
        try: args = (process/'cmdline').read_bytes().split(b'\0')
        except FileNotFoundError: continue
        if any(arg.startswith(prefix) for arg in args): busy = True
    if action == 'inspect': return {'identity':identity, 'busy':busy}
    if identity != expected: raise ValueError('Recovery state identity changed')
    if action == 'reconcile':
        if root == original and os.path.lexists(destination): raise ValueError('Ambiguous archive state')
        return {'state':'not-archived' if root == original else 'archived'}
    if busy: raise ValueError('Previous Root processes are still running; restart the TV')
    # Preserve all recovery evidence; never recursively delete or overwrite it.
    if os.path.lexists(destination): raise ValueError('Archive already exists')
    os.rename(root, destination)
    fd = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try: os.fsync(fd)
    finally: os.close(fd)
    return {'archived': str(destination)}

if __name__ == '__main__':
    name = 'com.cleanyourtv.root.preview.service'
    artifacts = ['/var/lib/webosbrew/init.d/50-clean-your-tv-root',
                 '/var/luna-service2/manifests.d/com.cleanyourtv.root.preview.recovery.json']
    artifacts += ['/var/luna-service2-dev/'+kind+'/'+name+suffix for kind,suffix in
                  (('services.d','.service'),('roles.d','.service.json'),
                   ('client-permissions.d','.service.json'),('api-permissions.d','.api.json'))]
    print(json.dumps(operate(sys.argv[1], '/var/lib/clean-your-tv-root',
          '/media/developer/apps/usr/palm', '/var/webos-profile/override/clean-your-tv-root.json',
          sys.argv[2] if len(sys.argv)>2 else None, json.loads(sys.argv[3]) if len(sys.argv)>3 else None,
          artifacts=artifacts)))
'''
