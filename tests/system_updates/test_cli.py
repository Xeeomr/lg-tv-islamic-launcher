import importlib
import unittest
from test_core import CoreBase, profile

class CliTests(CoreBase):
    def test_rpc_reserves_and_wakes_worker_without_installing(self):
        try:cli=importlib.import_module('system_updater.cli')
        except ModuleNotFoundError:self.fail('detached system worker is missing')
        self.io.integrity=lambda:None;wakes=[]
        result=cli.handle('install',{'edition':'no-root','release':'v1.1.0','profile':profile()},self.store,self.io,wake=lambda:wakes.append(True))
        self.assertEqual(result['phase'],'preparing');self.assertEqual(wakes,[True]);self.assertFalse(any(c.startswith('install:') for c in self.io.calls))
    def test_rpc_rejects_paths_and_edition_confusion(self):
        try:cli=importlib.import_module('system_updater.cli')
        except ModuleNotFoundError:self.fail('detached system worker is missing')
        with self.assertRaises(ValueError):cli.validate_request('install',{'edition':'root','release':'v1.1.0','profile':{},'path':'/tmp/evil'})
        with self.assertRaises(ValueError):cli.validate_request('check',{'edition':'unknown'})

    def test_worker_keeps_the_actual_selected_interpreter(self):
        import sys
        from unittest.mock import patch
        cli=importlib.import_module('system_updater.cli')
        with patch.object(cli.subprocess,'Popen') as spawn:
            cli.spawn_worker()
        self.assertEqual(spawn.call_args.args[0][0],sys.executable)
