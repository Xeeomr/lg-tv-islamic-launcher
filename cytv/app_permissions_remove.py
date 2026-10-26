"""Clean webOS-generated Root Updater app permissions after package removal."""
SCRIPT = r'''
import json, os, stat, subprocess
from pathlib import Path

def operate(root, base, refresh, uid=0):
    root,base=Path(root),Path(base)
    app='com.cleanyourtv.root.updater'
    if any(os.path.lexists(base/folder/name) for folder,name in
           (('applications',app),('services',app+'.service'),('packages',app))):
        raise ValueError('Root Updater package is still present')
    role=root/'roles.d'/(app+'.app.json')
    client=root/'client-permissions.d'/(app+'.app.json')
    def read(path):
        for parent in path.parents:
            if not stat.S_ISDIR(parent.lstat().st_mode): raise ValueError('Indirect permission path')
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,'rb') as f:
            info=os.fstat(f.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid!=uid or info.st_nlink!=1 or info.st_mode & 0o022: raise ValueError('Unsafe permission file')
            raw=f.read(65537)
            if len(raw)>65536: raise ValueError('Oversized permission file')
            return json.loads(raw)
    expected={'appId':app,'type':'regular','allowedNames':[app+'-*'],'trustLevel':'public',
              'permissions':[{'service':app+'-*','outbound':['*']}]}
    if os.path.lexists(role) and read(role)!=expected: raise ValueError('Unknown app role ownership')
    if os.path.lexists(client):
        value=read(client)
        if not isinstance(value,dict) or set(value)!={app+'-*'} or not isinstance(value[app+'-*'],list) or not all(isinstance(g,str) for g in value[app+'-*']):
            raise ValueError('Unknown app permission ownership')
    # Validate both before deleting either. Missing files allow an interrupted cleanup to resume.
    for path in (role,client):
        if os.path.lexists(path): path.unlink()
    refresh()
    return True

if __name__=='__main__':
    ctl=next((p for p in ('/usr/bin/ls-control','/usr/sbin/ls-control') if Path(p).is_file()),None)
    if not ctl: raise ValueError('LS2 scanner unavailable')
    def refresh(): subprocess.run([ctl,'scan-services'],check=True,timeout=15,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    operate('/var/luna-service2-dev','/media/developer/apps/usr/palm',refresh)
    print('CYTV_APP_PERMISSIONS_REMOVED')
'''
