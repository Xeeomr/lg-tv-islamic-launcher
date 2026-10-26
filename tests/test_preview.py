"""Run with: python3 -m unittest discover -s tests -p test_preview.py"""
import importlib.util
from html.parser import HTMLParser
import json
from pathlib import Path
import threading
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class PreviewTest(unittest.TestCase):
    def test_static_export_works_under_a_github_pages_project_path(self):
        spec = importlib.util.spec_from_file_location('preview', ROOT / 'scripts/preview.py')
        preview = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(preview)
        self.assertTrue(hasattr(preview, 'export_site'), 'static Pages export is missing')

        class Resources(HTMLParser):
            def __init__(self):
                super().__init__()
                self.urls = []

            def handle_starttag(self, tag, attrs):
                for key, value in attrs:
                    if key in ('src', 'href') and not value.startswith('data:'):
                        self.urls.append(value)

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'clean-your-tv-lg-webos'
            preview.export_site(output)
            for page in ['index.html', 'launcher/index.html', 'root-launcher/index.html']:
                resources = Resources()
                resources.feed((output / page).read_text())
                self.assertTrue(resources.urls)
                for resource in resources.urls:
                    url = urljoin('/clean-your-tv-lg-webos/' + page, resource)
                    self.assertTrue(url.startswith('/clean-your-tv-lg-webos/'), url)
                    self.assertTrue((Path(directory) / url.lstrip('/')).is_file(), url)
            apps = json.loads((output / 'launcher/apps.js').read_text().removeprefix('window.TV_APPS = ').rstrip(';\n'))
            for app in apps['apps']:
                self.assertTrue(app['id'].startswith('preview.'))
                url = urljoin('/clean-your-tv-lg-webos/launcher/index.html', app['icon'])
                self.assertTrue(url.startswith('/clean-your-tv-lg-webos/preview/icons/'))
                self.assertTrue((Path(directory) / urlsplit(url).path.lstrip('/')).is_file())
            self.assertTrue((output / 'launcher/fonts/outfit.ttf').is_file())
            self.assertTrue((output / 'root-launcher/root-settings.js').is_file())
            self.assertFalse((output / 'root-launcher/native-bootstrap.js').exists())
            self.assertFalse((output / 'root-launcher/renewal-panel.js').exists())
            self.assertFalse((output / '.lgtv-key.json').exists())
            self.assertFalse((output / 'scripts').exists())

    def test_preview_serves_launcher_without_exposing_workspace(self):
        script = ROOT / 'scripts/preview.py'
        self.assertTrue(script.is_file(), 'local preview server is not implemented')
        spec = importlib.util.spec_from_file_location('preview', script)
        preview = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(preview)
        server = preview.make_server(0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = 'http://127.0.0.1:' + str(server.server_port)
        try:
            def get(path):
                with urlopen(base + path) as response:
                    self.assertEqual(response.headers['Cache-Control'], 'no-store')
                    return response.read().decode()

            self.assertIn('launcher/index.html', get('/'))
            root = get('/root-launcher/index.html')
            self.assertIn('root-settings.js', root)
            self.assertNotIn('native-bootstrap.js', root)
            self.assertNotIn('profile-bootstrap.js', root)
            self.assertEqual(json.loads(get('/root-launcher/apps.js').removeprefix('window.TV_APPS = ').rstrip(';\n'))['apps'][0]['id'], 'preview.youtube')
            page = get('/launcher/index.html')
            self.assertLess(page.index('/preview/bridge.js'), page.index('profile-bootstrap.js'))
            self.assertEqual(get('/launcher/style.css'), (ROOT / 'launcher/style.css').read_text())
            apps = json.loads(get('/launcher/apps.js').removeprefix('window.TV_APPS = ').rstrip(';\n'))
            self.assertGreaterEqual(len(apps['apps']), 10)
            for app in apps['apps']:
                self.assertTrue(app['icon'].startswith('../preview/icons/'))
                with urlopen(urljoin(base + '/launcher/index.html', app['icon'])) as response:
                    self.assertEqual(response.headers['Content-Type'], 'image/svg+xml')
                    icon = ET.fromstring(response.read())
                    self.assertEqual(icon.attrib['viewBox'], '0 0 720 404')
                    self.assertFalse(any(node.tag.endswith('}image') for node in icon.iter()))
            # A saved source must change the version; unchanged sources must not.
            with tempfile.TemporaryDirectory() as directory, patch.object(preview, 'ROOT', Path(directory)):
                style = Path(directory) / 'launcher/style.css'
                style.parent.mkdir()
                style.write_text('body { color: white; }')
                before = get('/preview/version')
                self.assertEqual(get('/preview/version'), before)
                style.write_text('body { color: black; background: white; }')
                self.assertNotEqual(get('/preview/version'), before)
                root_profile = Path(directory) / 'root-edition/ui/root-profile.js'
                root_profile.parent.mkdir(parents=True)
                before_profile = get('/preview/version')
                root_profile.write_text('/* changed Root bootstrap */')
                self.assertNotEqual(get('/preview/version'), before_profile)
            for path in ['/README.md', '/.lgtv-key.json', '/launcher/../config.js',
                         '/launcher/%2e%2e/.env', '/launcher/icons/private.png', '/scripts/build.sh',
                         '/preview/icons/%2e%2e/bridge.js', '/preview/icons/private.png']:
                with self.assertRaises(HTTPError) as error:
                    urlopen(base + path)
                self.assertEqual(error.exception.code, 404)
                error.exception.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
