import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from cytv import package
ROOT=Path(__file__).resolve().parents[2]

def load(path):
    spec=importlib.util.spec_from_file_location('release_'+path.stem,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

class ReleaseTests(unittest.TestCase):
    def test_final_assets_produce_both_exact_release_sets(self):
        build=load(ROOT/'system-updater/build.py');prepare=load(ROOT/'scripts/prepare-release.py')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp).resolve();payload=path/'payload';payload.mkdir();(payload/'root').mkdir();(payload/'root-updater').mkdir()
            versions={}
            for name,app in build.APPS.items():
                version='1.0.0';versions[name]=version
                files={'usr/palm/applications/'+app+'/appinfo.json':json.dumps({'id':app,'version':version}).encode()}
                if name=='root':
                    for service_file in ('service.js','app-inventory.js','handlers.js','services.json','package.json','activity.json','boot-recover.sh'):files['usr/palm/services/'+app+'.service/'+service_file]=('final '+service_file).encode()
                raw=package.ipk(app,version,files)
                target={'home':'launcher.ipk','helper':'helper.ipk','updater':'updater.ipk','root':'root/root.ipk','root-updater':'root-updater/root-updater.ipk'}[name]
                (payload/target).write_bytes(raw)
            (payload/'root/python_binding.py').write_bytes(b'fixed binding');(payload/'root/python_boot.js').write_bytes(b'fixed boot');(payload/'root/runtime').mkdir();(payload/'root/runtime/cli.py').write_bytes(b'fixed runtime')
            (payload/'root-updater/service.js').write_bytes(b'fixed updater')
            (payload/'root/bundle.json').write_text(json.dumps({'package':'root.ipk','files':{'runtime/cli.py':build.digest(b'fixed runtime'),'python_binding.py':build.digest(b'fixed binding'),'python_boot.js':build.digest(b'fixed boot')}}))
            (payload/'root-updater/bundle.json').write_text(json.dumps({'files':{'service.js':build.digest(b'fixed updater'),'root-updater.ipk':build.digest((payload/'root-updater/root-updater.ipk').read_bytes())}}))
            output=path/'release';manifests=build.prepare_release(payload,output,'v1.0.3','Changes')
            files={p.name:p.read_bytes() for p in output.iterdir()}
            prepare.verify_system_assets(manifests,{'tag':'v1.0.3','versions':versions},files)
            self.assertEqual({c['name'] for c in manifests['root']['components']},{'root','root-updater','root-infrastructure'})
            self.assertEqual({c['name'] for c in manifests['no-root']['components']},{'home','helper','updater'})
            import io,tarfile
            infra=next(c for c in manifests['root']['components'] if c['name']=='root-infrastructure')
            with tarfile.open(fileobj=io.BytesIO(files[infra['url'].rsplit('/',1)[1]]),mode='r:gz') as archive:
                service_files={m.name:archive.extractfile(m).read() for m in archive if m.name.startswith('service/')}
            self.assertEqual(len(service_files),7)
            self.assertEqual(service_files['service/service.js'],b'final service.js')
            self.assertEqual(files['com.gathin.tvhome_1.0.0_all.ipk'],(payload/'launcher.ipk').read_bytes())
            first=manifests['root']['components'][0]['url'].rsplit('/',1)[1]
            with self.assertRaisesRegex(ValueError,'hash'):
                prepare.verify_system_assets(manifests,{'tag':'v1.0.3','versions':versions},{**files,first:b'wrong'})
            with self.assertRaisesRegex(ValueError,'version'):
                prepare.verify_system_assets(manifests,{'tag':'v1.0.3','versions':{**versions,'home':'2.0.0'}},files)
