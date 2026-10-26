import importlib.util
from pathlib import Path
import unittest
import json
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


class CIScope(unittest.TestCase):
    def test_manual_draft_build_produces_installers_without_claiming_acceptance(self):
        spec = importlib.util.spec_from_file_location('ci_scope', ROOT/'scripts/ci-scope.py')
        scope = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scope)
        plan = {'version': '1.1.0', 'acceptance': ''}
        event = {'inputs': {'test_build': 'true'}}
        self.assertTrue(scope.build_installers(event, 'workflow_dispatch',
            'refs/heads/release/next', plan, '1.1.0', '1.0.3', True))
        self.assertFalse(scope.is_candidate(plan, '1.1.0', '1.0.3'))
        for kind, ref, inputs, version, notes in (
            ('push', 'refs/heads/release/next', event, '1.1.0', True),
            ('pull_request', 'refs/heads/release/next', event, '1.1.0', True),
            ('workflow_dispatch', 'refs/heads/main', event, '1.1.0', True),
            ('workflow_dispatch', 'refs/heads/feature', event, '1.1.0', True),
            ('workflow_dispatch', 'refs/heads/release/next', {}, '1.1.0', True),
            ('workflow_dispatch', 'refs/heads/release/next', {'inputs': {'test_build': 'false'}}, '1.1.0', True),
            ('workflow_dispatch', 'refs/heads/release/next', event, '1.0.3', True),
            ('workflow_dispatch', 'refs/heads/release/next', event, '1.1.0', False),
        ):
            with self.subTest(kind=kind, ref=ref, inputs=inputs, version=version, notes=notes):
                self.assertFalse(scope.build_installers(inputs, kind, ref, plan, version, '1.0.3', notes))

    def test_event_diff_handles_documentation_renames_and_full_release_tests(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, text=True).strip()
            git('init', '-b', 'main')
            git('config', 'user.name', 'CI test')
            git('config', 'user.email', 'ci@example.invalid')
            (root / 'README.md').write_text('before')
            git('add', '.'); git('commit', '-m', 'base')
            base = git('rev-parse', 'HEAD')
            (root / 'README.md').write_text('after')
            git('commit', '-am', 'docs')
            docs = git('rev-parse', 'HEAD')
            event = root / 'event.json'
            output = root / 'output'
            env = {**os.environ, 'GITHUB_EVENT_NAME': 'pull_request', 'GITHUB_REF': 'refs/pull/1/merge',
                   'GITHUB_EVENT_PATH': str(event), 'GITHUB_OUTPUT': str(output), 'CI_FULL_SUITE': 'false'}
            def route(head, full=False):
                event.write_text(json.dumps({'pull_request': {'base': {'sha': base}, 'head': {'sha': head}}}))
                subprocess.check_output(['python3', str(ROOT / 'scripts/ci-scope.py')], cwd=root,
                                        env={**env, 'CI_FULL_SUITE': str(full).lower()})
                return dict(line.split('=') for line in output.read_text().splitlines())
            self.assertEqual(route(docs)['any'], 'false')
            full = route(docs, full=True)
            self.assertTrue(all(full[name] == 'true'
                                for name in ('tv', 'installer', 'android', 'setup', 'preview')))
            (root / 'android').mkdir()
            git('mv', 'README.md', 'android/stage.py')
            git('commit', '-m', 'move doc to runtime code')
            result = route(git('rev-parse', 'HEAD'))
            self.assertEqual(result['android'], 'true')
            self.assertEqual(result['tv'], 'false')

    def test_routes_changes_and_shared_dependencies(self):
        path = ROOT / 'scripts/ci-scope.py'
        self.assertTrue(path.exists(), 'Component routing is missing')
        spec = importlib.util.spec_from_file_location('ci_scope', path)
        scope = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scope)
        cases = [
            (['README.md', 'docs/INSTALL.md', 'android/README.md'], set()),
            (['launcher/app.js'], {'tv', 'installer', 'setup', 'preview'}),
            (['native/service/service.js'], {'tv', 'installer', 'setup'}),
            (['root-edition/ui/main.js'], {'tv', 'installer', 'setup', 'preview'}),
            (['root-edition/preview.py'], {'tv', 'installer', 'setup', 'preview'}),
            (['cytv/transport.py'], {'installer', 'android', 'setup'}),
            (['cytv/desktop.py'], {'installer'}),
            (['android/app/src/main/AndroidManifest.xml'], {'android'}),
            (['preview/settings.html'], {'preview'}),
            (['preview/bridge.js'], {'preview'}),
            (['tests/preview-bridge.cjs'], {'preview'}),
            (['scripts/ci-scope.py'], set(scope.COMPONENTS)),
            (['new-component/main.py'], set(scope.COMPONENTS)),
            (['requirements.txt'], set(scope.COMPONENTS)),
            (['.gitignore'], set(scope.COMPONENTS)),
            (['docs/README.md', 'android/stage.py'], {'android'}),
        ]
        for paths, expected in cases:
            with self.subTest(paths=paths):
                self.assertEqual(scope.components(paths), expected)

    def test_only_final_new_release_is_a_candidate(self):
        path = ROOT / 'scripts/ci-scope.py'
        self.assertTrue(path.exists(), 'Candidate routing is missing')
        spec = importlib.util.spec_from_file_location('ci_scope', path)
        scope = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scope)
        self.assertTrue(scope.is_candidate({'version': '1.0.2', 'acceptance': 'TV passed'}, '1.0.2', '1.0.1'))
        for plan, version, previous in [
            ({'version': None, 'acceptance': ''}, '1.0.1', '1.0.1'),
            ({'version': '1.0.2', 'acceptance': ''}, '1.0.2', '1.0.1'),
            ({'version': '1.0.2', 'acceptance': 'TV passed'}, '1.0.3', '1.0.1'),
            ({'version': '1.0.2', 'acceptance': 'TV passed'}, '1.0.2', '1.0.2'),
            *[({'version': '1.0.2', 'acceptance': value}, '1.0.2', '1.0.1')
              for value in (None, False, 0, {}, [])],
        ]:
            with self.subTest(plan=plan, version=version):
                self.assertFalse(scope.is_candidate(plan, version, previous))
