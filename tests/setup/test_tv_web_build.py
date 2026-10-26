"""Compiler JSON uses UTF-8 independently of the Windows console code page."""
import unittest
from unittest.mock import patch

from scripts.tv_web_build import compile_web


class WebCompilerEncodingTests(unittest.TestCase):
    def test_unicode_assets_survive_a_legacy_windows_text_encoding(self):
        files = {'app.js': 'window.label = "한국어 / Русский";\n'.encode('utf-8')}
        with patch('subprocess._text_encoding', return_value='cp1252'):
            result = compile_web(files)
        self.assertEqual(result['app.js'], files['app.js'])
