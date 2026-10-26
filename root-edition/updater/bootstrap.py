"""Explicit one-time device setup, never an in-app updater self-upgrade."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

from updater.package import APP, inspect_package, safe_bytes

SERVICE='com.cleanyourtv.root.updater.service'
STATE=Path('/var/lib/clean-your-tv-root-updater')
ROOT_STATE=Path('/var/lib/clean-your-tv-root')
BASE=Path('/var/luna-service2-dev')
HOOK=Path('/var/lib/webosbrew/init.d/51-clean-your-tv-root-updater')


def permission_plan():
    ui=SERVICE+'.ui';health=SERVICE+'.health'
    methods=('check','status','reconcile','rollback')
    clients={}
    for app in (APP,'com.cleanyourtv.root.updater'):
        for pattern in (app,app+'-*'):clients[pattern]=[ui]+([health] if app==APP else [])
    return {'role.json':{'appId':SERVICE,'type':'regular','allowedNames':[SERVICE],
                        'permissions':[{'service':SERVICE,'inbound':[APP,APP+'-*','com.cleanyourtv.root.updater','com.cleanyourtv.root.updater-*'],'outbound':[]}]},
            'client.json':clients,
            'api.json':{ui:[SERVICE+'/'+m for m in methods],health:[SERVICE+'/'+m for m in ('install','restoreProfile','ready','confirm')]}}


def digest(raw):return hashlib.sha256(raw).hexdigest()


def verify_bundle(bundle):
    bundle=Path(bundle)
    manifest=json.loads(safe_bytes(bundle/'bundle.json',limit=65536))
    if manifest.get('schema')!=1 or not isinstance(manifest.get('files'),dict):raise ValueError('Invalid updater bundle')
    required={'root-updater.ipk','run-updater.py','service.js','services.json','package.json','setup-updater.py',
              'updater/core.py','updater/store.py','updater/profile.py','updater/device.py','updater/package.py','updater/cli.py',
              'updater/fetch.js','updater/bridge.js','updater/luna.py','updater/bootstrap.py','updater/release-public.pem',
              'updater/ca-bundle.crt','updater/ca-LICENSE.txt',
              'observed_install.py','installer_status.py','provision.py','deploy.py','setup.py','system_permissions.py','activity.py','startup_hook.py','python_binding.py','python_boot.js'}
    if set(manifest['files'])!=required:raise ValueError('Unexpected updater bundle inventory')
    for name,sha in manifest['files'].items():
        if digest(safe_bytes(bundle/name))!=sha:raise ValueError('Updater bundle hash mismatch: '+name)
    return manifest


def atomic(path,raw,mode=0o600):
    from updater.store import Store
    if isinstance(raw,str):raw=raw.encode()
    for parent in (path.parent,*path.parent.parents):
        info=parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid!=0 or info.st_mode & 0o022:raise ValueError('Unsafe bootstrap path')
    temporary=path.with_name(path.name+'.updater-new')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    try:
        with os.fdopen(fd,'wb') as f:os.fchmod(f.fileno(),mode);f.write(raw);f.flush();os.fsync(f.fileno())
        if os.path.lexists(path):safe_bytes(path,uid=0)
        os.replace(temporary,path)
        directory=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:
        if temporary.exists():temporary.unlink()


def apply(bundle,baseline):
    import sys
    if sys.version_info < (3, 9):raise RuntimeError('Root Updater requires TV Python 3.9+')
    if os.geteuid()!=0 or not Path('/usr/bin/luna-send').is_file():raise PermissionError('Explicit rooted webOS device required')
    from deploy import require_node
    require_node()
    manifest=verify_bundle(bundle);bundle=Path(bundle);baseline=Path(baseline)
    from deploy import verify_bundle as root_bundle
    baseline_manifest=root_bundle(baseline)
    release=json.loads(safe_bytes(baseline/'release.json'))
    raw=safe_bytes(baseline/baseline_manifest['package'])
    descriptor={'version':release['version'],'sha256':digest(raw),'size':len(raw),'local':True}
    inspect_package(raw,descriptor)
    # Compatibility bootstrap is refused on legacy infrastructure. Host migration
    # must restore and provision the new runtime; never overwrite a live runtime.
    proof=safe_bytes(ROOT_STATE/'recovery-provision.json',limit=65536,uid=0)
    recovery=json.loads(proof);runtime=ROOT_STATE/'runtime'
    for name in ('cli.py','update_guard.py'):
        target=runtime/name
        if recovery.get('files',{}).get(str(target))!=digest(safe_bytes(target,uid=0)):
            raise ValueError('Updater-compatible Root infrastructure required; migrate from computer first')
    from updater.device import Device
    Device.require_home_resume_runtime(ROOT_STATE)
    current=json.loads(safe_bytes(Path('/media/developer/apps/usr/palm/applications')/APP/'appinfo.json'))
    if current.get('version')!=descriptor['version']:raise ValueError('Baseline must match installed Root version')
    if STATE.exists() or STATE.is_symlink():raise FileExistsError('Updater setup exists; inspect retained state')
    if os.path.lexists(HOOK):raise FileExistsError('Updater boot hook collision')
    STATE.mkdir(mode=0o700);(STATE/'cache').mkdir(mode=0o700);code=STATE/'code';code.mkdir(mode=0o700)
    from updater.store import Store
    from python_binding import install_launcher, verify_binding
    verify_binding(ROOT_STATE)
    install_launcher(STATE, atomic)
    store=Store(STATE)
    store.write('bootstrap',{'phase':'prepared','bundle':manifest})
    code_files={k:v for k,v in manifest['files'].items() if k not in ('root-updater.ipk','setup-updater.py')}
    for name in code_files:
        target=code/name;target.parent.mkdir(mode=0o700,exist_ok=True)
        atomic(target,safe_bytes(bundle/name))
    atomic(STATE/'cache'/(descriptor['sha256']+'.ipk'),raw)
    store.write('current',descriptor)
    store.write('infrastructure',{'schema':1,'runtime':1,'updater':1,'code':code_files,'recovery_sha256':digest(proof)})
    from updater.device import Device
    device=Device(store,code=code);device.integrity()
    status=device.routing_status()
    if status['active'] or not status['safe']:raise ValueError('Verify LG Home routing before one-time updater setup')
    from observed_install import install
    store.write('bootstrap',{'phase':'installing-updater'})
    install('com.cleanyourtv.root.updater',str(bundle/'root-updater.ipk'),timeout=180,
            on_ready=lambda:store.write('bootstrap',{'phase':'submitting-updater'}),
            on_accepted=lambda event:store.write('bootstrap',{'phase':'accepted-updater','evidence':event}))
    from updater.package import members,archive,verify_payload
    payload=archive(members(safe_bytes(bundle/'root-updater.ipk'))['data.tar.gz'])
    verify_payload(Path('/media/developer/apps'),{name:digest(raw) for name,raw in payload.items()})
    store.write('bootstrap',{'phase':'provisioning'})
    paths={'service':BASE/'services.d'/(SERVICE+'.service'),'role':BASE/'roles.d'/(SERVICE+'.service.json'),
           'client':BASE/'client-permissions.d'/(SERVICE+'.service.json'),'api':BASE/'api-permissions.d'/(SERVICE+'.api.json')}
    original={key:safe_bytes(path,uid=0) for key,path in paths.items()}
    expected='Exec=/usr/bin/run-js-service -n /media/developer/apps/usr/palm/services/'+SERVICE
    if original['service'].decode().splitlines().count(expected)!=1:raise ValueError('Unexpected updater service registration')
    plan=permission_plan();role=json.loads(original['role'])
    if role.get('appId')!=SERVICE:raise ValueError('Unexpected updater role identity')
    role.update(plan['role.json'])
    runner=STATE/'run-service'
    runner_bytes=('#!/bin/sh\nset -eu\n[ "$#" -eq 0 ] || exit 2\ncd '+str(code)+'\nexport NODE_PATH=/usr/palm/frameworks:/usr/lib/nodejs:/usr/lib/node_modules\nexec /usr/bin/node /usr/palm/services/jsservicelauncher/bootstrap-node.js -- '+str(STATE/'bootstrap.pid')+' /var/palm/ls2-dev '+str(code)+'\n').encode()
    atomic(runner,runner_bytes,0o700)
    updated={'service':original['service'].decode().replace(expected,'Exec='+str(runner)).encode(),
             'role':json.dumps(role).encode(),'client':json.dumps(plan['client.json']).encode(),'api':json.dumps(plan['api.json']).encode()}
    store.write('registration',{'files':{str(paths[k]):{'original':v.decode(),'installed':updated[k].decode()} for k,v in original.items()}})
    for key,path in paths.items():
        mode=stat.S_IMODE(path.stat().st_mode);atomic(path,updated[key],mode)
    atomic(HOOK,'#!/bin/sh\nunset NODE_OPTIONS NODE_PATH\n/usr/bin/node '+str(code/'python_boot.js')+' '+str(STATE)+' '+str(code/'run-updater.py')+' worker </dev/null >/dev/null 2>&1 &\n',0o700)
    import provision
    provision.refresh()
    store.write('bootstrap',{'phase':'complete','hardware_validated':False})
    return {'installed':True,'hardware_validated':False,'instruction':'Open Root Updater and verify the service on the TV before enabling Root.'}
