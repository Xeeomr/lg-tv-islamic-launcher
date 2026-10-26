"""Shipped app artwork must match each platform's declared image sizes."""
import json
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[2]


class BrandAssetsTests(unittest.TestCase):
    def test_webos_manifests_have_valid_and_distinct_app_icons(self):
        icons = []
        for folder in ('launcher', 'native/app', 'updater-app'):
            info = json.loads((ROOT / folder / 'appinfo.json').read_text())
            for field, size in (('icon', 80), ('largeIcon', 130)):
                raw = (ROOT / folder / info[field]).read_bytes()
                self.assertEqual(raw[:8], b'\x89PNG\r\n\x1a\n')
                self.assertEqual(struct.unpack('>II', raw[16:24]), (size, size))
            icons.append((ROOT / folder / info['icon']).read_bytes())
        self.assertEqual(len(set(icons)), 3, 'Home, Helper and Updater must be distinguishable')

    def test_windows_icon_directory_matches_embedded_pngs(self):
        raw = (ROOT / 'assets/icons/installer.ico').read_bytes()
        reserved, kind, count = struct.unpack_from('<HHH', raw)
        self.assertEqual((reserved, kind), (0, 1))
        sizes = []
        for i in range(count):
            width, height, _, _, planes, depth, length, offset = struct.unpack_from('<BBBBHHII', raw, 6 + i * 16)
            png = raw[offset:offset + length]
            self.assertGreaterEqual(offset, 6 + count * 16)
            self.assertEqual(len(png), length)
            self.assertEqual(png[:8], b'\x89PNG\r\n\x1a\n')
            self.assertEqual((planes, depth), (1, 32))
            self.assertEqual(struct.unpack('>II', png[16:24]), (width or 256, height or 256))
            sizes.append(width or 256)
        self.assertEqual(sorted(sizes), [16, 32, 48, 256])
