import json
import tempfile
import unittest
from unittest.mock import patch
from cytv import diagnostics, state
from cytv.errors import UserError


class HomeDiagnosticsTests(unittest.TestCase):
    def test_collects_one_allowlisted_report_and_stops_recording(self):
        class Remote:
            def __init__(self): self.commands = []
            def upload(self, path, data, mode):
                self.commands.append(json.loads(data))
            def run(self, command):
                session = self.commands[0]['nonce']
                return '\n'.join(json.dumps(x) for x in [
                    {'event':'launch','secret':'PAIRINGKEY'},
                    {'event':'home-diagnostic','session':'old','trigger':'home'},
                    {'event':'home-diagnostic','session':session,'trigger':'started','time':1},
                    {'event':'home-diagnostic','session':session,'trigger':'foreground','foreground':'com.webos.app.home','foregroundAgeMs':0,'secret':'PAIRINGKEY'},
                    {'event':'home-diagnostic','session':session,'trigger':'expired','time':2},
                ])
        with tempfile.TemporaryDirectory() as tmp:
            remote = Remote()
            path = diagnostics.collect_home_report(remote, state.Store(tmp),
                state.target('192.0.2.55', 'no-root'), lambda text: None)
            value = json.loads(path.read_text())
            self.assertTrue(value['helper_diagnostics']['complete'])
            self.assertEqual(len(value['helper_diagnostics']['records']), 3)
            self.assertEqual(len(list(path.parent.glob('*.json'))), 1)
            self.assertNotIn('PAIRINGKEY', path.read_text())
            self.assertEqual(remote.commands[-1]['cmd'], 'diagnostics-stop')

    def test_unsupported_helper_stops_and_explains_without_waiting_a_minute(self):
        class Remote:
            def __init__(self): self.commands=[]
            def upload(self,path,data,mode): self.commands.append(json.loads(data))
            def run(self,command): return '{}'
        with tempfile.TemporaryDirectory() as tmp, patch('time.sleep'), patch('time.monotonic', side_effect=[0,0,1,6]):
            remote=Remote()
            with self.assertRaisesRegex(UserError,'Helper'):
                diagnostics.collect_home_report(remote,state.Store(tmp),state.target('192.0.2.55', 'no-root'),lambda text:None)
            self.assertEqual(remote.commands[-1]['cmd'],'diagnostics-stop')

    def test_cli_action_saves_report_without_installing(self):
        from cytv import cli
        from unittest.mock import MagicMock
        with tempfile.TemporaryDirectory() as tmp, patch('cytv.cli.Installer') as installer, patch('cytv.diagnostics.collect_home_report') as collect:
            collect.return_value = __import__('pathlib').Path(tmp) / 'diagnostic-123456abcdef.json'
            code = cli.main(['home-diagnostics', '--host', '192.0.2.55', '--edition', 'no-root', '--data-dir', tmp, '--language', 'en'],
                            ask=lambda _: 'y', write=lambda _: None, connect=lambda *args: MagicMock())
            self.assertEqual(code, 0)
            collect.assert_called_once()
            installer.return_value.install.assert_not_called()

    def test_cancellation_stops_recording(self):
        class Remote:
            def __init__(self): self.commands=[]
            def upload(self,path,data,mode): self.commands.append(json.loads(data))
            def run(self,command): raise KeyboardInterrupt
        with tempfile.TemporaryDirectory() as tmp:
            remote=Remote()
            with self.assertRaises(KeyboardInterrupt):
                diagnostics.collect_home_report(remote,state.Store(tmp),state.target('192.0.2.55', 'no-root'),lambda text:None)
            self.assertEqual(remote.commands[-1]['cmd'],'diagnostics-stop')
