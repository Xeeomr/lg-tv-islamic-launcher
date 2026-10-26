import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def ar_members(raw):
    assert raw[:8] == b'!<arch>\n'
    members, offset = {}, 8
    while offset < len(raw):
        header = raw[offset:offset + 60]
        size = int(header[48:58])
        members[header[:16].decode().strip().rstrip('/')] = raw[offset + 60:offset + 60 + size]
        offset += 60 + size + size % 2
    return members


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ROOT / 'build.py').exists(), 'Offline package builder is missing')
        spec = importlib.util.spec_from_file_location('root_build', ROOT / 'build.py')
        self.builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.builder)

    def test_candidate_is_deterministic_isolated_and_hashes_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp).resolve() / 'first', Path(tmp).resolve() / 'second'
            self.builder.build(first)
            self.builder.build(second)
            self.assertEqual({str(p.relative_to(first)): p.read_bytes() for p in first.rglob('*') if p.is_file()},
                             {str(p.relative_to(second)): p.read_bytes() for p in second.rglob('*') if p.is_file()})
            from deploy import verify_bundle
            manifest = verify_bundle(first)
            self.assertIn('runtime/cli.py', manifest['files'])
            self.assertIn('setup.py', manifest['files'])
            ipk = next(first.glob('*.ipk'))
            parts = ar_members(ipk.read_bytes())
            self.assertEqual(set(parts), {'debian-binary', 'control.tar.gz', 'data.tar.gz'})
            self.assertEqual(parts['debian-binary'], b'2.0\n')
            with tarfile.open(fileobj=io.BytesIO(parts['data.tar.gz'])) as archive:
                files = {m.name: archive.extractfile(m).read() for m in archive}
                self.assertTrue(all(m.isfile() and 1577836800 <= m.mtime <= 1767225600 for m in archive))
            prefix = 'usr/palm/applications/com.cleanyourtv.root.preview/'
            self.assertTrue(all(n.startswith(prefix) or n.startswith('usr/palm/services/com.cleanyourtv.root.preview.service/') or n == 'usr/palm/packages/com.cleanyourtv.root.preview/packageinfo.json' for n in files))
            self.assertEqual(json.loads(files[prefix + 'appinfo.json'])['id'], 'com.cleanyourtv.root.preview')
            self.assertEqual(json.loads(files['usr/palm/packages/com.cleanyourtv.root.preview/packageinfo.json'])['services'], ['com.cleanyourtv.root.preview.service'])
            service_prefix = 'usr/palm/services/com.cleanyourtv.root.preview.service/'
            self.assertEqual({n[len(service_prefix):] for n in files if n.startswith(service_prefix)}, {'service.js', 'app-inventory.js', 'handlers.js', 'services.json', 'package.json', 'boot-recover.sh', 'activity.json'})
            with tarfile.open(fileobj=io.BytesIO(parts['data.tar.gz'])) as archive:
                self.assertEqual(archive.getmember(service_prefix + 'boot-recover.sh').mode, 0o755)
            self.assertEqual(files[prefix + 'apps.js'], b'window.TV_APPS = {apps: [], inputs: []};\n')
            self.assertNotIn(prefix + 'user-data.js', files)
            self.assertNotIn(prefix + 'native-bootstrap.js', files)
            with tarfile.open(fileobj=io.BytesIO(parts['control.tar.gz'])) as archive:
                self.assertEqual(archive.getnames(), ['control'])
                self.assertGreaterEqual(archive.getmember('control').mtime, 1577836800)
            release = json.loads((first / 'release.json').read_text())
            self.assertFalse(release['hardware_validated'])
            for name, digest in release['files'].items():
                self.assertEqual(hashlib.sha256(files[name]).hexdigest(), digest)
            self.assertEqual((first / 'SHA256SUMS').read_text(), hashlib.sha256(ipk.read_bytes()).hexdigest() + '  ' + ipk.name + '\n')

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp).resolve() / 'existing'
            output.mkdir()
            (output / 'keep').write_text('user data')
            with self.assertRaises(FileExistsError):
                self.builder.build(output)
            self.assertEqual(list(output.iterdir()), [output / 'keep'])

    def test_versioned_package_and_bootstrap_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp).resolve() / 'candidate'
            package = self.builder.build(output, version='1.2.3')
            self.assertEqual(package.name, 'com.cleanyourtv.root.preview_1.2.3_all.ipk')
            self.assertEqual(json.loads((output / 'release.json').read_text())['version'], '1.2.3')
            with tarfile.open(fileobj=io.BytesIO(ar_members(package.read_bytes())['data.tar.gz'])) as archive:
                prefix = 'usr/palm/applications/com.cleanyourtv.root.preview/'
                self.assertEqual(json.loads(archive.extractfile(prefix + 'appinfo.json').read())['version'], '1.2.3')
                self.assertIn(b'window.ROOT_VERSION = "1.2.3"', archive.extractfile(prefix + 'index.html').read())
            from deploy import verify_bundle
            verify_bundle(output)

    def test_invalid_versions_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            for index, version in enumerate(('1', 'v1.2.3', '1.2.3;id', '01.2.3', '1.2.-1', '1.2.3-beta')):
                output = Path(tmp).resolve() / str(index)
                with self.assertRaises(ValueError):
                    self.builder.build(output, version=version)
                self.assertFalse(output.exists())

    def test_archive_rejects_unsafe_paths(self):
        for name in ('../secret', '/absolute', 'a/../b', 'a//b', './a', 'a\\b', 'a\x00b'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.builder.tgz({name: b'data'})

    def test_service_identity_mismatch_is_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            source = root / 'service'
            source.mkdir()
            for name in self.builder.SERVICE_FILES:
                (source / name).write_bytes((self.builder.SERVICE_SOURCE / name).read_bytes())
            (source / 'services.json').write_text('{"id":"com.gathin.tvhome"}')
            self.builder.SERVICE_SOURCE = source
            with self.assertRaises(ValueError):
                self.builder.build(root / 'candidate')
            self.assertFalse((root / 'candidate').exists())

    def test_output_through_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / 'real').mkdir()
            (root / 'link').symlink_to(root / 'real', target_is_directory=True)
            with self.assertRaises(ValueError):
                self.builder.build(root / 'link' / 'candidate')
            self.assertFalse((root / 'real' / 'candidate').exists())


if __name__ == '__main__':
    unittest.main()
