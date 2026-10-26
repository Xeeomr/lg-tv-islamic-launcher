import socket
import unittest
from unittest.mock import patch

from cytv import inspect_tv


class InspectionTests(unittest.TestCase):
    def test_ssh_banner_is_checked_without_login_or_sending_commands(self):
        class Connection:
            def __enter__(self): return self
            def __exit__(self, *args): self.closed = True
            def settimeout(self, value): pass
            def recv(self, size): return b'SSH-2.0-dropbear_2022.83\r\n'
        connection = Connection()
        with patch.object(inspect_tv.socket, 'create_connection', return_value=connection):
            self.assertTrue(inspect_tv.ssh_available('192.0.2.10', 22))
        self.assertTrue(connection.closed)
        with patch.object(inspect_tv.socket, 'create_connection', side_effect=socket.timeout):
            self.assertFalse(inspect_tv.ssh_available('192.0.2.10', 22))

    def test_root_port_is_recommendation_not_proof_of_root(self):
        with patch.object(inspect_tv, 'ssh_available', side_effect=lambda host, port: port == 22):
            result = inspect_tv.inspect('192.0.2.10')
        self.assertEqual(result, {'root_ssh': True, 'developer_ssh': False, 'root_port': 22})

    def test_nonstandard_root_port_is_probed_when_given(self):
        with patch.object(inspect_tv, 'ssh_available', return_value=False) as probe:
            result = inspect_tv.inspect('192.0.2.10', 2222)
        self.assertEqual(result['root_port'], 2222)
        self.assertEqual({call.args[1] for call in probe.call_args_list}, {2222, 9922})

    def test_explicit_developer_port_does_not_recommend_another_root_endpoint(self):
        with patch.object(inspect_tv, 'ssh_available', return_value=True) as probe:
            result = inspect_tv.inspect('192.0.2.10', 9922)
        self.assertFalse(result['root_ssh'])
        self.assertTrue(result['developer_ssh'])
        self.assertEqual(result['root_port'], 9922)
        probe.assert_called_once_with('192.0.2.10', 9922)

    def test_fragmented_ssh_banner_and_unrelated_service_are_handled(self):
        class Connection:
            def __init__(self, chunks): self.chunks = iter(chunks)
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def settimeout(self, value): pass
            def recv(self, size): return next(self.chunks, b'')
        for chunks, expected in [([b'S', b'SH-2.0-dropbear\r', b'\n'], True),
                                 ([b'HTTP/1.1 200 OK\r\n'], False)]:
            with patch.object(inspect_tv.socket, 'create_connection', return_value=Connection(chunks)):
                self.assertEqual(inspect_tv.ssh_available('192.0.2.10', 22), expected)


if __name__ == '__main__':
    unittest.main()
