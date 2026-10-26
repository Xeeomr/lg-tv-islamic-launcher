"""Own, narrowly scoped system registration for recovery ActivityManager calls."""
import json,os
from pathlib import Path

NAME='com.cleanyourtv.root.preview.service'
STATE=Path('/var/lib/clean-your-tv-root')
MANIFEST=Path('/var/luna-service2/manifests.d/com.cleanyourtv.root.preview.recovery.json')

def contents():
    base=STATE/'permissions'
    group=NAME+'.recoveryActivity'
    files={base/'client.json':{NAME:[group],NAME+'*':[group]},
           base/'api.json':{group:['com.webos.service.activitymanager/'+m for m in ('list','create','cancel','adopt','complete')]}}
    files[MANIFEST]={'id':'com.cleanyourtv.root.preview.recovery','version':'1.0.0','clientPermissionFiles':[str(base/'client.json')],'apiPermissionFiles':[str(base/'api.json')]}
    return {path:(json.dumps(value,sort_keys=True,indent=2)+'\n').encode() for path,value in files.items()}

def apply(secure,write):
    files=contents();receipt=STATE/'system-permissions.json'
    expected={str(p):data.decode() for p,data in files.items()}
    if receipt.exists():
        if json.loads(secure(receipt))!=expected:raise ValueError('System permissions receipt conflict')
    else:
        if any(os.path.lexists(p) for p in files):raise ValueError('System permissions path collision')
        write(receipt,json.dumps(expected).encode())
    base=STATE/'permissions'
    if base.is_symlink():raise ValueError('Indirect system permissions directory')
    base.mkdir(mode=0o700,exist_ok=True)
    for path,data in files.items():
        if os.path.lexists(path):
            if secure(path)!=data:raise ValueError('System permissions drift')
        else:write(path,data)
    return {'returnValue':True,'scope':'recovery ActivityManager only'}

def remove(secure):
    receipt=STATE/'system-permissions.json'
    if not receipt.exists():return
    files=contents()
    if json.loads(secure(receipt))!={str(p):v.decode() for p,v in files.items()}:raise ValueError('System permissions receipt conflict')
    for path,data in files.items():
        if os.path.lexists(path) and secure(path)!=data:raise ValueError('System permissions drift')
    for path in reversed(list(files)):
        if path.exists():
            path.unlink()
            fd=os.open(path.parent,os.O_RDONLY)
            try:os.fsync(fd)
            finally:os.close(fd)
    # Keep receipt for retry and audit; exact paths are idempotently removable.
