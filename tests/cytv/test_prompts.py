from pathlib import Path
import tempfile
import unittest

from cytv.prompts import identity_path, confirm, root_credentials, trust_tv


class PromptTests(unittest.TestCase):
    def test_identity_path_accepts_quoted_dragged_file_after_invalid_path(self):
        with tempfile.TemporaryDirectory(prefix='cytv key ') as tmp:
            key = Path(tmp) / 'private key'
            key.write_text('test-only; not a real key')
            answers = iter([str(Path(tmp) / 'missing'), '"' + str(key) + '"'])
            result = identity_path(lambda _: next(answers), lambda _: None)
            self.assertEqual(result, str(key.resolve()))

    def test_confirmation_reprompts_typo_and_accepts_explicit_russian_answer(self):
        answers = iter(['maybe', 'да'])
        self.assertTrue(confirm('Install?', lambda _: next(answers), lambda _: None))
        self.assertFalse(confirm('Install?', lambda _: '', lambda _: None))
        self.assertTrue(confirm('Install?', lambda _: '', lambda _: None, default=True))

    def test_root_credentials_defaults_to_password_and_only_opens_key_picker_on_request(self):
        output = []
        self.assertIsNone(root_credentials(lambda _: '', output.append))
        self.assertNotIn('Drag the private key', '\n'.join(output))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'root-key'
            path.write_text('test-only')
            answers = iter(['2', str(path)])
            self.assertEqual(root_credentials(lambda _: next(answers), output.append), str(path.resolve()))

    def test_first_tv_connection_is_plain_confirmation_with_details_optional(self):
        output = []
        self.assertTrue(trust_tv('192.0.2.10', 22, 'SHA256:test-key', lambda _: 'y', output.append))
        text = '\n'.join(output)
        self.assertIn('192.0.2.10', text)
        self.assertIn('trusted home network', text)
        self.assertNotIn('SHA256:test-key', text)
        answers = iter(['?', 'y'])
        self.assertTrue(trust_tv('192.0.2.10', 22, 'SHA256:test-key', lambda _: next(answers), output.append))
        self.assertIn('SHA256:test-key', '\n'.join(output))
        self.assertTrue(trust_tv('192.0.2.10', 22, 'SHA256:test-key', lambda _: '', output.append))
        self.assertFalse(trust_tv('192.0.2.10', 22, 'SHA256:test-key', lambda _: 'n', output.append))


if __name__ == '__main__':
    unittest.main()
