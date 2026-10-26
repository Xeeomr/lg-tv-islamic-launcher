import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cytv.tv import Inventory, SSAP
from cytv.errors import TVNotReady, TVConnectionError


class InventoryTests(unittest.TestCase):
    def test_fresh_inventory_uses_local_fallback_and_never_fetches_foreign_urls(self):
        requests = []
        inventory = Inventory('192.0.2.10', b'fallback-png', lambda url: requests.append(url) or b'png')
        result = inventory.build([
            {'id': 'youtube', 'title': 'YouTube', 'icon': 'http://192.0.2.10:3000/icon.png'},
            {'id': 'foreign', 'title': 'Foreign', 'icon': 'http://example.com/icon.png'},
            {'id': 'hidden', 'title': 'Hidden', 'hidden': True},
            {'id': 'no-icon', 'title': 'No icon'},
        ], [{'appId': 'com.webos.app.hdmi1', 'id': 'HDMI_1'}])
        self.assertEqual(requests, ['http://192.0.2.10:3000/icon.png'])
        self.assertEqual([a['id'] for a in result['apps']], ['youtube', 'foreign', 'no-icon'])
        self.assertEqual(result['apps'][1]['icon'], 'data:image/png;base64,ZmFsbGJhY2stcG5n')
        self.assertEqual(result['inputs'], [{'appId': 'com.webos.app.hdmi1', 'label': 'HDMI_1'}])

    def test_ssap_rejects_error_instead_of_empty_success(self):
        session = object.__new__(SSAP)
        session.counter = 0
        class Socket:
            def send(self, data):
                self.request = json.loads(data)
            def recv(self, timeout):
                return json.dumps({'id': self.request['id'], 'type': 'error', 'error': 'denied'})
        session.ws = Socket()
        with self.assertRaisesRegex(RuntimeError, 'permission'):
            session.call('ssap://com.webos.applicationManager/listLaunchPoints')

    def test_standby_close_before_register_is_actionable_and_closes_socket(self):
        from websockets.exceptions import ConnectionClosedError
        from websockets.frames import Close
        class Socket:
            closed = False
            def send(self, data):
                raise ConnectionClosedError(Close(1008, 'Try Again Later (EWS)'), Close(1008, 'Try Again Later (EWS)'), True)
            def close(self): self.closed = True
        socket = Socket()
        with tempfile.TemporaryDirectory() as tmp, \
             patch('websockets.sync.client.connect', return_value=socket), \
             self.assertRaises(TVNotReady) as caught:
            with SSAP('192.0.2.10', tmp, lambda _: None):
                self.fail('Sleeping TV must not register')
        self.assertTrue(socket.closed)
        self.assertEqual(caught.exception.close_code, 1008)
        self.assertEqual(caught.exception.reason_code, 'tv-not-ready')
        self.assertIn('remote', str(caught.exception))

    def test_pairing_timeout_and_other_policy_closes_do_not_become_standby_retry(self):
        from websockets.exceptions import ConnectionClosedError
        from websockets.frames import Close
        class Socket:
            def send(self, data): pass
            def recv(self, timeout): raise TimeoutError
            def close(self): self.closed = True
        socket = Socket()
        with tempfile.TemporaryDirectory() as tmp, patch('websockets.sync.client.connect', return_value=socket), \
             self.assertRaisesRegex(TVConnectionError, 'pairing request'):
            with SSAP('192.0.2.10', tmp, lambda _: None): pass
        self.assertTrue(socket.closed)
        class Denied(Socket):
            def send(self, data):
                raise ConnectionClosedError(Close(1008, 'PRIVATE-REMOTE-TEXT'), Close(1008, ''), True)
        with tempfile.TemporaryDirectory() as tmp, patch('websockets.sync.client.connect', return_value=Denied()), \
             self.assertRaises(TVConnectionError) as caught:
            with SSAP('192.0.2.10', tmp, lambda _: None): pass
        self.assertNotIsInstance(caught.exception, TVNotReady)
        self.assertNotIn('PRIVATE-REMOTE-TEXT', str(caught.exception))


if __name__ == '__main__':
    unittest.main()
