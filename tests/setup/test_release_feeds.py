import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('prepare_release', ROOT / 'scripts/prepare-release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)
from cytv.package import ipk
from cytv.package import data_files, read_ar, ar, tgz
import json


def packages(home='1.3.5', root='0.1.9', helper='0.6.16'):
    result = {}
    for kind, app, version in [('home', 'com.gathin.tvhome', home), ('root', 'com.cleanyourtv.root.preview', root), ('helper', 'com.local.nativehome', helper)]:
        result[kind] = ipk(app, version, {'usr/palm/applications/' + app + '/appinfo.json': json.dumps({'id': app, 'version': version}).encode()})
    return result


def build(home='1.3.5', root='0.1.9', helper='0.6.16'):
    return {'tag': 'v0.10.9', 'versions': {'home': home, 'root': root, 'helper': helper}}


class ReleaseFeeds(unittest.TestCase):
    def test_android_preview_metadata_is_validated_separately_from_tv_versions(self):
        values = {'release':'0.10.9','cytv':'0.2.12','home':'1.3.4','helper':'0.6.16',
                  'root':'0.1.8','updater':'0.1.5','android':'0.1.3-preview','android_version_code':4}
        release.validate_versions(values)
        release.validate_versions({k:v for k,v in values.items() if not k.startswith('android')})
        # v0.10.8 provenance predates both the release and Android fields.
        release.validate_versions({k:v for k,v in values.items() if k != 'release' and not k.startswith('android')})
        for key, value in [('android','bad'),('android_version_code',0),('android_version_code',True),('home','invalid')]:
            with self.subTest(key=key,value=value), self.assertRaises(ValueError):
                release.validate_versions({**values,key:value})

    def prepare(self, current=None, prior=None, prior_build=None, rollback=None):
        return release.prepare_manifests('v0.10.9', current or build(), packages(), prior_build or build('1.3.4', '0.1.8'), prior or packages('1.3.4', '0.1.8'), rollback)

    def test_versions_and_hashes_come_from_actual_packages(self):
        manifests, files = self.prepare()
        self.assertEqual(manifests['root']['version'], '0.1.9')
        self.assertEqual(manifests['home']['home'], '1.3.5')
        self.assertEqual(manifests['previous']['home'], '1.3.4')
        self.assertEqual(files['com.gathin.tvhome_1.3.4_all.ipk'], packages('1.3.4', '0.1.8')['home'])
        self.assertEqual(manifests['home']['sha256'], release.digest(packages()['home']))

    def test_stale_package_cannot_be_signed_as_new_version(self):
        with self.assertRaisesRegex(ValueError, 'package version'):
            self.prepare(current=build('1.3.6'))

    def test_incompatible_helper_baseline_stops_release(self):
        with self.assertRaisesRegex(ValueError, 'Helper baseline'):
            self.prepare(prior=packages('1.3.4', '0.1.8', '0.6.15'), prior_build=build('1.3.4', '0.1.8', '0.6.15'))

    def test_changed_bytes_without_version_bump_stop_release(self):
        prior = packages()
        prior['home'] = ipk('com.gathin.tvhome', '1.3.5', {'usr/palm/applications/com.gathin.tvhome/appinfo.json': json.dumps({'id': 'com.gathin.tvhome', 'version': '1.3.5'}).encode(), 'extra.txt': b'changed'})
        with self.assertRaisesRegex(ValueError, 'without version bump'):
            self.prepare(prior=prior, prior_build=build())

    def test_installer_only_release_preserves_older_rollback(self):
        prior = packages()
        rollback = ({'home': '1.3.4', 'helper': '0.6.16'}, packages('1.3.4')['home'])
        manifests, _ = self.prepare(prior=prior, prior_build=build(), rollback=rollback)
        self.assertEqual(manifests['previous']['home'], '1.3.4')

    def test_version_regression_stops_release(self):
        with self.assertRaisesRegex(ValueError, 'regression'):
            self.prepare(prior=packages('1.3.6'), prior_build=build('1.3.6'))

    def test_changed_helper_bytes_without_version_bump_stop_release(self):
        prior = packages('1.3.4', '0.1.8')
        prior['helper'] = ipk('com.local.nativehome', '0.6.16', {'usr/palm/applications/com.local.nativehome/appinfo.json': json.dumps({'id': 'com.local.nativehome', 'version': '0.6.16'}).encode(), 'extra.txt': b'changed'})
        with self.assertRaisesRegex(ValueError, 'without version bump'):
            self.prepare(prior=prior)

    def test_reviewed_permission_only_helper_transition_preserves_exact_home_rollback(self):
        prior_helper = (ROOT/'native/published/com.local.nativehome_0.6.16_arm.ipk').read_bytes()
        helper_files = data_files(prior_helper)
        app = 'usr/palm/applications/com.local.nativehome/'
        repair = (ROOT/'native/app/state-permissions.js').read_bytes()
        helper_files[app+'state-permissions.js'] = repair
        for name in (app+'appinfo.json', 'usr/palm/services/com.local.nativehome.service/package.json',
                     'usr/palm/packages/com.local.nativehome/packageinfo.json'):
            info = json.loads(helper_files[name]); info['version'] = '0.6.17'
            if name == app+'appinfo.json':
                info['iconColor'] = '#241d19'
            helper_files[name] = json.dumps(info).encode()
        prior = packages(); prior['helper'] = prior_helper
        current = packages('1.3.6', '0.1.10', '0.6.17')
        approval = {'from_helper':'0.6.16', 'to_helper':'0.6.17', 'rollback_home':'1.3.5',
                    'rollback_sha256':release.digest(prior['home']),
                    'prior_helper_sha256':release.digest(prior_helper),
                    'state_permissions_sha256':release.digest(repair)}
        executables = {app+n for n in ('detach','relay','resume')}
        def prepare(files=helper_files, approval=approval, raw=None):
            # This approval reproduces the historical permission-only repair.
            # Keep its original tar dates; modern packages require their own approval.
            if raw is None:
                with patch('cytv.package.IPK_MTIME', 0):
                    raw = ipk('com.local.nativehome','0.6.17',files,
                        executable=executables, helper_state=True, architecture='arm')
            candidate = dict(current, helper=raw)
            return release.prepare_manifests('v0.10.10', {'tag':'v0.10.10','versions':{'home':'1.3.6','root':'0.1.10','helper':'0.6.17'}},
                candidate, build(), prior, compatibility=approval)
        manifests, files = prepare()
        self.assertEqual(manifests['previous']['helper'], '0.6.17')
        self.assertEqual(manifests['previous']['home'], '1.3.5')
        self.assertEqual(files['com.gathin.tvhome_1.3.5_all.ipk'], prior['home'])
        for name in (app+'native.js', app+'relay', 'usr/palm/services/com.local.nativehome.service/app-inventory.js'):
            with self.subTest(changed=name), self.assertRaisesRegex(ValueError, 'Helper.*compatibility'):
                prepare(dict(helper_files, **{name:b'unreviewed runtime change'}))
        for field in approval:
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'Helper.*compatibility'):
                prepare(approval=dict(approval, **{field:'wrong'}))
        info = json.loads(helper_files[app+'appinfo.json']); info['requiredACG'] = ['unreviewed.permission']
        with self.assertRaisesRegex(ValueError, 'Helper.*compatibility'):
            prepare(dict(helper_files, **{app+'appinfo.json':json.dumps(info).encode()}))
        with self.assertRaisesRegex(ValueError, 'Helper.*compatibility'):
            prepare(raw=ipk('com.local.nativehome','0.6.17',helper_files,helper_state=True,architecture='arm'))
        parts = read_ar(ipk('com.local.nativehome','0.6.17',helper_files,
                           executable=executables,helper_state=True,architecture='arm'))
        parts['control.tar.gz'] = tgz({'control':b'Package: com.local.nativehome\nVersion: 0.6.17\n',
                                      'postinst':b'#!/bin/sh\nexit 99\n'}, executable={'postinst'})
        with self.assertRaisesRegex(ValueError, 'Helper.*compatibility'):
            prepare(raw=ar(parts))

    def test_tested_runtime_transition_requires_exact_archive_and_rollback_pins(self):
        import gzip
        import hashlib
        prior = packages('1.3.7', '0.1.11', '0.6.17')
        current = packages('1.3.8', '0.1.11', '0.6.18')
        parts = read_ar(current['helper'])
        canonical = ar({n: gzip.decompress(b) if n.endswith('.tar.gz') else b for n, b in parts.items()})
        approval = {'from_helper':'0.6.17', 'to_helper':'0.6.18',
                    'rollback_home':'1.3.7', 'rollback_sha256':release.digest(prior['home']),
                    'prior_helper_sha256':release.digest(prior['helper']),
                    'candidate_archive_sha256':hashlib.sha256(canonical).hexdigest(),
                    'acceptance':'Operator confirmed successful candidate and rollback checks.'}
        def prepare(candidate=current, approved=approval):
            return release.prepare_manifests('v1.0.2',
                {'tag':'v1.0.2','versions':{'home':'1.3.8','root':'0.1.11','helper':'0.6.18'}},
                candidate, build('1.3.7','0.1.11','0.6.17'), prior, compatibility=approved)
        manifests, files = prepare()
        self.assertEqual(manifests['previous']['helper'], '0.6.18')
        self.assertEqual(files['com.gathin.tvhome_1.3.7_all.ipk'], prior['home'])
        for field in approval:
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'Helper.*compatibility'):
                prepare(approved={**approval, field:''})
        recompressed = ar({n: gzip.compress(gzip.decompress(b), compresslevel=1, mtime=123)
                           if n.endswith('.tar.gz') else b for n, b in parts.items()})
        self.assertEqual(prepare(candidate={**current, 'helper':recompressed})[0], manifests)
        changed_modes = data_files(current['helper'])
        with self.assertRaisesRegex(ValueError, 'Helper.*compatibility'):
            prepare(candidate={**current, 'helper':ipk('com.local.nativehome','0.6.18',
                changed_modes, executable=set(changed_modes))})
        changed = data_files(current['helper']); changed['runtime.js'] = b'unreviewed'
        with self.assertRaisesRegex(ValueError, 'Helper.*compatibility'):
            prepare(candidate={**current, 'helper':ipk('com.local.nativehome','0.6.18',changed)})
        parts['control.tar.gz'] = tgz({'control':b'changed installation control'})
        with self.assertRaisesRegex(ValueError, 'Helper.*compatibility'):
            prepare(candidate={**current, 'helper':ar(parts)})
