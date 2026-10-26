"""Large optional assets use bounded SSH chunks and the existing digest receipt."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from cytv.errors import UserError
from cytv.transport import SSH


class FileUploadTests(unittest.TestCase):
    def test_streams_file_and_requires_verified_receipt(self):
        class Channel:
            def __init__(self): self.sent = []; self.closed = False; self.eof = False
            def settimeout(self, timeout): pass
            def sendall(self, data): self.sent.append(data)
            def shutdown_write(self): self.eof = True
            def close(self): self.closed = True

        with tempfile.TemporaryDirectory() as tmp:
            data = b'cytv' * 200000
            source = Path(tmp) / 'runtime.tar.gz'
            source.write_bytes(data)
            for reply in (b'CYTV_UPLOAD_OK', b'UNCONFIRMED'):
                with self.subTest(reply=reply):
                    channel, commands = Channel(), []
                    ssh = SSH(None)
                    ssh.channel = lambda command: commands.append(command) or channel
                    ssh.chunks = lambda connection, timeout: [reply]
                    if reply == b'CYTV_UPLOAD_OK':
                        ssh.upload_file('/private/runtime.tar.gz', source, timeout=600)
                    else:
                        with self.assertRaises(UserError):
                            ssh.upload_file('/private/runtime.tar.gz', source, timeout=600)
                    self.assertEqual(b''.join(channel.sent), data)
                    self.assertLessEqual(max(map(len, channel.sent)), 256 * 1024)
                    self.assertIn(hashlib.sha256(data).hexdigest(), commands[0])
                    self.assertTrue(channel.eof)
                    self.assertTrue(channel.closed)

    def test_rejects_symlink_source_before_opening_remote_channel(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'source'
            source.write_bytes(b'cytv')
            link = Path(tmp) / 'link'
            link.symlink_to(source)
            ssh = SSH(None)
            ssh.channel = lambda command: self.fail('Opened remote channel for indirect file')
            with self.assertRaises(ValueError):
                ssh.upload_file('/private/runtime.tar.gz', link)
