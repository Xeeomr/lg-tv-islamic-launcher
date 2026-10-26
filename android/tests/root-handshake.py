"""Loopback-only negative SSH fixture. Never emulates a successful TV install."""
import socket
import os
import paramiko
import time

class RejectPassword(paramiko.ServerInterface):
    def get_allowed_auths(self, username): return 'password'
    def check_auth_none(self, username): return paramiko.AUTH_FAILED
    def check_auth_password(self, username, password): return paramiko.AUTH_FAILED

with socket.socket() as listener:
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    port = int(os.environ.get('CYTV_TEST_SSH_PORT', '32222'))
    listener.bind(('127.0.0.1', port))
    listener.listen(2)
    listener.settimeout(120)
    key = paramiko.RSAKey.generate(2048)
    print(f'Loopback negative SSH fixture ready on {port}', flush=True)
    connection, _ = listener.accept()
    with paramiko.Transport(connection) as transport:
        transport.add_server_key(key)
        transport.start_server(server=RejectPassword())
        deadline = time.monotonic() + 60
        while transport.is_active() and time.monotonic() < deadline:
            time.sleep(.1)
    print('Negative SSH fixture completed; no commands executed.', flush=True)
