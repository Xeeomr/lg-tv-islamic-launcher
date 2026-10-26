import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from cytv import package
ROOT = Path(__file__).resolve().parents[2]

def load(name):
    spec=importlib.util.spec_from_file_location('system_'+name, ROOT/'system-updater'/ (name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def fixture(root):
    for name, app, version in [('launcher','com.gathin.tvhome','1.3.8'),('helper','com.local.nativehome','0.6.18'),('updater','com.cleanyourtv.updater','0.1.6')]:
        files={'usr/palm/applications/'+app+'/appinfo.json':json.dumps({'id':app,'version':version,**({'systemUpdateProtocol':1} if name=='launcher' else {})}).encode()}
        (root/(name+'.ipk')).write_bytes(package.ipk(app,version,files))

class BuildTests(unittest.TestCase):
    def test_baseline_keeps_exact_personalized_packages_and_readback(self):
        build=load('build');setup=load('setup')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp).resolve();fixture(path)
            out=path/'baseline';build.prepare_baseline(path,'no-root',out,release='v1.0.3')
            manifest=setup.verify_baseline(out)
            self.assertEqual([c['name'] for c in manifest['components']],['home','helper','updater'])
            for component in manifest['components']:
                self.assertTrue(component['local'])
                raw=(out/'cache'/component['sha256']).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(),component['sha256'])
                self.assertEqual(raw,(path/({'home':'launcher'}.get(component['name'],component['name'])+'.ipk')).read_bytes())
            next((out/'cache').iterdir()).write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError,'hash'):setup.verify_baseline(out)

    def test_bundle_is_reproducible_independent_and_complete(self):
        build=load('build');setup=load('setup')
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp).resolve()/'a';b=Path(tmp).resolve()/'b';build.build(a);build.build(b)
            self.assertEqual({p.relative_to(a).as_posix():p.read_bytes() for p in a.rglob('*') if p.is_file()}, {p.relative_to(b).as_posix():p.read_bytes() for p in b.rglob('*') if p.is_file()})
            manifest=setup.verify_bundle(a)
            self.assertIn('system_updater/support/store.py',manifest['files'])
            self.assertIn('observed_install.py',manifest['files'])
            self.assertIn('python_binding.py',manifest['files'])
            self.assertIn('python_boot.js',manifest['files'])
            inventory=json.loads((a/'infrastructure-paths.json').read_text())
            self.assertIn('support/python_binding.py',inventory)
            self.assertIn('support/python_boot.js',inventory)
            files=package.data_files((a/'system-updater.ipk').read_bytes())
            service='usr/palm/services/com.cleanyourtv.system.updater.service/'
            self.assertEqual(json.loads(files[service+'services.json'])['id'],'com.cleanyourtv.system.updater.service')
            self.assertNotIn(service+'system_updater/core.py',files)
            permissions=setup.permission_plan()
            self.assertNotIn('*',permissions['client.json'])
            self.assertIn('com.gathin.tvhome-*',permissions['client.json'])

    def test_setup_refuses_existing_state_before_any_effect(self):
        setup=load('setup')
        with tempfile.TemporaryDirectory() as tmp:
            state=Path(tmp)/'state';state.mkdir()
            with self.assertRaisesRegex(FileExistsError,'exists'):
                setup.provision(Path(tmp)/'bundle',Path(tmp)/'baseline',state=state)

    def test_setup_installs_owned_permissions_and_reads_captured_baseline(self):
        build=load('build');setup=load('setup')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp).resolve();payload=path/'payload';payload.mkdir();fixture(payload)
            installed=path/'apps';installed.mkdir();base=path/'ls2';base.mkdir();hooks=path/'hooks';hooks.mkdir()
            for kind in ('services.d','roles.d','client-permissions.d','api-permissions.d'):(base/kind).mkdir()
            for name,app,service in [('launcher','com.gathin.tvhome','com.gathin.tvhome.renewal'),('helper','com.local.nativehome','com.local.nativehome.service'),('updater','com.cleanyourtv.updater','com.cleanyourtv.updater.service')]:
                raw=(payload/(name+'.ipk')).read_bytes();files=package.data_files(raw)
                info=json.loads(next(iter(files.values())))
                files['usr/palm/packages/'+app+'/packageinfo.json']=json.dumps({'id':app,'version':info['version'],'app':app,'services':[service]}).encode()
                files['usr/palm/services/'+service+'/service.js']=b'original bytes'
                for filename,data in files.items():
                    target=installed/filename;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
            mutable=installed/'usr/palm/services/com.local.nativehome.service/state/preferences.json';mutable.parent.mkdir();mutable.write_text('private preferences')
            bundle=path/'bundle';build.build(bundle)
            baseline=setup.snapshot(bundle,'no-root',path/'baseline',installed=installed)
            manifest=setup.verify_baseline(baseline)
            self.assertEqual([c['version'] for c in manifest['components']],['1.3.8','0.6.18','0.1.6'])
            for item in manifest['components']:
                self.assertFalse(any('/state/' in n for n in package.data_files((baseline/'cache'/item['sha256']).read_bytes())))
            def install(app,filename,timeout,on_ready,on_accepted):
                on_ready();on_accepted({'confirmed':True})
                for name,data in package.data_files(Path(filename).read_bytes()).items():
                    target=installed/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                service=setup.SERVICE
                (base/'services.d'/(service+'.service')).write_text('[Luna Service]\nName='+service+'\nExec=/usr/bin/run-js-service -n '+str(installed/'usr/palm/services'/service)+'\n')
                (base/'roles.d'/(service+'.service.json')).write_text(json.dumps({'appId':service,'type':'regular'}))
                (base/'client-permissions.d'/(service+'.service.json')).write_text('{}')
                (base/'api-permissions.d'/(service+'.api.json')).write_text('{}')
            state=path/'state';hook=hooks/'52-system'
            result=setup.provision(bundle,baseline,state=state,installed=installed,base=base,hook=hook,install=install,refresh=lambda:None)
            self.assertTrue(result['installed'])
            self.assertEqual(json.loads((state/'bootstrap.json').read_text())['phase'],'complete')
            self.assertEqual(json.loads((state/'current-no-root.json').read_text()),manifest)
            self.assertEqual((state/'code/system_updater/core.py').stat().st_mode&0o777,0o600)
            self.assertEqual(hook.stat().st_mode&0o777,0o700)
            self.assertIn(str(state/'run-service'),(base/'services.d'/(setup.SERVICE+'.service')).read_text())
            self.assertNotIn('/media/developer/apps',hook.read_text())
            self.assertEqual(mutable.read_text(),'private preferences')
            with self.assertRaises(FileExistsError):setup.provision(bundle,baseline,state=state)

    def test_bootstrap_rejects_ambiguous_legacy_installer_state(self):
        setup=load('setup')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();journal=root/'transaction.json'
            journal.write_text('{"phase":"installing"}')
            with self.assertRaisesRegex(ValueError,'legacy'):setup.require_legacy_idle([journal])
            journal.write_text('{"phase":"complete"}')
            setup.require_legacy_idle([journal])
            journal.write_text('{"status":"recovery-required"}')
            with self.assertRaisesRegex(ValueError,'legacy'):setup.require_legacy_idle([journal])

    def test_host_transfer_contains_only_verified_bundle_inventory(self):
        build=load('build');setup=load('setup')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();bundle=root/'bundle';build.build(bundle)
            (bundle/'private-extra.txt').write_text('local private data')
            transfers=[]
            def run(argv,**kwargs):
                if argv[0]=='scp':
                    paths=[Path(p) for p in argv if Path(p).is_dir()]
                    self.assertEqual(len(paths),1)
                    transfers.extend(p.relative_to(paths[0]).as_posix() for p in paths[0].rglob('*') if p.is_file())
            setup.execute(bundle,None,'test-tv',run=run,edition='root')
            self.assertNotIn('private-extra.txt',transfers)
            self.assertIn('bundle.json',transfers)
            self.assertIn('setup-system-updater.py',transfers)

    def test_old_home_is_rejected_before_baseline_or_state_is_written(self):
        build=load('build');setup=load('setup')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp).resolve();bundle=path/'bundle';build.build(bundle)
            installed=path/'installed';home=installed/'usr/palm/applications/com.gathin.tvhome';home.mkdir(parents=True)
            (home/'appinfo.json').write_text('{"id":"com.gathin.tvhome","version":"1.0.0"}')
            with self.assertRaisesRegex(ValueError,'transition Home'):
                setup.snapshot(bundle,'no-root',path/'baseline',installed=installed)
            self.assertFalse((path/'baseline').exists())

    def test_lockdown_disables_only_legacy_mutation_and_updates_owned_receipts(self):
        setup=load('setup')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();base=root/'ls2';(base/'api-permissions.d').mkdir(parents=True)
            state=root/'state';state.mkdir();updater=root/'root-updater';updater.mkdir()
            api=base/'api-permissions.d/com.cleanyourtv.updater.permissions.json'
            methods=['com.cleanyourtv.updater.service/'+m for m in ('check','install','rollback','reconcile','healthy')]+['org.webosbrew.hbchannel.service/install']
            original=json.dumps({'legacy':methods})+'\n';api.write_text(original)
            entries=[]
            for folder in ('api-permissions.d','client-permissions.d','manifests.d'):
                path=base/folder/'com.cleanyourtv.updater.permissions.json';path.parent.mkdir(exist_ok=True)
                if path!=api:path.write_text('{}')
                raw=path.read_text();entries.append({'path':str(path),'content':raw,'sha256':hashlib.sha256(raw.encode()).hexdigest()})
            ownership=base/'com.cleanyourtv.updater.permissions.receipt.json';ownership.write_text(json.dumps({'schema':1,'files':entries}))
            root_api=base/'api-permissions.d/com.cleanyourtv.root.updater.service.api.json'
            root_api.write_text(json.dumps({'root':['com.cleanyourtv.root.updater.service/'+m for m in ('check','status','install','rollback','reconcile','restoreProfile','ready','confirm')]}))
            registration=updater/'registration.json';registration.write_text(json.dumps({'files':{str(root_api):{'original':'{}','installed':root_api.read_text()}}}))
            setup.apply_legacy_lockdown(state,bases=[base],root_updater=updater)
            remaining=json.loads(api.read_text())['legacy'];self.assertEqual(remaining,['com.cleanyourtv.updater.service/check','com.cleanyourtv.updater.service/healthy'])
            self.assertEqual(json.loads(root_api.read_text())['root'],['com.cleanyourtv.root.updater.service/check','com.cleanyourtv.root.updater.service/status','com.cleanyourtv.root.updater.service/restoreProfile'])
            self.assertEqual(json.loads(registration.read_text())['files'][str(root_api)]['installed'],root_api.read_text())
            self.assertEqual(next(e for e in json.loads(ownership.read_text())['files'] if e['path']==str(api))['content'],api.read_text())
            receipt=json.loads((state/'legacy-lockdown.json').read_text());self.assertEqual(receipt['files'][str(api)]['original'],original)
            api.write_text('conflict')
            with self.assertRaisesRegex(ValueError,'changed'):setup.apply_legacy_lockdown(state,bases=[base],root_updater=updater)

    def test_bootstrap_requires_legacy_root_home_resume_receipt(self):
        from unittest.mock import patch
        setup=load('setup')
        with tempfile.TemporaryDirectory() as tmp:
            journal=Path(tmp).resolve()/'transaction.json';journal.write_text('{"schema":1,"phase":"complete"}')
            with patch.object(setup,'ROOT_UPDATER_TRANSACTION',journal,create=True):
                with self.assertRaisesRegex(ValueError,'legacy Root Home'):setup.require_legacy_idle([journal])
                journal.write_text('{"schema":1,"phase":"complete","homeResumePhase":"complete"}')
                setup.require_legacy_idle([journal])

    def test_missing_pinned_infrastructure_is_explicit_and_cannot_expand_destinations(self):
        from unittest.mock import patch
        build=load('build');setup=load('setup')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();bundle=root/'bundle';build.build(bundle)
            names=json.loads((bundle/'infrastructure-paths.json').read_text())
            roots={kind:root/kind for kind in ('runtime','updater','service')}
            missing={'updater/updater/ca-bundle.crt','updater/updater/ca-LICENSE.txt'}
            self.assertTrue(missing<=set(names))
            for name in names:
                if name in missing:continue
                kind,relative=name.split('/',1);path=(roots['runtime'].parent if kind=='support' else roots[kind])/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(name.encode())
            files,absent=setup.capture_infrastructure(names,**roots)
            self.assertEqual(set(absent),missing);self.assertEqual(set(files)|set(absent),set(names))
            installed=root/'installed'
            for kind,app in (('root','com.cleanyourtv.root.preview'),('root-updater','com.cleanyourtv.root.updater')):
                appdir=installed/'usr/palm/applications'/app;appdir.mkdir(parents=True)
                (appdir/'appinfo.json').write_text(json.dumps({'id':app,'version':'1.0.0','systemUpdateProtocol':1,'main':'index.html'}));(appdir/'index.html').write_text('Home')
                package_dir=installed/'usr/palm/packages'/app;package_dir.mkdir(parents=True);(package_dir/'packageinfo.json').write_text(json.dumps({'id':app,'app':app,'version':'1.0.0','services':[app+'.service']}))
                service_dir=installed/'usr/palm/services'/(app+'.service');service_dir.mkdir(parents=True);(service_dir/'service.js').write_text('service')
            baseline=setup.snapshot(bundle,'root',root/'baseline',installed=installed,**roots)
            manifest=setup.verify_baseline(baseline,bundle)
            captured=next(c for c in manifest['components'] if c['name']=='root-infrastructure')
            self.assertEqual(set(captured['absent']),missing)
            self.assertEqual(set(captured['files']),set(names)-missing)
            captured['absent'].append('runtime/arbitrary.py');(baseline/'baseline.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,'pinned bootstrap inventory'):setup.verify_baseline(baseline,bundle)
            descriptor={'kind':'infrastructure','files':{n:hashlib.sha256(b).hexdigest() for n,b in files.items()},'absent':absent}
            setup.verify_infrastructure_inventory(descriptor,files,names)
            with self.assertRaisesRegex(ValueError,'inventory'):
                setup.verify_infrastructure_inventory({**descriptor,'absent':absent+['runtime/arbitrary.py']},files,names)
            with self.assertRaisesRegex(ValueError,'inventory'):
                setup.verify_infrastructure_inventory({**descriptor,'absent':absent+absent},files,names)
            target=roots['updater']/'updater/ca-bundle.crt';target.symlink_to(root/'nonexistent')
            with self.assertRaisesRegex(ValueError,'Indirect'):setup.capture_infrastructure(names,**roots)
