import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from cytv.app_permissions_remove import SCRIPT

@unittest.skipUnless(os.name == 'posix', 'TV cleanup script requires POSIX filesystem semantics')
class AppPermissionsTests(unittest.TestCase):
    def test_owned_permissions_removed_and_repeat_safe(self):
        self.check()

    def test_foreign_role_preserves_both_files(self):
        self.check(foreign=True)

    def test_package_still_present_preserves_files(self):
        self.check(installed=True)

    def check(self, foreign=False, installed=False):
        scope={'__name__':'test'};exec(SCRIPT,scope)
        app='com.cleanyourtv.root.updater'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()/'bus';base=Path(tmp).resolve()/'apps'
            role=root/'roles.d'/(app+'.app.json');client=root/'client-permissions.d'/(app+'.app.json')
            role.parent.mkdir(parents=True);client.parent.mkdir(parents=True)
            role.write_text(json.dumps({'appId':'foreign' if foreign else app,'type':'regular','allowedNames':[app+'-*'],'trustLevel':'public','permissions':[{'service':app+'-*','outbound':['*']}]}))
            client.write_text(json.dumps({app+'-*':['application.launcher',app+'.service.group']}))
            if installed:(base/'applications'/app).mkdir(parents=True)
            refresh=Mock()
            if foreign or installed:
                with self.assertRaises(ValueError):scope['operate'](root,base,refresh,os.getuid())
                self.assertTrue(role.exists());self.assertTrue(client.exists());refresh.assert_not_called()
            else:
                scope['operate'](root,base,refresh,os.getuid())
                self.assertFalse(role.exists());self.assertFalse(client.exists())
                scope['operate'](root,base,refresh,os.getuid())
