"""Fixed-path TV effects. Loaded only from the independently provisioned updater."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from updater.package import APP, inspect_package, safe_bytes, verify_payload

STATE = Path('/var/lib/clean-your-tv-root-updater')
ROOT_STATE = Path('/var/lib/clean-your-tv-root')
INSTALLED = Path('/media/developer/apps')


class Device:
    def __init__(self, store, code=None, root_state=ROOT_STATE, installed=INSTALLED):
        self.store=store
        self.code=Path(code or Path(__file__).resolve().parents[1])
        self.root_state=Path(root_state)
        self.installed_root=Path(installed)
        self.state=Path(store.root)

    def integrity(self):
        receipt=self.store.read('infrastructure')
        if not receipt or receipt.get('schema')!=1 or receipt.get('runtime')!=1 or receipt.get('updater')!=1:
            raise ValueError('One-time Root Updater setup required')
        for name,digest in receipt['code'].items():
            path=Path(name)
            if path.is_absolute() or '..' in path.parts or str(path)!=name:raise ValueError('Unsafe infrastructure inventory')
            if hashlib.sha256(safe_bytes(self.code/name,uid=0)).hexdigest()!=digest:raise ValueError('Updater infrastructure changed')
        proof=safe_bytes(self.root_state/'recovery-provision.json',limit=65536,uid=0)
        if hashlib.sha256(proof).hexdigest()!=receipt['recovery_sha256']:raise ValueError('Recovery infrastructure changed; host setup required')
        recovery=json.loads(proof)
        if recovery.get('mode')!='recovery-only':raise ValueError('Recovery not provisioned')
        files=recovery.get('files',{})
        for name in ('cli.py','update_guard.py'):
            if str(self.root_state/'runtime'/name) not in files:raise ValueError('Updater-compatible recovery runtime required')
        for name,digest in files.items():
            path=Path(name)
            if not path.is_relative_to(self.root_state):raise ValueError('Foreign recovery infrastructure')
            if hashlib.sha256(safe_bytes(path,limit=1048576,uid=0)).hexdigest()!=digest:raise ValueError('Recovery integrity failed')
        from python_binding import verify_binding
        verify_binding(self.state);verify_binding(self.root_state)
        self.require_home_resume_runtime(self.root_state)
        return receipt

    @staticmethod
    def require_home_resume_runtime(root_state):
        # Called only after the root-owned recovery inventory has been verified.
        import ast
        tree=ast.parse((Path(root_state)/'runtime/update_guard.py').read_bytes())
        for node in tree.body:
            if (isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='HOME_RESUME_PROTOCOL' for target in node.targets)
                    and isinstance(node.value,ast.Constant) and type(node.value.value) is int and node.value.value==1):
                return
        raise ValueError('Home-resume compatible Root runtime required; migrate from computer first')

    def fetch(self, method, payload=None, binary=False):
        if method not in ('offer','verify','package'):raise ValueError('Invalid verifier operation')
        result=subprocess.run(['/usr/bin/node',str(self.code/'updater/fetch.js'),method],
                              input=json.dumps(payload or {}).encode(),stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,timeout=80,check=True)
        if len(result.stdout)>(32*1024*1024 if binary else 65536):raise ValueError('Oversized verifier response')
        return result.stdout if binary else json.loads(result.stdout)

    def descriptor(self, value, downloaded=False):
        if not isinstance(value,dict):raise ValueError('Missing package descriptor')
        if downloaded or 'proof' in value:
            checked=self.fetch('verify',{'proof':value.get('proof')})
            if any(value.get(k)!=v for k,v in checked.items()):raise ValueError('Saved descriptor mismatch')
        elif value.get('local') is not True:
            raise ValueError('Untrusted previous package')
        return value

    def installed(self):
        raw=safe_bytes(self.installed_root/('usr/palm/applications/'+APP+'/appinfo.json'),limit=65536)
        app=json.loads(raw)
        if app.get('id')!=APP or app.get('type')!='web':raise ValueError('Root application unavailable')
        return {'version':app['version']}

    def offer(self):
        self.integrity()
        candidate=self.fetch('offer')['candidate'];self.descriptor(candidate,True)
        prior=self.store.read('current');installed=self.installed()['version']
        reason='available'
        if tuple(map(int,candidate['version'].split('.')))<=tuple(map(int,installed.split('.'))):reason='current'
        elif not prior or prior.get('version')!=installed:reason='missing-rollback'
        elif not (self.state/'cache'/(prior['sha256']+'.ipk')).is_file():reason='missing-rollback'
        return {'installed':installed,'candidate':candidate,'prior':prior,'canInstall':reason=='available','reason':reason}

    def cached(self, descriptor):
        digest=descriptor.get('sha256','')
        import re
        if not re.fullmatch('[a-f0-9]{64}',digest):raise ValueError('Invalid package digest')
        return self.state/'cache'/(digest+'.ipk')

    def prepare(self, candidate, prior):
        self.integrity();self.descriptor(candidate,True);self.descriptor(prior)
        previous=safe_bytes(self.cached(prior),uid=0);inspect_package(previous,prior)
        # Include decompressed application, cached rollback and filesystem overhead.
        if shutil.disk_usage(self.state).free < candidate['size']+64*1024*1024:raise ValueError('Insufficient space for update and rollback')
        target=self.cached(candidate)
        if os.path.lexists(target):inspect_package(safe_bytes(target,uid=0),candidate)
        else:
            raw=self.fetch('package',{'proof':candidate['proof']},binary=True);inspect_package(raw,candidate)
            fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
            self.sync(target.parent)
        return {'candidate':candidate,'prior':prior}

    @staticmethod
    def sync(path):
        fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:os.fsync(fd)
        finally:os.close(fd)

    def runtime(self, mode, transaction=None):
        from python_binding import command as python_command
        command=[python_command(self.root_state),str(self.root_state/'runtime/cli.py'),mode]
        if transaction is not None:
            import re
            if mode not in ('suspend-update','finish-update','abort-update') or not re.fullmatch('[a-f0-9]{32}',transaction):
                raise ValueError('Invalid runtime update request')
            command.append(transaction)
        result=subprocess.run(command,
                              stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                              timeout=630 if mode in ('restore','suspend-update') else 45,check=True)
        value=json.loads(result.stdout)
        if value.get('returnValue') is not True:raise ValueError('Root recovery operation failed')
        return value.get('result')

    def routing_status(self):
        return self.route_state(self.runtime('status'))

    @staticmethod
    def route_state(status):
        intent=status.get('intent')
        phase=intent.get('phase') if intent else 'disabled'
        effective=status.get('effective',{})
        profiles=effective.get('profiles',{})
        routes=[effective.get('sam_home'),profiles.get('defaultApps',{}).get('categories',{}).get('home'),profiles.get('idleApp',{}).get('appId')]
        active=phase!='disabled' or APP in routes
        safe=not active and routes==['com.webos.app.home']*3 and profiles.get('idleApp',{}).get('support') is True
        return {'active':active,'safe':safe,'intent':intent}

    def reserve_route(self):
        # Import only the pinned runtime whose hashes integrity() just checked.
        self.integrity()
        sys.path.insert(0,str(self.root_state/'runtime'))
        import update_guard
        transaction=self.store.read('transaction')['id']
        update_guard.reserve(transaction,self.root_state)

    def restore_route(self):
        self.reserve_route()
        transaction=self.store.read('transaction')['id']
        if self.runtime('suspend-update',transaction) not in ('absent','restored'):raise ValueError('Root route restoration unconfirmed')
        status=self.runtime('status')
        intent=status.get('intent')
        if intent and intent.get('phase')!='disabled':raise ValueError('Root intent remains enabled')

    def finish(self, transaction):
        if not transaction or transaction.get('phase') not in ('complete','rolled-back','aborted'):return
        with self.store.lock():
            current=self.store.read('transaction')
            if not current or (current['id'],current['phase'])!=(transaction['id'],transaction['phase']):return
            if current.get('homeResumePhase')==current['phase']:return current.get('homeResume')
            try:
                result=self.runtime('abort-update' if current['phase']=='aborted' else 'finish-update',current['id'])
                if not isinstance(result,dict) or result.get('status') not in ('restored','skipped','cancelled','failed','unchanged','attempted'):
                    raise ValueError('Home state restoration unconfirmed')
                current['homeResumePhase']=current['phase']
            except Exception as error:
                result={'status':'failed','error':str(error)[:512]}
            current['homeResume']=result
            self.store.write('transaction',current)
            return result

    def install(self, manifest, on_submit, on_terminal):
        self.descriptor(manifest)
        path=self.cached(manifest);inspect_package(safe_bytes(path,uid=0),manifest)
        from observed_install import install
        result=install(APP,str(path),timeout=180,
                       on_ready=lambda:on_submit({'package':str(path),'version':manifest['version']}),
                       on_accepted=lambda e:self.store.write('installer-accepted',e))
        if result.get('completed') is not True:raise RuntimeError('Installer outcome unknown')
        on_terminal({'success':True,'event':result['event']})

    def repair_registration(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('updater_support_provision',self.code/'provision.py')
        provision=importlib.util.module_from_spec(spec);spec.loader.exec_module(provision)
        snapshot=json.loads(safe_bytes(self.root_state/'ls2-provision-snapshot.json',limit=65536,uid=0))
        if snapshot.get('phase') not in (None,):raise ValueError('Root provisioning is being removed')
        original={key:snapshot['files'][str(path)]['original'] for key,path in provision.FILES.items()}
        planned=provision.plan(original)
        for key,path in provision.FILES.items():
            record=snapshot['files'][str(path)];current=safe_bytes(path,limit=65536,uid=0)
            if hashlib.sha256(planned[key]).hexdigest()!=record['installed_sha256']:raise ValueError('Root registration contract mismatch')
            digest=hashlib.sha256(current).hexdigest()
            if digest not in (record['original_sha256'],record['installed_sha256']):raise ValueError('Root service registration conflict')
            if digest!=record['installed_sha256']:
                provision.write(path,planned[key],record['mode']);os.chown(path,record['uid'],record['gid'])
        provision.refresh()
        if provision.rpc('status').get('root') is not True:raise ValueError('Root recovery service registration not effective')

    def verify_installed(self, manifest):
        hashes=inspect_package(safe_bytes(self.cached(manifest),uid=0),manifest)
        verify_payload(self.installed_root,hashes)
        self.repair_registration();self.integrity()
        if self.installed()['version']!=manifest['version']:raise ValueError('Installed version mismatch')
        return True

    def launch(self):
        from updater.luna import call
        return call('luna://com.webos.applicationManager/launch',{'id':APP})

    @staticmethod
    def now():return time.time()
