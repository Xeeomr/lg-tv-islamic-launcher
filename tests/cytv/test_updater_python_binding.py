"""Both updater subprocess paths preserve the selected Python binding."""
import importlib
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'root-edition'))

class UpdaterBindingTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'posix', 'TV updater requires fcntl')
    def test_root_updater_worker_keeps_actual_interpreter(self):
        cli=importlib.import_module('updater.cli')
        selected='/var/lib/clean-your-tv-python/4a71641c8d5536175e404a961624e8656eba30e97b5026f6bd7dc31e4bbeaaea/bin/python3.13'
        with patch.object(sys,'executable',selected),patch.object(cli.subprocess,'Popen') as spawn:
            cli.spawn_worker()
        self.assertEqual(spawn.call_args.args[0][0],selected)
    def test_root_device_runtime_uses_persisted_launcher(self):
        from updater.device import Device
        from types import SimpleNamespace
        selected='/var/lib/clean-your-tv-root/python-launcher'
        device=Device(SimpleNamespace(root='/var/lib/clean-your-tv-root-updater'))
        with patch('python_binding.command',return_value=selected),patch('updater.device.subprocess.run',return_value=SimpleNamespace(stdout=b'{"returnValue":true,"result":"restored"}')) as run:
            self.assertEqual(device.runtime('restore'),'restored')
        self.assertEqual(run.call_args.args[0][0],selected)
