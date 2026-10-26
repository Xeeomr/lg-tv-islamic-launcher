"""Remove only No-root updater permission files covered by their ownership receipt."""
SCRIPT = r'''
import hashlib, json, os, stat, subprocess
from pathlib import Path

def operate(root, refresh, uid=0):
    root=Path(root)
    receipt=root/'com.cleanyourtv.updater.permissions.receipt.json'
    expected={str(root/folder/'com.cleanyourtv.updater.permissions.json') for folder in ('api-permissions.d','client-permissions.d','manifests.d')}
    def read(path):
        for parent in path.parents:
            if not stat.S_ISDIR(parent.lstat().st_mode): raise ValueError('Indirect permission path')
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,'rb') as f:
            info=os.fstat(f.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid!=uid or info.st_nlink!=1 or info.st_mode & 0o022: raise ValueError('Unsafe permission file')
            raw=f.read(65537)
            if len(raw)>65536: raise ValueError('Oversized permission file')
            return raw
    if os.path.lexists(receipt):
        value=json.loads(read(receipt));files=value.get('files',[])
        if value.get('schema')!=1 or len(files)!=3 or {f['path'] for f in files}!=expected: raise ValueError('Unknown permission ownership receipt')
        for entry in files:
            raw=entry['content'].encode()
            if hashlib.sha256(raw).hexdigest()!=entry['sha256']: raise ValueError('Invalid permission receipt hash')
            if os.path.lexists(entry['path']) and read(Path(entry['path']))!=raw: raise ValueError('Permission file changed')
        for entry in sorted(files,key=lambda f:'manifests.d' not in f['path']):
            if os.path.lexists(entry['path']): Path(entry['path']).unlink()
        refresh()
        receipt.unlink()
    elif any(os.path.lexists(p) for p in expected):
        raise ValueError('Updater permissions lack ownership evidence')
    return True

if __name__=='__main__':
    ctl=next((p for p in ('/usr/bin/ls-control','/usr/sbin/ls-control') if Path(p).is_file()),None)
    if not ctl: raise ValueError('LS2 scanner unavailable')
    def refresh(): subprocess.run([ctl,'scan-services'],check=True,timeout=15,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    operate('/var/luna-service2-dev',refresh)
    print('CYTV_LEGACY_PERMISSIONS_REMOVED')
'''
