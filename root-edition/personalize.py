"""Copy packaged preferences from the user's existing Home into the isolated UI.

Never evaluates JavaScript or reads browser databases. This is explicit migration
from an installed trusted launcher, not an importer for arbitrary downloaded JS.
"""
import os
from pathlib import Path, PurePosixPath
import re
import stat

APP='com.cleanyourtv.root.preview'

def prepare(source):
    source=Path(source)
    if source.is_symlink() or not source.is_dir():raise ValueError('Invalid source directory')
    # Installed developer assets can retain desktop ownership/modes. Treat them
    # strictly as UI data; never evaluate or import them in a root process.
    def read(name,limit):
        p=source/name
        if any(x.is_symlink() for x in (p,*p.parents)):
            raise ValueError('Indirect source')
        fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,'rb') as stream:
            before=os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size>limit:
                raise ValueError('Invalid packaged data file')
            data=stream.read(limit+1);after=os.fstat(stream.fileno())
            if len(data)>limit or (before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_size,after.st_mtime_ns,after.st_ctime_ns):
                raise ValueError('Source changed')
            return data
    apps=read('apps.js',4*1024*1024);config=read('config.js',1024*1024)
    if b'window.TV_APPS' not in apps or b'window.CONFIG' not in config:
        raise ValueError('Unexpected packaged preferences')
    files={'apps.js':apps,'config.js':config+b'\nwindow.CONFIG.hiddenApps=(window.CONFIG.hiddenApps||[]).concat(["'+APP.encode()+b'"]);\n'}
    icons=set(re.findall(r'''["'](icons/[^"']+)["']''',apps.decode('utf-8')))
    if len(icons)>200:raise ValueError('Too many icons')
    for name in sorted(icons):
        p=PurePosixPath(name)
        if len(p.parts)!=2 or '..' in p.parts or '\\' in name or p.suffix.lower() not in ('.png','.jpg','.jpeg','.webp'):
            raise ValueError('Invalid icon path')
        files[name]=read(name,256*1024)
    if sum(map(len,files.values()))>16*1024*1024:raise ValueError('Profile too large')
    return files


def from_profile(path):
    """Import JSON data only; never execute updater code or modify its backup."""
    import json
    path=Path(path)
    if any(p.is_symlink() for p in (path,*path.parents)):raise ValueError('Indirect profile')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        st=os.fstat(stream.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_size>4*1024*1024:raise ValueError('Invalid profile size')
        data=stream.read(4*1024*1024+1)
    if len(data)>4*1024*1024:raise ValueError('Profile too large')
    value=json.loads(data)
    if not isinstance(value,dict) or value.get('schema')!=1:raise ValueError('Invalid profile schema')
    inventory=value.get('inventory');config=value.get('config')
    if not isinstance(inventory,dict) or not isinstance(config,dict):raise ValueError('Missing profile data')
    apps=inventory.get('apps');inputs=inventory.get('inputs')
    if not isinstance(apps,list) or not isinstance(inputs,list) or len(apps)>200 or len(inputs)>100:raise ValueError('Invalid inventory')
    for app in apps:
        if (not isinstance(app,dict) or not isinstance(app.get('id'),str) or not app['id']
                or not isinstance(app.get('title'),str) or len(app['title'])>256
                or not isinstance(app.get('icon'),str)
                or not re.fullmatch(r'data:image/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+',app['icon'])):
            raise ValueError('Invalid application profile')
    if type(config.get('columns')) is not int or not 1<=config['columns']<=8:raise ValueError('Invalid columns')
    for key in ('dockApps','hiddenApps'):
        if not isinstance(config.get(key),list) or not all(isinstance(x,str) for x in config[key]):raise ValueError('Invalid app selection')
    config=dict(config);config['hiddenApps']=list(dict.fromkeys(config['hiddenApps']+[APP]))
    return {'apps.js':('window.TV_APPS='+json.dumps(inventory)+';\n').encode(),
            'config.js':('window.CONFIG='+json.dumps(config)+';\n').encode()}
