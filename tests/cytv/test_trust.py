from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import paramiko
from cytv.errors import UserError
from cytv.transport import trusted_host_keys


class TrustTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old, cls.new = paramiko.RSAKey.generate(1024), paramiko.RSAKey.generate(1024)

    def record(self, host, key):
        return f'{host} {key.get_name()} {key.get_base64()}\n'

    def test_existing_cytv_pin_wins_over_changed_global_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            local, global_file = root/'local', root/'global'
            local.write_text(self.record('192.0.2.10', self.old))
            global_file.write_text(self.record('192.0.2.10', self.new))
            keys = trusted_host_keys(local, '192.0.2.10', 22, global_file)
            self.assertTrue(keys.check('192.0.2.10', self.old))
            self.assertFalse(keys.check('192.0.2.10', self.new))

    def test_standard_hashed_entry_is_imported_for_exact_host_and_port_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home/'.ssh').mkdir()
            target = '[192.0.2.10]:2222'
            global_file = home/'.ssh/known_hosts'
            global_file.write_text(self.record(paramiko.HostKeys.hash_host(target), self.old) +
                                   self.record('192.0.2.20', self.new))
            with patch('cytv.transport.Path.home', return_value=home):
                keys = trusted_host_keys(home/'local', '192.0.2.10', 2222)
                other_port = trusted_host_keys(home/'local', '192.0.2.10', 22)
            self.assertTrue(keys.check(target, self.old))
            self.assertIsNone(keys.lookup('192.0.2.20'))
            self.assertIsNone(other_port.lookup('192.0.2.10'))

    def test_revoked_matching_record_is_never_offered_as_first_use(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            global_file = root/'known_hosts'
            global_file.write_text('@revoked ' + self.record('192.0.2.10', self.old))
            with self.assertRaises(UserError):
                trusted_host_keys(root/'local', '192.0.2.10', 22, global_file)

    def test_unrelated_bad_records_and_non_utf8_comments_do_not_block_pinned_tv(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            local, global_file = root/'local', root/'global'
            local.write_text(self.record('192.0.2.10', self.old))
            global_file.write_bytes(b'# legacy comment \xff\n' + b'unrelated.example ssh-rsa corrupt-base64\n')
            keys = trusted_host_keys(local, '192.0.2.10', 22, global_file)
            self.assertTrue(keys.check('192.0.2.10', self.old))

    def test_malformed_matching_record_is_blocked_with_sanitized_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            global_file = root/'known_hosts'
            global_file.write_text('192.0.2.10 ssh-rsa PRIVATE-CORRUPT-KEY\n')
            with self.assertRaises(UserError) as caught:
                trusted_host_keys(root/'local', '192.0.2.10', 22, global_file)
            self.assertNotIn('PRIVATE-CORRUPT-KEY', str(caught.exception))


if __name__ == '__main__':
    unittest.main()
