"""Read-only connection hints. An SSH listener alone never proves root access."""
from concurrent.futures import ThreadPoolExecutor
import socket
import time


def ssh_available(host, port, timeout=1.2):
    deadline = time.monotonic() + timeout
    try:
        with socket.create_connection((host, port), timeout=timeout) as connection:
            data = bytearray()
            while len(data) < 1024 and time.monotonic() < deadline:
                connection.settimeout(max(0.001, deadline - time.monotonic()))
                part = connection.recv(1024 - len(data))
                if not part:
                    break
                data.extend(part)
                if any(line.startswith((b'SSH-2.0-', b'SSH-1.99-')) for line in data.split(b'\n')[:-1]):
                    return True
    except OSError:
        pass
    return False


def inspect(host, port=None):
    root_port = port or 22
    if root_port == 9922:
        # This explicitly selected endpoint is the normal Developer Mode port.
        # Base the current choice on the port we will actually connect to.
        return {'root_ssh': False, 'developer_ssh': ssh_available(host, 9922), 'root_port': root_port}
    with ThreadPoolExecutor(max_workers=2) as pool:
        root = pool.submit(ssh_available, host, root_port)
        developer = pool.submit(ssh_available, host, 9922)
        return {'root_ssh': root.result(), 'developer_ssh': developer.result(), 'root_port': root_port}
