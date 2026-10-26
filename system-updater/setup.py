#!/usr/bin/env python3
"""Explicit computer bootstrap; never repairs or replaces an existing supervisor."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import uuid

SERVICE='com.cleanyourtv.system.updater.service'
APP='com.cleanyourtv.system.updater'
STATE=Path('/var/lib/clean-your-tv-system-updater')
INSTALLED=Path('/media/developer/apps')
BASE=Path('/var/luna-service2-dev')
HOOK=Path('/var/lib/webosbrew/init.d/52-clean-your-tv-system-updater')
ROOT_UPDATER_TRANSACTION=Path('/var/lib/clean-your-tv-root-updater/transaction.json')
APPS={'home':'com.gathin.tvhome','helper':'com.local.nativehome','updater':'com.cleanyourtv.updater','root':'com.cleanyourtv.root.preview','root-updater':'com.cleanyourtv.root.updater'}
CODE={'python_boot.js','python_binding.py','infrastructure-paths.json','system_updater/__init__.py','system_updater/support/__init__.py','system_updater/core.py','system_updater/device.py','system_updater/cli.py','system_updater/policy.js','system_updater/release-public.pem','system_updater/ca-bundle.crt','system_updater/ca-LICENSE.txt','system_updater/support/store.py','system_updater/support/package.py','system_updater/support/profile.py','system_updater/support/luna.py','observed_install.py','installer_status.py','service.js','run-system-updater.py','services.json','package.json'}

def digest(raw):return hashlib.sha256(raw).hexdigest()

def safe(path,uid=None):
    path=Path(path)
    if any(p.is_symlink() for p in (path,*path.parents)):raise ValueError('Indirect file')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        info=os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_size>96*1024*1024 or (uid is not None and (info.st_uid!=uid or info.st_mode&0o022)):raise ValueError('Unsafe file')
        return stream.read(96*1024*1024+1)

def entries(raw):
    result={}
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
        total=0
        for member in archive:
            name=member.name;p=PurePosixPath(name)
            if member.isdir():continue
            if not member.isfile() or p.is_absolute() or str(p)!=name or '..' in p.parts or '\\' in name or '\x00' in name or name in result or member.size>32*1024*1024:raise ValueError('Unsafe archive')
            total+=member.size
            if total>96*1024*1024 or len(result)>4096:raise ValueError('Oversized archive')
            result[name]=archive.extractfile(member).read()
    return result

def package_files(raw):
    if raw[:8]!=b'!<arch>\n':raise ValueError('Invalid IPK')
    offset=8;parts={}
    while offset<len(raw):
        header=raw[offset:offset+60]
        if len(header)!=60 or header[58:]!=b'`\n':raise ValueError('Invalid IPK')
        size=int(header[48:58]);name=header[:16].decode().strip().rstrip('/')
        if size<0 or name in parts or offset+60+size>len(raw):raise ValueError('Invalid IPK')
        parts[name]=raw[offset+60:offset+60+size];offset+=60+size+size%2
    if set(parts)!={'debian-binary','control.tar.gz','data.tar.gz'} or parts['debian-binary']!=b'2.0\n':raise ValueError('Invalid IPK inventory')
    return entries(parts['data.tar.gz'])

def verify_bundle(bundle):
    bundle=Path(bundle);manifest=json.loads(safe(bundle/'bundle.json'))
    if manifest.get('schema')!=1 or manifest.get('supervisor')!=1 or set(manifest.get('files',{}))!=CODE|{'setup-system-updater.py','system-updater.ipk'}:raise ValueError('Unexpected supervisor bundle inventory')
    for name,sha in manifest['files'].items():
        if digest(safe(bundle/name))!=sha:raise ValueError('Supervisor bundle hash mismatch')
    return manifest

def infrastructure_name(name):
    if not isinstance(name,str):raise ValueError('Invalid infrastructure inventory')
    path=PurePosixPath(name)
    if path.is_absolute() or str(path)!=name or '..' in path.parts or '\\' in name or '\x00' in name or len(path.parts)<2 or path.parts[0] not in ('runtime','updater','service','support'):raise ValueError('Invalid infrastructure inventory')
    if path.parts[0]=='support' and name not in ('support/python_binding.py','support/python_boot.js'):raise ValueError('Invalid infrastructure support path')
    return name

def infrastructure_paths(bundle):
    names=json.loads(safe(Path(bundle)/'infrastructure-paths.json'))
    if not isinstance(names,list) or not names or len(set(map(infrastructure_name,names)))!=len(names):raise ValueError('Invalid pinned infrastructure inventory')
    return names

def infrastructure_destination(name,runtime=Path('/var/lib/clean-your-tv-root/runtime'),updater=Path('/var/lib/clean-your-tv-root-updater/code'),service=Path('/var/lib/clean-your-tv-root/service')):
    kind,relative=infrastructure_name(name).split('/',1)
    path=Path({'runtime':runtime,'updater':updater,'service':service,'support':Path(runtime).parent}[kind])/relative
    if any(parent.is_symlink() for parent in path.parents):raise ValueError('Indirect infrastructure path')
    return path

def capture_infrastructure(names,runtime=Path('/var/lib/clean-your-tv-root/runtime'),updater=Path('/var/lib/clean-your-tv-root-updater/code'),service=Path('/var/lib/clean-your-tv-root/service')):
    files={};absent=[]
    for name in names:
        path=infrastructure_destination(name,runtime,updater,service)
        try:path.lstat()
        except FileNotFoundError:absent.append(name);continue
        files[name]=safe(path,os.geteuid())
    return files,sorted(absent)

def verify_infrastructure_inventory(item,files,pinned=None):
    absent=item.get('absent',[])
    if item.get('kind')!='infrastructure' or item.get('files')!={n:digest(b) for n,b in files.items()} or not files or not isinstance(absent,list) or any(not isinstance(n,str) for n in absent) or len(set(absent))!=len(absent) or set(absent)&set(files):raise ValueError('Invalid infrastructure inventory')
    names=set(files)|set(absent)
    for name in names:infrastructure_name(name)
    if pinned is not None and names!=set(pinned):raise ValueError('Baseline infrastructure inventory differs from pinned bootstrap inventory')
    return names

def infrastructure_readback(item,raw):
    for name,data in entries(raw).items():
        if safe(infrastructure_destination(name),os.geteuid())!=data:raise ValueError('Installed infrastructure baseline mismatch')
    for name in item.get('absent',[]):
        try:infrastructure_destination(name).lstat()
        except FileNotFoundError:continue
        raise ValueError('Absent infrastructure baseline changed')


def verify_baseline(baseline,bundle=None):
    baseline=Path(baseline);manifest=json.loads(safe(baseline/'baseline.json'))
    edition=manifest.get('edition');expected={'root','root-updater'} if edition=='root' else {'home','helper','updater'}
    if edition=='root':expected.add('root-infrastructure')
    if manifest.get('schema')!=1 or manifest.get('supervisor')!=1 or edition not in ('root','no-root') or not re.fullmatch(r'v\d{1,4}\.\d{1,4}\.\d{1,4}',manifest.get('release','')) or {c['name'] for c in manifest['components']}!=expected or len(manifest['components'])!=len(expected):raise ValueError('Invalid baseline')
    for item in manifest['components']:
        sha=item.get('sha256','')
        if not re.fullmatch('[a-f0-9]{64}',sha) or item.get('local') is not True:raise ValueError('Invalid baseline descriptor')
        raw=safe(baseline/'cache'/sha)
        if len(raw)!=item['size'] or digest(raw)!=sha:raise ValueError('Baseline hash mismatch')
        if item['name']=='root-infrastructure':
            files=entries(raw)
            verify_infrastructure_inventory(item,files,infrastructure_paths(bundle) if bundle is not None else None)
        else:
            app=APPS[item['name']];files=package_files(raw)
            info=json.loads(files['usr/palm/applications/'+app+'/appinfo.json'])
            if item.get('kind')!='ipk' or item.get('application')!=app or info.get('id')!=app or info.get('version')!=item['version']:raise ValueError('Baseline package identity mismatch')
    return manifest

def tgz(files):
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w',format=tarfile.USTAR_FORMAT) as archive:
        for name,raw in sorted(files.items()):
            item=tarfile.TarInfo(name);item.size=len(raw);item.mode=0o644;item.mtime=1704067200
            # Helper native binaries must remain runnable after rollback.
            if name.rsplit('/',1)[-1] in ('detach','relay','resume','boot-recover.sh'):item.mode=0o755
            archive.addfile(item,io.BytesIO(raw))
    return gzip.compress(buffer.getvalue(),mtime=0)

def require_transition_home(installed,edition):
    app=APPS['root' if edition=='root' else 'home']
    info=json.loads(safe(Path(installed)/'usr/palm/applications'/app/'appinfo.json'))
    if info.get('id')!=app or type(info.get('systemUpdateProtocol')) is not int or info['systemUpdateProtocol']!=1:raise ValueError('Install the transition Home from computer before enabling System Updates')

def snapshot(bundle,edition,output,installed=INSTALLED,runtime=Path('/var/lib/clean-your-tv-root/runtime'),updater=Path('/var/lib/clean-your-tv-root-updater/code'),service=Path('/var/lib/clean-your-tv-root/service')):
    verify_bundle(bundle)
    names=('root','root-updater') if edition=='root' else ('home','helper','updater')
    if edition not in ('root','no-root'):raise ValueError('Invalid edition')
    require_transition_home(installed,edition)
    output=Path(output);output.mkdir(mode=0o700);(output/'cache').mkdir(mode=0o700)
    components=[]
    for name in names:
        app=APPS[name];info=json.loads(safe(Path(installed)/'usr/palm/applications'/app/'appinfo.json'))
        if info.get('id')!=app or not re.fullmatch(r'\d{1,4}\.\d{1,4}\.\d{1,4}',info.get('version','')):raise ValueError('Installed package identity invalid')
        metadata=json.loads(safe(Path(installed)/'usr/palm/packages'/app/'packageinfo.json'))
        services=metadata.get('services',[])
        allowed={'home':['com.gathin.tvhome.renewal'],'helper':['com.local.nativehome.service'],'updater':['com.cleanyourtv.updater.service'],'root':['com.cleanyourtv.root.preview.service'],'root-updater':['com.cleanyourtv.root.updater.service']}
        if metadata.get('id')!=app or metadata.get('version')!=info['version'] or services!=allowed[name]:raise ValueError('Installed package services invalid')
        files={}
        prefixes=['usr/palm/applications/'+app,'usr/palm/packages/'+app]+['usr/palm/services/'+s for s in services]
        for prefix in prefixes:
            folder=Path(installed)/prefix
            for path in sorted(folder.rglob('*')):
                rel=path.relative_to(folder)
                if 'state' in rel.parts:continue
                if path.is_symlink():raise ValueError('Indirect installed package')
                if path.is_file():files[prefix+'/'+rel.as_posix()]=safe(path)
        control=('Package: '+app+'\nVersion: '+info['version']+'\nArchitecture: '+('arm' if name=='helper' else 'all')+'\nMaintainer: Clean Your TV\nDescription: Captured installed baseline\n').encode()
        raw=bytearray(b'!<arch>\n')
        for part,data in {'debian-binary':b'2.0\n','control.tar.gz':tgz({'control':control}),'data.tar.gz':tgz(files)}.items():
            raw.extend(f'{part + "/":<16}{0:<12}{0:<6}{0:<6}{"100644":<8}{len(data):<10}`\n'.encode());raw.extend(data)
            if len(data)%2:raw.extend(b'\n')
        raw=bytes(raw);sha=digest(raw);(output/'cache'/sha).write_bytes(raw)
        components.append({'name':name,'kind':'ipk','application':app,'version':info['version'],'sha256':sha,'size':len(raw),'local':True})
    if edition=='root':
        files,absent=capture_infrastructure(infrastructure_paths(bundle),runtime,updater,service)
        raw=tgz(files);sha=digest(raw);(output/'cache'/sha).write_bytes(raw)
        components.append({'name':'root-infrastructure','kind':'infrastructure','version':components[0]['version'],'sha256':sha,'size':len(raw),'local':True,'files':{n:digest(b) for n,b in files.items()},'absent':absent})
    manifest={'schema':1,'supervisor':1,'edition':edition,'release':'v0.0.0','notes':'Exact installed baseline captured during explicit computer setup.','components':components}
    (output/'baseline.json').write_text(json.dumps(manifest)+'\n')
    verify_baseline(output,bundle)
    return output


def permission_plan():
    group=SERVICE+'.ui';launcher=SERVICE+'.launcher'
    clients={}
    for app in ('com.gathin.tvhome','com.cleanyourtv.root.preview','com.cleanyourtv.updater','com.cleanyourtv.root.updater'):
        for pattern in (app,app+'-*'):clients[pattern]=[group]+([launcher] if app in ('com.gathin.tvhome','com.cleanyourtv.root.preview') else [])
    return {'role.json':{'appId':SERVICE,'type':'regular','allowedNames':[SERVICE],'permissions':[{'service':SERVICE,'inbound':list(clients),'outbound':[]}]},
            'client.json':clients,'api.json':{group:[SERVICE+'/'+m for m in ('check','status','rollback','reconcile')],launcher:[SERVICE+'/'+m for m in ('install','restoreProfile','healthy')]}}

def atomic(path,raw,mode=0o600):
    path=Path(path);raw=raw.encode() if isinstance(raw,str) else raw
    for parent in path.parents:
        info=parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid not in (0,os.geteuid()) or (info.st_mode&0o022 and not info.st_mode&stat.S_ISVTX):raise ValueError('Unsafe destination parent')
    if os.path.lexists(path):safe(path,os.geteuid())
    tmp=path.with_name(path.name+'.system-new')
    fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    try:
        with os.fdopen(fd,'wb') as stream:os.fchmod(stream.fileno(),mode);stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.replace(tmp,path);fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:os.fsync(fd)
        finally:os.close(fd)
    finally:
        if tmp.exists():tmp.unlink()

def require_legacy_idle(paths=None):
    paths=paths or [ROOT_UPDATER_TRANSACTION,INSTALLED/'usr/palm/services/com.cleanyourtv.updater.service/state/transaction.json']
    for path in paths:
        if os.path.lexists(path):
            value=json.loads(safe(path))
            if not isinstance(value,dict) or value.get('phase',value.get('status')) not in ('complete','healthy','rolled-back','aborted'):raise ValueError('Unfinished legacy update requires recovery before supervisor setup')
            if path==ROOT_UPDATER_TRANSACTION and value.get('homeResumePhase')!=value.get('phase'):raise ValueError('Pending legacy Root Home recovery must finish before supervisor setup')


def legacy_lockdown_targets(bases,root_updater):
    return {str(Path(base)/folder/name) for base in bases for folder,name in (('api-permissions.d','com.cleanyourtv.updater.permissions.json'),('','com.cleanyourtv.updater.permissions.receipt.json'))}|{str(Path(bases[0])/'api-permissions.d/com.cleanyourtv.root.updater.service.api.json'),str(Path(root_updater)/'registration.json')}

def apply_legacy_lockdown(state,bases=None,root_updater=Path('/var/lib/clean-your-tv-root-updater')):
    bases=[Path(p) for p in (bases or [BASE,Path('/var/luna-service2')])];root_updater=Path(root_updater);state=Path(state)
    receipt=state/'legacy-lockdown.json';allowed=legacy_lockdown_targets(bases,root_updater)
    forbidden={'com.cleanyourtv.updater.service/'+m for m in ('install','rollback','reconcile')}|{'com.cleanyourtv.root.updater.service/'+m for m in ('install','rollback','reconcile','ready','confirm')}|{'org.webosbrew.hbchannel.service/install'}
    def disabled(raw):
        value=json.loads(raw)
        if not isinstance(value,dict) or any(not isinstance(k,str) or not isinstance(v,list) or any(not isinstance(uri,str) for uri in v) for k,v in value.items()):raise ValueError('Invalid legacy API permissions')
        for methods in value.values():
            if any(uri.endswith('/*') and any(target.startswith(uri[:-1]) for target in forbidden) for uri in methods):raise ValueError('Unknown wildcard legacy mutating grant')
        return (json.dumps({k:[uri for uri in v if uri not in forbidden] for k,v in value.items()},sort_keys=True,separators=(',',':'))+'\n').encode()
    if os.path.lexists(receipt):value=json.loads(safe(receipt,os.geteuid()))
    else:
        files={}
        def add(path,raw,new):files[str(path)]={'original':raw.decode(),'disabled':new.decode(),'mode':stat.S_IMODE(path.stat().st_mode)}
        for base in bases:
            api=base/'api-permissions.d/com.cleanyourtv.updater.permissions.json';ownership=base/'com.cleanyourtv.updater.permissions.receipt.json'
            if not os.path.lexists(api) and not os.path.lexists(ownership):continue
            original=safe(api,os.geteuid());proof_raw=safe(ownership,os.geteuid());proof=json.loads(proof_raw)
            expected={str(base/folder/'com.cleanyourtv.updater.permissions.json') for folder in ('api-permissions.d','client-permissions.d','manifests.d')}
            if proof.get('schema')!=1 or not isinstance(proof.get('files'),list) or len(proof['files'])!=3 or {e.get('path') for e in proof['files']}!=expected:raise ValueError('Unknown legacy permission ownership')
            for entry in proof['files']:
                raw=safe(Path(entry['path']),os.geteuid())
                if raw.decode()!=entry.get('content') or digest(raw)!=entry.get('sha256'):raise ValueError('Legacy permission changed')
            new=disabled(original);add(api,original,new)
            for entry in proof['files']:
                if entry['path']==str(api):entry.update(content=new.decode(),sha256=digest(new))
            add(ownership,proof_raw,(json.dumps(proof,sort_keys=True,separators=(',',':'))+'\n').encode())
        api=bases[0]/'api-permissions.d/com.cleanyourtv.root.updater.service.api.json';registration=root_updater/'registration.json'
        if os.path.lexists(api) or os.path.lexists(registration):
            original=safe(api,os.geteuid());proof_raw=safe(registration,os.geteuid());proof=json.loads(proof_raw)
            if not isinstance(proof.get('files'),dict) or str(api) not in proof['files'] or proof['files'][str(api)].get('installed')!=original.decode():raise ValueError('Root updater permission ownership changed')
            new=disabled(original);add(api,original,new);proof['files'][str(api)]['installed']=new.decode()
            add(registration,proof_raw,(json.dumps(proof,sort_keys=True,separators=(',',':'))+'\n').encode())
        value={'schema':1,'files':files};atomic(receipt,json.dumps(value,sort_keys=True))
    if value.get('schema')!=1 or not isinstance(value.get('files'),dict) or set(value['files'])-allowed:raise ValueError('Unknown legacy lockdown receipt')
    for name,record in value['files'].items():
        if set(record)!={'original','disabled','mode'} or not isinstance(record['original'],str) or not isinstance(record['disabled'],str) or type(record['mode']) is not int or not 0<=record['mode']<=0o777 or record['mode']&0o022 or safe(Path(name),os.geteuid()) not in (record['original'].encode(),record['disabled'].encode()):raise ValueError('Legacy lockdown permission changed')
    for name,record in value['files'].items():
        if safe(Path(name),os.geteuid())!=record['disabled'].encode():atomic(Path(name),record['disabled'],record['mode'])
    return value


def provision(bundle,baseline,state=STATE,installed=INSTALLED,base=BASE,hook=HOOK,install=None,refresh=None):
    state=Path(state)
    if os.path.lexists(state):raise FileExistsError('Supervisor setup exists; inspect retained state from computer before changing it')
    require_legacy_idle()
    bundle=Path(bundle);baseline=Path(baseline);manifest=verify_bundle(bundle);current=verify_baseline(baseline,bundle)
    require_transition_home(installed,current['edition'])
    if os.path.lexists(hook):raise FileExistsError('Supervisor boot hook exists')
    # Prove baseline payloads match installed files before creating any durable state.
    for item in current['components']:
        raw=safe(baseline/'cache'/item['sha256'])
        if item['kind']=='ipk':
            for name,data in package_files(raw).items():
                if safe(Path(installed)/name)!=data:raise ValueError('Installed baseline payload mismatch: '+name)
        else:infrastructure_readback(item,raw)
    state.mkdir(mode=0o700);code=state/'code';code.mkdir(mode=0o700);(state/'cache').mkdir(mode=0o700)
    def record(name,value):atomic(state/(name+'.json'),json.dumps(value,sort_keys=True))
    sys.path.insert(0,str(bundle))
    from python_binding import install_launcher
    install_launcher(state, atomic)
    record('bootstrap',{'phase':'prepared','edition':current['edition']})
    for name in CODE:
        path=code/name;path.parent.mkdir(parents=True,mode=0o700,exist_ok=True);atomic(path,safe(bundle/name))
    record('infrastructure',{'schema':1,'code':{name:manifest['files'][name] for name in sorted(CODE)}})
    for item in current['components']:atomic(state/'cache'/item['sha256'],safe(baseline/'cache'/item['sha256']))
    record('baseline',current);record('current-'+current['edition'],current)
    if install is None:
        sys.path.insert(0,str(code));from observed_install import install
    require_legacy_idle()
    record('bootstrap',{'phase':'installing-supervisor'})
    install(APP,str(bundle/'system-updater.ipk'),timeout=180,on_ready=lambda:record('bootstrap',{'phase':'submitting-supervisor'}),on_accepted=lambda evidence:record('bootstrap',{'phase':'accepted-supervisor','evidence':evidence}))
    for name,data in package_files(safe(bundle/'system-updater.ipk')).items():
        if safe(Path(installed)/name)!=data:raise ValueError('Installed supervisor payload mismatch')
    record('bootstrap',{'phase':'provisioning'})
    paths={'service':Path(base)/'services.d'/(SERVICE+'.service'),'role':Path(base)/'roles.d'/(SERVICE+'.service.json'),'client':Path(base)/'client-permissions.d'/(SERVICE+'.service.json'),'api':Path(base)/'api-permissions.d'/(SERVICE+'.api.json')}
    original={key:safe(path,os.geteuid()) for key,path in paths.items()}
    expected='Exec=/usr/bin/run-js-service -n '+str(Path(installed)/'usr/palm/services'/SERVICE)
    if original['service'].decode().splitlines().count(expected)!=1 or json.loads(original['role']).get('appId')!=SERVICE:raise ValueError('Unexpected supervisor registration')
    runner=state/'run-service'
    atomic(runner,'#!/bin/sh\nset -eu\n[ "$#" -eq 0 ] || exit 2\ncd '+str(code)+'\nexport NODE_PATH=/usr/palm/frameworks:/usr/lib/nodejs:/usr/lib/node_modules\nexec /usr/bin/node /usr/palm/services/jsservicelauncher/bootstrap-node.js -- '+str(state/'bootstrap.pid')+' /var/palm/ls2-dev '+str(code)+'\n',0o700)
    plan=permission_plan();role=json.loads(original['role']);role.update(plan['role.json'])
    updated={'service':original['service'].decode().replace(expected,'Exec='+str(runner)).encode(),'role':json.dumps(role).encode(),'client':json.dumps(plan['client.json']).encode(),'api':json.dumps(plan['api.json']).encode()}
    record('registration',{'files':{str(paths[k]):{'original':original[k].decode(),'installed':v.decode()} for k,v in updated.items()}})
    for key,path in paths.items():atomic(path,updated[key],stat.S_IMODE(path.stat().st_mode))
    apply_legacy_lockdown(state)
    atomic(hook,'#!/bin/sh\nunset NODE_OPTIONS NODE_PATH\n/usr/bin/node '+str(code/'python_boot.js')+' '+str(state)+' '+str(code/'run-system-updater.py')+' worker </dev/null >/dev/null 2>&1 &\n',0o700)
    if refresh is None:
        executable=next((p for p in (Path('/usr/bin/ls-control'),Path('/usr/sbin/ls-control')) if p.is_file()),None)
        if executable is None:raise ValueError('ls-control unavailable')
        subprocess.run([str(executable),'scan-services'],check=True,timeout=15,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    else:refresh()
    require_legacy_idle()
    for item in current['components']:
        if item['kind']=='ipk':
            for name,data in package_files(safe(baseline/'cache'/item['sha256'])).items():
                if safe(Path(installed)/name)!=data:raise ValueError('Installed baseline changed during bootstrap')
        else:infrastructure_readback(item,safe(baseline/'cache'/item['sha256']))
    record('bootstrap',{'phase':'complete','edition':current['edition'],'hardware_validated':False})
    return {'installed':True,'edition':current['edition'],'hardware_validated':False}

def execute(bundle,baseline,alias,identity=None,run=subprocess.run,edition=None,python='/usr/bin/python3'):
    if python not in ('/usr/bin/python3','/var/lib/clean-your-tv-python/4a71641c8d5536175e404a961624e8656eba30e97b5026f6bd7dc31e4bbeaaea/bin/python3.13'):raise ValueError('Unapproved Python executable')
    manifest=verify_bundle(bundle)
    baseline_manifest=verify_baseline(baseline,bundle) if baseline is not None else None
    if baseline is None and edition not in ('root','no-root'):raise ValueError('Edition required')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',alias):raise ValueError('Use an explicit OpenSSH host alias')
    options=['-o','StrictHostKeyChecking=yes','-o','BatchMode=yes','-o','ConnectTimeout=10']
    if identity is not None:options+=['-i',str(Path(identity).expanduser().resolve())]
    remote='/tmp/cytv-system-updater-'+uuid.uuid4().hex
    run(['ssh',*options,alias,'umask 077; test "$(id -u)" = 0 && mkdir '+shlex.quote(remote)],check=True,stdin=subprocess.DEVNULL)
    with tempfile.TemporaryDirectory(prefix='system-transfer-') as temporary:
        staging=Path(temporary).resolve();source=staging/'bundle';source.mkdir()
        for name in (*manifest['files'],'bundle.json'):
            target=source/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(safe(Path(bundle)/name))
        sources=[str(source)]
        if baseline_manifest is not None:
            target=staging/'baseline';target.mkdir();(target/'cache').mkdir()
            (target/'baseline.json').write_bytes(safe(Path(baseline)/'baseline.json'))
            for item in baseline_manifest['components']:(target/'cache'/item['sha256']).write_bytes(safe(Path(baseline)/'cache'/item['sha256']))
            sources.append(str(target))
        run(['scp','-O',*options,'-r',*sources,alias+':'+remote+'/'],check=True,stdin=subprocess.DEVNULL)
    remote_bundle=remote+'/bundle'
    argv=['env','-u','PYTHONHOME','-u','PYTHONPATH','PYTHONDONTWRITEBYTECODE=1','PYTHONNOUSERSITE=1',python,remote_bundle+'/setup-system-updater.py','--device','--apply','--bundle',remote_bundle]
    if baseline is not None:argv+=['--baseline',remote+'/baseline']
    else:argv+=['--edition',edition]
    return run(['ssh',*options,alias,shlex.join(argv)],check=True,stdin=subprocess.DEVNULL)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--bundle',type=Path,required=True);parser.add_argument('--baseline',type=Path);parser.add_argument('--edition',choices=('root','no-root'));parser.add_argument('--ssh');parser.add_argument('--identity',type=Path);parser.add_argument('--apply',action='store_true');parser.add_argument('--device',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--python',default='/usr/bin/python3',choices=('/usr/bin/python3','/var/lib/clean-your-tv-python/4a71641c8d5536175e404a961624e8656eba30e97b5026f6bd7dc31e4bbeaaea/bin/python3.13'))
    args=parser.parse_args()
    if args.device:
        if not args.apply or os.geteuid()!=0 or not Path('/usr/bin/luna-send').is_file() or sys.version_info<(3,9):raise PermissionError('Explicit root webOS Python 3.9+ setup required')
        subprocess.run(['/usr/bin/node','-e','process.exit(Number(process.versions.node.split(".")[0])>=8?0:1)'],check=True)
        if args.baseline is None:
            if not args.edition:parser.error('--edition is required without --baseline')
            with tempfile.TemporaryDirectory(prefix='system-baseline-') as tmp:
                baseline=snapshot(args.bundle,args.edition,Path(tmp)/'baseline')
                print(json.dumps(provision(args.bundle,baseline)))
        else:print(json.dumps(provision(args.bundle,args.baseline)))
        return
    verify_bundle(args.bundle);baseline=verify_baseline(args.baseline,args.bundle) if args.baseline else {'edition':args.edition}
    if not baseline['edition']:parser.error('--edition is required without --baseline')
    print(json.dumps({'operation':'one-time-system-updater-setup','edition':baseline['edition'],'permissions':permission_plan(),'hardware_validated':False},indent=2))
    if args.apply:
        if not args.ssh:parser.error('--apply requires --ssh')
        execute(args.bundle,args.baseline,args.ssh,args.identity,edition=baseline['edition'],python=args.python)

if __name__=='__main__':main()
