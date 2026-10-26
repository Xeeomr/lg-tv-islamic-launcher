"""Fixed device-side cleanup of the Root Updater's owned registrations."""
SCRIPT = r'''
import fcntl, hashlib, json, os, re, signal, stat, subprocess, sys, time, tempfile
from pathlib import Path

APP = 'com.cleanyourtv.root.updater'
SERVICE = APP + '.service'

def read(path):
    for parent in path.parents:
        info = parent.lstat()
        if not stat.S_ISDIR(info.st_mode): raise ValueError('Indirect cleanup path')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_nlink != 1 or info.st_mode & 0o022:
            raise ValueError('Unsafe updater cleanup file')
        raw = stream.read(4*1024*1024+1)
        if len(raw) > 4*1024*1024: raise ValueError('Oversized cleanup file')
        return raw

def write(path, value):
    raw = json.dumps(value).encode()
    fd, name = tempfile.mkstemp(prefix='.cytv-removal-', dir=str(path.parent))
    temp = Path(name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(temp, path)
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)
    finally:
        if temp.exists(): temp.unlink()

def processes(code, proc=Path('/proc')):
    result = []
    for path in proc.iterdir():
        if not path.name.isdigit() or int(path.name) == os.getpid(): continue
        try:
            args = (path/'cmdline').read_bytes().split(b'\0')
            start = (path/'stat').read_text().rsplit(')',1)[1].split()[19]
        except FileNotFoundError: continue
        prefix = str(code).encode()
        if any(arg == prefix or arg.startswith(prefix+b'/') for arg in args):
            result.append((int(path.name), start))
    return result

def stop(code):
    for pid, start in processes(code):
        path = Path('/proc')/str(pid)
        try:
            if (path/'stat').read_text().rsplit(')',1)[1].split()[19] == start:
                os.kill(pid, signal.SIGTERM)
        except ProcessLookupError: pass
        except FileNotFoundError: pass
    for _ in range(50):
        if not processes(code): return
        time.sleep(.1)
    raise ValueError('Updater processes have not stopped')


def python_command(state):
    launcher=state/'python-launcher';receipt=state/'python-runtime.json'
    if not os.path.lexists(launcher) and not os.path.lexists(receipt):return '/usr/bin/python3'
    pinned='4a71641c8d5536175e404a961624e8656eba30e97b5026f6bd7dc31e4bbeaaea'
    executable='/var/lib/clean-your-tv-python/'+pinned+'/bin/python3.13'
    value=json.loads(read(receipt))
    if (not isinstance(value,dict) or set(value)!={'schema','executable','archive_sha256','inventory_sha256'} or value.get('schema')!=1
            or value.get('executable')!=executable or value.get('archive_sha256')!=pinned
            or not isinstance(value.get('inventory_sha256'),str) or not re.fullmatch('[a-f0-9]{64}',value['inventory_sha256'])
            or read(launcher)!=('#!/bin/sh\nunset PYTHONHOME PYTHONPATH\nexport PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1\nexec '+executable+' "$@"\n').encode()
            or stat.S_IMODE(launcher.stat().st_mode)!=0o700):raise ValueError('Unknown updater Python binding')
    return str(launcher)


def operate(action, state, base, hook, installed, destination, refresh, stop_processes=stop):
    state, base, hook, installed = map(Path, (state, base, hook, installed))
    if action not in ('inspect','disable','finalize'): raise ValueError('Unsupported cleanup action')
    if not re.fullmatch(re.escape(str(state))+r'\.archive-[0-9a-f]{32}', destination):
        raise ValueError('Invalid updater archive')
    archive = Path(destination)
    paths = {key:base/folder/(SERVICE+suffix) for key,folder,suffix in (
        ('service','services.d','.service'), ('role','roles.d','.service.json'),
        ('client','client-permissions.d','.service.json'), ('api','api-permissions.d','.api.json'))}
    package_paths = [installed/kind/(APP+suffix) for kind,suffix in (
        ('applications',''),('packages',''),('services','.service'))]
    if not os.path.lexists(state):
        if any(os.path.lexists(p) for p in [hook,*paths.values(),*package_paths]):
            raise ValueError('Updater artifacts exist without ownership state')
        return {'disabled':True,'removed':True,'archive':str(archive) if archive.exists() else None}
    for parent in (state,*state.parents):
        info=parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid not in (0,os.geteuid()) or (info.st_mode & 0o022 and not info.st_mode & stat.S_ISVTX):
            raise ValueError('Unsafe updater state directory')
    locks=[]
    try:
        for name in (() if action=='inspect' else ('daemon.lock','worker.lock')):
            fd=os.open(state/name,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW|os.O_NONBLOCK,0o600)
            locks.append(fd)
            info=os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.geteuid() or info.st_nlink!=1 or info.st_mode & 0o022:
                raise ValueError('Unsafe updater lock')
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        tx_path=state/'transaction.json'
        if os.path.lexists(tx_path):
            tx=json.loads(read(tx_path))
            if tx.get('schema')!=1 or tx.get('phase') not in ('complete','rolled-back','aborted'):
                raise ValueError('Updater transaction needs recovery before removal')
        registration=json.loads(read(state/'registration.json'))['files']
        if set(registration)!=set(map(str,paths.values())): raise ValueError('Unknown updater registration inventory')
        expected={key:registration[str(path)]['installed'].encode() for key,path in paths.items()}
        python=python_command(state)
        expected['hook']=('#!/bin/sh\nunset NODE_OPTIONS NODE_PATH\n/usr/bin/node '+str(state/'code/python_boot.js')+' '+str(state)+' '+str(state/'code/run-updater.py')+' worker </dev/null >/dev/null 2>&1 &\n').encode()
        legacy_hook=('#!/bin/sh\n/usr/bin/python3 '+str(state/'code/run-updater.py')+' worker </dev/null >/dev/null 2>&1 &\n').encode()
        retained_hook=hook if os.path.lexists(hook) else state/'removed-registration/hook'
        if python=='/usr/bin/python3' and read(retained_hook)==legacy_hook:expected['hook']=legacy_hook
        paths['hook']=hook
        journal=state/'cytv-removal.json'
        record=json.loads(read(journal)) if os.path.lexists(journal) else None
        if record is not None and (record.get('archive')!=destination or record.get('phase') not in ('disabling','disabled')):
            raise ValueError('Different updater removal already exists')
        saved=state/'removed-registration'
        manifest=base/'manifests.d'/(APP+'.json')
        manifest_raw=read(manifest if os.path.lexists(manifest) else saved/'manifest')
        manifest_value=json.loads(manifest_raw)
        manifest_expected={'id':APP,'version':manifest_value.get('version'),
            'serviceFiles':[str(paths['service'])], 'apiPermissionFiles':[str(paths['api'])],
            'roleFiles':[str(paths['role']),str(base/'roles.d'/(APP+'.app.json'))],
            'clientPermissionFiles':[str(paths['client']),str(base/'client-permissions.d'/(APP+'.app.json'))]}
        if manifest_value!=manifest_expected or not isinstance(manifest_value.get('version'),str) or not re.fullmatch(r'\d+\.\d+\.\d+',manifest_value['version']):
            raise ValueError('Unknown updater manifest')
        paths['manifest']=manifest;expected['manifest']=manifest_raw
        # Validate the entire set before changing any file. Never follow receipt paths.
        for key,path in paths.items():
            if os.path.lexists(path):
                if read(path)!=expected[key]: raise ValueError('Updater registration changed: '+key)
            elif record is None or read(saved/key)!=expected[key]:
                raise ValueError('Unverified missing updater registration: '+key)
        if action=='inspect': return {'ownership_verified':True,'phase':record['phase'] if record else 'installed'}
        if record is None:
            saved.mkdir(mode=0o700, exist_ok=True)
            info=saved.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.geteuid() or info.st_mode & 0o022 or any(saved.iterdir()):
                raise ValueError('Unexpected cleanup backup directory')
            write(journal,{'phase':'disabling','archive':destination})
        if action=='disable':
            for key,path in sorted(paths.items(), key=lambda item: (0 if item[0]=='hook' else 1 if item[0]=='manifest' else 2)):
                if os.path.lexists(path):
                    target=saved/key
                    if os.path.lexists(target): raise ValueError('Cleanup backup collision')
                    os.replace(path,target)
            refresh()
            stop_processes(state/'code')
            write(journal,{'phase':'disabled','archive':destination})
            return {'disabled':True,'removed':False}
        if record is None or record['phase']!='disabled': raise ValueError('Updater has not been disabled')
        if any(os.path.lexists(p) for p in [*paths.values(),*package_paths]):
            raise ValueError('Updater package or registration remains')
        stop_processes(state/'code')
        if os.path.lexists(archive): raise ValueError('Updater archive collision')
        state.rename(archive)
        return {'disabled':True,'removed':True,'archive':str(archive)}
    finally:
        for fd in reversed(locks): os.close(fd)

def main():
    if os.geteuid()!=0: raise PermissionError('Root required')
    ctl=next((p for p in ('/usr/bin/ls-control','/usr/sbin/ls-control') if Path(p).is_file()),None)
    if not ctl: raise ValueError('LS2 scanner unavailable')
    def refresh(): subprocess.run([ctl,'scan-services'],check=True,timeout=15,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    print(json.dumps(operate(sys.argv[1],'/var/lib/clean-your-tv-root-updater',
        '/var/luna-service2-dev','/var/lib/webosbrew/init.d/51-clean-your-tv-root-updater',
        '/media/developer/apps/usr/palm',sys.argv[2],refresh)))

if __name__=='__main__': main()
'''

# Dropbear on webOS limits exec request size. Keep the fixed script in one
# bounded command without uploading an executable or relying on shell heredocs.
import base64
import zlib
COMMAND = 'import base64,zlib;exec(zlib.decompress(base64.b64decode(' + repr(base64.b64encode(zlib.compress(SCRIPT.encode())).decode()) + ')))'
