import hashlib
import importlib.util
import io
from pathlib import Path
import tarfile
import unittest
from cytv import package


class RootRollbackFormatTests(unittest.TestCase):
    def test_personalized_root_is_accepted_by_real_updater_validator(self):
        app = package.ROOT_APP
        prefix = 'usr/palm/applications/' + app + '/'
        files = {prefix+'appinfo.json': ('{"id":"'+app+'","version":"0.1.3","type":"web","main":"index.html"}').encode(),
                 prefix+'index.html': b'<html></html>',
                 'usr/palm/packages/'+app+'/packageinfo.json': ('{"id":"'+app+'","app":"'+app+'","version":"0.1.3","services":[]}').encode()}
        raw, expected = package.personalize(package.ipk(app,'0.1.3',files), app, {'apps':[{'id':'youtube'}], 'inputs':[]})
        path = Path(__file__).resolve().parents[2] / 'root-edition/updater/package.py'
        spec = importlib.util.spec_from_file_location('root_updater_package_check', path)
        validator = importlib.util.module_from_spec(spec); spec.loader.exec_module(validator)
        actual = validator.inspect_package(raw, {'version':'0.1.3','size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
        self.assertEqual(actual, {name:hashlib.sha256(data).hexdigest() for name,data in expected.items()})

    def test_no_root_still_contains_parent_directories(self):
        app='com.gathin.tvhome'
        raw,_=package.personalize(package.ipk(app,'1.3.1',{'usr/palm/applications/'+app+'/index.html':b'home'}),app,{'apps':[{'id':'youtube'}]})
        with tarfile.open(fileobj=io.BytesIO(package.read_ar(raw)['data.tar.gz']),mode='r:gz') as archive:
            self.assertTrue(any(item.isdir() for item in archive))

    def test_root_preflight_rejects_directory_entries(self):
        raw = package.ipk(package.ROOT_APP, '0.1.3', {'usr/palm/applications/'+package.ROOT_APP+'/index.html': b'home'})
        with self.assertRaisesRegex(ValueError, 'rollback'):
            package.verify_root_rollback_format(raw)
        fixed, _ = package.personalize(raw, package.ROOT_APP, {'apps':[{'id':'youtube'}]})
        package.verify_root_rollback_format(fixed)
